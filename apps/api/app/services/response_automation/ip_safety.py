"""Validate candidate IPs for automated ``block_ip`` (built-in ML rule and adapters)."""

from __future__ import annotations

import ipaddress
from typing import TYPE_CHECKING

from app.services.scoring.features import extract_destination_ip

if TYPE_CHECKING:
    from app.core.config import Settings
    from app.models.normalized_alert import NormalizedAlert


# Reads the protected IP list from configuration and normalizes valid IPs.
def parse_protected_ip_csv(raw: str | None) -> frozenset[str]:
    if not raw or not str(raw).strip():
        return frozenset()
    out: set[str] = set()
    for part in str(raw).split(","):
        chunk = part.strip()
        if not chunk:
            continue
        try:
            out.add(str(ipaddress.ip_address(chunk)))
        except ValueError:
            continue
    return frozenset(out)


# Collects victim/infrastructure IPs that should never be blocked automatically.
def collect_infrastructure_ips(alert: NormalizedAlert | None) -> frozenset[str]:
    """IPs representing managed assets / victims — never used as block targets for this rule."""
    ips: set[str] = set()
    if alert is None:
        return frozenset()
    dest = extract_destination_ip(alert)
    if dest:
        try:
            ips.add(str(ipaddress.ip_address(dest.strip())))
        except ValueError:
            pass
    payload = alert.normalized_payload or {}
    asset_ip = payload.get("asset_ip")
    if isinstance(asset_ip, str) and asset_ip.strip():
        try:
            ips.add(str(ipaddress.ip_address(asset_ip.strip())))
        except ValueError:
            pass
    if alert.asset and getattr(alert.asset, "ip_address", None):
        aip = str(alert.asset.ip_address).strip()
        if aip:
            try:
                ips.add(str(ipaddress.ip_address(aip)))
            except ValueError:
                pass
    return frozenset(ips)


# Combines alert context and execution payload IPs for the final safety check.
def infrastructure_ips_for_block(
    alert: NormalizedAlert | None,
    *,
    execution_payload: dict | None = None,
) -> frozenset[str]:
    """Union of DB-linked alert context and execution payload hints (policy runs)."""
    merged: set[str] = set(collect_infrastructure_ips(alert))
    block = execution_payload.get("alert") if isinstance(execution_payload, dict) else None
    if isinstance(block, dict):
        for key in ("destination_ip", "asset_ip"):
            raw = block.get(key)
            if isinstance(raw, str) and raw.strip():
                try:
                    merged.add(str(ipaddress.ip_address(raw.strip())))
                except ValueError:
                    pass
    return frozenset(merged)


# Blocks unsafe network scopes such as loopback, multicast, or broadcast addresses.
def is_forbidden_network_ip(addr: ipaddress.IPv4Address | ipaddress.IPv6Address) -> bool:
    if addr.is_loopback or addr.is_multicast or addr.is_unspecified:
        return True
    if isinstance(addr, ipaddress.IPv4Address) and addr.packed == b"\xff\xff\xff\xff":
        return True
    return False


# Main validation function used before any automated block_ip action runs.
def validate_automated_block_ip_target(
    candidate: str | None,
    *,
    settings: Settings,
    alert: NormalizedAlert | None = None,
    execution_payload: dict | None = None,
) -> tuple[bool, str]:
    """Return (ok, error_message). Empty / invalid / unsafe / protected IPs fail."""
    # Empty, invalid, protected, or infrastructure IPs are rejected.
    if not candidate or not str(candidate).strip():
        return False, "No source IP target was resolved."
    trimmed = str(candidate).strip()
    try:
        addr = ipaddress.ip_address(trimmed)
    except ValueError:
        return False, f"Target '{trimmed}' is not a valid IP address."

    if is_forbidden_network_ip(addr):
        return False, f"Target '{trimmed}' is not eligible for automated blocking (unsafe network scope)."

    normalized_target = str(addr)
    # Protected IPs are configured manually, while infrastructure IPs come from the alert context.
    protected = parse_protected_ip_csv(getattr(settings, "automated_response_protected_ips", None))

    infra = infrastructure_ips_for_block(alert, execution_payload=execution_payload)
    if normalized_target in protected:
        return False, f"Target '{trimmed}' is listed in AUTOMATED_RESPONSE_PROTECTED_IPS."
    if normalized_target in infra:
        return False, f"Target '{trimmed}' matches infrastructure / victim addressing for this alert."

    return True, ""
