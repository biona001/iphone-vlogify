from pathlib import Path

from vlogify.cli import _normalize_image_output_path, _output_path_for_embed


def test_normalize_image_output_path_keeps_supported():
    path = Path("frame.jpg")
    assert _normalize_image_output_path(path).suffix == ".jpg"


def test_normalize_image_output_path_converts_heic():
    path = Path("frame.heic")
    assert _normalize_image_output_path(path).suffix == ".jpg"


def test_output_path_for_embed_converts_heic(tmp_path):
    input_path = tmp_path / "photo.heic"
    out_dir = tmp_path / "out"
    output_path = _output_path_for_embed(input_path, out_dir)

    assert output_path.parent == out_dir
    assert output_path.suffix == ".jpg"
