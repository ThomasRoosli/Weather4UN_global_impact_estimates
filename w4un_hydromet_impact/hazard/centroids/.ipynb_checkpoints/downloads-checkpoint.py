from climada.hazard import Centroids
from w4un_hydromet_impact.cross_section.exceptions import ClimadaError
from w4un_hydromet_impact.fabio import S3Location
from w4un_hydromet_impact.fabio.s3_facade import download_as_tempfile
from w4un_hydromet_impact.hazard.centroids.validations import check_centroids_consistency


def download_centroids(s3_location: S3Location) -> Centroids:
    """
    Downloads the requested centroid file from S3 and transforms it into a centroids object.
    Afterward, the built-in checks of CLIMADA for centroids are run.
    :param s3_location: The location of the file in S3.
    :return: valid centroids object with reduced extent
    """
    with download_as_tempfile(s3_location) as tmp_downloaded_centroids:
        try:
            centroids = Centroids.from_hdf5(tmp_downloaded_centroids.name)
        except Exception as error:
            raise ClimadaError(f'Cannot deserialize centroids from {s3_location}.') from error
    check_centroids_consistency(centroids, s3_location)
    return centroids
