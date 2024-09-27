import math
try:
    from itertools import pairwise
except:
    def pairwise(iterable):
        # pairwise('ABCDEFG') → AB BC CD DE EF FG
        iterator = iter(iterable)
        a = next(iterator, None)
        for b in iterator:
            yield a, b
            a = b

from typing import Optional

import numpy as np
from shapely.geometry.base import BaseGeometry

from climada.hazard import TCTracks
from w4un_hydromet_impact.hazard.tracks.data import Track, Point
from w4un_hydromet_impact.hazard.tracks.util import build_frequencies
from w4un_hydromet_impact.util.distances import calculate_distance_between_point_and_geometry
from w4un_hydromet_impact.util.types import FloatingArray, IntegerArray, TimestampArray, Timestamp


def calculate_distance(point1: Point, point2: Point) -> float:
    """
    Calculates the distance between two points.
    """
    return math.dist(point1, point2)


def build_tracks(tracks: TCTracks) -> list[Track]:
    """
    Calculates the internal track representation from the specified tracks.
    """
    return [Track(data.lat.values, data.lon.values, data.time.values, frequency)
            for data, frequency in zip(tracks.data, build_frequencies(tracks))]


def densify_tracks(tracks: list[Track], max_distance: float) -> list[Track]:
    """
    Densifies the points of the specified tracks so that they have got at most the specified distance.
    """
    return list(map(lambda track: densify_track(track, max_distance), tracks))


def densify_track(track: Track, max_distance: float) -> Track:
    """
    Densifies the points of the specified track so that they have got at most the specified distance.
    Adds as many points between two neighbor point as required.
    The priorities of the new points depend on their distance to their nearest neighbor.
    """
    required_points = _calculate_required_intermediate_points(track.latitudes, track.longitudes, max_distance)

    new_latitudes = _calculate_new_values(track.latitudes, required_points)
    new_longitudes = _calculate_new_values(track.longitudes, required_points)

    new_times = _calculate_new_times(track.times, required_points)
    return Track(new_latitudes, new_longitudes, new_times,
                 track.frequency)


def _calculate_required_intermediate_points(latitudes: FloatingArray, longitudes: FloatingArray,
                                            max_distance: float) -> IntegerArray:
    """
    Calculates the number of points to be inserted between two neighbored points
    so that two point have got at most the specified distance.
    """
    return np.array([
        math.ceil(calculate_distance((latitude1, longitude1), (latitude2, longitude2)) / max_distance - 1)
        for (latitude1, latitude2), (longitude1, longitude2) in zip(pairwise(latitudes), pairwise(longitudes))
    ])


def _calculate_new_values(values: FloatingArray, required_intermediate_values: IntegerArray) -> FloatingArray:
    """
    Extends the specified values by inserting the specified number of values between two neighbored ones.
    """
    if len(values) != len(required_intermediate_values) + 1:
        raise ValueError('Values does not contain one element more than required intermediate values:'
                         f' {len(values)} <> {len(required_intermediate_values)}+1')
    new_points = [np.linspace(value, next_value, num=required + 1, endpoint=False)
                  for (value, next_value), required in zip(pairwise(values), required_intermediate_values)]
    # add last point because not added before (endpoint always excluded)
    new_points.append(values[-1:])
    return np.concatenate(new_points)


def _calculate_new_times(times: TimestampArray, required_intermediate_values: IntegerArray) -> TimestampArray:
    """
    Extends the specified times by distributing the required intermediate values to the two neighbored ones
    so that the point exactly in the middle will have the greater time.
    """
    result = [
        time1 if r <= required // 2 else time2
        for (time1, time2), required in zip(pairwise(times), required_intermediate_values)
        for r in range(required + 1)
    ]
    result.append(times[-1])
    return np.array(result)


def find_first_time_closer_than(track: Track, geometry: BaseGeometry, distance_km: float) -> Optional[Timestamp]:
    """
    Calculates the timestamp of the first point of the specified track
    that is closer to the specified geometry than the specified distance.
    """
    return next(
        (time
         for latitude, longitude, time in zip(track.latitudes, track.longitudes, track.times)
         if calculate_distance_between_point_and_geometry(geometry,
                                                          latitude,
                                                          longitude) <= distance_km),
        None)


def find_closest_point(track: Track, geometry: BaseGeometry) -> tuple[Optional[Timestamp], float]:
    """
    Calculates the timestamp and the distance (in km) of the point on the specified track
    that is the closest to the specified geometry.
    """
    if not track:
        raise AssertionError('Track does not contain any points.')

    closest_distance = float('inf')
    closest_time = None

    for latitude, longitude, time in zip(track.latitudes, track.longitudes, track.times):
        distance = calculate_distance_between_point_and_geometry(geometry,
                                                                 latitude, longitude)
        if distance <= closest_distance:
            closest_distance = distance
            closest_time = time

    return closest_time, closest_distance
