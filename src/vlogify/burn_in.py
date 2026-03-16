import os
import shutil
import subprocess
import tempfile
from typing import Optional
from pathlib import Path

import ffmpeg


SUPPORTED_IMAGE_OUT = {".jpg", ".jpeg", ".png"}
_DRAW_TEXT_OK = None


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


def burn_in_text(input_path: Path, output_path: Path, text: str, corner: str = "bottom-left"):
    if not _ensure_drawtext_available():
        raise RuntimeError(
            "ffmpeg is installed but the drawtext filter is missing. "
            "Install freetype and reinstall ffmpeg (brew install freetype && brew reinstall ffmpeg)."
        )

    font_path = _find_font_path()
    safe_text = _escape_drawtext(text)

    x = "40"
    y = "40"
    if corner == "bottom-left":
        y = "h-th-40"
    elif corner == "bottom-right":
        x = "w-tw-40"
        y = "h-th-40"
    elif corner == "top-right":
        x = "w-tw-40"

    drawtext_args = {
        "text": safe_text,
        "x": x,
        "y": y,
        "fontsize": "h*0.045",
        "fontcolor": "white",
        "box": 1,
        "boxcolor": "black@0.35",
        "boxborderw": 18,
        "shadowcolor": "black@0.6",
        "shadowx": 2,
        "shadowy": 2,
    }

    if font_path:
        drawtext_args["fontfile"] = font_path

    temp_dir = None
    input_for_ffmpeg = input_path

    if input_path.suffix.lower() in {".heic", ".heif"}:
        converted = _convert_heic_with_sips(input_path)
        if converted:
            input_for_ffmpeg = converted
            temp_dir = converted.parent

    stream = ffmpeg.input(str(input_for_ffmpeg))
    video = stream.video.filter("drawtext", **drawtext_args)

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
