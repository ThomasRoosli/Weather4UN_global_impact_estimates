"""
This module provides functions to calculate impact data.
"""
import logging
from typing import Optional

from climada.engine.forecast import Forecast
from climada.entity import Exposures, ImpactFuncSet
from climada.hazard import Hazard
from climada.util.dates_times import datetime64_to_ordinal
from w4un_hydromet_impact.cross_section.exceptions import ClimadaError
from w4un_hydromet_impact.exchange.events import HazardSource
from w4un_hydromet_impact.geography.country import Country
from w4un_hydromet_impact.hazard.downloads import read_hazard
from w4un_hydromet_impact.hazard.metadata import HazardMetadata
from w4un_hydromet_impact.impact.data import ImpactForecastDefinitionItem
from w4un_hydromet_impact.impact.exposures.downloads import download_exposures
from w4un_hydromet_impact.impact.vulnerabilities.downloads import read_vulnerabilities
from w4un_hydromet_impact.util.dates import convert_datetime64_to_datetime

logger = logging.getLogger(__name__)


def calculate_impact_forecast(hazard_file_location: str,
                              hazard_meta_data: HazardMetadata,
                              hazard_source: HazardSource,
                              impact_forecast_definition_item: ImpactForecastDefinitionItem) -> Optional[Forecast]:
    """
    Calculates the impact forecast for the specified hazard in respect of the specified impact forecast definition.
    The definition includes one country to calculate the impact for.
    If there is no landfall within that country, the calculation returns immediately.
    Otherwise, the impact is calculated considering the specified exposures and vulnerability
    (specified by an impact function set).
    :param hazard_file_location: location of hazard file in S3
    :param hazard_meta_data: the metadata of the hazard
                             in order to access pre-calculated and country-specific hazard infos
    :param hazard_source: the hazard source (required in impact calculation)
    :param impact_forecast_definition_item: the definition of the impact forecast to calculate
                                            including the country, the exposures file and the vulnerability file
    :return: the impact forecast
    """
    country = impact_forecast_definition_item.country
    if not hazard_meta_data.has_landfall() or not hazard_meta_data.has_landfall(country.numeric):
        _log_that_no_landfall_in_country(country)
        return None

    logger.info('Checking impact for %s.', country)

    # get exposure
    exposures = _read_exposures(country)

    # get vulnerability
    vulnerability_location = impact_forecast_definition_item.vulnerability_location
    vulnerability = read_vulnerabilities(vulnerability_location)
    logger.info('Loaded vulnerability from %s', vulnerability_location)

    impact_type = impact_forecast_definition_item.impact_type

    logger.debug('Reading hazard from %s', hazard_file_location)
    hazard = read_hazard(hazard_file_location)
    logger.info('Start impact calculation for hazard %s and impact %s in %s using vulnerability file: %s',
                hazard_meta_data.event_name, impact_type, country, vulnerability_location)

    return _perform_impact_calculation(hazard, hazard_meta_data, hazard_source, exposures, vulnerability, country)


def _perform_impact_calculation(hazard: Hazard,  # pylint: disable=[R0913]
                                hazard_metadata: HazardMetadata,
                                hazard_source: HazardSource,
                                exposures: Exposures,
                                vulnerability: ImpactFuncSet,
                                country: Country) -> Forecast:
    """
    Performs the impact calculation itself.
    """
    # Adjust the event date of the hazard to the exposure (e.g. landfall in that specific country)
    lead_times = hazard_metadata.get_lead_times(country.numeric)
    # median timestamp of landfall in country
    event_date = datetime64_to_ordinal(lead_times.median)
    hazard.date[:] = event_date

    # extract the initialization time of the weather forecast data
    forecast_run = convert_datetime64_to_datetime(hazard_metadata.initialisation_time)

    try:
        impact_forecast = Forecast(
            {forecast_run: hazard},
            exposures,
            vulnerability,
            haz_model=hazard_source.provider,
            exposure_name=country.name
        )
        impact_forecast.calc()
    except Exception as error:
        raise ClimadaError(
            f'Cannot calculate impact for hazard {hazard_metadata.event_name} of type {hazard.haz_type}'
            f' in country {country}') from error

    return impact_forecast


def _read_exposures(country: Country) -> Exposures:
    logger.debug('Downloading exposures.')
    exposures = download_exposures(country)
    logger.info('Loaded exposures: %s', exposures.description)

    return exposures


def _log_that_no_landfall_in_country(country: Country) -> None:
    logger.info('Country %s does not have a landfall forecasted. Skip impact calculation.',
                country)
