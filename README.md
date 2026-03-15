# Vlogify your iPhone Videos and Live Photos

Generate a clean, vlog-style location label for each photo/video, and optionally burn it into the media.

Inspired by [aidvid.com](https://www.aidvid.com/).

## Installation

Install package dependencies:

```bash
brew install ffmpeg-full
brew link ffmpeg-full
```

Then install the package:

```bash
pip install -e .
```

## Quick Start

```bash
vlogify ~/Desktop/2026_March_Hawaii
```

Example output:

```
IMG_1446.MOV → Waikīkī, Honolulu
IMG_1450.MP4 → Island Vintage Shave Ice, Honolulu
IMG_1452.MOV → 1945 Kalākaua Ave, Honolulu, Hawaii
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
