import random
import re
import time
from dataclasses import dataclass

from geopy.exc import GeocoderServiceError, GeocoderTimedOut, GeocoderUnavailable
from geopy.geocoders import Nominatim


geolocator = Nominatim(
    user_agent="iphone-vlogify",
    timeout=10,
)

# Nominatim asks clients to stay below one request per second.
MIN_DELAY = 1.1
MAX_RETRIES = 5
BACKOFF_JITTER = 0.3

# Detailed results below this score are compared with a broader result. This
# avoids turning a gate, parking bay, or street address into the final label.
GOOD_LABEL_QUALITY = 70
DETAILED_ZOOM = 18
AREA_ZOOM = 14

_last_call_time = 0


@dataclass(frozen=True)
class GeocodeResult:
    label: str
    quality: int


def _respect_rate_limit():
    global _last_call_time

    elapsed = time.time() - _last_call_time
    if elapsed < MIN_DELAY:
        time.sleep(MIN_DELAY - elapsed)

    _last_call_time = time.time()


def _looks_like_code(value):
    """Return True for gate/bay identifiers such as 89 or D86/87|E86/87."""
    if not value:
        return False

    compact = re.sub(r"\s+", "", str(value))
    if re.fullmatch(r"\d+[A-Za-z]?", compact):
        return True

    return bool(
        re.fullmatch(
            r"[A-Za-z]?\d+[A-Za-z]?(?:[/|&-][A-Za-z]?\d+[A-Za-z]?)+",
            compact,
        )
    )


def _with_context(name, city=None, state=None):
    if not name:
        return None

    folded_name = name.casefold()
    if city:
        if city.casefold() not in folded_name:
            return f"{name}, {city}"
        return name
    if state and state.casefold() not in folded_name:
        return f"{name}, {state}"
    return name


def _airport_area(address):
    for key in ("airport", "suburb", "quarter", "neighbourhood"):
        value = address.get(key)
        if value and any(word in value.casefold() for word in ("airport", "aerodrome", "airfield")):
            return value
    return None


def _format_location_candidate(location):
    raw = getattr(location, "raw", {}) or {}
    address = raw.get("address", {}) or {}
    result_type = (raw.get("type") or raw.get("addresstype") or "").casefold()

    city = (
        address.get("city")
        or address.get("town")
        or address.get("village")
        or address.get("municipality")
    )
    state = address.get("state")
    suburb = address.get("suburb") or address.get("neighbourhood")

    # A detailed airport response is often a gate or parking position. Prefer
    # the named airport area when it is present in the same response.
    aeroway = address.get("aeroway")
    airport_area = _airport_area(address)
    if airport_area and (
        not aeroway
        or _looks_like_code(aeroway)
        or result_type in {"gate", "parking_position", "parking_space", "platform"}
    ):
        return GeocodeResult(_with_context(airport_area, city, state), 100)

    if aeroway:
        quality = 20 if _looks_like_code(aeroway) else 95
        return GeocodeResult(_with_context(aeroway, city, state), quality)

    feature_fields = (
        ("tourism", 90),
        ("attraction", 90),
        ("natural", 90),
        ("historic", 85),
        ("leisure", 78),
        ("amenity", 75),
        ("building", 70),
    )
    for field, quality in feature_fields:
        name = address.get(field)
        if name:
            if _looks_like_code(name):
                quality = 20
            return GeocodeResult(_with_context(name, city, state), quality)

    road = address.get("road")
    house_number = address.get("house_number")
    if road and (city or suburb or state):
        road_name = f"{house_number} {road}" if house_number else road
        if suburb and city:
            label = f"{road_name}, {suburb}, {city}"
        elif city and state:
            label = f"{road_name}, {city}, {state}"
        elif city:
            label = f"{road_name}, {city}"
        else:
            label = f"{road_name}, {state}"

        if house_number:
            quality = 35
        elif result_type in {"path", "footway", "cycleway", "bridleway", "track"}:
            quality = 60
        else:
            quality = 45
        return GeocodeResult(label, quality)

    if suburb and city:
        return GeocodeResult(f"{suburb}, {city}", 75)

    if city and state:
        return GeocodeResult(f"{city}, {state}", 75)
    if city:
        return GeocodeResult(city, 75)

    county = address.get("county")
    if county and state:
        return GeocodeResult(f"{county}, {state}", 45)
    if county:
        return GeocodeResult(county, 45)

    if state:
        return GeocodeResult(state, 35)

    address_line = getattr(location, "address", "") or raw.get("display_name", "")
    fallback = address_line.split(",")[0].strip() if address_line else "Unknown location"
    return GeocodeResult(fallback or "Unknown location", 20)


def _format_location(location):
    """Format a Nominatim location. Kept as a string API for compatibility."""
    return _format_location_candidate(location).label


def label_quality(label):
    """Estimate quality for labels loaded from the string-only location cache."""
    if not label or label == "Unknown location":
        return 0

    primary = label.split(",", 1)[0].strip()
    if _looks_like_code(primary):
        return 20
    if re.match(r"^\d+\s+\S", primary):
        return 35
    if re.search(
        r"\b(?:road|rd|street|st|avenue|ave|drive|dr|boulevard|blvd|highway|hwy|trail|path)\.?$",
        primary,
        flags=re.IGNORECASE,
    ):
        return 50
    return GOOD_LABEL_QUALITY


def _reverse_at_zoom(lat, lon, zoom):
    for attempt in range(MAX_RETRIES):
        try:
            _respect_rate_limit()
            return geolocator.reverse(
                (lat, lon),
                exactly_one=True,
                addressdetails=True,
                namedetails=True,
                zoom=zoom,
            )
        except (GeocoderTimedOut, GeocoderServiceError, GeocoderUnavailable):
            if attempt >= MAX_RETRIES - 1:
                print("⚠️ Geocoder service unavailable or rate limited.")
                print("Continuing with Unknown location for this file.")
                return None

            backoff = (MIN_DELAY * (2 ** attempt)) + random.uniform(0, BACKOFF_JITTER)
            print(
                "⚠️ Geocoder rate limited; backing off "
                f"{backoff:.1f}s (attempt {attempt + 1}/{MAX_RETRIES})"
            )
            time.sleep(backoff)


def reverse_geocode_result(lat, lon):
    detailed_location = _reverse_at_zoom(lat, lon, DETAILED_ZOOM)
    if not detailed_location:
        return GeocodeResult("Unknown location", 0)

    detailed = _format_location_candidate(detailed_location)
    if detailed.quality >= GOOD_LABEL_QUALITY:
        return detailed

    area_location = _reverse_at_zoom(lat, lon, AREA_ZOOM)
    if not area_location:
        return detailed

    area = _format_location_candidate(area_location)
    if area.quality > detailed.quality:
        return area
    return detailed


def reverse_geocode(lat, lon):
    return reverse_geocode_result(lat, lon).label
