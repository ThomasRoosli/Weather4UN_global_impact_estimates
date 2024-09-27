import logging

import numpy as np

from climada.hazard import Centroids, TropCyclone, Hazard
from climada_petals.hazard.tc_tracks_forecast import TCForecast
from w4un_hydromet_impact import CONFIG
from w4un_hydromet_impact.cross_section.exceptions import ClimadaError
from w4un_hydromet_impact.exchange.events import HazardSource
from w4un_hydromet_impact.hazard.constants import KnownWeatherDataProviders, KnownNwpModels
from w4un_hydromet_impact.hazard.intensities import find_affected_countries
from w4un_hydromet_impact.hazard.metadata import HazardMetadata, LeadTimes
from w4un_hydromet_impact.hazard.tracks.lead_times import calculate_landfalls_from_dense_tracks, \
    calculate_closest_times_from_tracks, calculate_band_falls_from_geometries_and_tracks
from w4un_hydromet_impact.hazard.tracks.names import extract_unique_storm_name_from_tc_tracks
from w4un_hydromet_impact.hazard.tracks.util import calculate_init_time
from w4un_hydromet_impact.hazard.tracks.validations import validate_tc_tracks
from w4un_hydromet_impact.hazard.validations import check_hazard_consistency
from w4un_hydromet_impact.util.dicts import update_if_missing, remove_keys

logger = logging.getLogger(__name__)


def create_hazard(tc_forecast: TCForecast, centroids: Centroids, hazard_source: HazardSource) -> TropCyclone:
    """
    Creates a TropCyclone hazard based on a weather forecast and special coordinates of interest.
    The frequencies of the individual ensemble members will be set according to the model definition.
    After creation, consistency of the output is checked by CLIMADA's check functionality.
    Note: The default optimization of CLIMADA to discard some points which are too far from the coast is not used
    because our centroid input has already been optimized to only contain coordinates of interest
    :param tc_forecast: TCForecast object of a storm event. It will be validated that the data of this object is
    attributed to the same storm name
    :param centroids: the centroids input (certain coordinates that this calculation is interested in)
    :param hazard_source: the source of the hazard (use for source-specific decisions)
    :return: A TropCyclone object based on the input data with adjusted frequencies
    """
    validate_tc_tracks(tc_forecast)
    # validation ensures that name is unique
    storm_name = extract_unique_storm_name_from_tc_tracks(tc_forecast)
    try:
        logger.debug("Creating tropical cyclone with max memory of %s GB.",
                     CONFIG.climada.tropical_cyclone.max_memory_gb)
        tropical_cyclone = TropCyclone.from_tracks(tc_forecast, centroids=centroids, ignore_distance_to_coast=True,
                                                   max_memory_gb=CONFIG.climada.tropical_cyclone.max_memory_gb,
                                                   model=CONFIG.climada.tropical_cyclone.model)
    except Exception as error:
        raise ClimadaError(f'Cannot build tropical cyclone from tracks of storm {storm_name}.') from error
    _set_frequencies_according_to_model_definition(tropical_cyclone, tc_forecast, hazard_source)
    check_hazard_consistency(tropical_cyclone)
    return tropical_cyclone


def _set_frequencies_according_to_model_definition(tropical_cyclone: TropCyclone,
                                                   tc_forecast: TCForecast,
                                                   hazard_source: HazardSource) -> None:
    """
    Sets the frequency array of the TropCyclone according to the frequency value given in the model definition.
    Example: frequencies before: [1,1,1]; frequencies after: [1/51, 1/51, 1/51]
    :param tropical_cyclone: The cyclone whose frequencies should be set
    :return:
    """
    if (hazard_source.provider, hazard_source.model) == (KnownWeatherDataProviders.ECMWF, KnownNwpModels.ENSEMBLE):
            total_frequency = np.sum(tropical_cyclone.frequency)
            tropical_cyclone.frequency[:] = tropical_cyclone.frequency[:] / total_frequency
    else:
        raise AssertionError(
            f'Unsupported hazard provider and NWP model: {hazard_source.provider}, {hazard_source.model}')


def hazard_metadata_from_tc_forecast(tc_forecast: TCForecast, hazard: Hazard) -> HazardMetadata:
    """
    Calculates the metadata of a hazard event (e.g. lead times per country) from tracks.
    :param tc_forecast: Tracks of a storm event
    :param hazard: the hazard caused by the event
    :return: the metadata
    """
    if len(tc_forecast.data) == 0:
        raise AssertionError('Missing forecast data.')

    # create list of event dates per region
    logger.debug("Calculating hazard metadata for forecast")

    event_name = extract_unique_storm_name_from_tc_tracks(tc_forecast)

    init_time = calculate_init_time(tc_forecast)

    # step 1/3: calculate first time per track that a country is entered
    lead_times_per_country = _calculate_direct_lead_times(tc_forecast)

    # add affected countries without landfall
    affected_countries_without_landfall = remove_keys(find_affected_countries(hazard), lead_times_per_country.keys())

    # step 2/3: calculate times per tracks that a country is close to
    if affected_countries_without_landfall:
        close_lead_times = _calculate_close_lead_times(affected_countries_without_landfall, tc_forecast)
        update_if_missing(lead_times_per_country, close_lead_times)

    # step 3/3: apply fallback to remaining affected countries
    remaining_countries = remove_keys(affected_countries_without_landfall, lead_times_per_country.keys())
    if remaining_countries:
        remaining_lead_times = _calculate_fallback_lead_times(remaining_countries, tc_forecast)
        update_if_missing(lead_times_per_country, remaining_lead_times)

    return HazardMetadata.from_lead_times(event_name, init_time, lead_times_per_country)


def _calculate_direct_lead_times(tc_forecast: TCForecast) -> dict[int, LeadTimes]:
    """
    Calculates the direct lead times per country from the specified tracks.
    Considers all times that a track crosses the border of a country.
    """
    resolution = CONFIG.climada.tropical_cyclone.grid_resolution
    lead_times_per_country = calculate_landfalls_from_dense_tracks(tc_forecast, resolution)

    logger.debug("Tracks have landfall in countries: %s", lead_times_per_country.keys())

    return lead_times_per_country


def _calculate_close_lead_times(affected_countries: dict[int, set[int]],
                                tracks: TCForecast) -> dict[int, LeadTimes]:
    """
    Calculates all tracks for the specified countries that are closer to that country than a configured radius.
    This function returns a dictionary with the countries as keys and a dictionary as value
    that is mapping from the index of a track to the timestamp of the first point that is closer.
    Only the specified affected countries are considered.
    """
    logger.debug("Affected countries without landfall: %s", affected_countries.keys())

    radius_km = CONFIG.climada.tropical_cyclone.landfall_radius_km

    return calculate_band_falls_from_geometries_and_tracks(tracks,
                                                           affected_countries.keys(),
                                                           radius_km)


def _calculate_fallback_lead_times(remaining_countries: dict[int, set[int]],
                                   tracks: TCForecast) -> dict[int, LeadTimes]:
    """
    Calculates the fallback lead times per country by setting the initialization date.
    Only the specified remaining countries are considered.
    The fallback times depends on the closest point of the affected tracks.
    """
    logger.debug("Applying fallback lead times to remaining affected countries: %s", remaining_countries.keys())

    # add time of affected track that is closest to country
    return calculate_closest_times_from_tracks(tracks, remaining_countries)
