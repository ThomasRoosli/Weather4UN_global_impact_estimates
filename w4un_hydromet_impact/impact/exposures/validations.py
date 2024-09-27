"""
This module contains functions validating exposures.
"""
import logging

import numpy as np

from climada.entity import Exposures
from w4un_hydromet_impact.geography.country import Country
from w4un_hydromet_impact.fabio import S3Location

logger = logging.getLogger(__name__)


def check_exposures_consistency(exposures: Exposures, exposures_location: S3Location) -> None:
    try:
        exposures.check()
    except ValueError as value_error:
        raise AssertionError(
            f'Imported invalid exposures from {exposures_location}'
            f' with error: {value_error}') from value_error


def assert_exposures_match_country(exposures: Exposures, country: Country) -> None:
    """
    Asserts that the region of the specified exposures matches the specified country.
    """

    country_codes_exposures = exposures.gdf.region_id.unique()
    country_codes_exposures_count = len(country_codes_exposures)
    if country_codes_exposures_count == 0:
        raise AssertionError(
            f'Exposures "{exposures.description}" do not contain any country.')
    if country_codes_exposures_count > 1:
        raise AssertionError(
            f'Exposures "{exposures.description}" contain more than one country: {np.sort(country_codes_exposures)}')

    if country_codes_exposures[0] != country.numeric:
        raise ValueError(f'Region {country_codes_exposures[0]} from "{exposures.description}"'
                         f' does not match country code {country}.')
