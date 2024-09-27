"""
This module provides functions to save hazard data.
"""
import json
import logging

from climada.hazard import Hazard

from w4un_hydromet_impact.exchange.events import HazardSource
from w4un_hydromet_impact.hazard.file_names import build_file_name_from_hazard
from w4un_hydromet_impact.hazard.metadata import HazardMetadata

from w4un_hydromet_impact.hazard.validations import check_hazard_metadata, check_hazard_consistency, validate_hazard

logger = logging.getLogger(__name__)



def save_hazard_data(hazard: Hazard, metadata: HazardMetadata,
                     source: HazardSource) -> tuple[str, str]:
    """
    Writes a hazard and its metadata to our cloud object storage.
    The file names of the output are constructed by extracting the base name, the hazard initialization time
    and the hazard type so that a structure like '<hazard type>_<base name>_<init_time>_hazard.hdf5'
    (e.g. 'TC_ELOISE_20130925060000_hazard.hdf5') or '<hazard type>_<base name>_<init_time>_hazard_metadata.json'
    (e.g. 'TC_ELOISE_20130925060000_hazard_metadata.json') is created.
    The hazard input is checked for consistency by CLIMADA's check functionality.
    Furthermore, the hazard input is validated by checking if all of its members have the same name
    :param hazard: the hazard to be saved. It must contain data which has the same base name
    :param metadata: the metadata of the hazard
    :param source: the source of the hazard
    :return: the location of the hazard file and the location of the metadata file
    """
    check_hazard_consistency(hazard)
    validate_hazard(hazard)
    check_hazard_metadata(metadata)

    file_location_hazard = build_file_name_from_hazard(metadata, source, suffix='hazard.hdf5')
    hazard.write_hdf5(file_location_hazard)
    logger.info('Hazard calculated successfully. Stored %s', file_location_hazard)

    file_location_metadata = build_file_name_from_hazard(metadata, source, suffix='hazard_metadata.json')
    with open(file_location_metadata, 'wb') as file:
        metadata.write_json(file)
    logger.info('Hazard metadata calculated successfully. Stored %s', file_location_metadata)

    return file_location_hazard, file_location_metadata
