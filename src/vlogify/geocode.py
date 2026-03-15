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

    # priority order for nice vlog captions
    name = (
        addr.get("aeroway")
        or addr.get("tourism")
        or addr.get("attraction")
        or addr.get("leisure")
        or addr.get("building")
        or addr.get("amenity")
    )

    city = (
        addr.get("city")
        or addr.get("town")
        or addr.get("village")
    )

    if name and city:
        return f"{name}, {city}"

    if name:
        return name

    if city:
        return city

    return location.address.split(",")[0]


def reverse_geocode(lat, lon):

    try:

        _respect_rate_limit()

        location = geolocator.reverse(
            (lat, lon),
            language="en",
            exactly_one=True
        )

        if not location:
            raise RuntimeError("Geocoder returned no result")

        return _short_name(location)

    except (GeocoderTimedOut, GeocoderUnavailable):
        print(
            "\nERROR: Geocoding service timed out.\n"
            "This usually means the public Nominatim server is overloaded.\n"
            "Please wait a minute and try again.\n"
        )
        sys.exit(1)

    except GeocoderServiceError:
        print(
            "\nERROR: Geocoding service rejected the request.\n"
            "You may have hit the rate limit.\n"
            "Please wait about 60 seconds before retrying.\n"
        )
        sys.exit(1)
