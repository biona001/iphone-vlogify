import argparse
import sys
from pathlib import Path
from typing import Optional
from vlogify.metadata import extract_gps
from vlogify.geocode import reverse_geocode
from vlogify.location_cache import LocationCache
from vlogify.metadata import extract_timestamp
from vlogify.burn_in import burn_in_text, SUPPORTED_IMAGE_OUT

SUPPORTED_EXT = {".mov", ".mp4", ".jpg", ".jpeg", ".heic"}


def _output_path_for_file(path: Path, out_dir: Optional[Path]):
    if out_dir:
        out_dir.mkdir(parents=True, exist_ok=True)
        return out_dir / path.name

    return path.with_name(f"{path.stem}_vlogify{path.suffix}")


def _normalize_image_output_path(path: Path):
    if path.suffix.lower() in SUPPORTED_IMAGE_OUT:
        return path

    return path.with_suffix(".jpg")


def _output_path_for_embed(path: Path, out_dir: Optional[Path]):
    output_path = _output_path_for_file(path, out_dir)
    if path.suffix.lower() not in {".mov", ".mp4"}:
        normalized = _normalize_image_output_path(output_path)
        if normalized.suffix != output_path.suffix:
            print(f"    ↳ {path.name} will be written as {normalized.name}")
        return normalized

    return output_path


def process_file(path: Path, cache: LocationCache, embed: bool, out_dir: Optional[Path], corner: str):

    gps = extract_gps(str(path))

    if not gps:
        print(f"{path.name} → No GPS metadata")
        return

    lat, lon = gps

    location = cache.get(lat, lon)

    if not location:
        location = reverse_geocode(lat, lon)
        cache.set(lat, lon, location)

    print(f"{path.name} → {location}")

    if embed:
        output_path = _output_path_for_embed(path, out_dir)
        burn_in_text(path, output_path, location, corner=corner)


def extract_all_gps(files):

    results = []

    for file in files:

        gps = extract_gps(str(file))

        if gps:
            lat, lon = gps
            timestamp = extract_timestamp(str(file))

            results.append((file, lat, lon, timestamp))

    return results

def process_directory(path: Path, cache: LocationCache, embed: bool, out_dir: Optional[Path], corner: str):

    files = [
        f for f in path.iterdir()
        if f.suffix.lower() in SUPPORTED_EXT
    ]

    if not files:
        print("No supported media files found.")
        return

    # Extract GPS + timestamps
    files_with_coords = []

    for file in files:

        gps = extract_gps(str(file))

        if not gps:
            print(f"{file.name} → No GPS metadata")
            continue

        lat, lon = gps
        timestamp = extract_timestamp(str(file))

        files_with_coords.append((file, lat, lon, timestamp))

    if not files_with_coords:
        print("No GPS metadata found.")
        return

    # Sort by timestamp (fallback to filename)
    files_with_coords.sort(key=lambda x: (x[3] or 0, x[0].name))

    for file, lat, lon, _ in files_with_coords:
        location = cache.get(lat, lon)

        if not location:
            location = reverse_geocode(lat, lon)
            cache.set(lat, lon, location)

        print(f"{file.name} → {location}")

        if embed:
            output_path = _output_path_for_embed(file, out_dir)
            burn_in_text(file, output_path, location, corner=corner)

def main():
    parser = argparse.ArgumentParser(description="Add a location label to your iPhone media.")
    parser.add_argument("path", help="File or directory to process")
    parser.add_argument(
        "--embed",
        action="store_true",
        help="Burn the location label into the media (creates new files).",
    )
    parser.add_argument(
        "--out-dir",
        help="Directory for embedded outputs (default: alongside file or ./vlogify_out for folders).",
    )
    parser.add_argument(
        "--corner",
        choices=["bottom-left", "bottom-right", "top-left", "top-right"],
        default="bottom-left",
        help="Where to place the label when embedding.",
    )

    args = parser.parse_args()

    path = Path(args.path)

    if not path.exists():
        print(f"Error: path does not exist: {path}")
        sys.exit(1)

    cache = LocationCache()

    if path.is_file():
        out_dir = Path(args.out_dir) if args.out_dir else None
        process_file(path, cache, args.embed, out_dir, args.corner)

    elif path.is_dir():
        out_dir = Path(args.out_dir) if args.out_dir else (path / "vlogify_out" if args.embed else None)
        process_directory(path, cache, args.embed, out_dir, args.corner)

    else:
        print("Unsupported path type.")
