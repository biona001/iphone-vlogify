import sys
from pathlib import Path
from vlogify.metadata import extract_gps
from vlogify.geocode import reverse_geocode
from vlogify.location_cache import LocationCache

SUPPORTED_EXT = {".mov", ".mp4", ".jpg", ".jpeg", ".heic"}
cache = LocationCache()

def process_file(path, cache):

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


def process_directory(path):

    cache = LocationCache()

    files = [f for f in path.iterdir() if f.suffix.lower() in SUPPORTED_EXT]

    for file in sorted(files):
        process_file(file, cache)


def main():

    if len(sys.argv) < 2:
        print("Usage: vlogify <file_or_directory>")
        sys.exit(1)

    path = Path(sys.argv[1])

    if not path.exists():
        print(f"Error: path does not exist: {path}")
        sys.exit(1)

    if path.is_file():
        process_file(path)

    elif path.is_dir():
        process_directory(path)

    else:
        print("Unsupported path type.")