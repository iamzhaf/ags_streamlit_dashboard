import pandas as pd
import traceback
import re
import json
import os,sys
import numpy as np
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4, landscape
import plotly.io as pio
import uuid
from reportlab.lib.units import inch
from PIL import Image


# # Load contractor config reference json file
# AGS_CONFIG_ROOT_PATH = r"C:\Users\Zhafran\OneDrive\01 Work\02 Current Work\TERS Consultant\Projects\Soil_Data_Insights_Dashboard\ags_streamlit_dashboard\ags_configs"
# with open(os.path.join(AGS_CONFIG_ROOT_PATH,"ryo_engineering.json"),"r") as file:
#     RYO_AGS_CONFIG = json.load(file)


class AGSColumnCleaner:
    def __init__(self, context=None):
        self.context = context

    def clean_text(self, text):
        text = text.lower()
        text = re.sub(r"\bfor\b", "", text)
        text = re.sub(r"[.:()]", "", text)
        text = re.sub(r"[\/]", "_", text)
        text = re.sub(r"\s+", "_", text)
        text = re.sub(r"__+", "_", text)
        text = text.strip("-_ ")
        text = self._apply_context_rules(text)
        return text

    def _apply_context_rules(self, text):
        # Default: no extra rules
        return text

    def clean_columns(self, columns):
        return [self.clean_text(col) for col in columns]
    

    def _lowercase_column_names(self,column):
        return column.lower()


class LabColumnCleaner(AGSColumnCleaner):
    def __init__(self):
        super().__init__(context="lab")

    def _apply_context_rules(self, text):
        # Remove digits or unit between "depth" and "_m"
        text = re.sub(r"(depth)[^a-zA-Z]*(_m)", r"\1\2", text)
        text = text.replace("_f_", "_phi_")
        return text


def create_spt_column_names(spt_data):
    # Create a new list to store the filled values
    filled = []
    prev_value = None
    
    for item in spt_data.columns[2:]:
        if item.startswith("Unnamed"):
            filled.append(prev_value)
        else:
            filled.append(item)
            prev_value = item

    # For each field name in `filled`, we want to pair it with a repeated subfield name.
    # Here, we repeat the pattern ["no_of_blows", "penetration_mm"] six times to align with
    # the 12 columns in the `filled` list (each main field has two subfields).
    subfields = ["no_of_blows", "penetration_mm"] * 6

    # Combine each element in filled with its corresponding subfield elements
    # joining them using an underscore to form new column names like '1st 75mm (Seating)_no_of_blows'.
    spt_cols = spt_data.columns[:2].tolist() + [f"{main}_{sub}" for main, sub in zip(filled, subfields)]

    col_cleaner = AGSColumnCleaner()

    # clean up text columns
    spt_cols = [col_cleaner.clean_text(cols) for cols in spt_cols]

    return spt_cols


def insert_end_depth_of_soil_layer_column(soil_layer):
    soil_layer.insert(2,"end_depth_of_soil_layer_m",soil_layer["start_depth_of_soil_layer_m"].shift(-1))
    soil_layer = soil_layer.dropna(subset=soil_layer.columns[2:],how="all")
    return soil_layer


def clean_and_structure_spt_table(spt_df):
    
    spt_df.columns = create_spt_column_names(spt_df)
    
    spt_df = spt_df.iloc[2:,:].reset_index(drop=True)
    
    # remove rows where all rows with missing values
    spt_df = spt_df.dropna(subset=["depth_to_top_of_test"],how="all")
    
    # fillna with zeros 
    spt_df = spt_df.fillna(0)

    return spt_df


def get_contrator_config_reference_json_file(contractor):
    
    contractor_filename_mapper = {"Ryo Engineering": "ryo_engineering"}

    # get the base dir
    parent_dir = os.path.dirname(__file__) 

    # set the config json path
    config_path = os.path.join(parent_dir, 'ags_configs', f"{contractor_filename_mapper["Ryo Engineering"]}.json")

    AGS_CONFIG = None

    with open(config_path,"r") as file:
        AGS_CONFIG = json.load(file)

    return AGS_CONFIG    


def extract_borehole_number(df):

    df = df.copy()

    borehole_id = None
    
    # remove all rows with missing values
    df = df.dropna(how="all")

    if df.shape[0] >2:
        def match_borehole_id_fieldname(name):
            borehole_id_fieldname_pattern_matching = r'\bBH[\s\.]*No\.?\b'
            if not pd.isnull(name):
                match_result = re.match(borehole_id_fieldname_pattern_matching,name,re.IGNORECASE)
                return match_result
            else:
                return None
    
        for name,value in zip(df.iloc[:,0],df.iloc[:,1]):
            match_result = match_borehole_id_fieldname(name)
            if match_result:
                if not pd.isnull(value):
                    borehole_id = value.strip()
                else:
                    continue  
            else:
                continue
    
    return borehole_id


def add_spt_n_blow_counts(spt_df):
    # Append (SPT-N) test blow counts and test penetration (mm)
    spt_df["spt_n"], spt_df["penetration_mm"] = create_test_segments_blow_count_and_penetration(spt_df)
    return spt_df


def create_test_segments_blow_count_and_penetration(spt_data):
    # Define the test segments
    test_segments = ["1st", "2nd", "3rd", "4th"]
    
    # Compute total blows for test
    total_blows_test = sum(
        spt_data[f"{seg}_75mm_test_no_of_blows"] for seg in test_segments
    )

    # Compute total penetration for test
    total_penetration_mm_test = sum(
        spt_data[f"{seg}_75mm_test_penetration_mm"] for seg in test_segments
    )

    return total_blows_test, total_penetration_mm_test


def create_geological_soil_data_columns(soil_data):

    # Create a list to store first level col
    first = []
    
    col_cleaner = AGSColumnCleaner()

    for item in soil_data.columns:
        item = col_cleaner.clean_text(item)
        if item.startswith("unnamed"):
            first.append(prev_value)
        else:
            first.append(item)
            prev_value = item

    second_level = [col_cleaner.clean_text(str(c)) if not pd.isnull(c) else "" for c in soil_data.iloc[0,:].values]

    last_level = [col_cleaner.clean_text(str(c)) if not pd.isnull(c) else "" for c in soil_data.iloc[1,:].values]

    final_cols = [col_cleaner.clean_text("_".join([first,sec,last])) for first,sec,last in zip(first,second_level,last_level)]
    
    return final_cols


def clean_and_structure_soil_stratum_layer_table(soil_layer):
    
    soil_layer.columns = create_geological_soil_data_columns(soil_layer)
    
    soil_layer = soil_layer.iloc[2:,:].reset_index(drop=True)
    
    # remove rows where all rows with missing values
    soil_layer = soil_layer.dropna(subset=soil_layer.columns[1:],how="all")
    
    # fillna with zeros 
    soil_layer = soil_layer.fillna(0)

    return soil_layer


def generate_soil_type_classification(geoclassification,spt_n):
    """
    Classifies the soil type based on geological classification and SPT-N value.
        
    Parameters:
        geoclassification (str): Geological classification code of the soil stratum (e.g., 'FILL', 'G(V)', 'G(VI)', etc).
        spt_n (int or float): Standard Penetration Test (SPT-N) blow count for the last 300 mm of penetration.

    Returns:
        str: Descriptive soil type classification based on geoclassification and SPT-N value.
    """
    # remove in-between whitespaces and trailing/leading whitespaces
    geoclassification = geoclassification.strip()
    geoclassification = re.sub(r"[\s+]","",geoclassification)

    spt_n_to_string = lambda x : int(spt_n) if not np.NaN else ""
    
    if geoclassification == "FILL":
        return "FILL"
    elif ((geoclassification == "G(V)") or (geoclassification == "G(VI)")) and (spt_n>=30) and (spt_n<50):
        return geoclassification + " " + "N>=30"
    elif  ((geoclassification == "G(V)") or (geoclassification == "G(VI)"))  and (spt_n>=50):
        return geoclassification + " " + "N>=50"
    elif (geoclassification == "G(VI)") and (spt_n<10):
        return geoclassification + " " + "N<10"    
    elif (geoclassification == "G(VI)") and (spt_n<30):
        return geoclassification + " " + "N<30"
    else:
        return "NO CLASSIFICATION"
    

def spt_n_groupings(spt_n):
    """
    Categorize SPT-N value into 4 groups: 
        N<10;
        N<30;
        N>=50;
        N<=100;
     
    Parameters:
        spt_n (int or float): Standard Penetration Test (SPT-N) blow count for the last 300 mm of penetration.

    Returns:
        str: Classification of SPT-N value.
    """
    if spt_n <= 10:
            return "N≤10"
    elif spt_n <= 30:
        return "10<N≤30"
    elif spt_n <= 50:
        return "30<N≤50"
    elif spt_n > 50:
        return "N>50"
    else:
        return "UNKNOWN"
        
def map_soil_layer_to_spt(soil_layer_data,spt_data,spt_depth_col="depth_to_top_of_test"):
    """
    Parameters:
    
        spt_df: DataFrame containing SPT results with columns:
            - 'spt_id' or 'spt_no'
            - 'depth_to_top_of_test'
            - 'spt_n' => the spt_n blow count is the summation of total blows during 2nd 150mm last 150mm.
            
        soil_df: DataFrame containing soil layer info with columns:
            - 'start_depth_of_soil_layer_m'
            - 'end_depth_of_soil_layer_m'
            - 'geological_classification'
            - 'soil_description_borelog_soil_name
    Returns:
        A new DataFrame mapping each SPT to the correct soil layer.
    """
    
    results = []

    for d_from, d_to, geo_class,soil_desc in zip(
        soil_layer_data['start_depth_of_soil_layer_m'],
        soil_layer_data['end_depth_of_soil_layer_m'],
        soil_layer_data['geological_classification'],
        soil_layer_data['soil_description_borelog_soil_name']
    ):
        for spt_id, spt_depth, spt_n,spt_penetration in zip(
            spt_data['spt_no'],
            spt_data[spt_depth_col],
            spt_data['spt_n'],
            spt_data["penetration_mm"]
        ):
            if (d_from <= spt_depth) and (spt_depth < d_to):
                results.append({
                    'spt_no': spt_id,
                    'spt_depth_to_top_of_test': spt_depth,
                    'spt_n': spt_n,
                    'spt_penetration_mm':spt_penetration,
                    'soil_layer': geo_class,
                    'soil_type':generate_soil_type_classification(geo_class,spt_n),
                    'soil_description': soil_desc,
                    'soil_layer_start_depth_m': d_from,
                    'soil_layer_end_depth_m': d_to
                })

    return pd.DataFrame(results)


def get_valid_borehole_sheets(ags_excel_file, all_sheet_names, config, extract_borehole_number_fn,verbose=False):
    """
    Validate sheets in an AGS Excel file by checking the Project_Borehole_Information section.

    Parameters:
    - ags_excel_file: Path or file-like object of the AGS Excel file
    - all_sheet_names: List of all worksheet names
    - config: Dictionary containing 'skiprows' and 'columns_section' for Project_Borehole_Information
    - extract_borehole_number_fn: A callable function that extracts the borehole ID from df_info

    Returns:
    - valid_borehole_sheets: List of validated sheet names
    """

    valid_borehole_sheets = []

    for sheet in all_sheet_names:
        try:
            # Extract Project_Borehole_Information section
            df_info = pd.read_excel(
                ags_excel_file,
                sheet_name=sheet,
                skiprows=config["skiprows"],
                usecols=config["columns_section"]
            )

            # Check for >90% missing values in first 2 columns
            col1_null_ratio = df_info.iloc[:, 0].isnull().sum() / df_info.shape[0]
            col2_null_ratio = df_info.iloc[:, 1].isnull().sum() / df_info.shape[0]

            if any([col1_null_ratio > 0.9, col2_null_ratio > 0.9]):
                if verbose:
                    print("="*60)
                    print(f"'{sheet}': Not valid borehole datasheet'")
                continue

            # Extract borehole ID
            borehole_id = extract_borehole_number_fn(df_info)

            if borehole_id == sheet.strip():
                valid_borehole_sheets.append(sheet)
                if verbose:
                    print("="*60)
                    print(f"'{sheet}': Valid borehole datasheet'")
                    print(f"Borehole detected in '{sheet}': {borehole_id}")
            else:
                if verbose:
                    print("="*60)
                    print(f"'{sheet}': Not valid borehole datasheet'")
                continue

        except Exception as e:
            if verbose:
                print("="*60)
                print(f"Failed to extract from {sheet}: {e}")
                traceback.print_exc()

    return valid_borehole_sheets


def clean_and_structure_lab_test_table(triaxial_test):
    
    triaxial_test.columns = create_soil_sampling_test_data_columns(triaxial_test)
    
    triaxial_test = triaxial_test.iloc[2:,:].reset_index(drop=True)
    
    # Drop rows where depth_m is missing (i.e. rows with no sampling)
    triaxial_test = triaxial_test.dropna(subset=["depth_m"],how="all")

    if "ref_no1" in triaxial_test.columns:
        # Drop rows where depth_m is missing (i.e. rows with no sampling)
        triaxial_test = triaxial_test.dropna(subset=["ref_no1"],how="all")

    if "ref_no" in triaxial_test.columns:
        # Drop rows where depth_m is missing (i.e. rows with no sampling)
        triaxial_test = triaxial_test.dropna(subset=["ref_no"],how="all")

    mask = (triaxial_test['depth_m'] == 0) & (triaxial_test['depth_m'].shift(1) == 0)
    triaxial_test = triaxial_test[~mask]

    # reset and keep index
    triaxial_test = triaxial_test.reset_index()

    return triaxial_test


def create_soil_sampling_test_data_columns(soil_sampling_data):

    # Create a list to store first level col
    first = []

    col_cleaner = AGSColumnCleaner()

    for item in soil_sampling_data.columns:
        item = col_cleaner.clean_text(item)
        if item.startswith("unnamed"):
            first.append(prev_value)
        else:
            first.append(item)
            prev_value = item

    lab_data_col_cleaner = LabColumnCleaner()

    second_level = [lab_data_col_cleaner.clean_text(str(c)) if not pd.isnull(c) else "" for c in soil_sampling_data.iloc[0,:].values]

    last_level = [lab_data_col_cleaner.clean_text(str(c)) if not pd.isnull(c) else "" for c in soil_sampling_data.iloc[1,:].values]

    final_cols = [lab_data_col_cleaner.clean_text("_".join([first,sec,last])) for first,sec,last in zip(first,second_level,last_level)]
    
    return final_cols


def clean_and_structure_triaxial_test_table(triaxial_test):
    
    triaxial_test.columns = create_soil_sampling_test_data_columns(triaxial_test)
    
    triaxial_test = triaxial_test.iloc[2:,:].reset_index(drop=True)
    
    # Drop rows where ref_no1 is missing (i.e. rows with no sampling)
    triaxial_test = triaxial_test.dropna(subset=["depth_m"],how="all")

    mask = (triaxial_test['depth_m'] == 0) & (triaxial_test['depth_m'].shift(1) == 0)
    triaxial_test = triaxial_test[~mask]
        
    # reset and keep index
    triaxial_test = triaxial_test.reset_index()

    return triaxial_test


def parse_triaxial_row(test_str, c_str, phi_str,verbose=False):
    """
    Smart parser that handles:
    - UU format like 'Cu1=105, Cu2=166, Cu3=173'
    - Standard test type string characters like "CU/CD/DS" format
    - Test values (string characters) like '30/-/-'
    
    Returns a dictionary of parsed cohesion (c_) and friction angle (phi_) values
    """
    
    def parse_uu_format(s):
        matches = re.findall(r'Cu\d*=?\s*(\d+(?:\.\d+)?)', s)
        values = [float(m) for m in matches if m not in ['-', '']]
        return {f'c_UU_{i+1}': v for i, v in enumerate(values)}, values

    def split_or_empty(s):
        return s.split('/') if pd.notna(s) else []

    result = {}

    if verbose:
        print("="*60)
        print("{} {}".format(type(test_str),test_str))

    # Check for UU with Cu1= format
    if pd.notna(test_str) and "UU" in test_str and re.search(r'Cu\d*=', str(c_str)):
        parsed, values = parse_uu_format(str(c_str))
        result.update(parsed)
        if values:
            result['c_UU_mean'] = round(sum(values) / len(values),1)
        return result

    # Handle standard CU/CD/DS format
    test_types = split_or_empty(test_str)
    c_values = split_or_empty(c_str)
    phi_values = split_or_empty(phi_str)

    # Pad values
    while len(c_values) < len(test_types):
        c_values.append(None)
    while len(phi_values) < len(test_types):
        phi_values.append(None)

    # Map each test type to c and phi
    for i, test in enumerate(test_types):
        if not test:
            continue
        c_val = c_values[i] if c_values[i] not in [None, '-', ''] else None
        phi_val = phi_values[i] if phi_values[i] not in [None, '-', ''] else None
        result[f'c_{test}'] = float(c_val) if c_val else None
        result[f'phi_{test}'] = float(phi_val) if phi_val else None

    return result


def merge_and_process_lab_trixial_test_data(lab_test_df, trixial_test_df,verbose=False):
    """
    Processes triaxial lab test data if present, else returns only normal lab test data.

    Parameters:
        normal_lab_test_df (DataFrame): DataFrame with standard lab test results.
        lab_trixial_test_df (DataFrame): DataFrame with triaxial test data.
        parse_triaxial_row_func (function): Function to parse each row of triaxial data.

    Returns:
        DataFrame: Combined DataFrame of normal and parsed triaxial lab test data.
    """
    
    # Check if all values from 3rd column onwards are NaN
    empty_triaxial_test_data = trixial_test_df.iloc[:, 2:].isnull().all().all()

    if empty_triaxial_test_data:
        print("⚠️ Triaxial test data is empty — skipping processing.")
        return lab_test_df
    
    # Parse triaxial test rows
    trixial_test_df["shear_strength_c_kn_m2"] = trixial_test_df["shear_strength_c_kn_m2"].astype(str)

    trixial_test_df["shear_strength_phi_o"] = trixial_test_df["shear_strength_phi_o"].astype(str)
    
    parsed = trixial_test_df.apply(
        lambda row: parse_triaxial_row(
            row['shear_strength_test_type'],
            row['shear_strength_c_kn_m2'],
            row['shear_strength_phi_o'],verbose=verbose
        ),
        axis=1
    )
    
    parsed_df = pd.DataFrame(parsed.tolist())
    
    parsed_trixial_test_df = pd.concat([
        trixial_test_df.loc[:, [trixial_test_df.columns[0], trixial_test_df.columns[2]]], 
        parsed_df
    ], axis=1)

    # Merge with normal lab test data
    combined_df = pd.merge(lab_test_df, parsed_trixial_test_df, on="index", how="left")

    return combined_df


def map_soil_specimen_to_spt(soil_specimen_data, spt_data, sample_ref_col="ref_no1", borehole_id_col="borehole_id", verbose=False):
    """
    Parameters:
        spt_data: DataFrame containing SPT results with columns:
            - 'spt_no' or 'spt_no'
            - 'soil_layer_start_depth_m'
            - 'soil_layer_end_depth_m'
            
        soil_sample_data: DataFrame containing soil specimen lab test data 

    Returns:
        A new DataFrame mapping each SPT to the correct soil layer.
    """

    results = []

    if verbose:
        if borehole_id_col in soil_specimen_data.columns:
            bh_id_val = soil_specimen_data[borehole_id_col].iloc[0]
            print(f"Total specimens to map for borehole id {bh_id_val}: {soil_specimen_data.shape[0]} soil specimens")
    
    # Loop through each soil specimen
    for sample,depth in zip(soil_specimen_data[sample_ref_col], soil_specimen_data["depth_m"]):
        # Check if sample is core or non-core type
        if re.match(r"^C", sample):

            if verbose:
                print("=" * 100)
                print(f"This sample is a core sample — skip mapping. Sample: {sample} | Specimen Depth: {depth}")
            continue

        else:

            candidate_spts = []
            abs_distance = []

            if verbose:
                print("=" * 100)
                print(f"Checking sample {sample} at depth {depth:.2f}m")
                
            # Search for SPTs within the same soil layer
            for d_from,d_to,spt_no,spt_depth in zip(spt_data["soil_layer_start_depth_m"],spt_data["soil_layer_end_depth_m"],spt_data["spt_no"],spt_data["spt_depth_to_top_of_test"]):
                
                if (d_from <= depth) and (depth < d_to):
                    
                    if verbose:
                        print(f"Candidate: {spt_no} | Soil Layer: {d_from}-{d_to} | SPT Depth: {spt_depth}")
                    
                    candidate_spts.append([spt_no,spt_depth])
                    
                    abs_distance.append(abs(depth-spt_depth))

            # Skip if no candidates found
            if not candidate_spts:
                if verbose:
                    print(f"[WARNING] No matching SPT found for sample {sample}")
                continue
                    
            # Get the closest SPT by minimum depth difference
            identified_spt_idx = np.argmin(abs_distance)

            identified_spt,identified_spt_depth = candidate_spts[identified_spt_idx]

            # Show best candidate
            if verbose:
                print(f"Identified SPT For Sample: {sample} => SPT: {identified_spt} | SPT Depth: {identified_spt_depth} | Specimen Depth: {depth}")
    
            results.append(
                        {
                            "spt_no":identified_spt,
                            "spt_depth":identified_spt_depth,
                            "sample_ref_no":sample,
                            "sample_depth":depth
                        })


    col_clean = AGSColumnCleaner()

    if results:
        # Merge with the lab results 
        results = pd.DataFrame(results).drop_duplicates()
        
        results = pd.merge(results, soil_specimen_data, left_on=["sample_ref_no"], right_on=[sample_ref_col], how="left")
        # Standardize column
        results.columns = [col_clean.clean_text(i) for i in results.columns]
        
        return results

    else:
        return None

    
def clean_and_structure_proj_borehole_drilling_table(proj_borehole_drill_data):

    # drop rows where all columns are NaN or mssing
    proj_borehole_drill_data = proj_borehole_drill_data.dropna(how="all") 

    # replace missing or NaN values with "Missing"
    proj_borehole_drill_data = proj_borehole_drill_data.fillna("Missing")
    
    column_cleaner = AGSColumnCleaner()   
    cols = [column_cleaner.clean_text(f) for f in proj_borehole_drill_data.iloc[:,0]]
    
    proj_borehole_drill_data = pd.DataFrame(proj_borehole_drill_data.iloc[:,1]).T.reset_index(drop=True)
    
    proj_borehole_drill_data.columns = cols
    
    return proj_borehole_drill_data


def extract_relevant_columns(df,cols_to_extract):
    return df[cols_to_extract]

def find_table_indices(df, start_marker="PROJ_ID", end_marker="STOP"):
    """
    Find the indices that define the table boundaries in an AGS file.
    
    Args:
        df (pd.DataFrame): The raw AGS data DataFrame
        start_marker (str): The marker to identify the start of the table (default: "PROJ_ID")
        end_marker (str): The marker to identify the end of the table (default: "STOP")
        
    Returns:
        tuple: (start_row, end_row, start_col, end_col) - Indices defining the table boundaries
    """
    start_row = 0
    end_row = 0
    start_col = 0
    end_col = 0

    for i, row in enumerate(df.iloc[:,:].values):
        for j, val in enumerate(row):
            if j == 0 and str(val).strip().upper() == end_marker:
                end_row = i
                break
            
            val = str(val).strip().upper()
            if val == start_marker:
                start_row = i
                start_col = j
            
            if val == end_marker:
                end_col = j
                break
    
    return start_row, end_row, start_col, end_col

def clean_plotly_figure_for_export(fig):
    """
    Strips customdata and hovertemplate to make Plotly figures export-safe.
    """
    for trace in fig.data:
        trace.customdata = None
        trace.hovertemplate = None

    fig.update_layout(
        legend_title_text=None,  # Remove legend title

        # ✅ X and Y axis tick font size
        xaxis=dict(
            tickfont=dict(size=20),
            title_font=dict(size=25)  # X-axis title
        ),
        yaxis=dict(
            tickfont=dict(size=20),
            title_font=dict(size=25)  # Y-axis title
        ),

        # ✅ Legend label font
        legend=dict(
            font=dict(size=20)
        )
    )

    return fig

def export_plotly_charts_to_pdf(figures,title,sub_title_1,sub_title_2,output_pdf="charts_export.pdf"):
    temp_images = []
    
    for fig in figures:
        # ✅ Clean the figure before export
        safe_fig = clean_plotly_figure_for_export(fig)

        # Save as temporary PNG image
        temp_name = f"temp_chart_{uuid.uuid4().hex}.png"
        pio.write_image(safe_fig, temp_name, format="png", width=1200, height=1600)
        temp_images.append(temp_name)

    # Create the PDF
    c = canvas.Canvas(output_pdf, pagesize=A4,topMargin=12,bottomMargin=6)
    for i,data in enumerate(zip(temp_images,title,sub_title_1,sub_title_2)):
        # Set page size
        c.setPageSize(A4)
        page_width, page_height = A4

        image_path = data[0]
        figure_title = data[1]
        sub_title_1 = data[2]
        sub_title_2 = data[3]

        # Load image dimensions
        img = Image.open(image_path)
        img_width_px, img_height_px = img.size

        if figure_title == "Plasticity Chart - Plasticity Index, PI (%) vs Liquid Limit, LL (%)":
            max_width = page_width - 0.5 * inch
            max_height = page_height - 2 * inch  # half of A4 height

            scale_w = min(max_width / img_width_px, max_height / img_height_px)
            draw_width = img_width_px * scale_w
            draw_height = img_height_px

            x_pos = (page_width - draw_width) / 2
            y_pos = (page_height - draw_height) / 2
        else:
            max_width = page_width - 0.5 * inch
            max_height = page_height - 2 * inch

            scale = min(max_width / img_width_px, max_height / img_height_px)
            draw_width = img_width_px * scale
            draw_height = img_height_px * scale
            
            x_pos = (page_width - draw_width) / 2
            y_pos = (page_height - draw_height) / 2

        title_left_margin = 1 * inch

        c.setFont("Helvetica-Bold", 14)
        c.drawString(title_left_margin, page_height - 50, f"Figure: {figure_title}")

        c.setFont("Helvetica", 12)
        c.drawString(title_left_margin, page_height - 70, f"{sub_title_1}")

        c.setFont("Helvetica", 12)
        c.drawString(title_left_margin, page_height - 90, f"{sub_title_2}")


        # Draw full-page chart (with margins)
        # Draw the image
        c.drawImage(
            image_path,
            x=x_pos,
            y=y_pos,
            width=draw_width,
            height=draw_height,
            preserveAspectRatio=True
        )
        c.showPage()
    c.save()

    # Clean up temp images
    for img in temp_images:
        os.remove(img)

    return output_pdf



def long_to_wide(df, index_col, test_type_col, value_cols):
    """
    Transforms a long-format DataFrame to wide-format where each test type's values are in separate columns.

    Parameters:
        df (pd.DataFrame): The input long DataFrame.
        index_col (str): The column to use as the unique row identifier (e.g., 'test_id').
        test_type_col (str): The column holding test type/category (e.g., 'test_type').
        value_cols (list): List of columns containing the test values (e.g., ['value_1', 'value_2']).

    Returns:
        pd.DataFrame: Wide-format DataFrame.
    """
    wide = df.pivot(index=index_col, columns=test_type_col, values=value_cols)
    # flatten the multiindex columns
    wide.columns = [f"{val}_{test}" for val, test in wide.columns]
    wide = wide.reset_index()
    return wide