from datetime import datetime
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

def extract_timestamp(file_path):

    with exiftool.ExifToolHelper() as et:
        metadata = et.get_metadata(file_path)[0]

    timestamp = (
        metadata.get("QuickTime:CreateDate")
        or metadata.get("EXIF:DateTimeOriginal")
    )

    if not timestamp:
        return None

    # format example: "2026:03:11 01:03:22"
    try:
        return datetime.strptime(timestamp, "%Y:%m:%d %H:%M:%S")
    except Exception:
        return None
