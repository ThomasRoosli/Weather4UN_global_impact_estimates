"""
This module provides functions to derive information from names.
"""
from climada.hazard import Hazard


def extract_base_name_from_event_name(event_name: str) -> str:
    """
    Extracts the base name from an event name.
    In our structure, it is given by the part of the input string before '_'.
    Example: 'ELOISE_1' -> 'ELOISE'
    """
    return event_name.split('_')[0]


def extract_base_names_from_hazard(hazard: Hazard) -> set[str]:
    """
    Extracts the base names of the specified hazard.
    """
    return {extract_base_name_from_event_name(event_name_of_member) for event_name_of_member in hazard.event_name}


def extract_base_name_from_hazard(hazard: Hazard) -> str:
    """
    Extracts the base name from a hazard.
    """
    event_name_of_first_member = _retrieve_event_name_of_first_member(hazard)  # e.g. 'ELOISE_1' or 'a75_3'
    return extract_base_name_from_event_name(event_name_of_first_member)  # e.g. 'ELOISE' or 'a75'


def _retrieve_event_name_of_first_member(hazard: Hazard) -> str:
    return hazard.event_name[0]
