"""
Utilities for dictionary not available via Python.

TODO: replace with standard libraries when available.
"""
from typing import TypeVar, Iterable

_K = TypeVar('_K')
_V = TypeVar('_V')


def update_if_missing(dictionary: dict[_K, _V], entries: dict[_K, _V]) -> None:
    """
    Adds the specified entries to the specified dictionary if an entry is missing.
    """
    for key, value in entries.items():
        if key not in dictionary:
            dictionary[key] = value


def remove_keys(dictionary: dict[_K, _V], keys_to_remove: Iterable[_K]) -> dict[_K, _V]:
    """
    Returns a new dictionary containing the entries of the specified one, but without the specified keys to remove.
    """
    return {key: value
            for key, value in dictionary.items()
            if key not in keys_to_remove}


def retain_keys(dictionary: dict[_K, _V], keys_to_retain: Iterable[_K]) -> dict[_K, _V]:
    """
    Returns a new dictionary containing the entries of the specified one, but only with the specified keys to retain.
    """
    return {key: value
            for key, value in dictionary.items()
            if key in keys_to_retain}
