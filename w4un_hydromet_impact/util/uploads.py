"""
This module provides methods to upload common data into S3 during processing.
"""
import json
import logging
import os
from io import BytesIO, TextIOWrapper
from tempfile import NamedTemporaryFile
from typing import Any

from geopandas import GeoSeries
from matplotlib import pyplot as plt
from matplotlib.figure import Figure

from w4un_hydromet_impact.cross_section.exceptions import PlottingError
from w4un_hydromet_impact.fabio import S3Location
from w4un_hydromet_impact.fabio.s3_facade import upload_file

logger = logging.getLogger(__name__)


def upload_json(obj: Any, s3_location: S3Location) -> None:
    """
    Uploads the specified object as JSON file into the specified location.
    """
    with BytesIO() as file, TextIOWrapper(file, encoding='utf-8') as wrapper:
        json.dump(obj, wrapper, indent=4)
        wrapper.flush()
        upload_file(file, s3_location)


def upload_geo_object(geo_object: GeoSeries, s3_location: S3Location) -> None:
    """
    Uploads the specified geo object as JSON file into the specified location.
    """
    # to_file supports file name only; alternatives do not support driver
    with NamedTemporaryFile(mode='w+') as tmp_file:
        geo_object.to_file(tmp_file.name, driver='GeoJSON')
        tmp_file.flush()
        # cannot pass tmp_file directly because it is text-based
        with open(tmp_file.name, 'rb') as file:
            upload_file(file, s3_location)


def upload_figure(figure: Figure, s3_location: S3Location) -> None:
    """
    Upload the specified figure into the specified location.
    """
    with NamedTemporaryFile(mode='w+b') as tmp_file:
        try:
            figure.savefig(tmp_file)
        except Exception as error:
            raise PlottingError(f'Cannot serialize figure for file {s3_location.file_name}.') from error
        file_size = os.stat(tmp_file.name).st_size
        upload_file(tmp_file, s3_location)

        logger.info('Done with plotting %s bytes.', file_size)

    # https://stackoverflow.com/questions/8213522/when-to-use-cla-clf-or-close-for-clearing-a-plot
    figure.clear()
    plt.close(figure)
