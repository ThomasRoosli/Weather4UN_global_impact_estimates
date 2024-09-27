# disable pylint because of: No name 'PositiveInt' in module 'pydantic'
from typing import Iterable

from pydantic import PositiveInt, Field  # pylint: disable=[E0611]
from pydantic.dataclasses import dataclass
from shapely.geometry.base import BaseGeometry

from climada.util import country_to_iso, get_country_geometries, natearth_country_to_int


@dataclass(frozen=True, validate_on_init=True)
class Country:
    """
    A country with its ISO-3166-1 numeric code (three digits), alpha-3 code (three letters) and English short name.
    E.g. for Switzerland the triple 756, CHE, Switzerland.
    """
    numeric: PositiveInt
    alpha3: str = Field(min_length=3, max_length=3)
    alpha2: str = Field(min_length=2, max_length=2)
    name: str = Field(strip_whitespace=True, min_length=1)

    def __str__(self) -> str:
        return f'{self.numeric} ({self.name})'


def create_country_from_identifier(identifier: "str | int") -> Country:
    """
    Loads a country reference from an identifier (numeric code, alpha3 code or name).
    """
    return Country(numeric=country_to_iso(identifier, 'numeric'),
                   alpha3=country_to_iso(identifier),
                   name=country_to_iso(identifier, 'name'),
                   alpha2=country_to_iso(identifier, 'alpha2'))


def load_country_geometries(country_codes: Iterable[int]) -> dict[int, BaseGeometry]:
    """
    Loads the geometries of the specified countries.
    """
    country_geometries = get_country_geometries(country_to_iso(country_codes))

    return {natearth_country_to_int(country_geometry): country_geometry.geometry
            for country_geometry in country_geometries.itertuples()}
