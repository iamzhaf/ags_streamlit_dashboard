from .base_transformer import BaseTransformer
import os,sys
import pandas as pd
from utils import find_table_indices
from utils import map_soil_layer_to_spt
from utils import map_soil_specimen_to_spt
from utils import map_stratum_layer_to_rock_samples
from utils import long_to_wide
from utils import spt_n_groupings
from utils import drop_metadata_rows
from utils import map_sample_to_stratum
from utils import map_core_to_stratum_layer
import streamlit as st

class AGSSgTransformer(BaseTransformer):
    """
    This class helps turn messy soil investigation data from Excel files into neat, organized tables.
    It takes information about boreholes, soil layers, and test results, and matches them up so it's easy to study and use later.

    Key functions:
    - Loads and cleans Excel data about soil and boreholes.
    - Matches up soil layers, boreholes, and test results so they line up correctly.
    - Organizes everything into easy-to-use tables for analysis.
    - Makes it much simpler for engineers and scientists to work with complicated soil data.

    Parameters:
    file: The Excel file with the soil investigation data.
    sheet_name: The list of sheet names in the Excel file.
    config: A dictionary with settings that tell the class how to process the data.
    """
    def __init__(self, file, sheet_name, config):
        super().__init__(file, sheet_name, config)
        self.transformed_dfs = {}
        self.boreholes_df = {}
        self.sample_spts = {}
        self.trig_boreholes = {}
        self.clss_boreholes = {}
        self.borehole_clss_trig = {}
        self.soil_layer_samples = {}
        self.core_mapped_dfs = {}
        self.core_dfs = {}
        self.iprm_stratum_df = {}
        self.columns_mapping = {
            'geol_top': 'start_depth_of_soil_layer_m',
            'geol_base': 'end_depth_of_soil_layer_m',
            'geol_desc': 'soil_description_borelog_soil_name',
            'geol_geol': 'geological_classification',
            'ispt_top': 'spt_depth_to_top_of_test',
            "samp_top": "depth_m",
            "trig_cu": "uu",
        }
        self.geol_cols_mapping = {
            'layer_id':'layer_no',
            'geol_top': 'start_depth_of_soil_layer_m',
            'geol_base': 'end_depth_of_soil_layer_m',
            'geol_desc': 'soil_description_borelog_soil_name',
            'geol_geol': 'geological_classification'
        }
        self.final_view_cols_mapping = {
            "hole_fdep": "drilling_depth_m",
            "hole_gl": "g_elevation_m",
            "hole_natn": "northing_m",
            "hole_nate": "easting_m",
            "hole_id": "hole_id",
            "spt_depth": "spt_depth_to_top_of_test",
            "proj_id": "project_no",
            "proj_clnt": "client",
            "proj_loc": "project",
            "proj_cont": "contractor",
            "clss_ll": "atterberg_limit_%_ll_%",
            "clss_pl": "atterberg_limit_%_pl_%",
            "clss_bden": "bulk_density_mg_m3",
            "clss_lden": "dry_density_mg_m3",
            "clss_pd": "partical_density",
            "clss_nmc": "water_content_%",
            "hole_id":"bh_no",
            "ref_no":"sample_ref_no",
            "depth_m":"sample_depth",
            "geological_classification":"soil_type"
        }
        self.borehole_attributes = ["hole_id","hole_type","hole_nate","hole_natn","hole_gl","hole_fdep"]
        self.project_attriutes = ["proj_id","proj_clnt","proj_loc","proj_cont"]
        self.section_join_transformers = {
            "CLSS" : self._join_clss,
            "TRIG" : self._join_trig,
            "ROCK" : self._join_rock_samples,
            "CORE" : self._join_core_data,
            "CNMT" : self._join_contaminant_chemical_data,
            "CONG" : self._join_consolidation,
            "GRAD" : self._join_grad,
            "PTST" : self._join_ptst,
            "TRIX" : self._join_trix,
            "IPRM" : self._join_iprm
        }


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

            columns = [str(c).replace("*","").strip().lower() for c in df.iloc[start_row, start_col:end_col+1]]

            # st.write(section_name)
            # st.write(start_row,end_row,start_col,end_col)
            # st.write(columns)

            if end_row is not None:

                transformed_df = df.iloc[start_row+1:end_row, start_col:end_col+1]

            if end_row is None:

                transformed_df = df.iloc[start_row+1:, start_col:end_col+1]
         
            transformed_df.columns = columns

            # drop all columns with NaN or missing values for all rows
            transformed_df = transformed_df.dropna(axis=1,how="all")  

            # drop metadata rows
            transformed_df = drop_metadata_rows(transformed_df)

            # drop rows with STOP in first column
            first_col = transformed_df.columns[0]
            transformed_df = transformed_df[transformed_df[first_col] != "STOP"]

            # drop row whose row values are NaN or missing for start marker column
            transformed_df = transformed_df.dropna(subset=start_marker.lower(),how="all")

            return transformed_df
        
        else:

            return None
        
            
    def _load_and_process_transformed_data(self,section_name):

        # Load the raw data
        raw_df = self._load_data(section_name)

        # Process the raw data
        transformed_df = self._transform_raw_data(raw_df, section_name)

        # reset index
        transformed_df = transformed_df.reset_index(drop=True)

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

            # combined = pd.merge(df_spt,
            #                         mapped_spt_soil_df.loc[:,["spt_no","soil_layer","soil_type","soil_description","soil_layer_start_depth_m","soil_layer_end_depth_m"]],
            #                         on="spt_no",how="left")

            # st.write("Joinig SPT with Stratum for {}".format(borehole))
            combined = pd.merge(df_soil,mapped_spt_soil_df.loc[:,["stratum_id","spt_no"]],on="stratum_id",how="left")
            combined = pd.merge(combined,df_spt.drop(columns=["hole_id"]),on="spt_no",how="left")
            # st.write(combined)
            self.boreholes_df[borehole] = combined


    def _append_borehole_attributes(self):


        for borehole in self.boreholes_df:

            # st.write("Appending borehole attributes for {}".format(borehole))
            
            df = self.boreholes_df[borehole]
            
            hole_df = self.transformed_dfs["HOLE"][self.transformed_dfs["HOLE"]["hole_id"] == borehole]
        
            # safe extraction with NaN for missing columns for desired borehole attributes
            hole_df = hole_df.reindex(columns=self.borehole_attributes) 

            df = pd.merge(df,hole_df,on="hole_id",how="left")

            self.boreholes_df[borehole] = df

            # st.write(df)
           

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
                                start_depth_col="start_depth_of_soil_layer_m",
                                end_depth_col="end_depth_of_soil_layer_m",
                                verbose=False)

            # st.write("Mapping Soil Specimen to SPT for {}".format(borehole))
            # st.write(mapped_samp_spt_df)

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


    def _join_clss(self):

        self._transformed_clss_df()

        for borehole in self.transformed_dfs["HOLE"]["hole_id"].unique():

            borehole_clss = self.clss_boreholes[borehole]

            borehole_clss = borehole_clss.rename(columns={"ref_no":"sample_ref_no"})

            cols_to_keep = ["sample_ref_no"] + [c for c in borehole_clss.columns if c.startswith("clss_")]

            borehole_clss = borehole_clss[cols_to_keep]

            self.boreholes_df[borehole] = pd.merge(self.boreholes_df[borehole],borehole_clss,on="sample_ref_no",how="left")

            # st.write("Completed joining CLSS for {}".format(borehole))
            # st.write(self.boreholes_df[borehole])

        # st.write("Successfully Completed joining CLSS for all boreholes")



    def _join_trig(self):

        self._transformed_trig_df()

        for borehole in self.transformed_dfs["HOLE"]["hole_id"].unique():

            borehole_trig = self.trig_boreholes[borehole]

            borehole_trig = borehole_trig.rename(columns={"ref_no":"sample_ref_no"})

            self.boreholes_df[borehole] = pd.merge(self.boreholes_df[borehole],borehole_trig,on="sample_ref_no",how="left")

            # st.write("Completed joining TRIG for {}".format(borehole))
            # st.write(self.boreholes_df[borehole])

        # st.write("Successfully Completed joining TRIG for all boreholes")


    def _join_borehole_sample_spt(self):

        for borehole in self.transformed_dfs["HOLE"]["hole_id"].unique():

            df_borehole = self.boreholes_df[borehole]

            borehole_sample_spt = self.sample_spts[borehole][["spt_no","spt_depth","ref_no","depth_m"]]

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


    def _final_view_columns_mapping(self,df):
        
        df = df.rename(columns=self.final_view_cols_mapping)
        
        return df   


    def _add_real_elevation_level_spt(self,df):
        df["spt_elevation_level"] = df["g_elevation_m"].astype("float") - df["spt_depth_to_top_of_test"].astype("float")
        return df


    def _add_real_elevation_level_specimen(self,df):
        df["sample_elevation_level"] = df["g_elevation_m"].astype("float") - df["samp_top"].astype("float")
        return df

    def _process_final_view(self,df):

        steps = [self._add_project_details,self._final_view_columns_mapping,self._add_real_elevation_level_spt,self._add_real_elevation_level_specimen]

        return self._apply_pipeline(df,steps)


    def _add_project_details(self, df):
        """
        Adds project info to the data (column wise) and fills in any missing project details by copying values from above.
        """
        df = pd.concat([self.transformed_dfs["PROJ"][self.project_attriutes], df], axis=1)
        df[self.project_attriutes] = df[self.project_attriutes].ffill()
        return df

    def _generate_final_view(self):

        # union all boreholes (row wise)
        self.final_view_df = pd.concat([df for df in self.boreholes_df.values()], axis=0).reset_index(drop=True)

        self.final_view_df = self._process_final_view(self.final_view_df)

        self.final_view_cols = self._reorder_columns(
                                                columns=self.final_view_df.columns.tolist(),
                                                columns_to_move=["spt_elevation_level","sample_elevation_level"],
                                                name_col_start="drilling_depth_m",
                                                name_col_end="sample_ref_no")

        self.final_view_cols = self._reorder_columns(
                                                columns=self.final_view_df.columns.tolist(),
                                                columns_to_move=["spt_n_grouping"],
                                                name_col_start="soil_type",
                                                name_col_end="spt_no")


        self.final_view_df = self.final_view_df[self.final_view_cols]

        # st.write(self.final_view_df)


    def _process_rock_samples(self,df):

        steps = [self._rename_columns,self._create_sample_ref_no]

        return self._apply_pipeline(df,steps)


    def _create_stratum_id(self,df):

        stratum_id = (
                        df["hole_id"].astype(str) + "_" +
                        df["geol_geol"].astype(str) + "_" +
                        df["layer_no"].astype(str).str.zfill(3)
                    )

        df.insert(1,"stratum_id",stratum_id)

        return df


    def _create_stratum_layer_no(self,df):

        layer_no = df.groupby("hole_id").cumcount() + 1

        df.insert(1,"layer_no",layer_no)

        return df
            

    def _process_stratum_data(self,df):

        steps = [self._create_stratum_layer_no,self._create_stratum_id]

        return self._apply_pipeline(df,steps)


    def _transformed_stratum_data(self):

        dfs = []

        # st.write(self.transformed_dfs["HOLE"]["hole_id"].unique())

        for borehole in self.transformed_dfs["HOLE"]["hole_id"].unique():

            # st.write(borehole)

            df_borehole_stratum= self.transformed_dfs["GEOL"][self.transformed_dfs["GEOL"]["hole_id"] == borehole]

            df_borehole_stratum["geol_top"] = df_borehole_stratum["geol_top"].astype("float")

            df_borehole_stratum["geol_base"] = df_borehole_stratum["geol_base"].astype("float")

            df_borehole_stratum = df_borehole_stratum.sort_values(by=["geol_top"],ascending=True)

            df_borehole_stratum = df_borehole_stratum.reset_index(drop=True)

            # st.write(df_borehole_stratum)

            df_borehole_stratum = self._process_stratum_data(df_borehole_stratum)

            dfs.append(df_borehole_stratum)

        self.transformed_dfs["GEOL"] = pd.concat(dfs, axis=0).reset_index(drop=True)

            
    def _join_rock_samples(self):

        # st.write("Joining borehole rock samples with stratum layer")
        
        for borehole in self.transformed_dfs["HOLE"]["hole_id"].unique():
            
            combined_boreholes = self.boreholes_df[borehole]

            rock_samples = self.transformed_dfs["ROCK"][self.transformed_dfs["ROCK"]["hole_id"] == borehole]

            rock_samples = self._create_sample_ref_no(rock_samples)

            cols_to_keep = ["ref_no"] + [col for col in rock_samples.columns if col.startswith("rock_")]

            rock_samples = rock_samples[cols_to_keep]

            rock_samples = rock_samples.rename(columns={"ref_no":"sample_ref_no"})

            combined_df = pd.merge(combined_boreholes,rock_samples,on="sample_ref_no",how="left")

            # st.write(combined_df)

            self.boreholes_df[borehole] = combined_df



    def _generate_sample_soil_layer_dataframes(self):

        for borehole in self.transformed_dfs["HOLE"]["hole_id"].unique():

            df_samples = self.transformed_dfs["SAMP"][self.transformed_dfs["SAMP"]["hole_id"] == borehole.strip()]

            # st.write("Samples for borehole {}".format(borehole))
            # st.write(df_samples)

            df_samples = self._process_samp_df(df_samples)

            df_borehole = self.boreholes_df[borehole]


            mapped_sample_stratum = map_sample_to_stratum(
                                                            sample_df=df_samples,
                                                            borehole_with_stratum=df_borehole,
                                                            stratum_id_col="stratum_id",
                                                            stratum_top_col="start_depth_of_soil_layer_m",
                                                            stratum_base_col="end_depth_of_soil_layer_m",
                                                            sample_depth_col="depth_m"
                                                            )

            self.soil_layer_samples[borehole] = mapped_sample_stratum   

            # st.write("Mapped Sample to Stratum {}".format(borehole))
            # st.write(mapped_sample_stratum)


    def _join_layer_spt_with_sample_spt(self):

        for borehole in self.transformed_dfs["HOLE"]["hole_id"].unique():

            df_borehole = self.boreholes_df[borehole]

            sample_spt = self.sample_spts[borehole].dropna(subset=["spt_no"],how="all")

            df_borehole = pd.merge(
                                    df_borehole,
                                    sample_spt.loc[:,["spt_no","sample_ref_no"]],
                                    on=["spt_no"],
                                    how="left"
                                    )

            self.boreholes_df[borehole] = df_borehole

            # st.write("Joined borehole SPT with Sample SPT")
            # st.write(self.boreholes_df[borehole])


    def _join_layer_sample_with_sample_spt(self):

        for borehole in self.transformed_dfs["HOLE"]["hole_id"].unique():

            df_layer_samples = self.soil_layer_samples[borehole]

            df_layer_samples = pd.merge(
                                    df_layer_samples,
                                    self.sample_spts[borehole].loc[:,["spt_no","sample_ref_no"]],
                                    left_on=["ref_no"],
                                    right_on=["sample_ref_no"],
                                    how="outer",
                                    indicator=True
                                    )

            # fill missing sample_ref_no with ref_no using chain method
            df_layer_samples["sample_ref_no"] = df_layer_samples["sample_ref_no"].fillna(df_layer_samples["ref_no"])

            df_layer_samples = df_layer_samples.rename(columns={
                                                                    "matched_stratum_id":"stratum_id",
                                                                    "matched_stratum_top":"start_depth_of_soil_layer_m",
                                                                    "matched_stratum_base":"end_depth_of_soil_layer_m"})

            self.soil_layer_samples[borehole] = df_layer_samples

            # st.write("Joined Layer Samples with Sample SPT")
            # st.write(df_layer_samples)

    
    def _join_layer_spt_with_layer_samples(self):

        for borehole in self.transformed_dfs["HOLE"]["hole_id"].unique():

            df_layer_samples = self.soil_layer_samples[borehole]

            df_layer_samples = df_layer_samples[df_layer_samples["_merge"] == "left_only"]

            df_layer_spts = self.boreholes_df[borehole]

            combined_df = pd.concat([df_layer_spts,df_layer_samples],axis=0)

            # join stratum id with geol layer data
            stratum_layer = self.transformed_dfs["GEOL"][self.transformed_dfs["GEOL"]["hole_id"] == borehole]

            cols_to_extract = ["stratum_id","layer_no","geol_top","geol_base","geol_geol","geol_desc"]

            stratum_layer = stratum_layer[cols_to_extract]

            stratum_layer = stratum_layer.rename(columns=self.geol_cols_mapping)

            combined_df = pd.merge(combined_df,stratum_layer,on=["stratum_id"],how="left",suffixes=("","_ref"))

            cols_to_be_filled = [v for v in stratum_layer.columns.tolist() if v is not "stratum_id"]

            for col in cols_to_be_filled:
                combined_df[col] = combined_df[col].fillna(combined_df[col+"_ref"])   

            cols_to_drop = ["geol_leg","geol_geo2","geol_geo3"] + [v+"_ref" for v in stratum_layer.columns.tolist() if v is not "stratum_id"] + ["_merge"] + ["ref_no","samp_ref","samp_type","depth_m","samp_base","samp_dia","samp_desc","samp_rem"]

            combined_df = combined_df.drop(columns=cols_to_drop,errors="ignore")

            # join with samp data
            samples = self.transformed_dfs["SAMP"][self.transformed_dfs["SAMP"]["hole_id"] == borehole]

            samples = self._create_sample_ref_no(samples)

            samples = samples.rename(columns={"ref_no":"sample_ref_no"})

            # st.write(samples.columns.tolist())

            combined_df = pd.merge(combined_df,samples.loc[:,["sample_ref_no","samp_top","samp_base","samp_desc","samp_rem"]],on=["sample_ref_no"],how="left")

            # sort by stratum top then by sample top
            combined_df = combined_df.sort_values(by=["start_depth_of_soil_layer_m","samp_top","spt_depth_to_top_of_test"],ascending=[True,True,True])

            # fill hole attributes
            hole_columns = [col for col in combined_df.columns.tolist() if col.startswith("hole_")]

            for col in hole_columns:
                combined_df[col] = combined_df[col].ffill()

            self.boreholes_df[borehole] = combined_df

            # sort by stratum top then by 

            # st.write("Joined Layer SPT with Layer Samples")
            # st.write(self.boreholes_df[borehole])

    
    def _create_core_ref_no(self,core_data):

        core_row_number = core_data.groupby("hole_id").cumcount()+1

        core_ref_no = "CORE_" + core_row_number.astype(str)

        core_data.insert(loc=1,column="core_ref_no",value=core_ref_no)

        return core_data

    
    def _transformed_core_data(self):

        for borehole in self.transformed_dfs["HOLE"]["hole_id"].unique():

            core_data = self.transformed_dfs["CORE"][self.transformed_dfs["CORE"]["hole_id"] == borehole]

            # create core ref no 
            core_data = self._create_core_ref_no(core_data)

            # st.write(core_data)

            self.core_dfs[borehole] = core_data


    def _map_core_data_with_stratum(self):

        for borehole in self.transformed_dfs["HOLE"]["hole_id"].unique():

            core_data = self.core_dfs[borehole]

            geol_data = self.transformed_dfs["GEOL"][self.transformed_dfs["GEOL"]["hole_id"] == borehole]

            mapped = map_core_to_stratum_layer(
                                        core_data,
                                        geol_data,
                                        "stratum_id",
                                        "geol_top",
                                        "geol_base" 
                                )


            self.core_mapped_dfs[borehole] = mapped

    
    def _join_core_data(self):


        self._transformed_core_data()
        self._map_core_data_with_stratum()

        for borehole in self.transformed_dfs["HOLE"]["hole_id"].unique():

            core_mapped = self.core_mapped_dfs[borehole]

            core_data = self.core_dfs[borehole]

            core_mapped = core_mapped.rename(columns={"matched_stratum_id":"stratum_id"})

            combined_df = pd.merge(self.boreholes_df[borehole],core_mapped.loc[:,["stratum_id","core_ref_no"]],on=["stratum_id"],how="left")

            cols_to_extract = ["core_ref_no"] + [col for col in core_data.columns if col.startswith("core_") and col not in ["core_ref_no"]]

            combined_df = pd.merge(combined_df,core_data[cols_to_extract],on=["core_ref_no"],how="left")

            self.boreholes_df[borehole] = combined_df

            # st.write("Completed Joining Core Data for borehole: ",borehole)
            # st.write(self.boreholes_df[borehole])


    def _tranformed_cont_chem_data(self):


        self.transformed_dfs["CNMT"] = self._create_sample_ref_no(self.transformed_dfs["CNMT"])

        self.transformed_dfs["CNMT"] = self.transformed_dfs["CNMT"].rename(columns={"ref_no":"sample_ref_no"})

        # st.write(self.transformed_dfs["CNMT"])


    def _tranformed_consolidation(self):


        self.transformed_dfs["CONG"] = self._create_sample_ref_no(self.transformed_dfs["CONG"])

        self.transformed_dfs["CONG"] = self.transformed_dfs["CONG"].rename(columns={"ref_no":"sample_ref_no"})

        # st.write(self.transformed_dfs["CONG"])


    
    def _tranformed_grad(self):

        self.transformed_dfs["GRAD"] = self._create_sample_ref_no(self.transformed_dfs["GRAD"])

        self.transformed_dfs["GRAD"] = self.transformed_dfs["GRAD"].rename(columns={"ref_no":"sample_ref_no"})

        # st.write(self.transformed_dfs["GRAD"])

    
    def _transformed_ptst(self):

        self.transformed_dfs["PTST"] = self._create_sample_ref_no(self.transformed_dfs["PTST"])

        self.transformed_dfs["PTST"] = self.transformed_dfs["PTST"].rename(columns={"ref_no":"sample_ref_no"})

        # st.write(self.transformed_dfs["PTST"])

    
    def _transformed_trix(self):

        self.transformed_dfs["TRIX"] = self._create_sample_ref_no(self.transformed_dfs["TRIX"])

        self.transformed_dfs["TRIX"] = self.transformed_dfs["TRIX"].rename(columns={"ref_no":"sample_ref_no"})

        # st.write(self.transformed_dfs["TRIX"])  

        
    def _join_contaminant_chemical_data(self):

        self._tranformed_cont_chem_data()

        for borehole in self.transformed_dfs["CNMT"]["hole_id"].unique():

            cnmt_data = self.transformed_dfs["CNMT"][self.transformed_dfs["CNMT"]["hole_id"] == borehole]

            cols_to_extract = ["sample_ref_no"] + [col for col in cnmt_data.columns if col.startswith("cnmt_")]

            cnmt_data = cnmt_data[cols_to_extract]

            # st.write(cnmt_data)

            # only join if cnmt data is not empty
            if len(cnmt_data) > 0:

                combined_df = pd.merge(self.boreholes_df[borehole],cnmt_data,on=["sample_ref_no"],how="left")

                self.boreholes_df[borehole] = combined_df

                # st.write("Completed Joining Contaminant Chemical Data for borehole: ",borehole)

                # st.write(self.boreholes_df[borehole])

            else:

                continue


    def _join_consolidation(self):

        self._tranformed_consolidation()

        for borehole in self.transformed_dfs["CONG"]["hole_id"].unique():

            cong_data = self.transformed_dfs["CONG"][self.transformed_dfs["CONG"]["hole_id"] == borehole]

            cols_to_extract = ["sample_ref_no"] + [col for col in cong_data.columns if col.startswith("cong_")]

            cong_data = cong_data[cols_to_extract]

            # st.write(cong_data)

            # only join if cong data is not empty
            if len(cong_data) > 0:

                combined_df = pd.merge(self.boreholes_df[borehole],cong_data,on=["sample_ref_no"],how="left")

                self.boreholes_df[borehole] = combined_df

                # st.write("Completed Joining Consolidation Data for borehole: ",borehole)

                # st.write(self.boreholes_df[borehole])

            else:

                continue

    
    def _join_grad(self):

        self._tranformed_grad()

        for borehole in self.transformed_dfs["GRAD"]["hole_id"].unique():

            grad_data = self.transformed_dfs["GRAD"][self.transformed_dfs["GRAD"]["hole_id"] == borehole]

            cols_to_extract = ["sample_ref_no"] + [col for col in grad_data.columns if col.startswith("grad_")]

            grad_data = grad_data[cols_to_extract]

            # st.write(grad_data)

            # only join if grad data is not empty
            if len(grad_data) > 0:

                combined_df = pd.merge(self.boreholes_df[borehole],grad_data,on=["sample_ref_no"],how="left")

                self.boreholes_df[borehole] = combined_df

                # st.write("Completed Joining Particle Size Distribution (GRAD) Data for borehole: ",borehole)

                # st.write(self.boreholes_df[borehole])

            else:

                continue


    def _join_ptst(self):

        self._transformed_ptst()

        for borehole in self.transformed_dfs["PTST"]["hole_id"].unique():

            ptst_data = self.transformed_dfs["PTST"][self.transformed_dfs["PTST"]["hole_id"] == borehole]

            cols_to_extract = ["sample_ref_no"] + [col for col in ptst_data.columns if col.startswith("ptst_")]

            ptst_data = ptst_data[cols_to_extract]

            # st.write(ptst_data)

            # only join if ptst data is not empty
            if len(ptst_data) > 0:

                combined_df = pd.merge(self.boreholes_df[borehole],ptst_data,on=["sample_ref_no"],how="left")

                self.boreholes_df[borehole] = combined_df

                # st.write("Completed Joining PTST Data for borehole: ",borehole)

                # st.write(self.boreholes_df[borehole])

            else:

                continue


    def _join_trix(self):

        self._transformed_trix()

        for borehole in self.transformed_dfs["TRIX"]["hole_id"].unique():

            trix_data = self.transformed_dfs["TRIX"][self.transformed_dfs["TRIX"]["hole_id"] == borehole]

            cols_to_extract = ["sample_ref_no"] + [col for col in trix_data.columns if col.startswith("trix_")]

            trix_data = trix_data[cols_to_extract]

            # st.write(trix_data)

            # only join if trix data is not empty
            if len(trix_data) > 0:

                combined_df = pd.merge(self.boreholes_df[borehole],trix_data,on=["sample_ref_no"],how="left")

                self.boreholes_df[borehole] = combined_df

                # st.write("Completed Joining Particle Size Distribution (TRIX) Data for borehole: ",borehole)

                # st.write(self.boreholes_df[borehole])

            else:

                continue

    def _mapped_iprm_with_stratum(self):

        for borehole in self.transformed_dfs["IPRM"]["hole_id"].unique():

            iprm_data = self.transformed_dfs["IPRM"][self.transformed_dfs["IPRM"]["hole_id"] == borehole]

            stratum_layer_data = self.transformed_dfs["GEOL"][self.transformed_dfs["GEOL"]["hole_id"] == borehole]

            mapped = map_iprm_to_stratum_layer(
                                                iprm_data,
                                                stratum_layer_data,
                                                stratum_id="stratum_id",
                                                stratum_layer_depth_col="geol_top",
                                                end_stratum_layer_depth_col="geol_base"
                                                )


            self.iprm_stratum_df[borehole] = mapped

    def _join_iprm(self):

        self._mapped_iprm_with_stratum()

        for borehole in self.transformed_dfs["IPRM"]["hole_id"].unique():

            iprm_data = self.transformed_dfs["IPRM"][self.transformed_dfs["IPRM"]["hole_id"] == borehole]

            cols_to_extract = ["iprm_testn"] + [col for col in iprm_data.columns if col.startswith("iprm_")]

            iprm_data = iprm_data[cols_to_extract]

            mapped_iprm_stratum = self.iprm_stratum_df[borehole]

            mapped_iprm_stratum = mapped_iprm_stratum.rename(columns={"matched_stratum_id": "stratum_id"})

            combined = pd.merge(self.boreholes_df[borehole],mapped_iprm_stratum.loc[:,["iprm_testn","stratum_id"]],on=["sample_ref_no"],how="left")

            combined = pd.merge(combined,iprm_data,on=["sample_ref_no"],how="left")

            self.boreholes_df[borehole] = combined

            st.write("Completed Joining IPRM Data for borehole: ",borehole)

            st.write(self.boreholes_df[borehole])


    def extract_data(self):

        self.sections_config= self.config.get("sections")

        # create section names list to be used for mapping and processing
        self.section_names = list(self.sections_config.keys())

        # cleaned sheet names for mapping
        self.cleaned_sheet_names = self._process_sheets_names()

        self.section_names = [s for s in self.section_names if s in self.cleaned_sheet_names]

        # extract the geo data
        self._extract_geo_data(self.section_names)


    def _create_base_data(self):

            # process stratum dataframes
            self._transformed_stratum_data()

            # st.write("Processed GEOL Data")

            # st.write(self.transformed_dfs["GEOL"])

            # st.write(self.transformed_dfs["SAMP"])

            # generate spt and soil layer dataframes
            self._generate_spt_soil_layer_dataframes()

            # append borehole attributes
            self._append_borehole_attributes()

            # join all samples
            self._generate_sample_soil_layer_dataframes()

            # generate sample spt dataframes
            self._generate_samp_spt_dataframes()

            # join layer_sample with sample_spt
            self._join_layer_sample_with_sample_spt()

            # join layer_spt with sample_spt
            self._join_layer_spt_with_sample_spt()

            # join layer_spt with layer_samples
            self._join_layer_spt_with_layer_samples()


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

        self._create_base_data()

        # st.write("Base Data Created")

        # st.write(list(self.transformed_dfs.keys()))

        # st.write(self.boreholes_df[list(self.boreholes_df.keys())[0]])

        sections_to_join_with_base = list(s for s in self.transformed_dfs.keys() if s not in ["PROJ","HOLE","GEOL","SAMP","ISPT"])

        # st.write("Sections to join with base")
        # st.write(sections_to_join_with_base)

        for section in self.section_join_transformers.keys():
            # st.write(section)
            if section in sections_to_join_with_base:
                if self.section_join_transformers[section] is None:
                    continue
                # st.write("Processing: {}".format(section))
                # st.write(self.section_join_transformers[section].__name__)
                self.section_join_transformers[section]()
                continue

        # st.write(self.boreholes_df[list(self.boreholes_df.keys())[0]])

        # generate final view
        self._generate_final_view()

        # st.write(self.final_view_df)
        
        
        