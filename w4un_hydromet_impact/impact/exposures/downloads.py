import logging
from typing import Optional

from climada.entity import Exposures
from climada.util.api_client import Client
from w4un_hydromet_impact.geography.country import create_country_from_identifier, Country

climada_client = Client()
# just hardcode the climada api to be online, the check if it is online, does not work with the Lab-VM proxy
# climada_client.online = True

logger = logging.getLogger(__name__)

# Mapping from a prefix of the impact type to the prefix of the corresponding exposure file
# when defined using the country
_IMPACT_TYPE_PREFIX_TO_EXPOSURE_FILE_PREFIX_MAPPING = {'exposed_population': 'LitPop_pop_150arcsec_',
                                                       'direct_economic_damage': 'LitPop_150arcsec_'}


def download_exposures(country: Country) -> Exposures:
    """
    Downloads the requested exposure file from S3 and transforms it into an exposures object.
    Afterward, the built-in checks of CLIMADA for exposures are run.
    :param country: The name of the country.
    :return: valid exposures object with reduced extent
    """
    path = climada_client.download_dataset(
                dataset=climada_client.get_dataset_info(data_type='litpop',
                                                        properties={'country_iso3alpha': country.alpha3,
                                                                    'exponents':'(0,1)',
                                                                    'fin_mode':'pop',
                                                                    #'version':'v2'
                                                                    }
                                                        )
            )[1][0]
    exposures = Exposures.from_hdf5(path)

    return exposures


# def download_exposures(s3_location: S3Location, expected_country: Optional[Country] = None) -> Exposures:
#     """
#     Downloads the requested exposure file from S3 and transforms it into an exposures object.
#     Afterward, the built-in checks of CLIMADA for exposures are run.
#     :param s3_location: The location of the file in the S3 bucket.
#     :param expected_country: A country that is expected to be referenced from the exposures (only checked if specified)
#     :return: valid exposures object with reduced extent
#     """
#     with download_as_tempfile(s3_location) as tmp_downloaded_exposures:
#         try:
#             exposures = Exposures.from_hdf5(tmp_downloaded_exposures.name)
#         except Exception as error:
#             raise ClimadaError(
#                 f'Cannot deserialize exposures from {s3_location}.') from error
#     check_exposures_consistency(exposures, s3_location)
#     if expected_country:
#         assert_exposures_match_country(exposures, expected_country)
#     return exposures


def exposures_file_name_by_country(country_id: "str | int", impact_type: str) -> str:
    """
    Derives the name of exposure file from impact type and country.
    E.g., for country 'Mozambique' (or 'MOZ' or 508) and impact 'exposed_population_33mps',
    the file name will be 'LitPop_pop_150arcsec_MOZ.hdf5'.
    :param country_id: an identifier of the country; either as name, ISO-3166 alpha-3 or ISO-3166 numeric code
    :param impact_type: the impact type
    :return: the name of the exposures file
    """
    if not country_id:
        raise AssertionError('Missing country.')
    if not impact_type:
        raise AssertionError('Missing impact type.')

    country = create_country_from_identifier(country_id)

    exposure_file_name_part = ''
    for impact_type_prefix, exposure_file_prefix in _IMPACT_TYPE_PREFIX_TO_EXPOSURE_FILE_PREFIX_MAPPING.items():
        if impact_type.startswith(impact_type_prefix):
            exposure_file_name_part = exposure_file_prefix
            break
    if not exposure_file_name_part:
        raise ValueError(f'Exposure not defined for impact_type equals {impact_type} and country {country}')
    return build_exposures_file_name_from_prefix_and_country(exposure_file_name_part, country)


def build_exposures_file_name_from_prefix_and_country(prefix: str, country: Country) -> str:
    """
    Builds the name of an exposures file from a prefix and a country.
    E.g., for country 'Mozambique' and prefix 'LitPop_pop_150arcsec_',
    the file name will be 'LitPop_pop_150arcsec_MOZ.hdf5'.
    :param prefix: a prefix of the exposures file name
    :param country: the country that the exposures file is associated with
    :return: the name of the exposures file
    """
    return f'{prefix}{country.alpha3}.hdf5'
