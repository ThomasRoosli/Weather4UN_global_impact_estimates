"""
This module provides functions to validate general hazard-related objects.
"""
import logging

from climada.hazard import Hazard
from w4un_hydromet_impact.hazard.metadata import HazardMetadata
from w4un_hydromet_impact.hazard.names import extract_base_names_from_hazard

logger = logging.getLogger(__name__)


def check_hazard_metadata(metadata: HazardMetadata) -> None:
    try:
        metadata.check()
    except ValueError as value_error:
        raise AssertionError(f'Hazard metadata did not pass consistency check: {value_error}') from value_error


def check_hazard_consistency(hazard: Hazard) -> None:
    try:
        hazard.check()
    except ValueError as value_error:
        raise AssertionError(
            f'Hazard of type {hazard.haz_type} did not pass consistency check: {value_error}') from value_error


def validate_hazard(hazard: Hazard) -> None:
    base_names = extract_base_names_from_hazard(hazard)
    if len(base_names) > 1:
        raise ValueError(
            f'Problem with input names of hazard of type {hazard.haz_type}. More than one base name: {base_names}')
