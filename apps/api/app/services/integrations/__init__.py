# Exposes connector constants so other backend files can import them easily.
from app.services.integrations.state import SURICATA_CONNECTOR_KEY, WAZUH_CONNECTOR_KEY

# Controls what is exported from the integrations package.
__all__ = ["WAZUH_CONNECTOR_KEY", "SURICATA_CONNECTOR_KEY"]
