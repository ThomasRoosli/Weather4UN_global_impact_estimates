from typing import Optional, TYPE_CHECKING

from pydantic import BaseModel, PositiveFloat, PositiveInt, NonNegativeInt, Field



class ImpactCalculationSettings(BaseModel):
    impact_definition_wildcard: str = '<>'
    regexp_group_number: str = '(\\d+)'
    not_existing_file: str = 'not_existing'



class ClimadaTropicalCycloneSettings(BaseModel):
    """
    Climada settings for tropical cyclone handling that are not handled by Climada configuration.
    """
    max_memory_gb: PositiveFloat = Field(default=1)
    model: str = 'H1980'
    # assumed resolution of the centroids that are used (in degrees);
    # needed to ensure that point are dense enough to not omit anything
    grid_resolution: PositiveFloat = Field(default=1 / 24)
    # radius (in km) around a track point considered to be a landfall
    landfall_radius_km: NonNegativeInt = Field(default=50)


class ClimadaRoundingProperties(BaseModel):
    """
    Climada settings for rounding numbers.
    """
    # number of significant digits; omit to not round values
    significant_digits: Optional[PositiveInt] = Field(default=2)


# analog to pydantic/types.py in order to avoid type-checking error
# if TYPE_CHECKING:
#     ProbabilityFloat = float
# else:
#     class ProbabilityFloat(ConstrainedFloat):
#         """
#         A floating point value representing a probability, i.e. between 0 (inclusive) and 1 (inclusive).
#         """
#         ge = 0
#         le = 1


class WarnSettings(BaseModel):
    erosion: NonNegativeInt = 0
    dilation: NonNegativeInt = 4
    median_filtering: NonNegativeInt = 4
    gradually_decreased: bool = True
    small_regions_threshold: NonNegativeInt = 50


class ClimadaImpactSettings(BaseModel):
    """
    Climada settings for impact calculation that are not handled by Climada configuration.
    """
    # probability threshold for "potentially affected" set to 5%
    probability_threshold: float = Field(0.05, ge=0, le=1)
    default_grid_resolution: PositiveInt = 150_000
    minimum_grid_size: PositiveInt = 10
    warn: WarnSettings = WarnSettings()


class ClimadaSettings(BaseModel):
    """
    Climada settings not handled by Climada configuration.
    """
    tropical_cyclone: ClimadaTropicalCycloneSettings = ClimadaTropicalCycloneSettings()
    rounding: ClimadaRoundingProperties = ClimadaRoundingProperties()
    impact: ClimadaImpactSettings = ClimadaImpactSettings()


class ServiceSettings(BaseModel):
    site: str = 'localhost'
    climada: ClimadaSettings = ClimadaSettings()
    impact_calculation: ImpactCalculationSettings = ImpactCalculationSettings()

    class Config:
        env_prefix = 'C4M__'
