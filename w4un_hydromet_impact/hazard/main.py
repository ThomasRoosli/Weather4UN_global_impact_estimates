import logging
from typing import Tuple

# from xarray import DataArray

from climada.hazard import Centroids
from climada_petals.hazard.tc_tracks_forecast import TCForecast

from w4un_hydromet_impact.exchange.events import HazardSource
from w4un_hydromet_impact.hazard.constants import KnownHazardSources
from w4un_hydromet_impact.hazard.metadata import HazardMetadata
# from w4un_hydromet_impact.hazard.plots import upload_intensities
from w4un_hydromet_impact.hazard.store import save_hazard_data
# from w4un_hydromet_impact.hazard.tracks.plots import upload_tracks
from w4un_hydromet_impact.hazard.tropical_cyclone.cyclone_hazards import create_hazard, hazard_metadata_from_tc_forecast
from w4un_hydromet_impact.hazard.tropical_cyclone.ecmwf import load_tropical_cyclones_by_ecmwf
from w4un_hydromet_impact.hazard.tropical_cyclone.forecasts import make_name_and_sid_unique

# Heuristic value, good compromise between computation duration and sufficient resolution.
# Corresponds to 30 minutes.
TIME_STEP = 0.5

logger = logging.getLogger(__name__)

# type alias to express the possible types of events that can be sent
# HazardEventTypes = HazardExtractedEvent | HazardProductRealizationCreatedEvent


def calculate_hazard(weather_data_location: str,
                     centroid_location: str,
                     hazard_source: HazardSource = KnownHazardSources.TROPICAL_CYCLONE_FROM_ECMWF,
                     ) -> list[Tuple]:
    """
    Calculates the hazard of the specified weather forecast.
    :param weather_data_location: the location of the file containing the weather data in S3
    :param centroid_location: the location of the file containing the centroid to be used in S3
    :param hazard_source: the hazard source to be added to new events
    :param job_data: the job data to be added to new events
    :param export_destinations: allowed destinations for hazard products
    :return: a list of the events that have been sent
    """
    if hazard_source == KnownHazardSources.TROPICAL_CYCLONE_FROM_ECMWF:
            return _load_data_and_calculate_tc_hazard_by_ecmwf(weather_data_location,
                                                               centroid_location,
                                                               hazard_source,
                                                               )

    else:
        raise AssertionError(
            f'Calculating hazard from {hazard_source.primary_key_string()} is not supported.')


def _log_hazard_calculation_start(centroid_location: str,
                                  hazard_source: HazardSource,
                                  weather_data_location: str) -> None:
    logger.info('Beginning hazard calculation for %s. Weather data: %s, centroid: %s',
                hazard_source.primary_key_string(), weather_data_location.path, centroid_location.path)


def _load_data_and_calculate_tc_hazard_by_ecmwf(weather_data_location: str,
                                                centroid_location: str,
                                                hazard_source: HazardSource,
                                                ) -> list[Tuple]:
    """
    Calculates the hazard of the specified weather forecast
    assuming that it represents ensemble tracks of a tropical cyclone and is provided by ECMWF.
    :param weather_data_location: the location of the file containing the weather data in S3
    :param centroid_location: the location of the file containing the centroid to be used in S3
    :param hazard_source: the hazard source to be added to new events
    :param job_data: the job data to be added to new events
    :return: a list of the events that have been sent
    """

    tc_forecasts = load_tropical_cyclones_by_ecmwf(weather_data_location)

    if len(tc_forecasts) == 0:
        return []

    return _calculate_hazard_from_forecasts(tc_forecasts,
                                            centroid_location,
                                            hazard_source)


def _calculate_hazard_from_forecasts(tc_forecasts: list[TCForecast],
                                     centroid_location: str,
                                     hazard_source: HazardSource) -> list[Tuple]:
    """
    Calculates the hazard of the specified tropical cyclone forecasts.
    :param tc_forecasts: the forecasts
    :param centroid_location: the location of the file containing the centroid to be used in S3
    :param hazard_source: the hazard source to be added to new events
    :param job_data: the job data to be added to new events
    :return: a list of the events that have been sent
    """

    logger.info('Read centroid data.')
    centroids = Centroids.from_hdf5(centroid_location)

    logger.info('Calculate hazard from tropical cyclone tracks and save files.')
    hazard_events: list[Tuple] = []
    for tc_forecast in tc_forecasts:
        make_name_and_sid_unique(tc_forecast)

        # Our input data might only have six-hour reports. We need a better resolution, so we interpolate it.
        tc_forecast.equal_timestep(time_step_h=TIME_STEP)

        tropical_cyclone = create_hazard(tc_forecast, centroids, hazard_source)
        hazard_metadata: HazardMetadata = hazard_metadata_from_tc_forecast(tc_forecast, tropical_cyclone)

        file_location_hazard, file_location_metadata = save_hazard_data(tropical_cyclone,
                                                                        hazard_metadata,
                                                                        hazard_source)



        hazard_events.append((file_location_hazard, file_location_metadata))

        # # plot, upload and send intensities
        # intensities_location = upload_intensities(tropical_cyclone, hazard_metadata, hazard_source)
        # if intensities_location is not None:
        #     # skip if no intensities have been calculated
        #     hazard_events.append(_send_event(
        #         hazard_source,
        #         s3_location_metadata,
        #         intensities_location,
        #         HazardProductType.INTENSITIES,
        #         job_data,
        #         export_destinations
        #     ))
        # # plot, upload and send tracks
        # tracks_location = upload_tracks(tc_forecast, hazard_metadata, hazard_source)
        # hazard_events.append(_send_event(
        #     hazard_source,
        #     s3_location_metadata,
        #     tracks_location,
        #     HazardProductType.TRACKS,
        #     job_data,
        #     export_destinations
        # ))

        # enforce clean up
        del tropical_cyclone, hazard_metadata

    logger.info('Done with hazard calculation.')
    return hazard_events


# def _send_event(
#         hazard_source: HazardSource,
#         metadata: str,
#         product_location: str,
#         product_type: HazardProductType,
#         job_data: JobData,
#         export_destinations: ExportDestinations) -> HazardProductRealizationCreatedEvent:
#     realization_event: HazardProductRealizationCreatedEvent = HazardProductRealizationCreatedEvent.create(
#         metadata.file_name,
#         hazard_source,
#         product_type,
#         product_location.file_name,
#         job_data,
#         export_destinations
#     )
#
#     return realization_event
