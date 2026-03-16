from vlogify.burn_in import _escape_drawtext


def test_escape_drawtext_handles_special_chars():
    text = r"Bob's: Place \ Cafe"
    assert _escape_drawtext(text) == r"Bob\'s\: Place \\ Cafe"
