from enum import Enum

from pydantic import BaseModel  # pylint: disable=[E0611]
from typing_extensions import Self

from climada.util import country_to_iso


class BaseDto(BaseModel):
    class Config:
        frozen = True
        hide_input_in_errors = True

class S3LocationDto(BaseDto):
    """
    A file in an S3 bucket. The name of the bucket depends on the context of this element.
    """
    # name of the file
    fileName: str


class JobData(BaseDto):
    """
    Information about the job identifying all actions performed in the same context.
    """
    # identifier of the job (intended to be used for all logs in context of the job)
    correlationId: str

    @classmethod
    def create(cls, correlation_id: str) -> Self:
        """
        Note: To be consistent with all other classes in this module, it is recommended to replace classmethod
        create with regular instantiation of a class in the future, e.g. classInstanceName=ClassXX(...)
        """
        return cls(correlationId=correlation_id)


class HazardSource(BaseDto):
    """
    A tuple identifying the source of the hazard and the algorithm used to extract the hazard (from a weather forecast).
    """
    # type of the hazard
    type: str
    # input format of the hazard
    input: str
    # provider of the weather forecast
    provider: str
    # model of the weather forecast
    model: str

    def primary_key_string(self) -> str:
        """
        Returns the primary key of a hazard source as a string.
        """
        return f'{self.type}_{self.input}_{self.provider}_{self.model}'

    @classmethod
    def create(cls,
               hazard_type: str,
               hazard_input: str,
               weather_data_provider: str,
               nwp_model: str) -> Self:
        """
        Note: To be consistent with all other classes in this module, it is recommended to replace classmethod
        create with regular instantiation of a class in the future, e.g. classInstanceName=ClassXX(...)
        """
        return cls(type=hazard_type, input=hazard_input, provider=weather_data_provider, model=nwp_model)


class ExposureDefinition(BaseDto):
    """
    Definition of the exposures used in impact calculation.
    It does not specify the exposures file itself but a prefix and the corresponding country
    in order to derive the name of an HDF5 file (stored in S3's exposures bucket) from them.
    """
    # string identifier of the exposed country
    country: str


class CalculateImpactProperties(BaseDto):
    """
    Properties used to calculate the impact of a hazard for certain exposures.
    """
    # definition of the exposures file (not a reference)
    exposure: ExposureDefinition
    # vulnerability function defined by a file stored in S3's vulnerability bucket
    vulnerability: str
    # type of the impact
    type: str

    @classmethod
    def create(cls, country: str,
               vulnerability_file_name: str,
               impact_type: str) -> Self:
        """
        Note: To be consistent with all other classes in this module, it is recommended to replace classmethod
        create with regular instantiation of a class in the future, e.g. classInstanceName=ClassXX(...)
        """
        return cls(exposure=ExposureDefinition(country=country),
                   vulnerability=vulnerability_file_name,
                   type=impact_type)


class ImpactSummary(BaseDto):
    """
    The summary of an impact forecast consisting of a reference to a JSON file in S3's impact bucket
    and the impact polygon.
    """
    # reference to the impact polygon (as a file stored in S3)
    summary: str
    polygon: str


class CountryDto(BaseDto):
    """
    Unique identifier of the country following ISO 3166-1
    """
    # country name
    name: str
    # three-digit country codes
    numeric: int
    # two-letter country codes
    alpha2: str
    # three-letter country codes
    alpha3: str

    @classmethod
    def create(cls, country_name: str) -> Self:

        return cls(name=country_to_iso(country_name, 'name'),
                   numeric=country_to_iso(country_name, 'numeric'),
                   alpha3=country_to_iso(country_name, 'alpha3'),
                   alpha2=country_to_iso(country_name, 'alpha2'),
                   )


class ImpactSource(BaseDto):
    """
    Unique identifier of the source of an impact
    """
    # type of the impact
    type: str
    # string identifier of the exposed country
    country: CountryDto


class ImpactDataDto(BaseDto):
    """
    The impact and its metadata
    """
    # reference to the impact data (as a file stored in S3)
    fileName: str
    # reference to the impact metrics (as a file stored in S3)
    fileNameNpz: str
    # The summary of the impact; intended to be used without loading the impact itself,
    # i.e. it contains all necessary information describing the impact briefly
    summary: ImpactSummary
    # The source of the impact consisting of impact type and country
    source: ImpactSource



