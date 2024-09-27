from climada.entity import ImpactFuncSet


def read_vulnerabilities(file_location: str) -> ImpactFuncSet:
    """
    Downloads the requested vulnerability file from S3
    and transforms it into a vulnerabilities object.
    Afterward, the built-in checks of CLIMADA for vulnerabilities are run.
    :param file_location: The location of the file in the S3 bucket.
    :return: valid vulnerabilities object with reduced extent
    """
    vulnerabilities = ImpactFuncSet.from_excel(file_location)
    return vulnerabilities
