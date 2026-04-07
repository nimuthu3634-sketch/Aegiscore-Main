from __future__ import annotations

import asyncio
import base64
import json
import ssl
import time
from datetime import UTC, datetime
from typing import Any
from urllib import parse, request
from urllib.error import HTTPError, URLError

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.db.session import SessionLocal
from app.schemas.ingestion import WazuhConnectorStatusResponse
from app.services.ingestion.service import ingest_wazuh_event
from app.services.integrations.state import (
    WAZUH_CONNECTOR_KEY,
    get_connector_state,
    get_or_create_connector_state,
    mark_connector_error,
    mark_connector_running,
    mark_connector_success,
)


def _coerce_datetime(value: Any) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.astimezone(UTC)
    if isinstance(value, (int, float)):
        return datetime.fromtimestamp(value, UTC)
    if not isinstance(value, str):
        return None

    cleaned = value.strip()
    if not cleaned:
        return None
    if cleaned.endswith("Z"):
        cleaned = cleaned[:-1] + "+00:00"
    if len(cleaned) >= 5 and cleaned[-5] in {"+", "-"} and cleaned[-3] != ":":
        cleaned = f"{cleaned[:-2]}:{cleaned[-2:]}"
    try:
        parsed = datetime.fromisoformat(cleaned)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def _extract_external_id(payload: dict[str, Any]) -> str | None:
    for key in ("id", "_id", "event_id"):
        value = payload.get(key)
        if value not in (None, ""):
            return str(value)
    data = payload.get("data")
    if isinstance(data, dict):
        value = data.get("event_id")
        if value not in (None, ""):
            return str(value)
    return None


def _extract_timestamp(payload: dict[str, Any], field_name: str) -> str | None:
    value = payload.get(field_name)
    if value in (None, "") and isinstance(payload.get("data"), dict):
        value = payload["data"].get(field_name)
    parsed = _coerce_datetime(value)
    if parsed is None:
        return None
    return parsed.isoformat()


def _extract_event_list(response_payload: Any) -> list[dict[str, Any]]:
    if isinstance(response_payload, list):
        return [item for item in response_payload if isinstance(item, dict)]
    if not isinstance(response_payload, dict):
        return []

    candidates: list[Any] = [
        response_payload.get("affected_items"),
        response_payload.get("items"),
    ]
    data = response_payload.get("data")
    if isinstance(data, dict):
        candidates.extend([data.get("affected_items"), data.get("items")])
    elif isinstance(data, list):
        candidates.append(data)

    for candidate in candidates:
        if isinstance(candidate, list):
            return [item for item in candidate if isinstance(item, dict)]
    return []


class WazuhAPIClient:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.base_url = settings.wazuh_base_url.rstrip("/")
        self._cached_token: str | None = None
        self._cached_token_at: float = 0.0

    def _ssl_context(self) -> ssl.SSLContext:
        if not self.settings.wazuh_verify_tls:
            return ssl._create_unverified_context()  # noqa: S323

        context = ssl.create_default_context()
        if self.settings.wazuh_ca_file:
            context.load_verify_locations(cafile=self.settings.wazuh_ca_file)
        return context

    def _basic_auth_header(self) -> str:
        username = self.settings.wazuh_username or ""
        password = self.settings.wazuh_password or ""
        encoded = base64.b64encode(f"{username}:{password}".encode("utf-8")).decode("utf-8")
        return f"Basic {encoded}"

    def _request_json(
        self,
        *,
        method: str,
        path: str,
        headers: dict[str, str],
        params: dict[str, str] | None = None,
    ) -> Any:
        request_path = path if path.startswith("/") else f"/{path}"
        url = f"{self.base_url}{request_path}"
        if params:
            url = f"{url}?{parse.urlencode(params)}"

        req = request.Request(url=url, method=method, headers=headers)
        for attempt in range(self.settings.wazuh_retry_attempts + 1):
            try:
                with request.urlopen(
                    req,
                    timeout=self.settings.wazuh_timeout_seconds,
                    context=self._ssl_context(),
                ) as response:
                    body = response.read().decode("utf-8")
                    return json.loads(body) if body else {}
            except HTTPError as exc:
                detail = exc.read().decode("utf-8", errors="ignore")
                if attempt >= self.settings.wazuh_retry_attempts:
                    raise RuntimeError(
                        f"Wazuh API request failed ({exc.code}) for {request_path}: {detail}"
                    ) from exc
                time.sleep(self.settings.wazuh_retry_backoff_seconds * (attempt + 1))
            except (URLError, TimeoutError, json.JSONDecodeError) as exc:
                if attempt >= self.settings.wazuh_retry_attempts:
                    raise RuntimeError(
                        f"Wazuh API request failed for {request_path}: {exc}"
                    ) from exc
                time.sleep(self.settings.wazuh_retry_backoff_seconds * (attempt + 1))

    def _resolve_bearer_token(self) -> str:
        mode = self.settings.wazuh_auth_mode.lower()
        if mode == "bearer":
            if not self.settings.wazuh_bearer_token:
                raise RuntimeError("WAZUH_BEARER_TOKEN must be set for bearer auth mode.")
            return self.settings.wazuh_bearer_token

        if mode == "token":
            cache_age_seconds = time.time() - self._cached_token_at
            if self._cached_token and cache_age_seconds < 300:
                return self._cached_token

            payload = self._request_json(
                method="GET",
                path=self.settings.wazuh_auth_endpoint,
                headers={
                    "Accept": "application/json",
                    "Authorization": self._basic_auth_header(),
                },
            )
            token: str | None = None
            if isinstance(payload, dict):
                token = payload.get("token")
                data = payload.get("data")
                if token is None and isinstance(data, dict):
                    token = data.get("token")
            if not token:
                raise RuntimeError("Wazuh token auth succeeded but no token was returned.")
            self._cached_token = str(token)
            self._cached_token_at = time.time()
            return self._cached_token

        raise RuntimeError(f"Unsupported Wazuh auth mode: {self.settings.wazuh_auth_mode}")

    def _auth_headers(self) -> dict[str, str]:
        mode = self.settings.wazuh_auth_mode.lower()
        base_headers = {"Accept": "application/json"}
        if mode == "basic":
            if not self.settings.wazuh_username or not self.settings.wazuh_password:
                raise RuntimeError(
                    "WAZUH_USERNAME and WAZUH_PASSWORD must be set for basic auth mode."
                )
            return {**base_headers, "Authorization": self._basic_auth_header()}
        return {**base_headers, "Authorization": f"Bearer {self._resolve_bearer_token()}"}

    def fetch_events(self, *, checkpoint: dict[str, Any]) -> list[dict[str, Any]]:
        page_size = max(1, self.settings.wazuh_page_size)
        max_pages = max(1, self.settings.wazuh_max_pages_per_cycle)
        params_base = {"limit": str(page_size)}
        last_timestamp = checkpoint.get("last_timestamp")
        if isinstance(last_timestamp, str) and last_timestamp:
            params_base[self.settings.wazuh_since_param] = last_timestamp

        events: list[dict[str, Any]] = []
        for page_index in range(max_pages):
            params = {
                **params_base,
                self.settings.wazuh_offset_param: str(page_index * page_size),
            }

            try:
                response_payload = self._request_json(
                    method="GET",
                    path=self.settings.wazuh_alerts_path,
                    headers=self._auth_headers(),
                    params=params,
                )
            except RuntimeError:
                if self.settings.wazuh_auth_mode.lower() != "token":
                    raise
                # Token mode can fail after token expiry. Clear cache and retry this page once.
                self._cached_token = None
                self._cached_token_at = 0.0
                response_payload = self._request_json(
                    method="GET",
                    path=self.settings.wazuh_alerts_path,
                    headers=self._auth_headers(),
                    params=params,
                )

            page_events = _extract_event_list(response_payload)
            if not page_events:
                break
            events.extend(page_events)
            if len(page_events) < page_size:
                break
        return events


def _default_metrics(existing: dict[str, Any] | None = None) -> dict[str, int]:
    seed = existing if isinstance(existing, dict) else {}
    return {
        "poll_count": int(seed.get("poll_count", 0)),
        "total_fetched": int(seed.get("total_fetched", 0)),
        "total_ingested": int(seed.get("total_ingested", 0)),
        "total_duplicates": int(seed.get("total_duplicates", 0)),
        "total_failed": int(seed.get("total_failed", 0)),
    }


def _apply_checkpoint_filter(
    events: list[dict[str, Any]],
    *,
    checkpoint_timestamp: str | None,
    checkpoint_external_ids: set[str],
    timestamp_field: str,
) -> list[dict[str, Any]]:
    if checkpoint_timestamp is None:
        return events

    filtered: list[dict[str, Any]] = []
    for event in events:
        event_timestamp = _extract_timestamp(event, timestamp_field)
        if event_timestamp is None or event_timestamp > checkpoint_timestamp:
            filtered.append(event)
            continue

        if event_timestamp < checkpoint_timestamp:
            continue

        event_external_id = _extract_external_id(event)
        if event_external_id is None or event_external_id not in checkpoint_external_ids:
            filtered.append(event)
    return filtered


def run_wazuh_poll_cycle(
    session: Session,
    *,
    client: WazuhAPIClient | None = None,
) -> dict[str, int]:
    settings = get_settings()
    state = mark_connector_running(session, WAZUH_CONNECTOR_KEY)
    checkpoint = state.checkpoint if isinstance(state.checkpoint, dict) else {}
    metrics = _default_metrics(state.metrics if isinstance(state.metrics, dict) else None)

    checkpoint_timestamp = checkpoint.get("last_timestamp")
    checkpoint_ids = {
        str(value)
        for value in checkpoint.get("last_external_ids", [])
        if isinstance(value, str)
    }
    active_client = client or WazuhAPIClient(settings)
    events = active_client.fetch_events(checkpoint=checkpoint)
    scoped_events = _apply_checkpoint_filter(
        events,
        checkpoint_timestamp=checkpoint_timestamp if isinstance(checkpoint_timestamp, str) else None,
        checkpoint_external_ids=checkpoint_ids,
        timestamp_field=settings.wazuh_timestamp_field,
    )

    latest_timestamp = checkpoint_timestamp if isinstance(checkpoint_timestamp, str) else None
    latest_external_ids = set(checkpoint_ids)
    cycle_ingested = 0
    cycle_duplicates = 0
    cycle_failed = 0

    for event in scoped_events:
        try:
            result = ingest_wazuh_event(session, event, actor=None)
            if result.status == "duplicate":
                cycle_duplicates += 1
            else:
                cycle_ingested += 1
        except HTTPException:
            cycle_failed += 1
            continue

        event_timestamp = _extract_timestamp(event, settings.wazuh_timestamp_field)
        if event_timestamp is None:
            continue

        if latest_timestamp is None or event_timestamp > latest_timestamp:
            latest_timestamp = event_timestamp
            latest_external_ids = {result.external_id}
        elif event_timestamp == latest_timestamp:
            latest_external_ids.add(result.external_id)

    metrics["poll_count"] += 1
    metrics["total_fetched"] += len(events)
    metrics["total_ingested"] += cycle_ingested
    metrics["total_duplicates"] += cycle_duplicates
    metrics["total_failed"] += cycle_failed

    checkpoint_payload = {
        "last_timestamp": latest_timestamp,
        "last_external_ids": sorted(latest_external_ids)[:250],
    }
    mark_connector_success(
        session,
        connector=WAZUH_CONNECTOR_KEY,
        checkpoint=checkpoint_payload,
        metrics=metrics,
    )
    return {
        "fetched": len(events),
        "ingested": cycle_ingested,
        "duplicates": cycle_duplicates,
        "failed": cycle_failed,
    }


async def run_wazuh_connector_forever(stop_event: asyncio.Event) -> None:
    settings = get_settings()
    while not stop_event.is_set():
        with SessionLocal() as session:
            try:
                await asyncio.to_thread(run_wazuh_poll_cycle, session)
            except Exception as exc:  # pragma: no cover - guarded logging branch
                mark_connector_error(
                    session,
                    connector=WAZUH_CONNECTOR_KEY,
                    error_message=str(exc),
                )
        try:
            await asyncio.wait_for(
                stop_event.wait(),
                timeout=max(5, settings.wazuh_poll_interval_seconds),
            )
        except TimeoutError:
            continue


def get_wazuh_connector_status(session: Session) -> WazuhConnectorStatusResponse:
    settings = get_settings()
    state = get_connector_state(session, WAZUH_CONNECTOR_KEY)
    checkpoint = (
        state.checkpoint
        if state is not None and isinstance(state.checkpoint, dict)
        else {}
    )
    metrics = _default_metrics(
        state.metrics if state is not None and isinstance(state.metrics, dict) else None
    )
    return WazuhConnectorStatusResponse(
        connector=WAZUH_CONNECTOR_KEY,
        enabled=settings.wazuh_connector_enabled,
        status=state.status if state is not None else "idle",
        last_success_at=state.last_success_at if state is not None else None,
        last_error_at=state.last_error_at if state is not None else None,
        last_error_message=state.last_error_message if state is not None else None,
        last_checkpoint_timestamp=checkpoint.get("last_timestamp"),
        checkpoint_external_ids=[
            value
            for value in checkpoint.get("last_external_ids", [])
            if isinstance(value, str)
        ],
        metrics=metrics,
    )
