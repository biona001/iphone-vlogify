# Vlogify your iPhone Videos and Live Photos

Generate a clean, vlog-style location label for each photo/video, and optionally burn it into the media.

This is a hobby project I made to complement [aidvid.com](https://www.aidvid.com/) (without pay).

## Demo

[![Watch the demo](https://img.youtube.com/vi/Q0O7J4ktobQ/0.jpg)](https://www.youtube.com/watch?v=Q0O7J4ktobQ)

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

## Embed Labels Into Media

Burn the label directly into videos/images (creates new files):

```bash
vlogify --embed ~/Desktop/2026_March_Hawaii
```

Default outputs:
- Single file: `*_vlogify` next to the original file.
- Directory: `vlogify_out/` inside the target directory.

You can override the output directory:

```bash
vlogify --embed --out-dir ~/Desktop/vlogify_out ~/Desktop/2026_March_Hawaii
```

### Font and Placement

By default, a “vlog-like” font is chosen from common macOS fonts. You can set a custom font:

```bash
VLOGIFY_FONT_PATH=/path/to/your/font.ttf vlogify --embed ~/Desktop/2026_March_Hawaii
```

Corner placement:

```bash
vlogify --embed --corner bottom-right ~/Desktop/2026_March_Hawaii
```

Notes:
- HEIC inputs are written as `.jpg` when embedding, to ensure broad compatibility.
