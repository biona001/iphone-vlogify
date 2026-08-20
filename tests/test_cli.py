from pathlib import Path
from datetime import datetime, timedelta

from vlogify import cli


class _FakeCache:
    def __init__(self):
        self.store = {}
        self.set_calls = []

    def get(self, lat, lon):
        return self.store.get((lat, lon))

    def set(self, lat, lon, location):
        self.store[(lat, lon)] = location
        self.set_calls.append((lat, lon, location))


def test_process_file_embeds_when_enabled(monkeypatch, tmp_path):
    input_path = tmp_path / "clip.mov"
    input_path.write_bytes(b"")

    cache = _FakeCache()
    called = {"burn": None}

    def _fake_extract_gps(_):
        return 37.7, -122.4

    def _fake_reverse_geocode(lat, lon):
        assert (lat, lon) == (37.7, -122.4)
        return "San Francisco, CA"

    def _fake_burn_in_text(in_path, out_path, text, corner="bottom-left"):
        called["burn"] = (in_path, out_path, text, corner)

    monkeypatch.setattr(cli, "extract_gps", _fake_extract_gps)
    monkeypatch.setattr(cli, "reverse_geocode", _fake_reverse_geocode)
    monkeypatch.setattr(cli, "burn_in_text", _fake_burn_in_text)

    out_dir = tmp_path / "out"
    cli.process_file(input_path, cache, embed=True, out_dir=out_dir, corner="top-right")

    assert cache.set_calls == [(37.7, -122.4, "San Francisco, CA")]
    assert called["burn"] is not None
    _, out_path, text, corner = called["burn"]
    assert out_path.parent == out_dir
    assert text == "San Francisco, CA"
    assert corner == "top-right"


def test_nearby_weak_label_uses_stronger_label():
    timestamp = datetime(2026, 8, 15, 16, 0)
    weak = cli.LocatedFile(
        Path("weak.mov"),
        51.3272,
        -116.1826,
        timestamp,
        "Larch Valley Trail, Alberta",
        60,
    )
    strong = cli.LocatedFile(
        Path("strong.mov"),
        51.3231,
        -116.1862,
        timestamp + timedelta(minutes=30),
        "Moraine Lake",
        90,
    )

    cli._consolidate_nearby_labels([weak, strong])

    assert weak.label == "Moraine Lake"
    assert strong.label == "Moraine Lake"


def test_nearby_consolidation_preserves_distinct_strong_labels():
    timestamp = datetime(2026, 8, 14, 12, 0)
    first = cli.LocatedFile(
        Path("first.mov"), 51.17, -115.57, timestamp, "Banff Gondola", 90
    )
    second = cli.LocatedFile(
        Path("second.mov"),
        51.171,
        -115.571,
        timestamp + timedelta(minutes=5),
        "Cave and Basin",
        90,
    )

    cli._consolidate_nearby_labels([first, second])

    assert first.label == "Banff Gondola"
    assert second.label == "Cave and Basin"


def test_nearby_consolidation_respects_time_window():
    timestamp = datetime(2026, 8, 14, 12, 0)
    weak = cli.LocatedFile(
        Path("weak.mov"), 51.17, -115.57, timestamp, "201 Banff Avenue", 35
    )
    strong = cli.LocatedFile(
        Path("strong.mov"),
        51.171,
        -115.571,
        timestamp + timedelta(hours=3),
        "Banff Gondola",
        90,
    )

    cli._consolidate_nearby_labels([weak, strong])

    assert weak.label == "201 Banff Avenue"


def test_nearby_consolidation_does_not_chain_through_weak_labels():
    timestamp = datetime(2026, 8, 14, 12, 0)
    strong = cli.LocatedFile(
        Path("strong.mov"), 51.0, -115.0, timestamp, "Known Landmark", 90
    )
    middle = cli.LocatedFile(
        Path("middle.mov"), 51.0, -115.009, timestamp, "Middle Road", 45
    )
    far = cli.LocatedFile(
        Path("far.mov"), 51.0, -115.018, timestamp, "Far Road", 45
    )

    cli._consolidate_nearby_labels([strong, middle, far])

    assert middle.label == "Known Landmark"
    assert far.label == "Far Road"
