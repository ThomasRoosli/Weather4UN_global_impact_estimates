from geopy.distance import distance
from shapely import Point
from shapely.geometry.base import BaseGeometry


def calculate_kilometers_for_latitude(latitude: float) -> float:
    """
    Calculates the kilometers per degree on the specified latitude.
    """
    return distance((latitude, 0), (latitude, 1)).kilometers


def calculate_distance_between_point_and_geometry(geometry: BaseGeometry,
                                                  latitude: float, longitude: float) -> float:
    """
    Calculates the distance between a point a geometry object in kilometers.
    """
    point = Point(longitude, latitude)
    return geometry.distance(point) * calculate_kilometers_for_latitude(latitude)
