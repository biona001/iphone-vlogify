import sys
import time

from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError, GeocoderUnavailable


geolocator = Nominatim(
    user_agent="iphone-vlogify",
    timeout=10
)

# minimum delay between queries (Nominatim rule)
MIN_DELAY = 1.1

_last_call_time = 0


def _respect_rate_limit():
    global _last_call_time

    elapsed = time.time() - _last_call_time
    if elapsed < MIN_DELAY:
        time.sleep(MIN_DELAY - elapsed)

    _last_call_time = time.time()


def _short_name(location):

    addr = location.raw.get("address", {})

    # prefer large meaningful landmarks
    airport = addr.get("aeroway")
    tourism = addr.get("tourism")
    attraction = addr.get("attraction")
    leisure = addr.get("leisure")

    city = (
        addr.get("city")
        or addr.get("town")
        or addr.get("village")
    )

    suburb = addr.get("suburb") or addr.get("neighbourhood")

    # airports
    if airport:
        return f"{airport}, {city}" if city else airport

    # landmarks
    if tourism or attraction or leisure:
        name = tourism or attraction or leisure
        return f"{name}, {city}" if city else name

    # fallback: suburb + city
    if suburb and city:
        return f"{suburb}, {city}"

    # fallback: city
    if city:
        return city

    return location.address.split(",")[0]


def reverse_geocode(lat, lon):

    try:
        location = geolocator.reverse(
            (lat, lon),
            exactly_one=True,
            addressdetails=True
        )

        if not location:
            return "Unknown location"

        addr = location.raw.get("address", {})

        name = (
            addr.get("attraction")
            or addr.get("tourism")
            or addr.get("leisure")
            or addr.get("building")
            or addr.get("amenity")
            or addr.get("suburb")
            or addr.get("neighbourhood")
            or addr.get("city")
            or addr.get("town")
        )

        city = addr.get("city") or addr.get("town") or addr.get("county")

        if name and city and name != city:
            return f"{name}, {city}"

        return name or city or "Unknown location"

    except (GeocoderTimedOut, GeocoderServiceError):

        print("⚠️ Geocoder service unavailable or rate limited.")
        print("Please wait ~30–60 seconds before retrying.")
        raise SystemExit(1)
