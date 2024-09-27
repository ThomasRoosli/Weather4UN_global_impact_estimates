from typing import Sized

import numpy as np

from w4un_hydromet_impact.util.types import FloatingArray, TimestampArray

Point = tuple[float, float]
"""
A point of a track. Consisting of a latitude and a longitude value.
"""


class Track(Sized):
    """
    A track consisting of a sequence of points.
    Used to wrap all required information extracted from TCTracks.

    Attributes
    ----------
    _latitudes: the latitude values per point
    _longitudes: the longitude values per point
    _times: the timestamps per point
    _frequency: the frequency of the track
    """

    _latitudes: FloatingArray
    _longitudes: FloatingArray
    _times: TimestampArray
    _frequency: float

    def __init__(self, latitudes: FloatingArray, longitudes: FloatingArray, times: TimestampArray, frequency: float):
        if not len(latitudes) == len(longitudes) == len(times):
            raise ValueError('Numbers of latitudes, longitudes and times do not match:'
                             f' {len(latitudes)} <> {len(longitudes)} <> {len(times)}')
        self._latitudes = latitudes
        self._longitudes = longitudes
        self._times = times
        self._frequency = frequency

    def __len__(self) -> int:
        return len(self._times)

    def __eq__(self, other: object) -> bool:
        return (isinstance(other, Track)
                and self._frequency == other._frequency
                and np.array_equal(self._latitudes, other._latitudes)
                and np.array_equal(self._longitudes, other._longitudes)
                and np.array_equal(self._times, other._times))

    @property
    def latitudes(self) -> FloatingArray:
        """
        Returns the latitude values of all points.
        """
        return self._latitudes

    @property
    def longitudes(self) -> FloatingArray:
        """
        Returns the longitude values of all points.
        """
        return self._longitudes

    @property
    def times(self) -> TimestampArray:
        """
        Returns the timestamp values of all points.
        """
        return self._times

    @property
    def frequency(self) -> float:
        """
        Returns the frequency of this track.
        """
        return self._frequency
