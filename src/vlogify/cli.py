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

    files = [
        f for f in path.iterdir()
        if f.suffix.lower() in SUPPORTED_EXT
    ]

    if not files:
        print("No supported media files found.")
        return

    # Step 1: Extract GPS + timestamps
    files_with_coords = []

    for file in files:

        gps = extract_gps(str(file))

        if not gps:
            continue

        lat, lon = gps
        timestamp = extract_timestamp(str(file))

        files_with_coords.append((file, lat, lon, timestamp))

    if not files_with_coords:
        print("No GPS metadata found.")
        return

    # Step 2: Cluster by location
    clusters = cluster_locations(files_with_coords)

    # Step 3: Sort clusters by earliest timestamp
    sorted_clusters = sorted(
        clusters.values(),
        key=lambda items: min(
            t for _, _, _, t in items if t is not None
        )
    )

    # Step 4: Geocode ONCE per cluster
    cluster_cache = {}

    for items in sorted_clusters:

        cluster_id = id(items)  # unique per cluster

        # Use cached location if available
        if cluster_id not in cluster_cache:

            lat = items[0][1]
            lon = items[0][2]

            location = reverse_geocode(lat, lon)

            cluster_cache[cluster_id] = location

        location = cluster_cache[cluster_id]

        print(f"\n📍 {location}")

        # Step 5: Sort files within cluster by time
        for file, _, _, _ in sorted(
            items,
            key=lambda x: x[3] or 0
        ):
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