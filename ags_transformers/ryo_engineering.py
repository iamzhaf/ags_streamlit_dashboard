from .base_transformer import BaseTransformer
from utils import clean_and_structure_spt_table
from utils import add_spt_n_blow_counts
from utils import clean_and_structure_soil_stratum_layer_table
from utils import map_soil_layer_to_spt
from utils import insert_end_depth_of_soil_layer_column
from utils import clean_and_structure_lab_test_table
from utils import clean_and_structure_triaxial_test_table
from utils import merge_and_process_lab_trixial_test_data
from utils import map_soil_specimen_to_spt
from utils import clean_and_structure_proj_borehole_drilling_table
from utils import extract_relevant_columns
from utils import spt_n_groupings
import pandas as pd
import traceback

class RyoEngineeringTransformer(BaseTransformer):

    def __init__(self, file, sheet_name, config):

        super().__init__(file, sheet_name, config) 
        self.iteration_errors = []
        self.spt_df_transformed = None
        self.soil_layer_df_transformed = None
        self.mapped_spt_soil_df_transformed = None
        self.lab_test_df_transformed = None
        self.triaxial_test_df_transformed = None
        self.combined_lab_triaxial_test_transformed_df = None
        self.mapped_specimen_spt_final_transformed_df = None
        self.proj_borehole_info_transformed_df = None
        self.merge_view = None
        self.final_view_df = None
        self.result = None
        self.debug_df = None
        self.rel_cols = ["client","project",
                         "project_no","location","bh_no",
                         "northing_m","easting_m","g_elevation_m","drilling_depth_m"]


    def transform(self):

        self.sections_config= self.config.get("sections")

        try:
            
            
            spt_df = self._load_data("SPT")
            soil_df = self._load_data("Soil_Layer_Stratum_Data")
            lab_test_df = self._load_data("Soil_Lab_Test")
            triaxial_test_df = self._load_data("Soil_Triaxial_Test")
            project_details_df = self._load_data("Project_Borehole_Information")


            try:

                # Run Project Borehole info data transformation
                self.proj_borehole_info_transformed_df = self._proj_borehole_processor(project_details_df)
                self.proj_borehole_info_transformed_df = self._extract_rel_columns(self.proj_borehole_info_transformed_df,self.rel_cols)

            except Exception as e:
                # capture error message with traceback
                error_msg = traceback.format_exec()
                self.iteration_errors.append({
                    "step": "Project Borehole Info Transformation",
                    "error": str(e),
                    "trace": error_msg
                })

            # Run SPT data transformation
            self.spt_df_transformed = self._spt_processor(spt_df)

            # Run Soil data transformation
            self.soil_layer_df_transformed = self._soil_layer_processor(soil_df)

            try:

                # Join SPT with Soil Layers
                self.mapped_spt_soil_df_transformed = self._map_spt_to_soil_layer()

            except Exception as e:
                # capture error message with traceback
                error_msg = traceback.format_exec()
                self.iteration_errors.append({
                    "step": "Merge SPT with Soil Layer Data",
                    "error": str(e),
                    "trace": error_msg
                })

            # Run lab test data transformation
            self.lab_test_df_transformed = self._lab_test_processor(lab_test_df)

            # Run triaxial test data transformation
            self.triaxial_test_df_transformed = self._trixial_test_processor(triaxial_test_df)

            self.debug_df = self.spt_df_transformed

            try:

                # Join lab test and triaxial test 
                self.combined_lab_triaxial_test_transformed_df = self._merge_lab_test_and_triaxial_test_data()

            except Exception as e:
                # capture error message with traceback
                error_msg = traceback.format_exec()
                self.iteration_errors.append({
                    "step": "Merge lab test and triaxial test",
                    "error": str(e),
                    "trace": error_msg
                })

            try:

                # Map soil sample lab/triaxial test to SPT
                self.mapped_specimen_spt_final_transformed_df = self._merge_soil_specimen_to_spt()

            except Exception as e:
                # capture error message with traceback
                error_msg = traceback.format_exec()
                self.iteration_errors.append({
                    "step": "Merge SPT with lab/triaxial test Data",
                    "error": str(e),
                    "trace": error_msg
                })

            try:

                # Merge mapped_specimen_spt_final_transformed_df with mapped_spt_soil_df_transformed
                self.merge_view = self._merge_view()

            except Exception as e:
                # capture error message with traceback
                error_msg = traceback.format_exec()
                self.iteration_errors.append({
                    "step": "Merge mapped_specimen_spt with mapped_spt_soil",
                    "error": str(e),
                    "trace": error_msg
                })

            # Merge proj_borehole with mapped_specimen_spt_final_transformed_df
            self.final_view_df = pd.concat([self.proj_borehole_info_transformed_df,self.merge_view],axis=1)

            # Forward Fill for rel cols 
            self.final_view_df[self.rel_cols] = self.final_view_df[self.rel_cols].fillna(method="ffill")

            # Run data transformation for final_view
            self.final_view_df = self._final_merged_view_processor(self.final_view_df)
        except:
            self.final_view_df = None

        result_bool = isinstance(self.final_view_df, pd.DataFrame) and not self.final_view_df.empty

        self.result = {"final_view_df":self.final_view_df,"transformation_result":result_bool}

    
    def _load_data(self,section_name):
        
        spt_section = self.sections_config.get(section_name)
        df = None
        
        if spt_section:
            skiprows = spt_section.get("skiprows", 0)
            usecols = spt_section.get("columns_section")

            df = self.extract_data(skiprows, usecols)
            
        if df is None:
            raise ValueError(f"The section data, {section_name}, could not be extracted")

        return df


    def _apply_pipeline(self, df, steps):
        for step in steps:
            step_name = step.__name__
            print(f"Running: {step_name}")  # or use logging
            df = step(df)
        return df
    

    def _map_spt_to_soil_layer(self):
        if isinstance(self.soil_layer_df_transformed, pd.DataFrame) and isinstance(self.spt_df_transformed, pd.DataFrame):
            return map_soil_layer_to_spt(self.soil_layer_df_transformed,self.spt_df_transformed)
        else:
            return None


    def _merge_view(self):
        if self.mapped_specimen_spt_final_transformed_df is not None and not self.mapped_specimen_spt_final_transformed_df.empty:
            merged_view = pd.merge(
                self.mapped_spt_soil_df_transformed,
                self.mapped_specimen_spt_final_transformed_df,
                how="left",
                left_on=["spt_no", "spt_depth_to_top_of_test"],
                right_on=["spt_no", "spt_depth"]
            )
            return merged_view
        else:
            None


    def _merge_lab_test_and_triaxial_test_data(self):
        if isinstance(self.lab_test_df_transformed, pd.DataFrame) and isinstance(self.triaxial_test_df_transformed, pd.DataFrame):
            return merge_and_process_lab_trixial_test_data(self.lab_test_df_transformed,self.triaxial_test_df_transformed)
        else:
            return None


    def _merge_c_uu_c_uu_mean_columns(self,df):
        if isinstance(df,pd.DataFrame) and ("c_uu" in df.columns or "c_uu_mean" in df.columns):
            try:
                df["uu"] = df["c_uu"].combine_first(df["c_uu_mean"])
                return df
            except:
                df["uu"] = df["c_uu"]
                return df
        else:
                df["uu"] = None
        
        return df

    def _merge_soil_specimen_to_spt(self):
        if isinstance(self.combined_lab_triaxial_test_transformed_df, pd.DataFrame) and isinstance(self.mapped_spt_soil_df_transformed, pd.DataFrame):
            return map_soil_specimen_to_spt(self.combined_lab_triaxial_test_transformed_df,self.mapped_spt_soil_df_transformed,self.sheet_name,verbose=True)
        else:
            return None


    def _spt_processor(self,df):
        steps = [self._clean_spt_table,self._add_blow_counts]
        return self._apply_pipeline(df,steps)
    

    def _soil_layer_processor(self,df):
        steps = [self._clean_soil_layer_table,self._insert_end_depth_soil_layer]
        return self._apply_pipeline(df,steps)
    

    def _lab_test_processor(self,df):
        steps = [self._clean_lab_test_table]
        return self._apply_pipeline(df,steps)
    

    def _proj_borehole_processor(self,df):
        steps = [self._clean_proj_borehole_info_table]
        return self._apply_pipeline(df,steps)
    

    def _trixial_test_processor(self,df):
        steps = [self._clean_triaxial_test_table]
        return self._apply_pipeline(df,steps)
    

    def _final_merged_view_processor(self,df):
        steps = [
                    self._lower_case_column_name,
                    self._add_real_elevation_level_spt,
                    self._add_real_elevation_level_specimen,
                    self._add_spt_n_groupings,
                    self._restructure_columns_final_view_df,
                    self._merge_c_uu_c_uu_mean_columns,
                    self._remove_leading_trailing_spaces_in_soil_layer,
                    self._drop_unwanted_columns_final_view,
                    self._rename_column_names
                ]
        
        return self._apply_pipeline(df,steps)


    def _insert_end_depth_soil_layer(self,df):
        return insert_end_depth_of_soil_layer_column(df)


    def _clean_soil_layer_table(self,df):
        return clean_and_structure_soil_stratum_layer_table(df)


    def _clean_spt_table(self, df):
        return clean_and_structure_spt_table(df)
    

    def _add_blow_counts(self, df):
        return add_spt_n_blow_counts(df)
    

    def _clean_proj_borehole_info_table(self,df):
        return clean_and_structure_proj_borehole_drilling_table(df)
    

    def _clean_lab_test_table(self,df):
        return clean_and_structure_lab_test_table(df)
    

    def _clean_triaxial_test_table(self,df):
        return clean_and_structure_triaxial_test_table(df)
    

    def _extract_rel_columns(self,df,rel_cols):
        return extract_relevant_columns(df,rel_cols)
    

    def _add_real_elevation_level_spt(self,df):
        df["spt_elevation_level"] = df["g_elevation_m"].astype("float") - df["spt_depth_to_top_of_test"].astype("float")
        return df
    

    def _add_real_elevation_level_specimen(self,df):
        df["sample_elevation_level"] = df["g_elevation_m"].astype("float") - df["sample_depth"].astype("float")
        return df
    

    def _add_spt_n_groupings(self,df):
        df["spt_n_grouping"] = df["spt_n"].apply(lambda x: spt_n_groupings(x))
        return df

    def _drop_unwanted_columns_final_view(self,df):
        unwanted_cols = ["phi_uu"]
        df = df.drop(unwanted_cols,errors="ignore")
        return df
    
    def _lower_case_column_name(self,df):
        df.columns = [c.lower() for c in df.columns]
        return df
    

    def _remove_leading_trailing_spaces_in_soil_layer(self,df):
        df["soil_layer"] = df["soil_layer"].str.strip()
        return df
    

    def _rename_column_names(self,df):
        df = df.rename(columns={"bluk_density_mg_m3":"bulk_density_mg_m3"})
        return df


    def _restructure_columns_final_view_df(self,df):
        desired_cols = self.rel_cols + ["spt_no","spt_depth_to_top_of_test","spt_elevation_level","spt_n","spt_penetration_mm",
                                        "soil_type","spt_n_grouping","soil_layer","soil_description",
                                        "soil_layer_start_depth_m",
                                        "soil_layer_end_depth_m",
                                        "sample_ref_no",
                                        "sample_depth",
                                        "sample_elevation_level"]
        
        if isinstance(self.mapped_specimen_spt_final_transformed_df, pd.DataFrame) and not self.mapped_specimen_spt_final_transformed_df.empty:

            lab_test_cols = [c for c in self.mapped_specimen_spt_final_transformed_df.columns if c not in desired_cols + ["spt_depth","index","ref_no1"]]

            desired_cols = desired_cols + lab_test_cols 

        df = df[desired_cols]

        return df


    
