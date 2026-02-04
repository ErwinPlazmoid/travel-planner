from __future__ import annotations

from functools import lru_cache
from typing import Any, Dict, Optional

import requests
from django.conf import settings


ARTIC_BASE_URL = "https://api.artic.edu/api/v1"
ARTIC_TIMEOUT_SECONDS = getattr(settings, "ARTIC_TIMEOUT_SECONDS", 5)


class ArticAPIError(Exception):
    """Base exception for Art Institute of Chicago API errors."""


class PlaceNotFoundError(ArticAPIError):
    """Raised when a requested artwork/place does not exist."""


@lru_cache(maxsize=256)
def fetch_artwork_by_id(external_id: int) -> Optional[Dict[str, Any]]:
    """
    Fetch a single artwork from the Art Institute of Chicago API by ID.

    Returns the artwork data dict when found, or None on 404.
    Raises ArticAPIError for non-404 HTTP errors or network issues.
    """
    url = f"{ARTIC_BASE_URL}/artworks/{external_id}"

    try:
        response = requests.get(url, timeout=ARTIC_TIMEOUT_SECONDS)
    except requests.RequestException as exc:  # network / timeout, etc.
        raise ArticAPIError(f"Error calling Artic API: {exc}") from exc

    if response.status_code == 404:
        return None

    if not response.ok:
        raise ArticAPIError(
            f"Unexpected response from Artic API "
            f"(status {response.status_code}): {response.text}"
        )

    payload = response.json()
    return payload.get("data")


def validate_place_exists(external_id: int) -> Dict[str, Any]:
    """
    Validate that a place (artwork) exists in the Art Institute API.

    Returns the artwork data, or raises PlaceNotFoundError if not found.
    """
    artwork = fetch_artwork_by_id(external_id)
    if artwork is None:
        raise PlaceNotFoundError(f"Artwork with id={external_id} was not found.")
    return artwork
