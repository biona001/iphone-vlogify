from geopy.geocoders import Nominatim

geolocator = Nominatim(user_agent="iphone-vlogify")


def reverse_geocode(lat, lon):

    try:
        location = geolocator.reverse((lat, lon), language="en")

        if location:
            return location.address

    except Exception:
        pass

    return "Unknown location"
