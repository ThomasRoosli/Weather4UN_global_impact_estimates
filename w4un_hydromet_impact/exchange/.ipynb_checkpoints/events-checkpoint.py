from enum import StrEnum

from pydantic import BaseModel  # pylint: disable=[E0611]
from typing_extensions import Self

from climada.util import country_to_iso
from w4un_hydromet_impact import CONFIG


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


class HazardMetadataDto(S3LocationDto):
    """
    Hazard metadata consisting of a reference to a JSON file in S3's hazard bucket and the hazard source.
    """
    # the source of the hazard (that has been used to extract the hazard from the weather forecast)
    source: HazardSource


class ExportDestinations(BaseDto):
    """
    Defines the allowed destinations for climada products.
    """
    allowedPaths: list[str]


class HazardDataDto(S3LocationDto):
    """
    Hazard data consisting of a reference to an HDF5 file in S3's hazard bucket and the hazard metadata.
    """
    # Reference to tha hazard's metadata (as a file stored in S3) and the source of the hazard
    metadata: HazardMetadataDto
    # Allowed destinations for hazard products
    exportDestinations: ExportDestinations


class HazardExtractedEvent(BaseDto):
    """
    An event notifying that a hazard has been extracted (from a weather forecast).
    """
    # Reference to the hazard (as a file stored in S3), its metadata and the source of the hazard
    hazard: HazardDataDto
    # context that this event has been created in
    jobData: JobData

    @classmethod
    def create(cls,
               hazard_file: str,
               metadata_file: str,
               hazard_source: HazardSource,
               job_data: JobData,
               export_destinations: ExportDestinations) -> Self:
        """
        Note: To be consistent with all other classes in this module, it is recommended to replace classmethod
        create with regular instantiation of a class in the future, e.g. classInstanceName=ClassXX(...)
        """
        return cls(hazard=HazardDataDto(fileName=hazard_file,
                                        metadata=HazardMetadataDto(fileName=metadata_file, source=hazard_source),
                                        exportDestinations=export_destinations),
                   jobData=job_data)


class HazardProductType(StrEnum):
    INTENSITIES = 'intensities'
    TRACKS = 'tracks'


class HazardProductRealizationCreatedEvent(S3LocationDto):
    """
    An event notifying that a product realization is available (triggered by a hazard extracted event).
    """
    # Reference to tha hazard's metadata (as a file stored in S3) and the source of the hazard
    hazardMetadata: HazardMetadataDto
    # Type of hazard output
    productType: HazardProductType
    # context of the execution of this command
    jobData: JobData
    # Allowed destinations for impact products
    exportDestinations: ExportDestinations

    # re-enable pylint for too many arguments as metadata_file and hazard_source
    # are carried by HazardDataDto
    # pylint: disable=too-many-arguments
    @classmethod
    def create(cls,
               metadata_file: str,
               hazard_source: HazardSource,
               product_type: HazardProductType,
               realization_file_name: str,
               job_data: JobData,
               export_destinations: ExportDestinations) -> Self:
        """
        Note: To be consistent with all other classes in this module, it is recommended to replace classmethod
        create with regular instantiation of a class in the future, e.g. classInstanceName=ClassXX(...)
        """
        return cls(fileName=realization_file_name,
                   hazardMetadata=HazardMetadataDto(fileName=metadata_file, source=hazard_source),
                   productType=product_type,
                   jobData=job_data,
                   exportDestinations=export_destinations)


class ExtractHazardProperties(BaseDto):
    """
    Properties used to extract hazards (from a weather forecast).
    """
    # reference to the centroids (as a file in S3's centroids bucket)
    centroid: S3LocationDto
    # information about the weather forecast as well as the algorithm to be used
    source: HazardSource
    # Allowed destinations for hazard products
    exportDestinations: ExportDestinations


class WeatherDataFileDto(S3LocationDto):
    """
    A file in an S3 bucket.
    """
    # name of the bucket
    bucketName: str = CONFIG.buckets.weather_data


class ExtractHazardCommand(BaseDto):
    """
    A command requesting the extraction of the hazards (from a forecast).
    """
    # reference to the forecast (as a file in an S3 bucket)
    weatherData: WeatherDataFileDto
    # properties defining the hazards to extract and description of the weather data
    arguments: ExtractHazardProperties
    # context of the execution of this command
    jobData: JobData


class ExposureDefinition(BaseDto):
    """
    Definition of the exposures used in impact calculation.
    It does not specify the exposures file itself but a prefix and the corresponding country
    in order to derive the name of an HDF5 file (stored in S3's exposures bucket) from them.
    """
    # string identifier of the exposed country
    country: str
    # prefix of the exposures file name
    fileNamePrefix: str


class ImpactTaskSwitches(BaseDto):
    """
    A class representing switches for impact task operations.
    """
    # A flag indicating whether to save a polygon.
    createPolygon: bool
    # A flag determining if an aggregate plot should be created.
    createAggregate: bool


class CalculateImpactProperties(BaseDto):
    """
    Properties used to calculate the impact of a hazard for certain exposures.
    """
    # definition of the exposures file (not a reference)
    exposure: ExposureDefinition
    # vulnerability function defined by a file stored in S3's vulnerability bucket
    vulnerability: S3LocationDto
    # type of the impact
    type: str
    # Switches for impact task operations
    taskSwitches: ImpactTaskSwitches
    # Allowed destinations for impact products
    exportDestinations: ExportDestinations

    @classmethod
    def create(cls, country: str,
               exposure_file_prefix: str,
               vulnerability_file_name: str,
               impact_type: str,
               task_switches: ImpactTaskSwitches,
               export_destinations: ExportDestinations) -> Self:
        """
        Note: To be consistent with all other classes in this module, it is recommended to replace classmethod
        create with regular instantiation of a class in the future, e.g. classInstanceName=ClassXX(...)
        """
        return cls(exposure=ExposureDefinition(country=country, fileNamePrefix=exposure_file_prefix),
                   vulnerability=S3LocationDto(fileName=vulnerability_file_name),
                   type=impact_type, taskSwitches=task_switches, exportDestinations=export_destinations)


class CalculateImpactCommand(BaseDto):
    """
    A command requesting the calculation of the impact of a hazard using the specified arguments.
    """
    # reference to the hazard and its metadata
    hazard: HazardDataDto
    # properties defining which calculation to perform
    arguments: CalculateImpactProperties
    # context of the execution of this command
    jobData: JobData


class ImpactSummary(S3LocationDto):
    """
    The summary of an impact forecast consisting of a reference to a JSON file in S3's impact bucket
    and the impact polygon.
    """
    # reference to the impact polygon (as a file stored in S3)
    polygon: S3LocationDto


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
    # Allowed destinations for impact products
    exportDestinations: ExportDestinations


class ImpactCalculatedEvent(BaseDto):
    """
    An event notifying that the impact of a hazard has been calculated.
    """
    # The hazard and its metadata
    hazard: HazardDataDto
    # The impact and its metadata
    impact: ImpactDataDto
    # context that this event has been created in
    jobData: JobData


class ImpactProductType(StrEnum):
    MAP = 'map'
    HISTOGRAM = 'histogram'
    REGIONMAP = 'regionmap'


class ImpactProductRealizationCreatedEvent(S3LocationDto):
    """
    An event notifying that the public impact realization has been created.
    """
    #  The metadata of a hazard; intended to be used without having the hazard,
    #  i.e. it should include all information of the hazard that is needed to refer to the hazard without loading it
    hazardMetadata: HazardMetadataDto
    # The source of the impact consisting of impact type and country
    impactSource: ImpactSource
    # Type of impact output
    productType: ImpactProductType
    # context that this event has been created in
    jobData: JobData
    # Allowed destinations for impact products
    exportDestinations: ExportDestinations
