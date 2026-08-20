import os
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from functools import lru_cache
from typing import Optional
from pathlib import Path

import ffmpeg
from PIL import ImageFont


SUPPORTED_IMAGE_OUT = {".jpg", ".jpeg", ".png"}
_DRAW_TEXT_OK = None
TEXT_HEIGHT_RATIO = 0.045
MIN_TEXT_HEIGHT_RATIO = 0.037
AVERAGE_GLYPH_WIDTH_RATIO = 0.54
HORIZONTAL_MARGIN = 40
BOX_BORDER_WIDTH = 18
LINE_SPACING_RATIO = 0.010


@dataclass(frozen=True)
class TextLayout:
    lines: tuple[str, ...]
    font_ratio: float
    max_line_width_ratio: float


def _find_font_path():
    env_font = os.getenv("VLOGIFY_FONT_PATH")
    if env_font and Path(env_font).exists():
        return env_font

    candidates = [
        "/System/Library/Fonts/Supplemental/Avenir Next.ttf",
        "/System/Library/Fonts/Supplemental/Futura.ttc",
        "/System/Library/Fonts/Supplemental/Gill Sans.ttc",
        "/System/Library/Fonts/Supplemental/Helvetica Neue.ttc",
        "/Library/Fonts/Arial.ttf",
    ]

    for candidate in candidates:
        if Path(candidate).exists():
            return candidate

    return None


def _escape_drawtext(text: str) -> str:
    return (
        text.replace("\\", "\\\\")
        .replace(":", "\\:")
        .replace("'", "\\'")
    )


def _ensure_drawtext_available():
    global _DRAW_TEXT_OK

    if _DRAW_TEXT_OK is not None:
        return _DRAW_TEXT_OK

    ffmpeg_bin = shutil.which("ffmpeg")
    if not ffmpeg_bin:
        _DRAW_TEXT_OK = False
        return _DRAW_TEXT_OK

    try:
        result = subprocess.run(
            [ffmpeg_bin, "-hide_banner", "-filters"],
            check=False,
            capture_output=True,
            text=True,
        )
    except Exception:
        _DRAW_TEXT_OK = False
        return _DRAW_TEXT_OK

    _DRAW_TEXT_OK = "drawtext" in (result.stdout or "")
    return _DRAW_TEXT_OK


def _convert_heic_with_sips(input_path: Path) -> Optional[Path]:
    sips_bin = shutil.which("sips")
    if not sips_bin:
        return None

    temp_dir = Path(tempfile.mkdtemp(prefix="vlogify_heic_"))
    output_path = temp_dir / f"{input_path.stem}.jpg"

    try:
        subprocess.run(
            [sips_bin, "-s", "format", "jpeg", str(input_path), "--out", str(output_path)],
            check=True,
            capture_output=True,
            text=True,
        )
    except subprocess.CalledProcessError:
        shutil.rmtree(temp_dir, ignore_errors=True)
        return None

    return output_path


def _has_audio(input_path: Path):
    try:
        probe = ffmpeg.probe(str(input_path))
    except FileNotFoundError:
        return None
    except ffmpeg.Error:
        return False

    for stream in probe.get("streams", []):
        if stream.get("codec_type") == "audio":
            return True

    return False


def _video_dimensions(input_path: Path):
    try:
        probe = ffmpeg.probe(str(input_path))
    except (FileNotFoundError, ffmpeg.Error):
        return None

    for stream in probe.get("streams", []):
        if stream.get("codec_type") != "video":
            continue

        try:
            width = int(stream["width"])
            height = int(stream["height"])
        except (KeyError, TypeError, ValueError):
            return None

        rotation = (stream.get("tags") or {}).get("rotate")
        for side_data in stream.get("side_data_list", []):
            if side_data.get("rotation") is not None:
                rotation = side_data["rotation"]
                break

        try:
            rotated_sideways = abs(int(float(rotation))) % 180 == 90
        except (TypeError, ValueError):
            rotated_sideways = False

        if rotated_sideways:
            width, height = height, width

        return width, height

    return None


@lru_cache(maxsize=32)
def _load_measurement_font(font_path: Optional[str], font_size: int):
    try:
        return ImageFont.truetype(font_path or "DejaVuSans.ttf", font_size)
    except OSError:
        return None


def _measure_text(text: str, font_path: Optional[str], font_size: int):
    font = _load_measurement_font(font_path, font_size)
    if font and hasattr(font, "getlength"):
        return float(font.getlength(text))
    return len(text) * font_size * AVERAGE_GLYPH_WIDTH_RATIO


def _split_word_to_width(word, max_width, font_size, measure_text):
    parts = []
    current = ""
    for character in word:
        candidate = current + character
        if current and measure_text(candidate, font_size) > max_width:
            parts.append(current)
            current = character
        else:
            current = candidate
    if current:
        parts.append(current)
    return parts


def _wrap_to_pixel_width(text, max_width, font_size, measure_text):
    words = text.split()
    if not words:
        return [text]

    lines = []
    current = ""
    for word in words:
        candidate = f"{current} {word}" if current else word
        if measure_text(candidate, font_size) <= max_width:
            current = candidate
            continue

        if current:
            lines.append(current)
            current = ""

        if measure_text(word, font_size) <= max_width:
            current = word
            continue

        word_parts = _split_word_to_width(word, max_width, font_size, measure_text)
        lines.extend(word_parts[:-1])
        current = word_parts[-1]

    if current:
        lines.append(current)
    return lines


def _fit_text_layout(text, width, height, font_path=None, measure_text=None):
    """Fit a label on one line when readable, otherwise wrap it precisely."""
    if measure_text is None:
        measure_text = lambda value, size: _measure_text(value, font_path, size)

    usable_width = width - (2 * HORIZONTAL_MARGIN) - (2 * BOX_BORDER_WIDTH)
    if not text or usable_width <= 0 or width <= 0 or height <= 0:
        return TextLayout((text,), TEXT_HEIGHT_RATIO, 1.0)

    default_font_size = max(1, round(height * TEXT_HEIGHT_RATIO))
    full_width = measure_text(text, default_font_size)

    if full_width <= usable_width:
        lines = [text]
        font_ratio = TEXT_HEIGHT_RATIO
    else:
        fitted_ratio = TEXT_HEIGHT_RATIO * (usable_width / full_width) * 0.98
        if fitted_ratio >= MIN_TEXT_HEIGHT_RATIO:
            lines = [text]
            font_ratio = fitted_ratio
        else:
            lines = _wrap_to_pixel_width(
                text,
                usable_width,
                default_font_size,
                measure_text,
            )
            font_ratio = TEXT_HEIGHT_RATIO

    rendered_font_size = max(1, round(height * font_ratio))
    max_line_width = max(measure_text(line, rendered_font_size) for line in lines)
    return TextLayout(tuple(lines), font_ratio, min(1.0, max_line_width / width))


def _wrap_text_for_frame(text: str, width: int, height: int, font_path=None):
    return "\n".join(_fit_text_layout(text, width, height, font_path).lines)


def burn_in_text(input_path: Path, output_path: Path, text: str, corner: str = "bottom-left"):
    if not _ensure_drawtext_available():
        raise RuntimeError(
            "ffmpeg is installed but the drawtext filter is missing. "
            "Install freetype and reinstall ffmpeg (brew install freetype && brew reinstall ffmpeg)."
        )

    font_path = _find_font_path()

    temp_dir = None
    input_for_ffmpeg = input_path

    if input_path.suffix.lower() in {".heic", ".heif"}:
        converted = _convert_heic_with_sips(input_path)
        if converted:
            input_for_ffmpeg = converted
            temp_dir = converted.parent

    dimensions = _video_dimensions(input_for_ffmpeg)
    if dimensions:
        layout = _fit_text_layout(text, *dimensions, font_path)
    else:
        layout = _fit_text_layout(text, 1080, 1920, font_path)

    line_step_ratio = layout.font_ratio + LINE_SPACING_RATIO
    text_block_ratio = layout.font_ratio + (len(layout.lines) - 1) * line_step_ratio
    box_width = f"iw*{layout.max_line_width_ratio:.8f}+{2 * BOX_BORDER_WIDTH}"
    box_height = f"ih*{text_block_ratio:.8f}+{2 * BOX_BORDER_WIDTH}"

    if corner.endswith("right"):
        box_x = f"iw-({box_width})-{HORIZONTAL_MARGIN}"
        text_x = (
            f"w-(w*{layout.max_line_width_ratio:.8f}+{2 * BOX_BORDER_WIDTH})"
            f"-{HORIZONTAL_MARGIN}+{BOX_BORDER_WIDTH}"
        )
    else:
        box_x = str(HORIZONTAL_MARGIN)
        text_x = str(HORIZONTAL_MARGIN + BOX_BORDER_WIDTH)

    if corner.startswith("bottom"):
        box_y = f"ih-({box_height})-{HORIZONTAL_MARGIN}"
        first_text_y = (
            f"h-(h*{text_block_ratio:.8f}+{2 * BOX_BORDER_WIDTH})"
            f"-{HORIZONTAL_MARGIN}+{BOX_BORDER_WIDTH}"
        )
    else:
        box_y = str(HORIZONTAL_MARGIN)
        first_text_y = str(HORIZONTAL_MARGIN + BOX_BORDER_WIDTH)

    stream = ffmpeg.input(str(input_for_ffmpeg))
    video = stream.video.filter(
        "drawbox",
        x=box_x,
        y=box_y,
        width=box_width,
        height=box_height,
        color="black@0.35",
        thickness="fill",
    )
    for line_index, line in enumerate(layout.lines):
        text_y = first_text_y
        if line_index:
            text_y = f"({first_text_y})+{line_index}*h*{line_step_ratio:.8f}"

        drawtext_args = {
            "text": _escape_drawtext(line),
            "expansion": "none",
            "x": text_x,
            "y": text_y,
            "fontsize": f"h*{layout.font_ratio:.8f}",
            "fontcolor": "white",
            "shadowcolor": "black@0.6",
            "shadowx": 2,
            "shadowy": 2,
        }

        if font_path:
            drawtext_args["fontfile"] = font_path

        video = video.filter("drawtext", **drawtext_args)

    def _run_or_raise(stream):
        try:
            stream.overwrite_output().run(quiet=True, capture_stderr=True)
        except ffmpeg.Error as exc:
            stderr = exc.stderr.decode("utf-8", errors="replace") if exc.stderr else ""
            if stderr:
                raise RuntimeError(stderr.strip()) from exc
            raise

    try:
        if input_path.suffix.lower() in {".mov", ".mp4"}:
            audio_present = _has_audio(input_path)

            def _render_with_audio():
                audio = stream.audio
                out = ffmpeg.output(
                    video,
                    audio,
                    str(output_path),
                    vcodec="libx264",
                    acodec="copy",
                    movflags="faststart",
                )
                _run_or_raise(out)

            def _render_without_audio():
                out = ffmpeg.output(
                    video,
                    str(output_path),
                    vcodec="libx264",
                    movflags="faststart",
                )
                _run_or_raise(out)

            if audio_present is False:
                _render_without_audio()
            elif audio_present is True:
                _render_with_audio()
            else:
                try:
                    _render_with_audio()
                except ffmpeg.Error:
                    _render_without_audio()
        else:
            vcodec = "png" if output_path.suffix.lower() == ".png" else "mjpeg"
            out = ffmpeg.output(
                video,
                str(output_path),
                vcodec=vcodec,
                qscale=2,
            )
            _run_or_raise(out)
    finally:
        if temp_dir and temp_dir.exists():
            shutil.rmtree(temp_dir, ignore_errors=True)
