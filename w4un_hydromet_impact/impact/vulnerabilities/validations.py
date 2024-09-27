"""
This module contains functions validating vulnerabilities.
"""
import logging

from climada.entity import ImpactFuncSet
from w4un_hydromet_impact.fabio import S3Location

logger = logging.getLogger(__name__)


def check_vulnerabilities_consistency(vulnerabilities: ImpactFuncSet, vulnerabilities_location: S3Location) -> None:
    try:
        vulnerabilities.check()
    except ValueError as value_error:
        raise AssertionError(
            f'Imported invalid vulnerabilities from {vulnerabilities_location}'
            f' with error: {value_error}') from value_error
