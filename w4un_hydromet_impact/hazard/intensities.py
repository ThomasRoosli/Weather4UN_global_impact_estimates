import collections

import numpy as np

from climada.hazard import Hazard


def find_affected_countries(hazard: Hazard) -> dict[int, set[int]]:
    """
    Calculates the codes of all countries affected by the specified hazard,
    i.e. all countries with at least one point having a positive intensity.
    The codes are associated with the indexes of the corresponding tracks.
    """
    non_zero_indices = hazard.intensity.max(axis=0).col
    if non_zero_indices.size == 0:
        return {}

    # country codes of all affected centroids
    country_codes = hazard.centroids.region_id[non_zero_indices]
    # mapping between (indexes of) affected centroids and their country code
    country_codes_map = dict(zip(non_zero_indices, country_codes))

    # group (indexes of) affecting tracks by (indexes of) affected centroids
    grouped_non_zero_indices = {col: hazard.intensity[:, col].nonzero()[0]
                                for col in non_zero_indices
                                if np.any(hazard.intensity[:, col].data)}

    # collect (indexes of) all affecting tracks grouped by country code; skipping country code 0 (ocean)
    country_codes_with_tracks = collections.defaultdict(set)
    for index, tracks in grouped_non_zero_indices.items():
        country = country_codes_map[index]
        if country:
            country_codes_with_tracks[country].update(tracks)

    return country_codes_with_tracks
