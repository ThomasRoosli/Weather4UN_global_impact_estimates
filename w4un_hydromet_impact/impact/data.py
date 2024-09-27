from pydantic.dataclasses import dataclass
from typing_extensions import Self

from w4un_hydromet_impact.geography.country import Country, create_country_from_identifier


@dataclass(frozen=True, validate_on_init=True)
class ImpactForecastDefinitionItem:
    """
    An item of an impact forecast definition
    providing all inputs required to calculate the impact of a hazard for a certain country.
    """
    country: Country
    vulnerability_location: str
    impact_type: str

    @classmethod
    def create(cls,
               country: "Country | str | int",
               vulnerability_file_name: str,
               impact_type: str) -> Self:
        return cls(country=country if isinstance(country, Country) else create_country_from_identifier(country),
                   vulnerability_location=vulnerability_file_name,
                   impact_type=impact_type)
