import os,sys
from abc import ABC, abstractmethod
import pandas as pd
import numpy as np

class BaseTransformer(ABC):
    def __init__(self, file, sheet_name, config):
        self.file = file
        self.sheet_name = sheet_name
        self.config = config

    def extract_data(self,skiprows,usecols):
        """Utility function to extract Excel data with config options."""
        try:
            print(usecols,skiprows)
            df = pd.read_excel(
                self.file,
                sheet_name=self.sheet_name,
                skiprows=skiprows,
                usecols=usecols
            )
            return df
        except Exception as e:
            return None

    @abstractmethod
    def transform(self):
        """Contractor-specific transformation logic to be implemented by child class."""
        pass
