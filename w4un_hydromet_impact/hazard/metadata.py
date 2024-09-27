import json
import logging
from dataclasses import field
from io import TextIOWrapper
from typing import Optional, IO

import numpy as np
import pandas as pd
from pydantic.dataclasses import dataclass
from statsmodels.stats.weightstats import DescrStatsW
from typing_extensions import Self

from climada.util import country_to_iso

from w4un_hydromet_impact.util.types import Timestamp

logger = logging.getLogger(__name__)

_EVENT_NAME = 'event_name'
_INIT_TIME = 'initialisation_time'
_ALL_LEAD_TIMES = 'all_leadtimes'
_MEDIAN_LEAD_TIME = 'median_leadtime'
_LEAD_TIMES_PER_COUNTRY = 'leadtimes_per_country'
_COUNTRY_NAME = 'country_name'
_COUNTRY_ALPHA2 = 'country_alpha2'
_COUNTRY_ALPHA3 = 'country_alpha3'
_ENCODING = 'utf-8'


@dataclass(validate_on_init=True, config={'arbitrary_types_allowed': True}, frozen=True)
class LeadTimes:
    """
    Lead times af a hazard event

    Attributes
    ----------
    all: all lead times of the hazard in the corresponding country,
         i.e. the earliest datetime that a track enters that country
    median: the median of all lead times
    """
    all: list[Timestamp]
    median: Timestamp

    @classmethod
    def create(cls,
               lead_times: Optional[list[Timestamp]] = None,
               median: Optional[Timestamp] = None,
               weights: Optional[list[float]] = None) -> Self:
        """
        Creates the lead times based on the specified parameters.
        If median is not specified, it is derived from all values considering the specified weights.
        """
        if lead_times:
            if median:
                return cls(all=lead_times,
                           median=median)
            if not weights:
                weights = list(np.ones(len(lead_times), dtype=float))
            return cls(all=lead_times,
                       median=_calc_median_datetime64(lead_times, weights))
        if median:
            return cls(all=[median],
                       median=median)
        raise AssertionError('Neither all lead times nor median lead time specified.')

    def check(self, country_code: int = 0) -> None:
        """
        Checks these lead times for consistency. Raises a ValueError if not consistent.
        :param country_code: an optional country code that these lead times are associated with.
        """
        if len(self.all) == 0:
            if country_code:
                raise ValueError(f'Missing lead times for country code {country_code}.')
            raise ValueError('Missing lead times.')

    def __repr__(self) -> str:
        return f'{self.median} {self.all}'


@dataclass(validate_on_init=True, config={'arbitrary_types_allowed': True}, frozen=True)
class HazardMetadata:
    """
    Contains metadata of a hazard event.

    Attributes
    ----------
    event_name: name of the hazard, e.g. a storm name
    initialisation_time: datetime when the hazard has been forecasted
    leadtimes_per_country: dict containing the lead times per country; the key is the numeric ISO-3166 alpha3 code;
                having an entry in the dict means that the hazard has got a landfall in that country
    """
    event_name: str
    initialisation_time: Timestamp
    leadtimes_per_country: dict[int, LeadTimes] = field(default_factory=lambda: {})

    def get_country_codes(self) -> list[int]:
        """
        Returns all country codes.
        """
        result = list(self.leadtimes_per_country)
        result.sort()
        return result

    def get_lead_times(self, country_code: int) -> LeadTimes:
        """
        Returns the lead times for a specified country code.
        """
        if country_code not in self.leadtimes_per_country:
            raise AssertionError(f'No lead times found for country {country_code}.')

        return self.leadtimes_per_country[country_code]

    def has_landfall(self, country_code: Optional[int] = None) -> bool:
        """
        Returns if the hazard has a landfall in the specified country.
        :param country_code: the country code; if omitted, check whether there is a landfall for any country
        """
        if country_code:
            return country_code in self.leadtimes_per_country
        return bool(self.leadtimes_per_country)

    def check(self) -> None:
        """
        Checks this hazard metadata for consistency. Raises a ValueError if not consistent.
        """
        for country_code, lead_times in self.leadtimes_per_country.items():
            lead_times.check(country_code)

    def to_dict(self) -> dict:
        """
        Converts this metadata to a dictionary (for JSON export).
        """
        result: dict = {_EVENT_NAME: self.event_name,
                        _INIT_TIME: self.initialisation_time,
                        _LEAD_TIMES_PER_COUNTRY: {}}
        for country_code in self.get_country_codes():
            lead_time = self.get_lead_times(country_code)
            result[_LEAD_TIMES_PER_COUNTRY][country_code] = {
                _COUNTRY_NAME: country_to_iso(country_code, 'name'),
                _COUNTRY_ALPHA3: country_to_iso(country_code),
                _COUNTRY_ALPHA2: country_to_iso(country_code,'alpha2'),
                _ALL_LEAD_TIMES: lead_time.all,
                _MEDIAN_LEAD_TIME: lead_time.median,
            }
        return result

    def write_json(self, file: IO[bytes]) -> None:
        """
        Stores this metadata as JSON string.
        :param file: the file to store in
        """
        logger.info("Writing metadata to %s.", file)
        json_dict: dict = {_EVENT_NAME: self.event_name,
                           _INIT_TIME: str(self.initialisation_time),
                           _LEAD_TIMES_PER_COUNTRY: {}}
        for country_code, lead_times in self.leadtimes_per_country.items():
            json_dict[_LEAD_TIMES_PER_COUNTRY][str(country_code)] = {
                _COUNTRY_NAME: country_to_iso(country_code, 'name'),
                _COUNTRY_ALPHA3: country_to_iso(country_code),
                _COUNTRY_ALPHA2: country_to_iso(country_code,'alpha2'),
                _MEDIAN_LEAD_TIME: str(lead_times.median),
                _ALL_LEAD_TIMES: [str(d) for d in lead_times.all]
            }

        stream = TextIOWrapper(file, encoding='utf-8')
        json.dump(json_dict, stream, indent=4)
        stream.flush()
        # prevent from closing underlying file
        stream.detach()

    def __repr__(self) -> str:
        return (f'HazardMetadata[event={self.event_name}, '
                f'init={self.initialisation_time}, '
                f'lead_times={self.leadtimes_per_country}]')

    @classmethod
    def read_from_json(cls, file: IO[bytes]) -> Self:
        """
        Reads metadata from a JSON string stored in the specified file.
        :param file: the file
        :return: the metadata
        """
        logger.info("Reading metadata from %s.", file)
        stream = TextIOWrapper(file, encoding='utf-8')
        metadata_dict = json.load(stream)

        # prevent from closing underlying file
        stream.detach()

        return cls._from_dict(metadata_dict)

    @classmethod
    def _from_dict(cls, metadata_dict: dict) -> Self:
        """
        Converts a dictionary to hazard metadata.
        """
        event_name = metadata_dict[_EVENT_NAME]
        init_time = Timestamp(metadata_dict[_INIT_TIME])

        lead_times: dict[int, LeadTimes] = {}
        for country_code, lead_times_per_country in metadata_dict[_LEAD_TIMES_PER_COUNTRY].items():
            if country_code.isnumeric():
                all_lead_times = list(map(Timestamp, lead_times_per_country[_ALL_LEAD_TIMES]))
                median_lead_time = lead_times_per_country.get(_MEDIAN_LEAD_TIME, None)
                if not median_lead_time:
                    median_lead_time = _calc_median_datetime64(all_lead_times)
                else:
                    median_lead_time = Timestamp(median_lead_time)
                lead_times[int(country_code)] = LeadTimes.create(median=median_lead_time,
                                                                 lead_times=all_lead_times)

        return cls.from_lead_times(event_name, init_time, lead_times)

    @classmethod
    def from_lead_times(cls, event_name: str,
                        init_time: Timestamp,
                        lead_times: dict[int, LeadTimes]) -> Self:
        """
        Creates the metadata of a hazard using the specified country-specific lead times.
        """
        result = cls(event_name, init_time)
        for country_code, lead_times_per_country in lead_times.items():
            result.leadtimes_per_country[country_code] = lead_times_per_country
        return result


def _calc_median_datetime64(lead_times: list[Timestamp],
                            weights: Optional[list[float]] = None) -> Timestamp:
    """
    Calculates the median of an array of datetime64 values.
    :param lead_times: the lead times to calculate the median of
    :param weights: the weights of the lead times; if omitted, a uniform distribution is assumed
    :return: the median value
    """
    if weights is None:
        weights = list(np.ones(len(lead_times), dtype=float))

    lead_time_np = [lead_time.astype(np.int64) for lead_time in lead_times]
    weighted_statistics = DescrStatsW(data=lead_time_np, weights=weights)
    median_lead_time_np = weighted_statistics.quantile([0.5], return_pandas=False)[0]
    median_lead_time_pd = pd.to_datetime(median_lead_time_np)
    return Timestamp(median_lead_time_pd.value, 'ns')
