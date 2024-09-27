import logging

from xarray import DataArray

from climada_petals.hazard.tc_tracks_forecast import TCForecast

from exchange.events import HazardExtractedEvent, JobData, HazardSource, HazardProductType, \
    HazardProductRealizationCreatedEvent, ExportDestinations
from fabio import S3Location
from fabio.kafka_facade import send_kafka_message
from hazard.centroids.downloads import download_centroids
from hazard.constants import KnownHazardSources
from hazard.metadata import HazardMetadata
from hazard.plots import upload_intensities
from hazard.store import save_hazard_data
from hazard.tracks.plots import upload_tracks
from hazard.tropical_cyclone.cyclone_hazards import create_hazard, hazard_metadata_from_tc_forecast
from hazard.tropical_cyclone.ecmwf import load_tropical_cyclones_by_ecmwf
from hazard.tropical_cyclone.forecasts import make_name_and_sid_unique

# Heuristic value, good compromise between computation duration and sufficient resolution.
# Corresponds to 30 minutes.
TIME_STEP = 0.5

logger = logging.getLogger(__name__)

# type alias to express the possible types of events that can be sent
HazardEventTypes = HazardExtractedEvent | HazardProductRealizationCreatedEvent


def calculate_hazard(weather_data_location: S3Location,
                     centroid_location: S3Location,
                     hazard_source: HazardSource,
                     job_data: JobData,
                     export_destinations: ExportDestinations) -> list[HazardEventTypes]:
    """
    Calculates the hazard of the specified weather forecast.
    :param weather_data_location: the location of the file containing the weather data in S3
    :param centroid_location: the location of the file containing the centroid to be used in S3
    :param hazard_source: the hazard source to be added to new events
    :param job_data: the job data to be added to new events
    :param export_destinations: allowed destinations for hazard products
    :return: a list of the events that have been sent
    """
    match hazard_source:
        case KnownHazardSources.TROPICAL_CYCLONE_FROM_ECMWF:
            return _load_data_and_calculate_tc_hazard_by_ecmwf(weather_data_location,
                                                               centroid_location,
                                                               hazard_source,
                                                               job_data,
                                                               export_destinations)

        case _:
            raise AssertionError(
                f'Calculating hazard from {hazard_source.primary_key_string()} is not supported.')
    assert False  # this line is never reached and silences mypy "error: Missing return statement  [return]"


def _log_hazard_calculation_start(centroid_location: S3Location,
                                  hazard_source: HazardSource,
                                  weather_data_location: S3Location) -> None:
    logger.info('Beginning hazard calculation for %s. Weather data: %s, centroid: %s',
                hazard_source.primary_key_string(), weather_data_location.path, centroid_location.path)


def _load_data_and_calculate_tc_hazard_by_ecmwf(weather_data_location: S3Location,
                                                centroid_location: S3Location,
                                                hazard_source: HazardSource,
                                                job_data: JobData,
                                                export_destinations: ExportDestinations) -> list[HazardEventTypes]:
    """
    Calculates the hazard of the specified weather forecast
    assuming that it represents ensemble tracks of a tropical cyclone and is provided by ECMWF.
    :param weather_data_location: the location of the file containing the weather data in S3
    :param centroid_location: the location of the file containing the centroid to be used in S3
    :param hazard_source: the hazard source to be added to new events
    :param job_data: the job data to be added to new events
    :return: a list of the events that have been sent
    """
    _log_hazard_calculation_start(centroid_location, hazard_source, weather_data_location)

    tc_forecasts = load_tropical_cyclones_by_ecmwf(weather_data_location)

    if len(tc_forecasts) == 0:
        return []

    return _calculate_hazard_from_forecasts(tc_forecasts,
                                            centroid_location,
                                            hazard_source,
                                            job_data,
                                            export_destinations)


def _calculate_hazard_from_forecasts(tc_forecasts: list[TCForecast],
                                     centroid_location: S3Location,
                                     hazard_source: HazardSource,
                                     job_data: JobData,
                                     export_destinations: ExportDestinations) -> list[HazardEventTypes]:
    """
    Calculates the hazard of the specified tropical cyclone forecasts.
    :param tc_forecasts: the forecasts
    :param centroid_location: the location of the file containing the centroid to be used in S3
    :param hazard_source: the hazard source to be added to new events
    :param job_data: the job data to be added to new events
    :return: a list of the events that have been sent
    """

    logger.info('Read centroid data.')
    centroids = download_centroids(centroid_location)

    logger.info('Calculate hazard from tropical cyclone tracks and save files.')
    hazard_events: list[HazardEventTypes] = []
    for tc_forecast in tc_forecasts:
        make_name_and_sid_unique(tc_forecast)

        # Our input data might only have six-hour reports. We need a better resolution, so we interpolate it.
        tc_forecast.equal_timestep(time_step_h=TIME_STEP)

        tropical_cyclone = create_hazard(tc_forecast, centroids, hazard_source)
        hazard_metadata: HazardMetadata = hazard_metadata_from_tc_forecast(tc_forecast, tropical_cyclone)

        s3_location_hazard, s3_location_metadata = save_hazard_data(tropical_cyclone,
                                                                    hazard_metadata,
                                                                    hazard_source)

        hazard_extracted_event = HazardExtractedEvent.create(s3_location_hazard.file_name,
                                                             s3_location_metadata.file_name,
                                                             hazard_source,
                                                             job_data,
                                                             export_destinations)


        hazard_events.append(hazard_extracted_event)

        # plot, upload and send intensities
        intensities_location = upload_intensities(tropical_cyclone, hazard_metadata, hazard_source)
        if intensities_location is not None:
            # skip if no intensities have been calculated
            hazard_events.append(_send_event(
                hazard_source,
                s3_location_metadata,
                intensities_location,
                HazardProductType.INTENSITIES,
                job_data,
                export_destinations
            ))
        # plot, upload and send tracks
        tracks_location = upload_tracks(tc_forecast, hazard_metadata, hazard_source)
        hazard_events.append(_send_event(
            hazard_source,
            s3_location_metadata,
            tracks_location,
            HazardProductType.TRACKS,
            job_data,
            export_destinations
        ))

        # enforce clean up
        del tropical_cyclone, hazard_metadata

    logger.info('Done with hazard calculation.')
    return hazard_events


def _send_event(
        hazard_source: HazardSource,
        metadata: S3Location,
        product_location: S3Location,
        product_type: HazardProductType,
        job_data: JobData,
        export_destinations: ExportDestinations) -> HazardProductRealizationCreatedEvent:
    realization_event: HazardProductRealizationCreatedEvent = HazardProductRealizationCreatedEvent.create(
        metadata.file_name,
        hazard_source,
        product_type,
        product_location.file_name,
        job_data,
        export_destinations
    )

    return realization_event
