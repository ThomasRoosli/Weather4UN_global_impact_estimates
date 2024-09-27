"""
This module provides functions to build names for impact-related files.
"""
from climada.engine.forecast import Forecast

# year, month, day, hours
_FOLDER_NAME_DATE_FORMAT = "%Y%m%d%H"


def build_file_name_from_impact_forecast(impact_forecast: Forecast, impact_type: str, suffix: str) -> str:
    """
    Builds a unique file name from an impact forecast.
    E.g. if the hazard type is TC, the provider is ECMWF, the initialization time is 2023-06-08 at 12 pm,
    the event takes place on 2023-07-02 in Switzerland, the impact is of type snowfall, and suffix is 'impact.json',
    then the name is going to be '2023060812/TC_ECMWF_run2023060812_event20230702_Switzerland_snowfall_impact.json'.
    :param impact_forecast: the impact forecast
    :param impact_type: the impact type
    :param suffix: a suffix identifying the kind of the file
    """
    run_datetime = impact_forecast.run_datetime[0]
    summary = impact_forecast.summary_str()
    return f'{summary}_{impact_type}_{suffix}'
