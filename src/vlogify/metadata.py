import exifread

def extract_gps(image_path):
    with open(image_path, "rb") as f:
        tags = exifread.process_file(f)

    return {
        "lat": tags.get("GPS GPSLatitude"),
        "lon": tags.get("GPS GPSLongitude"),
    }
