"""
This module provides several functions to calculate the lead times of tracks.
The result of all functions are a dictionary associating a country (ISO-3166-1 alpha3 code) with its lead times,
i.e. the earliest time per track that this tracks affects the corresponding country.
"""
import logging
from typing import Iterable, Optional

import numpy as np
from shapely.geometry.base import BaseGeometry

from climada.hazard import TCTracks
from climada.util import get_country_code
from w4un_hydromet_impact.geography.country import load_country_geometries
from w4un_hydromet_impact.hazard.metadata import LeadTimes
from w4un_hydromet_impact.hazard.tracks import build_tracks, densify_tracks, find_closest_point, find_first_time_closer_than
from w4un_hydromet_impact.hazard.tracks.data import Track
from w4un_hydromet_impact.hazard.tracks.util import calculate_init_time
from w4un_hydromet_impact.util.types import Timestamp

logger = logging.getLogger(__name__)

_TimeAndFrequency = tuple[Timestamp, float]


def calculate_landfalls_from_tc_tracks(tc_tracks: TCTracks) -> dict[int, LeadTimes]:
    """
    Calculates the lead times per country and groups them by country.
    The lead times are based on the landfalls.
    The landfall is the first time that a track enters a country (or its starting point if it starts in that country).
    Only the points defined by the tracks are considered.
    This algorithm is based on calculating the unique country code per point.
    """
    tracks = build_tracks(tc_tracks)
    return _calculate_landfalls_from_tracks(tracks)


def _calculate_landfalls_from_tracks(tracks: list[Track]) -> dict[int, LeadTimes]:
    if len(tracks) == 0:
        return {}

    country_codes = _find_country_codes(tracks)
    unique_country_codes = np.unique([country_code for country_code in country_codes if country_code != 0])

    logger.debug("Landfall in countries: %s", unique_country_codes)

    # calculate first time per track that a country code appears
    lead_times_per_country: dict[int, LeadTimes] = {}
    for country_code in unique_country_codes:
        times = []
        frequencies = []
        # mask to select values from times per track
        country_mask = np.asarray(country_codes == country_code)
        offset = 0
        for track in tracks:
            length = len(track)
            country_track_times = track.times[country_mask[offset:offset + length]]
            if len(country_track_times) > 0:
                times.append(np.min(country_track_times))
                frequencies.append(track.frequency)
            offset += length
        lead_times_per_country[int(country_code)] = LeadTimes.create(lead_times=times, weights=frequencies)

    return lead_times_per_country


def _find_country_codes(tracks: list[Track]) -> list[int]:
    """
    Calculates the country codes associated with the specified points.
    The returned list has got the same order as the specified one.
    """
    # use gridded=True until issue https://github.com/CLIMADA-project/climada_python/issues/770 is resolved
    latitudes = [latitude for track in tracks for latitude in track.latitudes]
    longitudes = [longitude for track in tracks for longitude in track.longitudes]
    return get_country_code(latitudes, longitudes, gridded=True)


def calculate_landfalls_from_dense_tracks(tc_tracks: TCTracks, resolution: float) -> dict[int, LeadTimes]:
    """
    Calculates the lead times per country and groups them by country.
    The lead times are based on the landfalls.
    The landfall is the first time that a track enters a country (or its starting point if it starts in that country).
    Before starting the calculation, the tracks are densified
    so that the distance between two neighbored points is not greater than the specified resolution.
    This algorithm is based on calculating the unique country code per point.
    """
    tracks = build_tracks(tc_tracks)

    # ensure that distance between two points is not greater than required resolution
    dense_tracks = densify_tracks(tracks, resolution)

    return _calculate_landfalls_from_tracks(dense_tracks)


def calculate_band_falls_from_geometries_and_tracks(tc_tracks: TCTracks,
                                                    country_codes: Iterable[int],
                                                    radius_km: float) -> dict[int, LeadTimes]:
    """
    Calculates the "band falls" based on the geometries of the specified countries.
    A "band fall" of a track in a country exists
    when at least one point of that track is closer to that country than the specified radius.
    This function returns the times associated with the countries and points of a "band fall".
    """
    tracks = build_tracks(tc_tracks)

    band_falls_per_country: dict[int, LeadTimes] = {}

    for country_code, geometry in load_country_geometries(country_codes).items():
        first_times = []
        frequencies = []
        for track in tracks:
            minimum_time = find_first_time_closer_than(track, geometry, radius_km)
            if minimum_time is not None:
                first_times.append(minimum_time)
                frequencies.append(track.frequency)

        if first_times:
            band_falls_per_country[country_code] = LeadTimes.create(lead_times=first_times, weights=frequencies)

    return band_falls_per_country


def calculate_closest_times_from_tracks(tc_tracks: TCTracks,
                                        tracks_per_country: dict[int, set[int]]) -> dict[int, LeadTimes]:
    """
    Calculates the time of the closest point to the specified countries.
    Only the tracks (indexes) associated with the countries are considered.
    Therefore, the distance to the geometry of the country is calculated for each point of the considered tracks.
    Then, the time associated with the closest point is taken.
    The resulting dictionary is always having dictionaries with one entry only as result
    in order to be able to provide an interface matching the return value of other calculation functions.
    """
    tracks = build_tracks(tc_tracks)

    # add time of affected track that is closest to country
    closest_time_per_country: dict[int, LeadTimes] = {}

    for country_code, geometry in load_country_geometries(tracks_per_country.keys()).items():
        track_indexes = tracks_per_country[country_code]
        closest_time = _find_closest_time(tracks, track_indexes, geometry)
        if closest_time is not None:
            closest_time_per_country[country_code] = LeadTimes.create(median=closest_time)

    return closest_time_per_country


def _find_closest_time(tracks: list[Track],
                       track_indexes: Iterable[int],
                       geometry: BaseGeometry) -> Optional[Timestamp]:
    closest_distance = float('inf')
    closest_time = None
    for track_index in track_indexes:
        track = tracks[track_index]

        time, distance = find_closest_point(track, geometry)
        if time is not None and distance < closest_distance:
            closest_distance = distance
            closest_time = time

    return closest_time


def use_initialization_time_as_lead_time(tc_tracks: TCTracks, country_codes: Iterable[int]) -> dict[int, LeadTimes]:
    """
    Uses the initialization time of the specified tracks as lead time of the specified countries.
    """
    init_time = calculate_init_time(tc_tracks)

    # add initialization date as lead time for affected countries without landfall
    return {country_code: LeadTimes.create(lead_times=[init_time])
            for country_code in country_codes}
