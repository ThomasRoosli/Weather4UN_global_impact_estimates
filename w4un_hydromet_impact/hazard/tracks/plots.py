import copy
import logging

from matplotlib.figure import Figure

from climada.hazard import TCTracks
from w4un_hydromet_impact.cross_section.exceptions import ClimadaError
from w4un_hydromet_impact.exchange.buckets import s3_location_for_hazard_plot_file
from w4un_hydromet_impact.exchange.events import HazardSource
from w4un_hydromet_impact.fabio import S3Location
from w4un_hydromet_impact.hazard.file_names import build_file_name_from_hazard
from w4un_hydromet_impact.hazard.metadata import HazardMetadata
from w4un_hydromet_impact.hazard.tracks.names import extract_storm_names_from_tc_tracks
from w4un_hydromet_impact.util.uploads import upload_figure

logger = logging.getLogger(__name__)


def upload_tracks(tc_tracks: TCTracks, hazard_metadata: HazardMetadata, hazard_source: HazardSource) -> S3Location:
    """
    Plots the tracks of a forecast and uploads them to the product browser
    using file name '<hazard type>_<storm name>_<init_time>_tracks.png', e.g. 'TC_ELOISE_20130925060000_tracks.png'
    """
    s3_location_tracks_plot = s3_location_for_hazard_plot_file(
        build_file_name_from_hazard(hazard_metadata, hazard_source, suffix='tracks.png'))
    tracks_plot = _plot_tracks(tc_tracks)
    upload_figure(tracks_plot, s3_location_tracks_plot)
    logger.info('Tracks plotted successfully. Stored %s', s3_location_tracks_plot)
    return s3_location_tracks_plot


def _plot_tracks(tc_tracks: TCTracks) -> Figure:
    """
    Plots the specified tracks.
    :param tc_tracks: the tracks
    :return: a figure representing the plot
    """
    logger.info('Trying to plot tracks.')

    storm_names = extract_storm_names_from_tc_tracks(tc_tracks)
    try:
        tracks_knots = _tc_tracks_in_knots(tc_tracks)
        plotted_tracks = tracks_knots.plot()
        return plotted_tracks.figure
    except Exception as error:
        raise ClimadaError(f'Cannot plot tracks: {storm_names}') from error


# transformation in kn needed until issue
# https://github.com/CLIMADA-project/climada_python/issues/456 is resolved
def _tc_tracks_in_knots(tc_tracks: TCTracks) -> TCTracks:
    tracks_knots = copy.deepcopy(tc_tracks)
    for item_i in tracks_knots.data:
        # only change unit if it is in m/s otherwise continue
        if item_i.max_sustained_wind_unit != 'm/s':
            continue
        # change unit from m/s to kn
        item_i['max_sustained_wind'] = item_i.max_sustained_wind * 1.943844
        item_i['max_sustained_wind_unit'] = 'kn'
    return tracks_knots
