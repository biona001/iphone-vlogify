import exiftool


def extract_gps(file_path):
    """
    Extract GPS coordinates from photo or video.
    Returns (lat, lon) or None.
    """

    with exiftool.ExifToolHelper() as et:
        metadata = et.get_metadata(file_path)

    if not metadata:
        return None

    data = metadata[0]

    lat = data.get("Composite:GPSLatitude")
    lon = data.get("Composite:GPSLongitude")

    if lat and lon:
        return lat, lon

    return None

