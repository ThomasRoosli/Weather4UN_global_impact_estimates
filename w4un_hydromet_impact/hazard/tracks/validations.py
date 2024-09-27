"""
In this module, several validations of tracks business objects are grouped.
"""
from climada.hazard import TCTracks
from w4un_hydromet_impact.hazard.tracks.names import extract_storm_names_from_tc_tracks


def validate_tc_tracks(tc_tracks: TCTracks) -> None:
    storm_names = extract_storm_names_from_tc_tracks(tc_tracks)
    if len(storm_names) > 1:
        raise ValueError(f'Problem with tracks input names. More than one storm name: {storm_names}')
