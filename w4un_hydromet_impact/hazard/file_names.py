"""
This module provides functions to build names for hazard-related files.
"""
import pandas as pd

from w4un_hydromet_impact.exchange.events import HazardSource
from w4un_hydromet_impact.hazard.metadata import HazardMetadata

# year, month, day, hours, minutes, seconds
_FILE_NAME_DATE_FORMAT = "%Y%m%d%H%M%S"


def build_file_name_from_hazard(metadata: HazardMetadata, source: HazardSource, suffix: str) -> str:
    """
    Builds a unique file name from a hazard's metadata.
    E.g. if hazard type is TC, provider is ECMWF, hazard is named ELOISE, initialization time is 2023-06-08 at 12 pm,
    and suffix is 'hazard.hdf5', then the name is going to be 'TC_ECMWF_ELOISE_20230608120000_hazard.hdf5'.
    :param metadata: the metadata of the hazard
    :param source: the source of the hazard
    :param suffix: a suffix identifying the kind of the file
    """
    hazard_type = source.type  # e.g. 'TC'
    provider = source.provider  # e.g. 'ECMWF'
    base_name = metadata.event_name  # e.g. 'ELOISE' or 'a75'
    init_time = pd.to_datetime(metadata.initialisation_time).strftime(_FILE_NAME_DATE_FORMAT)  # e.g. 20230608104603
    return f'{hazard_type}_{provider}_{base_name}_{init_time}_{suffix}'
    # e.g. 'TC_ECMWF_ELOISE_20230608120000_hazard.hdf5'
