import numpy as np

from climada.hazard import TCTracks
from w4un_hydromet_impact.util.types import Timestamp


def calculate_init_time(tracks: TCTracks) -> Timestamp:
    """
    Calculates the initialization time from the specified tracks.
    The initialization time is assumed to be the earliest timestamp that any of the tracks starts at.
    """
    if len(tracks.data) == 0:
        raise AssertionError('Tracks are empty.')

    init_time = np.min([data.run_datetime for data in tracks.data])
    return Timestamp(init_time, 'ns')


def build_frequencies(tracks: TCTracks) -> list[float]:
    """
    Calculates the frequencies per track.
    """
    return [getattr(data, 'frequency', 1) for data in tracks.data]
