from types import SimpleNamespace

from vlogify import geocode
from vlogify.geocode import _format_location, label_quality


def _location(address_dict, address_line="Fallback Address", **raw_values):
    return SimpleNamespace(
        raw={"address": address_dict, **raw_values},
        address=address_line,
    )


def test_format_location_prefers_airport():
    loc = _location({"aeroway": "LAX", "city": "Los Angeles"})
    assert _format_location(loc) == "LAX, Los Angeles"


def test_format_location_replaces_airport_gate_with_airport_area():
    loc = _location(
        {
            "aeroway": "89",
            "suburb": "Calgary International Airport",
            "city": "Calgary",
        },
        type="parking_position",
    )
    assert _format_location(loc) == "Calgary International Airport"


def test_format_location_does_not_repeat_context_already_in_name():
    loc = _location(
        {"tourism": "Honolulu Zoo", "city": "Honolulu", "state": "Hawaii"},
        type="attraction",
    )
    assert _format_location(loc) == "Honolulu Zoo"


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


def test_reverse_geocode_uses_broader_place_for_weak_street(monkeypatch):
    detailed = _location(
        {"house_number": "201", "road": "Banff Avenue", "city": "Banff", "state": "Alberta"},
        type="pedestrian",
    )
    area = _location({"city": "Banff", "state": "Alberta"}, type="administrative")
    calls = []

    def _fake_reverse(_lat, _lon, zoom):
        calls.append(zoom)
        return detailed if zoom == geocode.DETAILED_ZOOM else area

    monkeypatch.setattr(geocode, "_reverse_at_zoom", _fake_reverse)

    result = geocode.reverse_geocode_result(51.17, -115.57)

    assert result.label == "Banff, Alberta"
    assert calls == [geocode.DETAILED_ZOOM, geocode.AREA_ZOOM]


def test_reverse_geocode_keeps_good_landmark_without_extra_query(monkeypatch):
    landmark = _location({"tourism": "Upper Falls", "state": "Alberta"}, type="attraction")
    calls = []

    def _fake_reverse(_lat, _lon, zoom):
        calls.append(zoom)
        return landmark

    monkeypatch.setattr(geocode, "_reverse_at_zoom", _fake_reverse)

    result = geocode.reverse_geocode_result(51.26, -115.83)

    assert result.label == "Upper Falls, Alberta"
    assert calls == [geocode.DETAILED_ZOOM]


def test_label_quality_flags_codes_and_addresses():
    assert label_quality("89, Calgary") < geocode.GOOD_LABEL_QUALITY
    assert label_quality("201 Banff Avenue, Banff") < geocode.GOOD_LABEL_QUALITY
    assert label_quality("Calgary International Airport") >= geocode.GOOD_LABEL_QUALITY
