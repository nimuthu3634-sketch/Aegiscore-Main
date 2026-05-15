# Exposes the main ingestion functions so other parts of the API can import them easily.
from app.services.ingestion.parsers import parse_suricata_event, parse_wazuh_event
from app.services.ingestion.service import ingest_suricata_event, ingest_wazuh_event

# Controls what is available when importing from this ingestion package.
__all__ = [
    "ingest_suricata_event",
    "ingest_wazuh_event",
    "parse_suricata_event",
    "parse_wazuh_event",
]
