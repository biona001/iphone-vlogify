from vlogify.burn_in import (
    MIN_TEXT_HEIGHT_RATIO,
    TEXT_HEIGHT_RATIO,
    _escape_drawtext,
    _fit_text_layout,
    _wrap_text_for_frame,
)


def test_escape_drawtext_handles_special_chars():
    text = r"Bob's: Place \ Cafe"
    assert _escape_drawtext(text) == r"Bob\'s\: Place \\ Cafe"


def test_wraps_long_text_for_portrait_video():
    wrapped = _wrap_text_for_frame("Johnston Canyon Trail, Alberta", 1080, 1920)

    assert "\n" in wrapped
    assert wrapped.replace("\n", " ") == "Johnston Canyon Trail, Alberta"


def test_keeps_same_text_on_one_line_when_it_fits():
    text = "Upper Falls, Alberta"

    assert _wrap_text_for_frame(text, 1080, 1920) == text
    assert _wrap_text_for_frame("Johnston Canyon Trail, Alberta", 1920, 1080) == (
        "Johnston Canyon Trail, Alberta"
    )


def test_breaks_an_unusually_long_single_word():
    wrapped = _wrap_text_for_frame("AReallyLongUnbrokenDestinationName", 1080, 1920)

    assert "\n" in wrapped


def test_shrinks_moderately_long_text_before_wrapping():
    measure = lambda value, size: len(value) * size * 0.46

    layout = _fit_text_layout(
        "Calgary International Airport",
        1080,
        1920,
        measure_text=measure,
    )

    assert layout.lines == ("Calgary International Airport",)
    assert MIN_TEXT_HEIGHT_RATIO <= layout.font_ratio < TEXT_HEIGHT_RATIO


def test_wraps_when_one_line_would_be_too_small():
    measure = lambda value, size: len(value) * size * 0.48

    layout = _fit_text_layout(
        "Johnston Canyon Trail, Alberta",
        1080,
        1920,
        measure_text=measure,
    )

    assert len(layout.lines) == 2
    assert layout.font_ratio == TEXT_HEIGHT_RATIO
