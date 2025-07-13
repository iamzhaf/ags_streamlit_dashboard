from .base_transformer import BaseTransformer
import os,sys
import pandas as pd
from utils import find_table_indices
from utils import map_soil_layer_to_spt
from utils import map_soil_specimen_to_spt
from utils import long_to_wide
from utils import spt_n_groupings

class AGSSgTransformer(BaseTransformer):
    def __init__(self, file, sheet_name, config):
        super().__init__(file, sheet_name, config)
        self.transformed_dfs = {}
        self.boreholes_df = {}
        self.sample_spts = {}
        self.trig_boreholes = {}
        self.clss_boreholes = {}
        self.borehole_clss_trig = {}
        self.columns_mapping = {
            'geol_top': 'start_depth_of_soil_layer_m',
            'geol_base': 'end_depth_of_soil_layer_m',
            'geol_desc': 'soil_description_borelog_soil_name',
            'geol_geol': 'geological_classification',
            'ispt_top': 'spt_depth_to_top_of_test',
            "samp_top": "depth_m",
            "trig_cu": "uu",
        }
        self.borehole_attributes = ["hole_id","hole_type","hole_nate","hole_natn","hole_gl","hole_fdep"]


    def _load_data(self, section_name):
        """
        Loads data for a given section name using the section config.
        If 'columns_section' is missing, assigns None to usecols.
        """
        configs = self.sections_config.get(section_name)

        df = None

        # get the sheet name 
        sheet_name = self.sheet_name[self.cleaned_sheet_names.index(section_name)]

        if configs:

            skiprows = configs.get("skiprows", 0)
            usecols = configs.get("columns_section", None)
            df = self.extract_data_per_sheet(skiprows, usecols,sheet_name)

        if df is None:
            raise ValueError(f"The section data, {section_name}, could not be extracted")

        return df


    def extract_data_per_sheet(self, skiprows, usecols=None, sheet_name=None):
        """
        Extract Excel data for specified sheet(s).

        Args:
            skiprows (int): Number of rows to skip at the start of the sheet(s).
            usecols (str, list-like, or None): Columns to read from the sheet(s), as per pandas.read_excel.

        Returns:
            pd.DataFrame or None:
        """
        try:
            df = pd.read_excel(
                self.file,
                sheet_name=sheet_name,
                skiprows=skiprows,
                usecols=usecols
            )
            return df
        except Exception as e:
            return None


    def _transform_raw_data(self,df,section_name):
        """
        Extracts and transforms a specific table section from a DataFrame based on configuration markers.

        This method locates a table section within the provided DataFrame `df` using start and end markers defined
        in the configuration for the given `section_name`. It extracts the relevant rows and columns, sets the column
        names based on the header row, and returns a cleaned DataFrame with standardized column names (stripped and lowercased).

        Args:
            df (pd.DataFrame): The input DataFrame containing raw data.
            section_name (str): The name of the section to extract, corresponding to a section in the configuration.

        Returns:
            pd.DataFrame or None: The transformed DataFrame for the specified section, or None if the section is not found
            in the configuration.
        """
        
        configs = self.sections_config.get(section_name)

        if configs:

            start_marker = configs.get("start_marker")
            
            end_marker = configs.get("end_marker")

            # get the start row, end row, start column, end column indices of the table
            start_row, end_row, start_col, end_col = find_table_indices(df, start_marker, end_marker)

            columns = df.iloc[start_row, start_col:end_col]

            transformed_df = df.iloc[start_row+1:end_row, start_col:end_col].dropna(how="all")

            transformed_df.columns = [c.strip().lower() for c in columns]

            return transformed_df
        
        else:

            return None
            
    def _load_and_process_transformed_data(self,section_name):

        # Load the raw data
        raw_df = self._load_data(section_name)

        # Process the raw data
        transformed_df = self._transform_raw_data(raw_df, section_name)

        return transformed_df


    def _process_sheets_names(self):
        cleaned_sheet_names = [sheet[:4].upper().strip() for sheet in self.sheet_name]
        return cleaned_sheet_names


    def _extract_geo_data(self,sections):
        
        # iterate the list of sections and load and process the data
        for s in sections:

            print(f"Processing...{s}")

            transformed_df = self._load_and_process_transformed_data(s)

            self.transformed_dfs[s] = transformed_df

    
    def _apply_pipeline(self, df, steps):
        """
        Sequentially applies a list of processing functions (steps) to a DataFrame.

        Each function in `steps` takes a DataFrame as input and returns a transformed DataFrame.
        The method prints the name of each step as it is applied, updating the DataFrame at each stage.

        Args:
            df (pd.DataFrame): The initial DataFrame to process.
            steps (list of callable): List of functions to apply to the DataFrame in order.

        Returns:
            pd.DataFrame: The DataFrame after all processing steps have been applied.
        """
        for step in steps:
            step_name = step.__name__
            print(f"Running: {step_name}")  # or use logging
            df = step(df)
        return df


    def _add_spt_id(self,df):
        df["spt_no"] = ["spt_" + str(i).zfill(3) for i in range(1, len(df) + 1)]
        return df
    
    
    def _add_penetration_spt_n(self,df):
        
        cols_to_fill_zeros = ["ispt_inc3","ispt_inc4","ispt_inc5","ispt_inc6","ispt_pen3","ispt_pen4","ispt_pen5","ispt_pen6"]
        
        df[cols_to_fill_zeros] = df[cols_to_fill_zeros].fillna(0)

        df["spt_n"] = df["ispt_inc3"].astype(int) + df["ispt_inc4"].astype(int) + df["ispt_inc5"].astype(int) + df["ispt_inc6"].astype(int)
        
        df["penetration_mm"] = df["ispt_pen3"].astype(int) + df["ispt_pen4"].astype(int) + df["ispt_pen5"].astype(int) + df["ispt_pen6"].astype(int)
        
        return df


    def _rename_columns(self,df):
        
        df = df.rename(columns=self.columns_mapping)
        
        return df   


    def _add_spt_n_groupings(self,df):
        df["spt_n_grouping"] = df["spt_n"].apply(lambda x: spt_n_groupings(x))
        return df


    def _process_spt_df(self,df):

        steps = [self._add_spt_id,self._add_penetration_spt_n,self._add_spt_n_groupings,self._rename_columns]

        return self._apply_pipeline(df,steps)


    def _process_soil_df(self,df):

        steps = [self._rename_columns]

        return self._apply_pipeline(df,steps)

    
    def _generate_spt_soil_layer_dataframes(self):

        for borehole in self.transformed_dfs["HOLE"]["hole_id"].unique():
            
            df_spt = self.transformed_dfs["ISPT"][self.transformed_dfs["ISPT"]["hole_id"] == borehole]
            
            df_soil = self.transformed_dfs["GEOL"][self.transformed_dfs["GEOL"]["hole_id"] == borehole]

            df_spt = self._process_spt_df(df_spt)

            df_soil = self._process_soil_df(df_soil)

            mapped_spt_soil_df = map_soil_layer_to_spt(df_soil,df_spt,spt_depth_col="spt_depth_to_top_of_test")

            mapped_spt_soil_df.insert(0,"hole_id",borehole)

            combined = pd.merge(df_spt,
                                    mapped_spt_soil_df.loc[:,["spt_no","soil_layer","soil_type","soil_description","soil_layer_start_depth_m","soil_layer_end_depth_m"]],
                                    on="spt_no",how="left")

            self.boreholes_df[borehole] = combined


    def _append_borehole_attributes(self):

        for borehole in self.boreholes_df:
            
            df = self.boreholes_df[borehole]
            
            hole_df = self.transformed_dfs["HOLE"][self.transformed_dfs["HOLE"]["hole_id"] == borehole][self.borehole_attributes]

            df = pd.merge(df,hole_df,on="hole_id",how="left")

            self.boreholes_df[borehole] = df
           

    def _create_sample_ref_no(self,df):
        """
        Create a new column 'sample_ref_no' as a composite key of 'sample_ref' and 'sample_type',
        delimited by '-', and insert it after 'hole_id' in each DataFrame in self.boreholes_df.
        """
        if 'samp_ref' in df.columns and 'samp_type' in df.columns and 'hole_id' in df.columns:
            sample_ref_no =  df['samp_type'].astype(str) + "-" + df['samp_ref'].astype(str)
            # Find the position of 'hole_id'
            hole_id_idx = df.columns.get_loc('hole_id')
            # Insert the new column after 'hole_id'
            df.insert(hole_id_idx + 1, 'ref_no', sample_ref_no) 
            return df
        else:
            return df


    def _process_samp_df(self,df):

        steps = [self._rename_columns,self._create_sample_ref_no]

        return self._apply_pipeline(df,steps)


    def _generate_samp_spt_dataframes(self):

        for borehole in self.transformed_dfs["HOLE"]["hole_id"].unique():

            borehole_spt = self.boreholes_df[borehole]

            borehole_samp = self.transformed_dfs["SAMP"][self.transformed_dfs["SAMP"]["hole_id"] == borehole]

            borehole_samp = self._process_samp_df(borehole_samp)

            mapped_samp_spt_df = map_soil_specimen_to_spt(soil_specimen_data=borehole_samp,
                                spt_data=borehole_spt,
                                sample_ref_col="ref_no",
                                borehole_id_col="hole_id",
                                verbose=True)

            self.sample_spts[borehole] = mapped_samp_spt_df


    def _process_trig_df(self,df):

        steps = [self._rename_columns,self._create_sample_ref_no]

        return self._apply_pipeline(df,steps)

    
    def _clean_trig_columns(self,df):

        new_columns = [c.replace("trig_","").strip().lower() for c in df.columns]

        df.columns = new_columns

        return df


    def _transformed_trig_df(self):

        for borehole in self.transformed_dfs["HOLE"]["hole_id"].unique():

            borehole_trig = self.transformed_dfs["TRIG"][self.transformed_dfs["TRIG"]["hole_id"] == borehole]

            borehole_trig = self._process_trig_df(borehole_trig)

            df_uu = borehole_trig[borehole_trig["trig_type"] == "UU"].rename(columns={"trig_cu":"uu"})

            df_other_tests = borehole_trig[borehole_trig["trig_type"] != "UU"]

            df_other_tests = self._transformed_long_to_wide(df_other_tests)

            df_combined = pd.merge(df_uu.loc[:,["ref_no","uu"]],df_other_tests,on="ref_no",how="outer")

            df_combined = self._clean_trig_columns(df_combined)

            self.trig_boreholes[borehole] = df_combined


    def _transformed_long_to_wide(self,df):

        return long_to_wide(df,"ref_no","trig_type",["trig_coh","trig_phi"])


    def _process_clss_df(self,df):

        steps = [self._rename_columns,self._create_sample_ref_no]

        return self._apply_pipeline(df,steps)

    
    def _transformed_clss_df(self):

        for borehole in self.transformed_dfs["HOLE"]["hole_id"].unique():

            borehole_clss = self.transformed_dfs["CLSS"][self.transformed_dfs["CLSS"]["hole_id"] == borehole]

            borehole_clss = self._process_clss_df(borehole_clss)

            self.clss_boreholes[borehole] = borehole_clss


    def _join_clss_trig(self):

        for borehole in self.transformed_dfs["HOLE"]["hole_id"].unique():

            borehole_clss = self.clss_boreholes[borehole]

            borehole_trig = self.trig_boreholes[borehole]

            self.borehole_clss_trig[borehole] = pd.merge(borehole_clss,borehole_trig,on="ref_no",how="left")


    def _join_borehole_sample_spt(self):

        for borehole in self.transformed_dfs["HOLE"]["hole_id"].unique():

            df_borehole = self.boreholes_df[borehole]

            borehole_sample_spt = self.sample_spts[borehole][["spt_no","ref_no","depth_m"]]

            self.boreholes_df[borehole] = pd.merge(df_borehole,borehole_sample_spt,on="spt_no",how="left")


    def _join_borehole_clss_trig(self):

        for borehole in self.transformed_dfs["HOLE"]["hole_id"].unique():

            df_borehole = self.boreholes_df[borehole]

            borehole_clss_trig = self.borehole_clss_trig[borehole]
            
            borehole_clss_trig = borehole_clss_trig.drop(columns=["hole_id","depth_m","?file_fset"], errors='ignore')

            self.boreholes_df[borehole] = pd.merge(df_borehole,borehole_clss_trig,on="ref_no",how="left")



    def _reorder_columns(self,columns,columns_to_move,name_col_start,name_col_end):

        place_holder = [c for c in columns if c not in columns_to_move]

        name_col_start_index = columns.index(name_col_start)

        name_col_end_index = columns.index(name_col_end)

        return place_holder[:name_col_start_index+1] + columns_to_move + place_holder[name_col_end_index:]


    def _reorder_borehole_attributes_columns(self):

        columns_to_move = ["hole_type","hole_natn","hole_nate","hole_gl","hole_fdep"]

        name_col_start = "hole_id"

        name_col_end = "spt_no"

        for borehole in self.boreholes_df:

            columns = self.boreholes_df[borehole].columns.tolist()

            cols = self._reorder_columns(columns,columns_to_move,name_col_start,name_col_end)

            self.boreholes_df[borehole] = self.boreholes_df[borehole][cols]


    def transform(self):
        """
        Main transformation pipeline for AGS Singapore data.
        Args:
            file_obj: Excel file object.
            sheet_names: List of all sheet names in the file.
            cleaned_sheet_names: List of cleaned sheet names for mapping.
        Returns:
            dict: boreholes_df with processed DataFrames per borehole.
        """

        self.sections_config= self.config.get("sections")

        # create section names list to be used for mapping and processing
        self.section_names = list(self.sections_config.keys())

        # cleaned sheet names for mapping
        self.cleaned_sheet_names = self._process_sheets_names()

        # extract the geo data
        self._extract_geo_data(self.section_names)

        # generate spt and soil layer dataframes
        self._generate_spt_soil_layer_dataframes()

        # append borehole attributes
        self._append_borehole_attributes()

        # generate sample spt dataframes
        self._generate_samp_spt_dataframes()

        # transform trig df
        self._transformed_trig_df()

        # transform clss df
        self._transformed_clss_df()

        # join clss and trig
        self._join_clss_trig()
        
        # join borehole and sample spt
        self._join_borehole_sample_spt()

        # join borehole and clss trig
        self._join_borehole_clss_trig()

        # reorder borehole attributes columns
        self._reorder_borehole_attributes_columns()
        
        