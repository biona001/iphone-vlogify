import sys
from pathlib import Path
from vlogify.metadata import extract_gps
from vlogify.geocode import reverse_geocode
from vlogify.location_cache import LocationCache
from vlogify.clustering import cluster_locations
from vlogify.metadata import extract_timestamp

SUPPORTED_EXT = {".mov", ".mp4", ".jpg", ".jpeg", ".heic"}


def process_file(path: Path, cache: LocationCache):

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


def extract_all_gps(files):

    results = []

    for file in files:

        gps = extract_gps(str(file))

        if gps:
            lat, lon = gps
            timestamp = extract_timestamp(str(file))

            results.append((file, lat, lon, timestamp))

    return results


def process_directory(path: Path):

    files = [f for f in path.iterdir() if f.suffix.lower() in SUPPORTED_EXT]

    if not files:
        print("No supported media files found.")
        return

    files_with_coords = extract_all_gps(files)

    if not files_with_coords:
        print("No GPS metadata found.")
        return

    clusters = cluster_locations(files_with_coords)

    cache = LocationCache()

    # sort group chapters by time
    sorted_clusters = sorted(
        clusters.values(),
        key=lambda items: min(
            t for _, _, _, t in items if t is not None
        )
    )

    for items in sorted_clusters:

        lat = items[0][1]
        lon = items[0][2]

        location = cache.get(lat, lon)

        if not location:
            location = reverse_geocode(lat, lon)
            cache.set(lat, lon, location)

        print(f"\n📍 {location}")

        for file, _, _, timestamp in sorted(items, key=lambda x: x[3] or 0):
            print(f"    {file.name}")


def main():

    if len(sys.argv) < 2:
        print("Usage: vlogify <file_or_directory>")
        sys.exit(1)

    path = Path(sys.argv[1])

    if not path.exists():
        print(f"Error: path does not exist: {path}")
        sys.exit(1)

    cache = LocationCache()

    if path.is_file():
        process_file(path, cache)

    elif path.is_dir():
        process_directory(path)

    else:
        print("Unsupported path type.")