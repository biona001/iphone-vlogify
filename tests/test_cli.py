from pathlib import Path

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
