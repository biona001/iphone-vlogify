import time
import random

from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError, GeocoderUnavailable


geolocator = Nominatim(
    user_agent="iphone-vlogify",
    timeout=10
)

# minimum delay between queries (Nominatim rule)
MIN_DELAY = 1.1
MAX_RETRIES = 5
BACKOFF_JITTER = 0.3

_last_call_time = 0


def _respect_rate_limit():
    global _last_call_time

    elapsed = time.time() - _last_call_time
    if elapsed < MIN_DELAY:
        time.sleep(MIN_DELAY - elapsed)

    _last_call_time = time.time()


def _format_location(location):

    addr = location.raw.get("address", {})

    # prefer meaningful landmarks or venues
    airport = addr.get("aeroway")
    tourism = addr.get("tourism")
    attraction = addr.get("attraction")
    leisure = addr.get("leisure")
    amenity = addr.get("amenity")
    building = addr.get("building")

    city = (
        addr.get("city")
        or addr.get("town")
        or addr.get("village")
    )

    state = addr.get("state")

    suburb = addr.get("suburb") or addr.get("neighbourhood")
    road = addr.get("road")
    house_number = addr.get("house_number")

    # airports
    if airport:
        return f"{airport}, {city}" if city else airport

    # landmarks
    if tourism or attraction or leisure or amenity or building:
        name = tourism or attraction or leisure or amenity or building
        if city:
            return f"{name}, {city}"
        if state:
            return f"{name}, {state}"
        return name

    # street-level (more informative than county)
    if road and (city or suburb or state):
        road_name = f"{house_number} {road}" if house_number else road
        if suburb and city:
            return f"{road_name}, {suburb}, {city}"
        if city and state:
            return f"{road_name}, {city}, {state}"
        if city:
            return f"{road_name}, {city}"
        if state:
            return f"{road_name}, {state}"

    # fallback: suburb + city
    if suburb and city:
        return f"{suburb}, {city}"

    # fallback: city + state
    if city and state:
        return f"{city}, {state}"
    if city:
        return city

    # fallback: state
    if state:
        return state

    return location.address.split(",")[0]


def reverse_geocode(lat, lon):

    for attempt in range(MAX_RETRIES):
        try:
            _respect_rate_limit()
            location = geolocator.reverse(
                (lat, lon),
                exactly_one=True,
                addressdetails=True
            )

            if not location:
                return "Unknown location"

            return _format_location(location)

        except (GeocoderTimedOut, GeocoderServiceError, GeocoderUnavailable):
            if attempt >= MAX_RETRIES - 1:
                print("⚠️ Geocoder service unavailable or rate limited.")
                print("Continuing with Unknown location for this file.")
                return "Unknown location"

            backoff = (MIN_DELAY * (2 ** attempt)) + random.uniform(0, BACKOFF_JITTER)
            print(
                "⚠️ Geocoder rate limited; backing off "
                f"{backoff:.1f}s (attempt {attempt + 1}/{MAX_RETRIES})"
            )
            time.sleep(backoff)
