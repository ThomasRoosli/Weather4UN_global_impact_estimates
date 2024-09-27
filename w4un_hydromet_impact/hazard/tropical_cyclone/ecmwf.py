"""
Module for loading a tropical cyclone stored in format used by ECMWF.
"""
import logging

from climada_petals.hazard.tc_tracks_forecast import TCForecast
from w4un_hydromet_impact.cross_section.exceptions import ClimadaError
from w4un_hydromet_impact.hazard.tropical_cyclone.forecasts import create_ensemble_tropical_cyclone_forecast_from_ecmwf, \
    filter_and_group_tropical_cyclone_forecast

logger = logging.getLogger(__name__)


def load_tropical_cyclones_by_ecmwf(weather_data_location: str) -> list[TCForecast]:
    """
    Loads the tropical cyclones from the specified weather forecast
    assuming that it represents ensemble tracks of a tropical cyclone and is provided by ECMWF.
    :param weather_data_location: the location of the file containing the weather data in S3
    :return: the tropical cyclones if any
    """
    logger.info('Read weather data, filter and group the tracks.')
    ensemble_tc_forecast = create_ensemble_tropical_cyclone_forecast_from_ecmwf(
        weather_data_location)
    filtered_and_grouped_tc_forecasts = filter_and_group_tropical_cyclone_forecast(ensemble_tc_forecast)

    if len(filtered_and_grouped_tc_forecasts) == 0:
        logger.info('Finished filtering and grouping the tracks, there are no filtered tracks in the forecast '
                    'and the event handling has stopped')
        return []
    logger.info('Finished filtering and grouping the tracks, including the tracks %s.',
                [tc_forecast.data[0].attrs['name'] for tc_forecast in filtered_and_grouped_tc_forecasts])

    return filtered_and_grouped_tc_forecasts



