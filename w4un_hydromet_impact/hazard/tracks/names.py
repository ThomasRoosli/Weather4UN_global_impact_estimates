from climada.hazard import TCTracks
from w4un_hydromet_impact.hazard.names import extract_base_name_from_event_name


def extract_storm_names_from_tc_tracks(tc_tracks: TCTracks) -> set[str]:
    """
    Extracts the names of all storms in the specified tracks.
    """
    return {extract_base_name_from_event_name(d.name) for d in tc_tracks.data}


def extract_unique_storm_name_from_tc_tracks(tc_tracks: TCTracks) -> str:
    """
    Extracts the name of the storm that the specified tracks are for. Raises an error if not unique.
    """
    names = extract_storm_names_from_tc_tracks(tc_tracks)
    if len(names) > 1:
        raise ValueError(f'Storm name of tracks is not unique: {names}')
    return next(iter(names))
