from geopy.geocoders import Nominatim

geolocator = Nominatim(user_agent="iphone-vlogify")


def reverse_geocode(lat, lon):

    try:
        location = geolocator.reverse((lat, lon), language="en")

        if not location:
            return "Unknown location"

        addr = location.raw.get("address", {})

        name = (
            addr.get("tourism")
            or addr.get("attraction")
            or addr.get("leisure")
            or addr.get("building")
            or addr.get("amenity")
        )

        city = addr.get("city") or addr.get("town") or addr.get("village")

        if name and city:
            return f"{name}, {city}"

        if city:
            return city

        return "Unknown location"

    except Exception:
        return "Unknown location"
