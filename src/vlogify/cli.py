import sys
from pathlib import Path
from vlogify.metadata import extract_gps


def main():

    if len(sys.argv) < 2:
        print("Usage: vlogify <file>")
        sys.exit(1)

    path = Path(sys.argv[1])

    if not path.exists():
        print(f"Error: file does not exist: {path}")
        sys.exit(1)
    if not path.is_file():
        print(f"Error: path is not a file: {path}")
        sys.exit(1)

    gps = extract_gps(str(path))

    if gps:
        lat, lon = gps
        print(f"GPS: {lat}, {lon}")
    else:
        print("No GPS metadata found.")