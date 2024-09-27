"""
Constants for hazard calculation.
"""
from w4un_hydromet_impact.exchange.events import HazardSource


class KnownHazardTypes:
    TROPICAL_CYCLONE = 'TC'
    WINDSTORM = 'WS'
    PRECIPITATION12 = 'PR12'
    PRECIPITATION24 = 'PR24'
    PRECIPITATION36 = 'PR36'
    PRECIPITATION48 = 'PR48'
    PRECIPITATION60 = 'PR60'


class KnownHazardInputs:
    TRACKS = 'tracks'
    SEVERITY_LEVELS = 'SeverityLevels'


class KnownWeatherDataProviders:
    ECMWF = 'ECMWF'
    LA_REUNION = 'LaReunion'
    METEOSWISS = 'MeteoSwiss'


class KnownNwpModels:
    ENSEMBLE = 'ens'
    EXTREME_WEATHER_IDENTIFIER = 'ExtremeWeatherIdentifier'


class KnownHazardSources:
    TROPICAL_CYCLONE_FROM_ECMWF = HazardSource.create(KnownHazardTypes.TROPICAL_CYCLONE,
                                                      KnownHazardInputs.TRACKS,
                                                      KnownWeatherDataProviders.ECMWF,
                                                      KnownNwpModels.ENSEMBLE)
