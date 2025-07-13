import os,sys
from abc import ABC, abstractmethod
import pandas as pd
import numpy as np

class BaseTransformer(ABC):
    """
    Abstract base class for transforming Excel data. Handles loading of Excel sheets by name(s),
    supporting both single sheet (string) and multiple sheets (list of strings).
    """
    def __init__(self, file, sheet_name, config):
        """
        Args:
            file: Path or file-like object to the Excel file.
            sheet_name (str or list of str): Sheet name(s) to process.
            config: Configuration dictionary or object.
        """
        self.file = file
        self.sheet_name = sheet_name
        self.config = config

    def extract_data(self, skiprows, usecols=None):
        """
        Extract Excel data for specified sheet(s).

        Args:
            skiprows (int): Number of rows to skip at the start of the sheet(s).
            usecols (str, list-like, or None): Columns to read from the sheet(s), as per pandas.read_excel.

        Returns:
            pd.DataFrame or dict[str, pd.DataFrame] or None:
                - If sheet_name is a string, returns a DataFrame for that sheet, or None on failure.
                - If sheet_name is a list, returns a dict mapping sheet names to DataFrames (or None for failed sheets).
        """
        try:
            df = pd.read_excel(
                self.file,
                sheet_name=self.sheet_name,
                skiprows=skiprows,
                usecols=usecols
            )
            return df
        except Exception as e:
            if isinstance(self.sheet_name, list):
                # If reading multiple sheets, return dict with None for failed sheets
                return {name: None for name in self.sheet_name}
            return None

    @abstractmethod
    def transform(self):
        """
        Contractor-specific transformation logic to be implemented by child class.
        """
        pass
