"""
This module provides functions to save impact data.
"""
import json
import logging
from decimal import ROUND_HALF_EVEN, ROUND_CEILING, ROUND_FLOOR, Context
from typing import Any

from statsmodels.stats.weightstats import DescrStatsW

from climada.engine import Impact
from climada.engine.forecast import Forecast
from w4un_hydromet_impact import CONFIG
from w4un_hydromet_impact.cross_section.exceptions import ClimadaError

from w4un_hydromet_impact.exchange.events import HazardSource

from w4un_hydromet_impact.hazard.metadata import HazardMetadata
from w4un_hydromet_impact.impact.file_names import build_file_name_from_impact_forecast
from w4un_hydromet_impact.impact.polygon import create_polygons_from_impact
from w4un_hydromet_impact.util.dates import convert_timedelta_to_days

logger = logging.getLogger(__name__)

_ROUND = ROUND_HALF_EVEN
_ROUND_UP = ROUND_CEILING
_ROUND_DOWN = ROUND_FLOOR


def save_impact_forecast(impact_forecast: Forecast,
                         impact_type: str,
                         hazard_metadata: HazardMetadata,
                         hazard_source: HazardSource,
                         base_path: str = '') -> tuple[str, str, str, str]:
    """
    Stores the results of the impact calculation (impact data, matrix, summary and polygon)
    in S3's ch.meteoswiss.hydrometimpact.impact.
    """

    impact_data = _extract_impact(impact_forecast)

    # save impact forecast data
    file_name_impact_data = base_path + '/' + build_file_name_from_impact_forecast(impact_forecast, impact_type, 'data.csv')
    impact_data.write_csv(file_name_impact_data)

    # save impact forecast matrix
    file_name_impact_matrix = base_path + '/' + build_file_name_from_impact_forecast(impact_forecast, impact_type, 'matrix.npz')
    impact_data.write_sparse_csr(file_name_impact_matrix)

    # save aggregate of impact forecast
    file_name_summary = base_path + '/' + build_file_name_from_impact_forecast(impact_forecast, impact_type, 'summary.json')
    summary = summarize_impact(impact_forecast, impact_type, hazard_metadata, hazard_source)
    with open(file_name_summary, 'w') as file:
        json.dump(summary, file, indent=4)  # indent=4 for pretty printing

    # save polygon of impact forecast
    file_name_polygon = base_path + '/' + build_file_name_from_impact_forecast(impact_forecast, impact_type, 'polygon.geojson')
    polygons = create_polygons_from_impact(impact_forecast)
    polygons.to_file(file_name_polygon, driver='GeoJSON')


    return file_name_impact_data, file_name_impact_matrix, file_name_summary, file_name_polygon


def summarize_impact(impact_forecast: Forecast,
                     impact_type: str,
                     hazard_metadata: HazardMetadata,
                     hazard_source: HazardSource) -> dict[str, Any]:
    """
    Creates a summary of the specified impact forecast as a dictionary.
    The impact type is passed directly, the event name is taken from the specified metadata.
    The summary includes the following keys:
    * countryName: name of the country that the impact has been calculated for
    * hazardType: type of the hazard
    * impactType: type of the impact
    * initializationTime: date and time in format 'YYYYMMDDHH' when the weather forecast has been started
    * eventData: data and time in format 'YYYYMMDDHH' of the landfall in the corresponding country
    * leadTime: time between initialization and event in days
    * mean, min, max, median: mean, minimum, maximum and median value of impact
    * 05perc, 25perc, 75perc, 95perc: percentiles of impact
    """
    impact = _extract_impact(impact_forecast)

    weighted_statistics = DescrStatsW(data=impact.at_event, weights=impact.frequency)
    percentiles = weighted_statistics.quantile(probs=[0.05, 0.25, 0.5, 0.75, 0.95])

    return {'countryName': impact_forecast.exposure_name,
            'hazardType': hazard_source.type,
            'impactType': impact_type,
            'initializationTime': impact_forecast.run_datetime[0].strftime('%Y%m%d%H'),
            'eventDate': impact_forecast.event_date.strftime('%Y%m%d%H'),
            'eventName': hazard_metadata.event_name,
            'leadTime': convert_timedelta_to_days(impact_forecast.lead_time()),
            'mean': _round_value(impact_forecast.ai_agg(), _ROUND),
            'min': _round_value(impact.at_event.min(), _ROUND_DOWN),
            'max': _round_value(impact.at_event.max(), _ROUND_UP),
            'median': _round_value(percentiles[0.5], _ROUND),
            '05perc': _round_value(percentiles[0.05], _ROUND_DOWN),
            '25perc': _round_value(percentiles[0.25], _ROUND_DOWN),
            '75perc': _round_value(percentiles[0.75], _ROUND_UP),
            '95perc': _round_value(percentiles[0.95], _ROUND_UP),
            'productStatus': 'alpha',
            'weatherModel': hazard_source.provider,
            'impactUnit': impact.unit,
            }


def _extract_impact(impact_forecast: Forecast) -> Impact:
    if len(impact_forecast.hazard) != 1:
        raise ClimadaError(f'Impact forecast does not contain one hazard, but: {len(impact_forecast.hazard)}')
    hazard = impact_forecast.hazard[0]
    try:
        impact = impact_forecast._impact[impact_forecast.hazard.index(hazard)]
    except Exception as error:
        raise ClimadaError('Impact forecast does not contain impact for hazard.') from error
    return impact


def _round_value(value: float, mode: str) -> float:
    if CONFIG.climada.rounding.significant_digits:
        return _round_significant(value, significant=CONFIG.climada.rounding.significant_digits, rounding_mode=mode)
    return value


def _round_significant(number: float, significant: int, rounding_mode: str) -> float:
    """
    Rounds a number using the specified mode to the specified significant digits.
    Uses rounding modes defined in decimal module.
    """
    if not significant or not number:
        return number
    if significant <= 0:
        raise AssertionError(f'Number of significant digits is not positive: {significant}')

    rounded_number = Context(prec=significant, rounding=rounding_mode).create_decimal(str(number))

    # return int if all significant digits are left of decimal point
    return int(rounded_number) if rounded_number.log10() + 1 >= significant else float(rounded_number)
