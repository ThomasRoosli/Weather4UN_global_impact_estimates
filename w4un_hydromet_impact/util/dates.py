"""
This module provides functions for conversion of dates and timestamps.

https://stackoverflow.com/questions/13703720/converting-between-datetime-timestamp-and-datetime64
"""
import datetime as dt

import numpy as np
import pandas as pd

_SECONDS_PER_DAY = 24 * 60 * 60


def convert_datetime64_to_datetime(value: np.datetime64) -> dt.datetime:
    """
    Converts a datetime64 object into a datetime object.
    """
    return pd.Timestamp(value).to_pydatetime()


def convert_timedelta_to_days(value: dt.timedelta) -> float:
    """
    Converts a time delta to a number of days.
    """
    return value.total_seconds() / _SECONDS_PER_DAY


def create_datetime64(year: int, month: int, day: int, hour: int = 0, minute: int = 0) -> np.datetime64:
    """
    Creates a datetime64 from year, month, day, hour and minute.
    """
    datetime = dt.datetime(year, month, day, hour, minute)
    return np.datetime64(datetime.strftime('%Y-%m-%dT%H:%M:%S.%f000'))
