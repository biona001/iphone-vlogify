from types import SimpleNamespace

from vlogify.geocode import _format_location


def _location(address_dict, address_line="Fallback Address"):
    return SimpleNamespace(raw={"address": address_dict}, address=address_line)


def test_format_location_prefers_airport():
    loc = _location({"aeroway": "LAX", "city": "Los Angeles"})
    assert _format_location(loc) == "LAX, Los Angeles"


def test_format_location_prefers_landmark():
    loc = _location({"tourism": "Golden Gate Bridge", "city": "San Francisco"})
    assert _format_location(loc) == "Golden Gate Bridge, San Francisco"


def test_format_location_road_city_state():
    loc = _location({"road": "Kalākaua Ave", "city": "Honolulu", "state": "HI"})
    assert _format_location(loc) == "Kalākaua Ave, Honolulu, HI"


def test_format_location_city_state_fallback():
    loc = _location({"city": "Honolulu", "state": "HI"})
    assert _format_location(loc) == "Honolulu, HI"


def test_format_location_address_fallback():
    loc = _location({}, address_line="123 Example Street, City")
    assert _format_location(loc) == "123 Example Street"
