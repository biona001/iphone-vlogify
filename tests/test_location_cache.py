from vlogify.location_cache import LocationCache


def test_location_cache_rounding():
    cache = LocationCache()
    cache.set(37.7749001, -122.4193999, "San Francisco, CA")

    assert cache.get(37.7749, -122.4194) == "San Francisco, CA"
    assert cache.get(37.77491, -122.41939) == "San Francisco, CA"
    assert cache.get(37.7755, -122.4194) is None
