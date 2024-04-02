#
# This source file is part of the Stanford Spezi open-source project
#
# SPDX-FileCopyrightText: 2024 Stanford University and the project authors (see CONTRIBUTORS.md)
#
# SPDX-License-Identifier: MIT
#
"""
Module for Flattening FHIR Resources

This module provides functionalities to transform nested Fast Healthcare Interoperability Resources
(FHIR) resources into flattened, tabular formats suitable for easier processing and analysis. It
includes classes and functions that handle the conversion of complex FHIR JSON structures into
pandas DataFrames, streamlining the manipulation of health-related information encoded in FHIR
standards.

Classes:
    ColumnNames: An Enum for standardized column names used in the flattened DataFrames.
    FHIRResourceType: An Enum for specifying FHIR resource types relevant to the application.
    FHIRDataFrame: A class representing a DataFrame specifically for FHIR data, with methods for
        validation and easy access to the data.
    ResourceFlattener: An abstract base class for flattening resources, with subclasses for specific
        resource types like ObservationFlattener.

Functions:
    flatten_fhir_resources: A function to flatten a list of FHIR resources into a FHIRDataFrame,
        utilizing the appropriate ResourceFlattener subclass based on the resource type.
"""


# Standard library imports
from datetime import date
from enum import Enum

# Related third-party imports
from dataclasses import dataclass
from typing import Any
import pandas as pd
from pandas.api.types import is_string_dtype, is_object_dtype

# Local application/library specific imports


class ColumnNames(Enum):
    """
    Enumerates standardized column names for use in flattened DataFrames.

    These column names represent common fields extracted from FHIR resources,
    ensuring consistency across the application.
    """

    USER_ID = "UserId"  # Represents a user's unique identifier.
    EFFECTIVE_DATE_TIME = (
        "EffectiveDateTime"  # The datetime when an observation was effective.
    )
    QUANTITY_NAME = (
        "QuantityName"  # The name of the measured quantity (e.g., Heart Rate).
    )
    QUANTITY_UNIT = (
        "QuantityUnit"  # The unit of the measured quantity (e.g., beats/minute).
    )
    QUANTITY_VALUE = "QuantityValue"  # The value of the measured quantity.
    LOINC_CODE = "LoincCode"  # The LOINC code associated with the observation.
    DISPLAY = (
        "Display"  # The display text associated with the observation's LOINC code.
    )
    APPLE_HEALTH_KIT_CODE = (
        "AppleHealthKitCode"  # A code used in Apple HealthKit for the observation.
    )


class FHIRResourceType(Enum):
    """
    Enumeration of FHIR resource types.

    This enum provides a list of FHIR resource types used in the application, ensuring
    consistency and preventing typos in resource type handling.

    Attributes:
        OBSERVATION (str): Represents an observation resource type.
        QUESTIONNAIRE_RESPONSE (str): Represents a questionnaire response resource type.

    Note:
        The `.value` attribute is used to access the string value of the enum members.
    """

    OBSERVATION = "Observation"
    QUESTIONNAIRE_RESPONSE = "QuestionnaireResponse"


@dataclass
class FHIRDataFrame:
    """
    Encapsulates a pandas DataFrame tailored for handling FHIR data.

    This class provides a structured format for FHIR data, making it easier to
    manipulate and analyze health-related information encoded in FHIR resources.
    It includes validation to ensure that the DataFrame contains required columns
    and that these columns have appropriate data types.

    Attributes:
        data_frame (pd.DataFrame): The underlying DataFrame storing the FHIR data.
        resource_type (FHIRResourceType): The type of FHIR resources contained in the DataFrame.
        resource_columns (dict): Maps resource types to their respective columns in the DataFrame.

    Methods:
        df: Returns the underlying pandas DataFrame.
        validate_columns: Validates the presence and data types of required columns in
            the DataFrame.
    """

    def __init__(
        self,
        data: pd.DataFrame,
        resource_type: FHIRResourceType,
    ) -> None:
        """
        Initializes a FHIRDataFrame with given data and resource type.

        Parameters:
            data (pd.DataFrame): The pandas DataFrame containing FHIR data.
            resource_type (FHIRResourceType): The type of FHIR resource.
        """
        self.data_frame = data
        self.resource_type = resource_type

        # Instantiate a ResourceFlattener to use its resource_columns
        flattener = ResourceFlattener(resource_type)
        self.resource_columns = flattener.resource_columns

        if resource_type not in self.resource_columns:
            raise ValueError(f"Unsupported resource type: {resource_type}")

    @property
    def df(self) -> pd.DataFrame:
        """
        A property to access the underlying pandas DataFrame containing FHIR data.

        Returns:
            pd.DataFrame: The pandas DataFrame storing the FHIR data.
        """
        return self.data_frame

    def validate_columns(self) -> bool:
        """
        Validates that the DataFrame contains all required columns for processing and
        checks the data type of specific columns. Raises a ValueError if any required
        column is missing or if a column does not have the expected data type.

        Returns:
            bool: True if all columns are present and correctly formatted, otherwise raises
                an error.
        """

        required_columns = [
            col.value for col in self.resource_columns.get(self.resource_type, [])
        ]

        missing_columns = [
            col for col in required_columns if col not in self.df.columns
        ]
        if missing_columns:
            formatted_missing_columns = ", ".join(missing_columns)
            raise ValueError(
                f"The DataFrame is missing required columns: {formatted_missing_columns}"
            )

        if ColumnNames.EFFECTIVE_DATE_TIME.value in self.df.columns:
            if not all(
                isinstance(d, date)
                for d in self.df[ColumnNames.EFFECTIVE_DATE_TIME.value]
            ):
                raise ValueError(
                    f"The {ColumnNames.EFFECTIVE_DATE_TIME.value} column is not of type"
                    "datetime.date."
                )

        for column in set(required_columns) - {
            ColumnNames.EFFECTIVE_DATE_TIME.value,
            ColumnNames.QUANTITY_VALUE.value,
        }:
            if column in self.df.columns:
                if not (
                    is_string_dtype(self.df[column]) or is_object_dtype(self.df[column])
                ):
                    raise ValueError(f"The '{column}' column does not contain strings.")

        return True


@dataclass
class ResourceFlattener:
    """
    Abstract base class for flattening FHIR resources into a structured DataFrame format.

    Subclasses of ResourceFlattener should implement the `flatten` method to convert
    specific types of FHIR resources (e.g., Observations, QuestionnaireResponses) into
    a flattened format suitable for analysis.

    Attributes:
        resource_type (FHIRResourceType): The FHIR resource type that the flattener handles.
        resource_columns (dict): Maps FHIRResourceType to a list of ColumnNames relevant for
            the resource.

    Methods:
        flatten: Abstract method to be implemented by subclasses, performing the actual
            flattening process.
    """

    def __init__(self, resource_type: FHIRResourceType):
        """
        Initializes the ResourceFlattener with a specific FHIR resource type.

        This method sets up the resource type and prepares a dictionary mapping the resource type
        to its relevant columns for the flattening process. It validates the resource type to ensure
        that it is supported for flattening.

        Parameters:
            resource_type (FHIRResourceType): The type of FHIR resource this flattener will handle.

        Raises:
            ValueError: If the specified resource type is unsupported.
        """
        self.resource_type = resource_type
        self.resource_columns = {
            FHIRResourceType.OBSERVATION: [
                ColumnNames.USER_ID,
                ColumnNames.EFFECTIVE_DATE_TIME,
                ColumnNames.QUANTITY_NAME,
                ColumnNames.QUANTITY_UNIT,
                ColumnNames.QUANTITY_VALUE,
                ColumnNames.LOINC_CODE,
                ColumnNames.DISPLAY,
                ColumnNames.APPLE_HEALTH_KIT_CODE,
            ],
            FHIRResourceType.QUESTIONNAIRE_RESPONSE: [
                ColumnNames.USER_ID,
                ColumnNames.EFFECTIVE_DATE_TIME,
                ColumnNames.QUANTITY_NAME,
                ColumnNames.QUANTITY_VALUE,
                ColumnNames.LOINC_CODE,
            ],
        }

        if resource_type not in self.resource_columns:
            raise ValueError(f"Unsupported resource type: {resource_type.name}")

    def flatten(self, resources: list[Any]) -> FHIRDataFrame:
        """
        Abstract method intended to transform a list of FHIR resources into a flattened
        FHIRDataFrame.

        This method should be implemented by subclasses to process specific types of FHIR resources,
        extracting relevant data and converting it into a structured, tabular format. The
        implementation will vary depending on the resource type, focusing on the extraction of key
        information suited for analysis and further processing.

        Parameters:
            resources (list[Any]): A list of FHIR resource objects to be flattened. The exact type
                                    of objects in the list should correspond to the FHIR resource
                                    type the subclass is designed to handle.

        Returns:
            FHIRDataFrame: A FHIRDataFrame object containing the flattened data from the resources,
                            ready for analysis and processing.

        Raises:
            NotImplementedError: Indicates that this method needs to be implemented by subclasses.
        """
        raise NotImplementedError("Subclasses should implement this method.")


@dataclass
class ObservationFlattener(ResourceFlattener):
    """
    Flattens FHIR Observation resources into a structured DataFrame.

    Extends ResourceFlattener, specifically handling the conversion of Observation
    resources into a tabular format, extracting key information such as user IDs,
    effective date-times, quantities, and associated codes.

    Methods:
        flatten: Transforms a list of Observation resources into a FHIRDataFrame.
    """

    def __init__(self):
        super().__init__(FHIRResourceType.OBSERVATION)

    def flatten(self, resources: list[Any]) -> FHIRDataFrame:
        """
        Transforms a list of Observation resources into a flattened FHIRDataFrame.

        This method processes each Observation resource, extracting key information such as
        effective date-time, quantities, and codes into a structured tabular format. The resulting
        DataFrame is suitable for analysis and further data processing tasks.

        Parameters:
            resources (list[Any]): A list of FHIR Observation resources to be flattened.

        Returns:
            FHIRDataFrame: A structured DataFrame containing the flattened data from the Observation
                resources.
        """
        flattened_data = []
        for observation in resources:
            
            effective_datetime = observation.dict().get("effectiveDateTime")
            if not effective_datetime: 
                effective_period = observation.dict().get("effectivePeriod", {}) 
                effective_datetime = effective_period.get("start", None)  
    
            coding = observation.dict()["code"]["coding"]
            loinc_code = coding[0]["code"] if len(coding) > 0 else ""
            display = coding[0]["display"] if len(coding) > 0 else ""
            apple_healthkit_code = (
                coding[1]["code"]
                if len(coding) > 1
                else (coding[0]["code"] if len(coding) > 0 else "")
            )
            quantity_name = (
                coding[1]["display"]
                if len(coding) > 1
                else (coding[0]["display"] if len(coding) > 0 else "")
            )

            flattened_entry = {
                ColumnNames.USER_ID.value: observation.subject.id,
                ColumnNames.EFFECTIVE_DATE_TIME.value: (
                    effective_datetime if effective_datetime else None
                ),
                ColumnNames.QUANTITY_NAME.value: quantity_name,
                ColumnNames.QUANTITY_UNIT.value: observation.dict()["valueQuantity"][
                    "unit"
                ],
                ColumnNames.QUANTITY_VALUE.value: observation.dict()["valueQuantity"][
                    "value"
                ],
                ColumnNames.LOINC_CODE.value: loinc_code,
                ColumnNames.DISPLAY.value: display,
                ColumnNames.APPLE_HEALTH_KIT_CODE.value: apple_healthkit_code,
            }

            flattened_data.append(flattened_entry)

        flattened_df = pd.DataFrame(flattened_data)
        flattened_df[ColumnNames.EFFECTIVE_DATE_TIME.value] = pd.to_datetime(
            flattened_df[ColumnNames.EFFECTIVE_DATE_TIME.value], errors="coerce"
        ).dt.date

        return FHIRDataFrame(flattened_df, FHIRResourceType.OBSERVATION)


def flatten_fhir_resources(  # pylint: disable=unused-variable
    resources: list[Any],
) -> FHIRDataFrame | None:
    """
    Flattens a list of FHIR resources into a structured DataFrame.

    This function determines the appropriate ResourceFlattener subclass to use
    based on the type of the first resource in the list. It then uses that flattener
    to transform the list of resources into a FHIRDataFrame.

    Parameters:
        resources (list[Any]): A list of FHIR resource objects to be flattened.

    Returns:
        FHIRDataFrame | None: A structured DataFrame containing the flattened FHIR data,
                               or None if the resources list is empty or unsupported.

    Raises:
        ValueError: If no suitable flattener is found for the resource type.
    """
    if not resources:
        print("No data available.")
        return None

    resource_type = resources[0].resource_type

    flattener_classes = {
        FHIRResourceType.OBSERVATION.value: ObservationFlattener
        # FHIRResourceType.QUESTIONNAIRE_RESPONSE.value: QuestionnaireResponseFlattener
    }

    if not (flattener_class := flattener_classes.get(resource_type)):
        raise ValueError(f"No flattener found for resource type: {resource_type.name}")

    flattener = flattener_class()
    return flattener.flatten(resources)