import logging
from typing import Optional

from matplotlib.figure import Figure

from climada.hazard import Hazard
from climada.util.coordinates import latlon_bounds
from w4un_hydromet_impact.cross_section.exceptions import ClimadaError
from w4un_hydromet_impact.hazard.metadata import HazardMetadata

logger = logging.getLogger(__name__)


def _plot_intensities(hazard: Hazard, metadata: HazardMetadata) -> Optional[Figure]:
    """
    Plots the hazard's intensities.
    :param hazard: the hazard
    :param metadata: the metadata of the hazard
    :return: a figure representing the plot
    """
    logger.info('Trying to plot hazard')

    try:
        return _create_hazard_plot(hazard, metadata)
    except AssertionError:
        logger.exception(
            'Plotting of hazard failed, probably because there were no non-zero intensities in Hazard to plot. '
            + 'Continuing pipeline.'
        )
        return None
    except Exception as error:
        raise ClimadaError(f'Cannot plot hazard: {metadata.event_name}') from error


def _create_hazard_plot(hazard: Hazard, metadata: HazardMetadata) -> Figure:
    """
    Write the intensities of a hazard to a png file, cropped to the extent of nonzero values or a custom.
    :param hazard: Hazard with intensity
    :param metadata: the hazard's metadata
    :return: a figure representing the plot
    """
    # calculate extent in order to crop plot to non-zero intensities
    extent = _calculate_bounds(hazard, metadata.event_name)

    # crop the hazard
    logger.info("Cropping hazard %s to %s before plotting.", metadata.event_name, extent)
    hazard_cropped = hazard.select(extent=extent)
    plotted_hazard = hazard_cropped.plot_intensity(0)
    return plotted_hazard.figure


def _calculate_bounds(hazard: Hazard, event_name: str) -> tuple[float, float, float, float]:
    """
    Calculates the bounds of the specified hazard including all non-zero intensities.
    :return: the extent as (minimum longitude, maximum longitude, minimum latitude, maximum latitude)
    """
    non_zero_indices = hazard.intensity.max(axis=0).col
    if non_zero_indices.size == 0:
        raise AssertionError(f'No non-zero intensities for hazard {event_name}, therefore not plotted.')

    bounds = latlon_bounds(
        hazard.centroids.lat[non_zero_indices],
        hazard.centroids.lon[non_zero_indices]
    )
    # (lon_min, lat_min, lon_max, lat_max) -> (lon_min, lon_max, lat_min, lat_max)
    return bounds[0], bounds[2], bounds[1], bounds[3]
