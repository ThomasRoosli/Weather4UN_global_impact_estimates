"""
This module provides methods to download data from S3 during processing.
"""

from climada.hazard import Hazard
from w4un_hydromet_impact.hazard.metadata import HazardMetadata
from w4un_hydromet_impact.hazard.validations import check_hazard_consistency, validate_hazard, check_hazard_metadata


def read_hazard(file_location: str) -> Hazard:
    """
    Downloads a hazard from the specified location.
    """
    hazard = Hazard.from_hdf5(file_location)

    check_hazard_consistency(hazard)
    validate_hazard(hazard)

    return hazard


def read_hazard_metadata(file_location: str) -> HazardMetadata:
    """
    Downloads hazard metadata from the specified location.
    """
    with open(file_location, 'rb') as stream:
        metadata = HazardMetadata.read_from_json(stream)
    check_hazard_metadata(metadata)
    return metadata
