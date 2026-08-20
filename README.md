# Automatically insert location labels for your iPhone Videos and Live Photos

Generate a clean, vlog-style location label for each photo/video, and optionally burn it into the media. Obviously, this tool only works when your photos/videos include location (GPS) metadata. Make sure Location Services are enabled for your camera app so new media is saved with location information.

This is a hobby project I made to complement [aidvid.com](https://www.aidvid.com/) (without pay). If it is unclear what's the point of this project, using aidvid.com once will probably clear things up. 

## Demo

[![Watch the demo](https://img.youtube.com/vi/Q0O7J4ktobQ/0.jpg)](https://www.youtube.com/watch?v=Q0O7J4ktobQ)

The location "Royal Hawaiian Hotel, Honolulu" was add by `vlogify` automatically!

## Installation

Clone the repo:

```bash
git clone https://github.com/biona001/iphone-vlogify.git
cd iphone-vlogify
```

Install dependencies (macOS):

```bash
brew install ffmpeg-full exiftool
brew link ffmpeg-full
```

Then install the package:

```bash
pip install -e .
```

Notes:
- `exiftool` is required for reading GPS and timestamps from media.
- `ffmpeg` must include the `drawtext` filter (most builds do). If embedding fails, reinstall with freetype support.
- `brew` is macOS-only. The project itself is Python and should be portable, but you’ll need a working `ffmpeg` on your system.
- For Linux/Windows, you can typically install `ffmpeg` via your OS package manager or a static build and then run the same `pip install -e .`. See the evaluation notes below for details.

## Quick Start

To label video or photo with a vlog-style location label, simply execute

```bash
vlogify --embed --out-dir OUTPUT_DIR FILE_OR_FOLDER
```

Without the `--embed` keyword, you'll only get the location of the files (no video output)

```
IMG_1464.MOV → 2330 Kalākaua Avenue, Waikīkī, Honolulu
IMG_1500.MOV → Hokulani Waikiki, Honolulu
IMG_1441.MOV → Royal Hawaiian Hotel, Honolulu
IMG_1651.MOV → USS Arizona, Waipahu
```

### Smart Location Labels

`vlogify` favors recognizable destinations over raw map details:

- Airport gates and parking positions fall back to the airport name.
- Street addresses are compared with a broader city or district label.
- Detailed landmarks are kept when they are more useful than the broader area.
- In folder mode, a weak label can inherit a clearly stronger label from media
  captured within 750 meters and two hours. Distinct strong landmarks are kept
  separate.

These rules are generic and do not require a trip-specific override file.

### Font and Placement

By default, a “vlog-like” font is chosen from common macOS fonts. You can set a custom font:

```bash
VLOGIFY_FONT_PATH=/path/to/your/font.ttf vlogify --embed ~/Desktop/2026_March_Hawaii
```

Corner placement:

```bash
vlogify --embed --corner bottom-right ~/Desktop/2026_March_Hawaii
```

## Supported Input File Formats

Supported extensions:
- `.mov`
- `.mp4`
- `.jpg`
- `.jpeg`
- `.heic`

Notes:
- HEIC inputs are written as `.jpg` when embedding, to ensure broad compatibility.

## Constraints and Limitations

- Requires location (GPS) metadata in your files. If Location Services were off, you’ll get `No GPS metadata`.
- Reverse geocoding uses OpenStreetMap via Nominatim. Requests are rate-limited and network-dependent, so you may see `Unknown location` if the service is unavailable.
- Location labels reveal precise places. Double-check outputs before sharing, especially for home or private locations.
