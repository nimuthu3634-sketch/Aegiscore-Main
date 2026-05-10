from __future__ import annotations

import os
from typing import Any

import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def fetch_latest_wazuh_indexer_alerts(limit: int = 20) -> list[dict[str, Any]]:
    base_url = os.getenv("WAZUH_INDEXER_URL", "https://host.docker.internal:9200").rstrip("/")
    username = os.getenv("WAZUH_INDEXER_USERNAME", "admin")
    password = os.getenv("WAZUH_INDEXER_PASSWORD", "")
    index = os.getenv("WAZUH_INDEXER_ALERT_INDEX", "wazuh-alerts-*")
    verify_tls = os.getenv("WAZUH_INDEXER_VERIFY_TLS", "false").lower() == "true"

    url = f"{base_url}/{index}/_search"

    query = {
        "size": limit,
        "sort": [
            {
                "timestamp": {
                    "order": "desc"
                }
            }
        ],
        "query": {
            "match_all": {}
        }
    }

    response = requests.get(
        url,
        auth=(username, password),
        json=query,
        verify=verify_tls,
        timeout=10,
    )
    response.raise_for_status()

    data = response.json()
    hits = data.get("hits", {}).get("hits", [])

    alerts = []
    for hit in hits:
        source = hit.get("_source", {})
        source["id"] = hit.get("_id")
        source["_index"] = hit.get("_index")
        alerts.append(source)

    return alerts