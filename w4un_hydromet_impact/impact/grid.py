from typing import Any, Literal, Tuple, Optional, Sized

import numpy as np
from typing_extensions import Self

from w4un_hydromet_impact import CONFIG
from w4un_hydromet_impact.util.types import IntegerArray, FloatingArray

_ARC_MILLISECONDS_PER_DEGREE = 3_600_000
_ARC_PRECISION = 12


class Point:
    """
    A point on a grid representing a longitude and a latitude value.

    Attributes
    ----------
    _longitude: the longitude value
    _latitude: the latitude value
    """
    _longitude: int
    _latitude: int

    def __init__(self, longitude: int, latitude: int):
        self._longitude = longitude
        self._latitude = latitude

    @property
    def latitude(self) -> int:
        return self._latitude

    @property
    def longitude(self) -> int:
        return self._longitude

    def __repr__(self) -> str:
        return f'({self._longitude}, {self._latitude})'

    def __sub__(self, other: Self) -> Self:
        return self.__class__(longitude=self._longitude - other._longitude,
                              latitude=self._latitude - other._latitude)

    def __eq__(self, other: object) -> bool:
        return (isinstance(other, Point)
                and self._longitude == other._longitude
                and self._latitude == other._latitude)


class ValuedPoint(Point):
    """
    A point with a value.
    """
    _value: float

    def __init__(self, longitude: int, latitude: int, value: float):
        super().__init__(longitude, latitude)
        self._value = value

    @property
    def value(self) -> float:
        return self._value

    def __repr__(self) -> str:
        return f'{super().__repr__()} -> {self._value}'

    def __eq__(self, other: object) -> bool:
        return (isinstance(other, ValuedPoint)
                and super().__eq__(other)
                and self._value == other._value)


class ProbabilityPoints(Sized):
    """
    Points associated with a probability.

    Attributes
    ----------
    _latitudes: the latitude values
    _longitudes: the longitude values
    _probabilities: the probability values
    """
    _latitudes: IntegerArray
    _longitudes: IntegerArray
    _probabilities: FloatingArray

    def __init__(self, latitudes: FloatingArray, longitudes: FloatingArray, probabilities: FloatingArray):
        if len(latitudes) != len(longitudes):
            raise ValueError(f'Number of latitude values does not match number of longitude values:'
                             f' {len(latitudes)} != {len(longitudes)}')
        if len(latitudes) != len(probabilities):
            raise ValueError(f'Number of points does not match number of probability values:'
                             f' {len(latitudes)} != {len(probabilities)}')

        # check if all probabilities are >= 0
        if (probabilities < 0).any():
            probability_lt_0 = [Point(latitude=latitude, longitude=longitude)
                                for latitude, longitude, probability in zip(latitudes, longitudes, probabilities)
                                if probability < 0]
            raise ValueError(f'{len(probability_lt_0)} / {len(probabilities)} points'
                             f' are associated with probability < 0: {probability_lt_0}')

        # check if all probabilities are <= 1
        if (probabilities > 1).any():
            probability_gt_1 = [Point(latitude=latitude, longitude=longitude)
                                for latitude, longitude, probability in zip(latitudes, longitudes, probabilities)
                                if probability > 1]
            raise ValueError(f'{len(probability_gt_1)} / {len(probabilities)} points'
                             f' are associated with probability > 1: {probability_gt_1}')

        self._latitudes = to_arc_milliseconds(latitudes)
        self._longitudes = to_arc_milliseconds(longitudes)
        self._probabilities = probabilities

    @property
    def latitudes(self) -> IntegerArray:
        return self._latitudes

    @property
    def longitudes(self) -> IntegerArray:
        return self._longitudes

    def __len__(self) -> int:
        return len(self._probabilities)

    @property
    def probabilities(self) -> FloatingArray:
        return self._probabilities

    @property
    def valued_points(self) -> list[ValuedPoint]:
        return [ValuedPoint(latitude=latitude, longitude=longitude, value=probability)
                for latitude, longitude, probability in zip(self._latitudes, self._longitudes, self._probabilities)]


# Type definition for the values of a grid:
# a 2-dimensional array of floats
Values = np.ndarray[Literal[2], np.dtype[np.floating]]

# Type definition for the coordinates of a grid:
# An array associated with each entry of the values array representing its coordinates.
# Each entry of the coordinates array is an array itself
# containing the latitude value as first and the longitude value as second entry.
Coordinates = np.ndarray[Tuple[Any, Literal[2]], np.dtype[np.signedinteger]]


class Grid:
    """
    A grid consisting of a 2d-array with values and an array of coordinates associated with each entry.

    Attributes
    ----------
    _values: The values of the grid in a 2d array. The rows are associated with the latitude values,
             the columns with the longitude values.
    _start: the starting point
    _resolution: the grid's resolution
    _coordinates: The coordinates associated with the values row-by-row.
                  Each coordinate is represented by a list with latitude as first value and longitude as second one.
    """
    _values: Values
    _start: Point
    _resolution: Point
    _coordinates: Coordinates

    @classmethod
    def from_coordinates(cls, values: Values, coordinates: Coordinates) -> Self:
        if len(values.shape) != 2:
            raise AssertionError('Values are not a rectangle.')

        resolution_lat = cls._get_resolution(values, coordinates, axis=0)
        resolution_lon = cls._get_resolution(values, coordinates, axis=1)

        return cls(values=values,
                   coordinates=coordinates,
                   start=Point(latitude=coordinates[0, 0], longitude=coordinates[0, 1]),
                   resolution=Point(latitude=resolution_lat, longitude=resolution_lon))

    @staticmethod
    def _get_resolution(values: Values, coordinates: Coordinates, axis: int) -> int:
        return CONFIG.climada.impact.default_grid_resolution if values.shape[axis] == 1 \
            else abs(coordinates[-1, axis] - coordinates[0, axis]) / (values.shape[axis] - 1)

    def __init__(self, values: Values, start: Point, resolution: Point, coordinates: Optional[Coordinates] = None):
        if coordinates is not None and values.shape[0] * values.shape[1] != len(coordinates):
            raise AssertionError(f'Size of values and number of points do not match:'
                                 f' {values.shape[0] * values.shape[1]} != {len(coordinates)}')

        self._values = values
        self._start = start
        self._resolution = resolution
        self._coordinates = coordinates if coordinates is not None \
            else Grid._calculate_coordinates(start, resolution, values)

    @staticmethod
    def _calculate_coordinates(start: Point, resolution: Point, values: Values) -> Coordinates:
        return np.array(
            [[start.latitude + resolution.latitude * lat_index, start.longitude + resolution.longitude * lon_index]
             for lat_index, lon_index in np.ndindex(*values.shape)])

    @property
    def values(self) -> Values:
        return self._values

    @property
    def shape(self) -> tuple[int, ...]:
        return self._values.shape

    @property
    def start(self) -> Point:
        return self._start

    @property
    def resolution(self) -> Point:
        return self._resolution

    @property
    def coordinates(self) -> Coordinates:
        return self._coordinates

    @property
    def latitudes(self) -> FloatingArray:
        """
        Returns all latitude values in degrees.
        """
        return from_arc_milliseconds(self._coordinates[:, 0]).reshape(self._values.shape)[:, 0]

    @property
    def longitudes(self) -> FloatingArray:
        """
        Returns all longitude values in degrees.
        """
        return from_arc_milliseconds(self._coordinates[:, 1]).reshape(self._values.shape)[0, :]

    def with_new_values(self, new_values: Values) -> Self:
        """
        Creates a new grid with the specified values and the same coordinates.
        """
        if self._values.shape != new_values.shape:
            raise AssertionError(
                f'Shape of new values {new_values.shape} does not match requirements {self._values.shape}.')
        return self.__class__(values=new_values,
                              coordinates=self._coordinates,
                              start=self._start,
                              resolution=self._resolution)

    def has_border(self) -> bool:
        # first column
        return (all(value == 0 for value in self._values[0, :])
                # last column
                and all(value == 0 for value in self._values[-1, :])
                # first row
                and all(value == 0 for value in self._values[:, 0])
                # last row
                and all(value == 0 for value in self._values[:, -1]))

    def add_border(self, border_size: int = 1) -> Self:
        new_values = np.pad(self._values, pad_width=border_size)

        new_start = Point(longitude=self._start.longitude - self._resolution.longitude * border_size,
                          latitude=self._start.latitude - self._resolution.latitude * border_size)

        new_coordinates = self._calculate_coordinates(new_start, self._resolution, new_values)

        return self.__class__(new_values,
                              coordinates=new_coordinates,
                              start=new_start,
                              resolution=self._resolution)


def to_arc_milliseconds(values: FloatingArray) -> IntegerArray:
    return np.round(np.multiply(values, _ARC_MILLISECONDS_PER_DEGREE)).astype(int)


def from_arc_milliseconds(values: IntegerArray) -> FloatingArray:
    return np.round(np.divide(values, _ARC_MILLISECONDS_PER_DEGREE), decimals=_ARC_PRECISION)
