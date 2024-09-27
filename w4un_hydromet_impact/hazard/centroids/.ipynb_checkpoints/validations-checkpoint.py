"""
This module contains functions validating centroids.
"""
from climada.hazard import Centroids
from w4un_hydromet_impact.fabio import S3Location


def check_centroids_consistency(centroids: Centroids, centroid_location: S3Location) -> None:
    try:
        centroids.check()
    except ValueError as value_error:
        raise AssertionError(
            f'Imported invalid centroids from {centroid_location}'
            f' with error: {value_error}') from value_error
