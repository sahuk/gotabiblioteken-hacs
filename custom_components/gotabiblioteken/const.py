"""Constants for the Götabiblioteken opening-hours integration."""

from __future__ import annotations

from datetime import timedelta

DOMAIN = "gotabiblioteken"

# Götabiblioteken's customer id in the Axiell opening-hours API.
# Fork-friendly: change this to point the integration at another Axiell
# library consortium.
CUSTOMER_ID = "637ce8087143292d469b8c9b"

API_URL = "https://api.axiell.com/openinghours/customers/{customer_id}/openinghours"

# Opening hours change rarely; three hours is plenty and kind to the API.
DEFAULT_SCAN_INTERVAL = timedelta(hours=3)

# How current the "open now" / midnight-rollover calculation stays between
# API refreshes (recomputed locally, no network).
LOCAL_REFRESH_INTERVAL = timedelta(minutes=1)

CONF_BRANCHES = "branches"
