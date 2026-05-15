from __future__ import annotations

from pathlib import Path
from typing import Any


# Builds the default counters used by live connector status tracking.
def default_connector_metrics(existing: dict[str, Any] | None = None) -> dict[str, int]:
    seed = existing if isinstance(existing, dict) else {}
    return {
        "poll_count": int(seed.get("poll_count", 0)),
        "total_fetched": int(seed.get("total_fetched", 0)),
        "total_ingested": int(seed.get("total_ingested", 0)),
        "total_duplicates": int(seed.get("total_duplicates", 0)),
        "total_failed": int(seed.get("total_failed", 0)),
    }


# Reads the saved file position so the connector can continue from the last line.
def parse_file_checkpoint(checkpoint: dict[str, Any]) -> tuple[int, int | None]:
    offset_raw = checkpoint.get("offset", 0)
    inode_raw = checkpoint.get("inode")
    offset = int(offset_raw) if isinstance(offset_raw, (int, float, str)) else 0
    inode = int(inode_raw) if isinstance(inode_raw, (int, float, str)) else None
    return max(0, offset), inode


# Creates the checkpoint payload saved after a successful file polling cycle.
def build_file_checkpoint(*, offset: int, inode: int | None) -> dict[str, Any]:
    payload: dict[str, Any] = {"offset": max(0, int(offset))}
    if inode is not None:
        payload["inode"] = int(inode)
    return payload


# Gets the current inode so log rotation can be detected.
def current_file_inode(path: Path) -> int | None:
    try:
        return path.stat().st_ino
    except OSError:
        return None
