import numpy as np
from sklearn.cluster import DBSCAN


def cluster_locations(files_with_coords, eps=0.0005):
    """
    files_with_coords = [(file_path, lat, lon), ...]

    eps values:
    0.0003 ≈ 30 meters
    0.0005 ≈ 50 meters
    0.001  ≈ 100 meters
    """

    coords = np.array([[lat, lon] for _, lat, lon, _ in files_with_coords])

    clustering = DBSCAN(
        eps=eps,
        min_samples=1,
        metric="euclidean"
    ).fit(coords)

    labels = clustering.labels_

    clusters = {}

    for label, (file, lat, lon, timestamp) in zip(labels, files_with_coords):
        clusters.setdefault(label, []).append((file, lat, lon, timestamp))

    return clusters