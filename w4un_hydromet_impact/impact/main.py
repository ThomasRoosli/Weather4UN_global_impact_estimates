import json
import logging
import re
from typing import Tuple

import numpy as np

from climada.engine import Impact
from climada.engine.forecast import Forecast
from w4un_hydromet_impact import CONFIG
from w4un_hydromet_impact.cross_section.exceptions import ClimadaError
from w4un_hydromet_impact.exchange.events import CalculateImpactProperties, HazardSource

from w4un_hydromet_impact.geography.country import create_country_from_identifier
from w4un_hydromet_impact.hazard.downloads import read_hazard_metadata

from w4un_hydromet_impact.impact.calculations import calculate_impact_forecast
from w4un_hydromet_impact.impact.data import ImpactForecastDefinitionItem
from w4un_hydromet_impact.impact.exposures.downloads import build_exposures_file_name_from_prefix_and_country

from w4un_hydromet_impact.impact.store import save_impact_forecast


logger = logging.getLogger(__name__)



def calculate_impact(file_location_hazard: str,
                     file_location_metadata: str,
                     hazard_source: HazardSource,
                     calculate_impact_properties: CalculateImpactProperties) -> list[Tuple]:
    """
    Calculates the impact of the specified hazard regarding the specified impact definition.
    :param hazard: A hazard forecast extracted from a weather forecast.
    :param calculate_impact_properties: the arguments of the impact calculation
    :param job_data: the job data to be added to new events
    :return: list of issued events to notify about the impact calculation
    """
    # ignore sonarqube rule: Too many local variables
    # pylint: disable=R0914


    impact_events: list[Tuple] = []
    country = calculate_impact_properties.exposure.country
    impact_type = calculate_impact_properties.type

    logger.info('Beginning impact calculation for %s regarding %s. Hazard location: %s, metadata location: %s',
                country, impact_type, file_location_hazard, file_location_metadata)

    # reading input data from S3
    logger.info("Reading hazard metadata from %s", file_location_metadata)
    hazard_metadata_content = read_hazard_metadata(file_location_metadata)
    logger.info("Hazard represents event: %s", hazard_metadata_content.event_name)

    # calculate
    impact_forecast_definition_item = _create_impact_forecast_definition_item(calculate_impact_properties)
    impact_forecast = calculate_impact_forecast(file_location_hazard,
                                                hazard_metadata_content,
                                                hazard_source,
                                                impact_forecast_definition_item)

    if impact_forecast is not None:
        data, matrix, summary, polygon = save_impact_forecast(impact_forecast,
                                                              impact_type,
                                                              hazard_metadata_content,
                                                              hazard_source)


        # send impact calculated event
        impact_events.append((data, matrix, summary, polygon))



    return impact_events


def _extract_one_and_only_capture_group_from_filename(filename: str, regexp: str) -> str:
    """
    Extracts the only capture group from a filename using a provided regular expression pattern.
    """
    match = re.match(regexp, filename)
    if match:
        if len(match.groups()) != 1:
            raise ValueError(f"Regular expression '{regexp}' should have exactly one capturing group.")
        # Assumes the number is captured in group 1 of the regular expression pattern
        return match.group(1)

    raise ValueError(f'Filename {filename} does not match the regexp {regexp}.')



def _create_impact_forecast_definition_item(
        calculate_impact_properties: CalculateImpactProperties) -> ImpactForecastDefinitionItem:
    """
    Creates an impact forecast definition item from the specified properties.
    """
    country_id = calculate_impact_properties.exposure.country

    # build exposure file name
    try:
        country = create_country_from_identifier(country_id)
    except Exception as error:
        raise ClimadaError(f'Country "{country_id}" not found.') from error

    vulnerability_file_name = calculate_impact_properties.vulnerability
    impact_type = calculate_impact_properties.type
    return ImpactForecastDefinitionItem.create(country,
                                               vulnerability_file_name,
                                               impact_type)
