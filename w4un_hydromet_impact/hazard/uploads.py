"""
This module provides methods to upload hazard-related data into S3 during processing.
"""
import logging
from io import BytesIO
from tempfile import NamedTemporaryFile

from climada.hazard import Hazard
from w4un_hydromet_impact.cross_section.exceptions import ClimadaError, HazardMetadataError
from w4un_hydromet_impact.fabio import S3Location
from w4un_hydromet_impact.fabio.s3_facade import upload_file
from w4un_hydromet_impact.hazard.metadata import HazardMetadata

logger = logging.getLogger(__name__)


def upload_hazard(hazard: Hazard, s3_location: S3Location) -> None:
    """
    Uploads the specified hazard into the specified location.
    """
    with NamedTemporaryFile() as tmp_file:
        try:
            hazard.write_hdf5(tmp_file.name)
        except Exception as error:
            raise ClimadaError(
                f'Cannot serialize hazard {hazard.event_name} for file {s3_location.file_name}.') from error
        tmp_file.flush()
        upload_file(tmp_file, s3_location)


def upload_hazard_metadata(metadata: HazardMetadata, s3_location: S3Location) -> None:
    """
    Uploads the specified hazard metadata into the specified location.
    """
    with BytesIO() as file:
        try:
            metadata.write_json(file)
        except Exception as error:
            raise HazardMetadataError(f'Cannot serialize hazard metadata for file {s3_location.file_name}.') from error
        upload_file(file, s3_location)
