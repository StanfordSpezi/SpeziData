#
# This source file is part of the Stanford Spezi open-source project
#
# SPDX-FileCopyrightText: 2024 Stanford University and the project authors (see CONTRIBUTORS.md)
#
# SPDX-License-Identifier: MIT
#

# Standard library imports
from datetime import datetime, date
from typing import Any, List, Optional

# Related third-party imports
import matplotlib.pyplot as plt

# Local application/library specific imports
from data_analysis.data_analyzer import FHIRDataProcessor
from data_flattening.FHIR_data_flattener import FHIRDataFrame


class DataVisualizer(FHIRDataProcessor):
    """
    Provides functionalities to visualize FHIR data, extending the FHIRDataProcessor class.
    It supports setting up various visualization parameters such as date range, user IDs for
    filtering, Y-axis bounds, and the option to combine multiple users' data into a single plot
    or separate plots for each user.

    Attributes:
        start_date (str, optional): Start date for filtering the data for visualization.
                                    Defaults to None.
        end_date (str, optional): End date for filtering the data for visualization.
                                  Defaults to None.
        user_ids (List[str], optional): List of user IDs to filter the data for visualization.
                                        Defaults to None.
        y_lower (float): Lower bound for the Y-axis. Defaults to 50.
        y_upper (float): Upper bound for the Y-axis. Defaults to 1000.
        combine_plots (bool): If True, combines data from multiple users into a single plot.
                            Otherwise, creates separate plots for each user. Defaults to True.
        dpi (float): Resolution of the plot image, specified as dots per inch. Defaults to 300.

    Methods:
        set_date_range(start_date, end_date): Sets the date range for data filtering.
        set_user_ids(user_ids): Sets the user IDs for data filtering.
        set_y_bounds(y_lower, y_upper): Sets the Y-axis bounds for visualization.
        set_combine_plots(combine_plots): Sets whether to combine multiple users' data
                                          into a single plot.
        set_dpi(dpi): Sets the DPI for the plot image.
        create_static_plot(flattened_FHIRDataFrame): Creates and displays a static plot
                                                     based on the filtered FHIR data.
    """

    def __init__(self):
        super().__init__()
        self.start_date = None
        self.end_date = None
        self.user_ids = None
        self.y_lower = 50
        self.y_upper = 1000
        self.combine_plots = True
        self.dpi = 300

    def set_date_range(self, start_date: str, end_date: str):
        """Sets the start and end dates for filtering the FHIR data before visualization."""
        self.start_date = start_date
        self.end_date = end_date

    def set_user_ids(self, user_ids: List[str]):
        """Sets the list of user IDs to filter the FHIR data for visualization."""
        self.user_ids = user_ids

    def set_y_bounds(self, y_lower: float, y_upper: float):
        """Sets the lower and upper bounds for the Y-axis of the plot."""
        self.y_lower = y_lower
        self.y_upper = y_upper

    def set_combine_plots(self, combine_plots: bool):
        """Determines whether to combine plots from multiple users into a single plot or create
        separate plots for each.
        """
        self.combine_plots = combine_plots

    def set_dpi(self, dpi: float):
        """Sets the resolution of the plot image, in dots per inch (DPI)."""
        self.dpi = dpi

    def create_static_plot(
        self: Any, flattened_FHIRDataFrame: FHIRDataFrame
    ) -> Optional[plt.Figure]:
        """
        Generates a static plot based on the filtered FHIR data, considering the visualization
        parameters set previously such as date range, user IDs, Y-axis bounds, and whether to
        combine plots. The plot is displayed and optionally returned if a single plot is created.

        Parameters:
            flattened_FHIRDataFrame (FHIRDataFrame): The FHIRDataFrame containing the data
            to be visualized.

        Returns:
            plt.Figure: The matplotlib figure object of the plot, if a single plot is generated.
            Returns None if separate plots are created for each user or
            if no plot is generated due to errors.
        """
        if not isinstance(
            flattened_FHIRDataFrame.df["EffectiveDateTime"].iloc[0], date
        ):
            print("The date type should be of type date.")
            return

        if flattened_FHIRDataFrame.df["LoincCode"].nunique() != 1:
            print(
                "Error: More than one unique LoincCode found."
                "Each plot should be based on a single LoincCode."
            )
            return

        self.validate_columns(flattened_FHIRDataFrame)
        flattened_df = flattened_FHIRDataFrame.df
        if self.start_date:
            self.start_date = datetime.strptime(self.start_date, "%Y-%m-%d").date()
        if self.end_date:
            self.end_date = datetime.strptime(self.end_date, "%Y-%m-%d").date()
        if self.start_date and self.end_date:
            flattened_df = flattened_df[
                (flattened_df["EffectiveDateTime"] >= self.start_date)
                & (flattened_df["EffectiveDateTime"] <= self.end_date)
            ]

        users_to_plot = (
            self.user_ids if self.user_ids else flattened_df["UserId"].unique()
        )

        if self.combine_plots:
            plt.figure(figsize=(10, 6), dpi=self.dpi)
            for uid in users_to_plot:
                user_df = flattened_df[flattened_df["UserId"] == uid]
                aggregated_data = (
                    user_df.groupby("EffectiveDateTime")["QuantityValue"]
                    .sum()
                    .reset_index()
                )
                plt.bar(
                    aggregated_data["EffectiveDateTime"],
                    aggregated_data["QuantityValue"],
                    edgecolor="black",
                    linewidth=1.5,
                    label=f"User {uid}",
                )
            plt.ylim(self.y_lower, self.y_upper)
            plt.legend()
            plt.title(
                f"{flattened_df['QuantityName'].iloc[0]} from {self.start_date} to {self.end_date}"
            )
            plt.xlabel("Date")
            plt.ylabel(
                f"{flattened_df['QuantityName'].iloc[0]} ({flattened_df['QuantityUnit'].iloc[0]})"
            )
            plt.xticks(rotation=45)
            plt.yticks()
            plt.tight_layout()
            fig = plt.gcf()
            plt.show()

        else:
            for uid in users_to_plot:
                plt.figure(figsize=(10, 6), dpi=self.dpi)
                user_df = flattened_df[flattened_df["UserId"] == uid]
                aggregated_data = (
                    user_df.groupby("EffectiveDateTime")["QuantityValue"]
                    .sum()
                    .reset_index()
                )
                plt.bar(
                    aggregated_data["EffectiveDateTime"],
                    aggregated_data["QuantityValue"],
                    edgecolor="black",
                    linewidth=1.5,
                    label=f"User {uid}",
                )
                plt.legend()
                plt.title(
                    f"{user_df['QuantityName'].iloc[0]} for User {uid} "
                    f"from {self.start_date} to {self.end_date}"
                )
                plt.xlabel("Date")
                plt.ylabel(
                    f"{user_df['QuantityName'].iloc[0]} ({user_df['QuantityUnit'].iloc[0]})"
                )
                plt.xticks(rotation=45)
                plt.yticks()
                plt.tight_layout()
                if len(users_to_plot) == 1:
                    fig = plt.gcf()
                plt.show()

        return fig
