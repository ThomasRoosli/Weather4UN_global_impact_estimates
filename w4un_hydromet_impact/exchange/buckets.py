"""
This module specified the climada4mch-specific buckets and their requirements regarding naming of files.

These requirements are handled via factory functions per bucket and kind of file.
"""
from w4un_hydromet_impact import CONFIG
from w4un_hydromet_impact.fabio import S3Location


def s3_location_for_weather_data_file(file_name: str) -> S3Location:
    """
    Creates a location for a weather data file.
    :param file_name: the name of the file
    :return: the location
    """
    return S3Location.create(CONFIG.buckets.weather_data, file_name)


def s3_location_for_centroid_file(file_name: str) -> S3Location:
    """
    Creates a location for a centroid file.
    :param file_name: the name of the file
    :return: the location
    """
    return S3Location.create(CONFIG.buckets.centroids, file_name)


def s3_location_for_hazard_file(file_name: str) -> S3Location:
    """
    Creates a location for a hazard file.
    :param file_name: the name of the file
    :return: the location
    """
    return S3Location.create(CONFIG.buckets.hazard, file_name)


def s3_location_for_exposure_file(file_name: str) -> S3Location:
    """
    Creates a location for an exposure file.
    :param file_name: the name of the file
    :return: the location
    """
    return S3Location.create(CONFIG.buckets.exposure, file_name)


def s3_location_for_vulnerability_file(file_name: str) -> S3Location:
    """
    Creates a location for a vulnerability file.
    :param file_name: the name of the file
    :return: the location
    """
    return S3Location.create(CONFIG.buckets.vulnerability, file_name)


def s3_location_for_outlook_file(file_name: str) -> S3Location:
    """
    Creates a location for an outlook file.
    :param file_name: the name of the file
    :return: the location
    """
    return S3Location.create(CONFIG.buckets.outlook, file_name)


def s3_location_for_hazard_plot_file(file_name: str) -> S3Location:
    """
    Creates a location for a hazard plotting file.
    :param file_name: the name of the file
    :return: the location
    """
    return S3Location.create(CONFIG.buckets.hazard, file_name)


def s3_location_for_impact_file(file_name: str) -> S3Location:
    """
    Creates a location for an impact file.
    :param file_name: the name of the file
    :return: the location
    """
    return S3Location.create(CONFIG.buckets.impact, file_name)


def s3_location_for_not_existing_file() -> S3Location:
    """
    Creates an artifial location for a non existing file. This is used to notify the calling process that
    the file does not exist and further processing is skipped.
    :return: the location
    """
    return S3Location.create('None', CONFIG.impact_calculation.not_existing_file)
