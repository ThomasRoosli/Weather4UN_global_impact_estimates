"""
This module defines Climada4Mch-specific errors.
"""


class ClimadaError(Exception):
    """
    Problem caused by Climada library.
    """


class HazardMetadataError(Exception):
    """
    Problem caused by Climada4Mch hazard metadata.
    """


class PlottingError(Exception):
    """
    Problem caused by plotting a figure.
    """
