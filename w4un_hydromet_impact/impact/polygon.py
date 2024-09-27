"""
Module to create polygons from impacts.
"""
import logging
from typing import Optional

import numpy as np
from geopandas import GeoSeries
from matplotlib import pyplot as plt
from matplotlib.path import Path
from shapely import Polygon, MultiPolygon

from climada.engine import Impact
from climada.engine.forecast import Forecast
from climada_petals.engine.warn import Warn, Operation
from w4un_hydromet_impact import CONFIG
from w4un_hydromet_impact.impact.grid import ProbabilityPoints, Grid

logger = logging.getLogger(__name__)

POLYGON_LINE_WIDTH = 1.0
POLYGON_LINE_STYLE = ':'
POLYGON_COLOR = '#525252'


def create_polygons_from_impact(impact_forecast: Forecast) -> GeoSeries:
    """
    Creates polygons representing the areas covered by the specified impact (forecast).
    """
    if len(impact_forecast._impact) != 1:
        raise AssertionError(f'Impact forecast does not contain exactly 1 impact, but: {len(impact_forecast._impact)}')
    impact = impact_forecast._impact[0]

    points = _convert_impact_to_probability_points(impact)

    if any(probability > 0 for probability in points.probabilities):
        probability_grid = _transform_probability_points_to_grid(points)

        minimum_grid = _ensure_minimum_grid(probability_grid)

        warn_grid = _apply_warn_parameters(minimum_grid)

        if np.count_nonzero(warn_grid.values) == 0:
            logger.info('Grid %s only contains values with 0 probability.', warn_grid.shape)
            polygons = []
        else:
            improved_grid = _prepare_create_polygons(warn_grid)

            polygons = _create_polygons_from_grid(improved_grid)
    else:
        logger.info('None of %s points has got a probability greater than 0.', len(points))
        polygons = []

    return _create_geo_series_from_polygons(polygons, impact)


def _convert_impact_to_probability_points(impact: Impact) -> ProbabilityPoints:
    """
    Calculates all points affected by the specified impact associated with their probability that they are affected.
    """
    # probability of impact
    values = (impact.imp_mat > 0).sum(axis=0) / impact.imp_mat.shape[0]
    values = np.asarray(values).ravel()

    return ProbabilityPoints(latitudes=impact.coord_exp[:, 0],
                             longitudes=impact.coord_exp[:, 1],
                             probabilities=values)


def _transform_probability_points_to_grid(points: ProbabilityPoints) -> Grid:
    """
    Transforms the affected points with their probability into a grid.
    Points that have not been specified are assumed to have the probability 0.
    """
    values, coordinates = Warn.zeropadding(points.latitudes,
                                           points.longitudes,
                                           points.probabilities)
    return Grid.from_coordinates(values, coordinates)


def _ensure_minimum_grid(grid: Grid) -> Grid:
    """
    Ensure that the grid has got a configured minimum size.
    """
    grid_size = min(*grid.shape)

    if grid_size >= CONFIG.climada.impact.minimum_grid_size:
        return grid

    diff = CONFIG.climada.impact.minimum_grid_size - grid_size
    required_border = (diff + 1) // 2

    return grid.add_border(required_border)


def _warn_levels() -> list[float]:
    """
    The warn levels applied when converting a grid to a polygon.
    The second entry represents the minimum probability to be considered.
    """
    return [0, CONFIG.climada.impact.probability_threshold]


def _apply_warn_parameters(grid: Grid) -> Grid:
    """
    Applies the warning parameters to the specified grid. The resulting grid contains only 0 or 1 values.
    """
    warn_parameters = Warn.WarnParameters(
        _warn_levels(),
        operations=[
            (Operation.erosion, CONFIG.climada.impact.warn.erosion),
            (Operation.dilation, CONFIG.climada.impact.warn.dilation),
            (Operation.median_filtering, CONFIG.climada.impact.warn.median_filtering)
        ],
        gradual_decr=CONFIG.climada.impact.warn.gradually_decreased,
        change_sm=CONFIG.climada.impact.warn.small_regions_threshold
    )
    warn_def = Warn.from_map(grid.values, grid.coordinates, warn_parameters)
    return grid.with_new_values(warn_def.warning)


def _prepare_create_polygons(grid: Grid) -> Grid:
    """
    Prepares creating polygons by modifying the grid in order to match the requirements of the polygon calculation.
    Ensures that the cells with non-zero values to not touch the edges
    because the polygon algorithm will not return a closed polygon, otherwise.
    """
    if grid.has_border():
        return grid
    return grid.add_border()


def _create_polygons_from_grid(grid: Grid) -> list[Polygon]:
    """
    Calculates the polygons represented by the specified grid. The polygons may have holes.
    """
    # create contour
    contour = plt.contour(grid.longitudes, grid.latitudes, grid.values,
                          linewidths=POLYGON_LINE_WIDTH, linestyles=POLYGON_LINE_STYLE,
                          levels=_warn_levels(), colors=[POLYGON_COLOR])

    # create polygons
    ### copied from
    ### https://gis.stackexchange.com/questions/99917/converting-matplotlib-contour-objects-to-shapely-objects
    ### user kpenner

    # we have two contours and take the second one because it's above our warn level
    multi_poly = None
    collection = contour.collections[-1]

    for path in collection.get_paths():
        poly = _create_polygon_from_path(path)
        if not poly:
            continue
        if multi_poly is None:
            multi_poly = poly
        else:
            multi_poly = multi_poly.union(poly)

    if multi_poly is None:
        return []
    if isinstance(multi_poly, Polygon):
        return [multi_poly]
    if isinstance(multi_poly, MultiPolygon):
        return multi_poly.geoms
    raise ValueError(f'Unexpected polygon: {multi_poly}')


def _create_polygon_from_path(path: Path) -> Optional[Polygon]:
    polygons = path.to_polygons()
    if not polygons:
        return None
    # in case several arrays are returned by path.to_polygons(), combine them
    if len(polygons) > 1:
        polygons_combined = np.empty(0)
        for single in polygons:
            if len(polygons_combined):
                polygons_combined = np.concatenate([polygons_combined, single])
            else:
                polygons_combined = single
        polygons = [polygons_combined]


    poly = None
    for poly_points in polygons:
        poly_longitudes = poly_points[:, 0]
        poly_latitudes = poly_points[:, 1]
        # be careful with the following---check to make sure
        # your coordinate system expects lat first, lon second
        poly_init = Polygon(list(zip(poly_longitudes, poly_latitudes)))
        if poly_init.is_valid:
            poly_clean = poly_init
        else:
            poly_clean = poly_init.buffer(0.)
        if poly is None:
            poly = poly_clean
        else:
            poly = poly.difference(poly_clean)

    return poly


def _create_geo_series_from_polygons(polygons: list[Polygon], impact: Impact) -> GeoSeries:
    """
    Converts the specified polygons into a geo object.
    """
    return GeoSeries(polygons, crs=impact.crs)
