"""
This module provides methods to upload hazard-related data into S3 during processing.
"""
#import logging
#from tempfile import NamedTemporaryFile

#from climada.engine import Impact
#from w4un_hydromet_impact.cross_section.exceptions import ClimadaError
#from w4un_hydromet_impact.fabio import S3Location
#from w4un_hydromet_impact.fabio.s3_facade import upload_file

#logger = logging.getLogger(__name__)


#def upload_impact_data(impact_forecast: Impact, s3_location: S3Location) -> None:
    """
    Uploads the specified impact data into the specified location.
    """
#    with NamedTemporaryFile() as tmp_file:
#        try:
#            impact_forecast.write_csv(tmp_file.name)
#        except Exception as error:
#            raise ClimadaError(
#                f'Cannot serialize impact for file {s3_location.file_name}.') from error
#        tmp_file.flush()
#        upload_file(tmp_file, s3_location)


#def upload_impact_matrix(impact_forecast: Impact, s3_location: S3Location) -> None:
    """
    Uploads the specified impact matrix into the specified location.
    """
#    with NamedTemporaryFile(suffix='.npz') as tmp_file:
#        try:
#            impact_forecast.write_sparse_csr(tmp_file.name)
#        except Exception as error:
#            raise ClimadaError(
#                f'Cannot serialize impact matrix for file {s3_location.file_name}.') from error
#        tmp_file.flush()
#        upload_file(tmp_file, s3_location)
