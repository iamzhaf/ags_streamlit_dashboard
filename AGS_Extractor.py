import os,sys
import streamlit as st
import pandas as pd
import traceback
from streamlit_option_menu import option_menu
from st_pages import _get_pages_from_config
from utils import find_table_indices
from utils import get_valid_borehole_sheets, extract_borehole_number
from utils import get_contrator_config_reference_json_file as get_contract_config
import importlib
from ags_transformers.ryo_engineering import RyoEngineeringTransformer
from ags_transformers.ags_sg import AGSSgTransformer
import json
from utils import map_soil_layer_to_spt

borehole_html_table = None

def load_css(file_path):
    with open(file_path) as f:
        st.html(f"""<style>
                {f.read()}
                </style>""")

def wide_space_default():
    st.set_page_config(layout="wide",page_icon="assets/icon.png")
    

wide_space_default()
        

@st.cache_data
def create_valid_borehole_list_df(sheet_names):
    borehole_sheets_list_df = pd.DataFrame({"#":[*range(1,len(valid_borehole_sheets)+1)],"Borehole Data Sheetnames":[i for i in valid_sheets]})
    return borehole_sheets_list_df


@st.cache_data
def create_valid_ags_file_list_df(file):
    ags_file_list_df = pd.DataFrame({"#":[*range(1,len(file)+1)],"AGS File Name":[i for i in file]})
    return ags_file_list_df


@st.cache_data
def create_final_view_df(final_views_dfs):
    df = pd.concat([df for df in final_views_dfs.values()],axis=0,ignore_index=True)
    return df


@st.cache_data
def convert_for_download(df):
    return df.to_csv(index=False).encode("utf-8-sig")


@st.cache_data
def sort_df(df,sort_columns):
    if sort_columns:
        if "spt_n_grouping" in sort_columns:
            order = ["N≤10","10<N≤30","30<N≤50","N>50","UNKNOWN"]
            df["spt_n_grouping"] = pd.Categorical(df["spt_n_grouping"], categories=order, ordered=True)

        sorted_df = df.sort_values(by=sort_columns, ascending=True)
        return sorted_df
    else:
        return df

# Load external CSS
CSS_PATH = os.path.join("assets/styles.css")
load_css(CSS_PATH)

pages = _get_pages_from_config()

contractor_map = {
    "AGS(SG) Standard": ("ags_sg","AGSStandardTransformer"),
    "Ryo Engineering": ("ryo_engineering","RyoEngineeringTransformer"),
    "SI Contractor B": ("contractor_b",None),
    "SI Contractor C": ("contractor_c",None)
}

st.title("⚙️ AGS Excel File Data Extractor")

uploaded_files = st.file_uploader("Upload AGS Excel file (.xlsx)", type=["xlsx","xls"],key="ags-uploader",accept_multiple_files=True)

# Initialize session state to track uploaded filenames
if "ags_uploaded_files" not in st.session_state:
    st.session_state["ags_uploaded_files"] = []


# Convert to set for comparison
prev_filenames = set(st.session_state["ags_uploaded_files"])
current_filenames = set(f.name for f in uploaded_files) if uploaded_files else set()

# Detect new files or changes in upload
new_files_uploaded = current_filenames != prev_filenames

contractor_selected = st.selectbox("Choose the provider of AGS file", [*contractor_map.keys()], 
                                                                                          key="Contractor-Selection")

# Detect when user clears file upload
if uploaded_files is None and "ags_excel_filenames" in st.session_state and new_files_uploaded:
    st.session_state.pop("ags_excel_filenames")
    st.session_state.pop("validity", None)
    st.session_state.pop("validated_sheet_names", None)
    st.session_state.pop("validated_contractor_config",None)
    st.session_state.pop("ags_excel_filenames", None)
    st.session_state.pop("ags_sg_file", None)
    st.session_state.pop("final_merged_view_df")


# Detect file name change or first upload
if uploaded_files:

    if new_files_uploaded:
        st.session_state["ags_uploaded_files"] = list(current_filenames)  # update the session state

        if contractor_selected == "AGS(SG) Standard":
            st.session_state["ags_excel_filenames"] = {}
            # Process each file

            # Load AGS-SG config to get required sheets
            with open("ags_configs/ags_sg.json", "r") as f:
                ags_sg_config = json.load(f)
                config = ags_sg_config["sections"]

            for file in uploaded_files:
                # Read Excel
                excel = pd.ExcelFile(file)
                sheet_names = excel.sheet_names
                # Check if uploaded file is a AGS(SG) file
                # Get only sections where required is True
                required_sheets = [sheet for sheet, c in config.items() 
                                if c.get("required", "False") == "True"]
                all_sheets = [sheet for sheet, c in config.items() ]
                
                # Check if any sheet contains section in ags_sg
                ags_valid_sheets = any(any(pattern in sheet.strip().upper()[:4] for pattern in required_sheets) for sheet in sheet_names)
            
                sheet_to_processed =  [sheet for sheet in sheet_names if sheet.strip().upper()[:4] in all_sheets]

                if ags_valid_sheets:
                    st.session_state["ags_excel_filenames"][file.name] = sheet_to_processed
                    # st.success("✅ Uploaded File is a valid AGS(SG) File"

            if st.session_state["ags_excel_filenames"]:
                st.session_state["validity"] = True
                st.session_state["ags_sg_file"] = True
            else:
                st.warning("⚠️ No valid AGS file found.")
                st.session_state["validity"] = False
                st.session_state["ags_sg_file"] = False

        if contractor_selected != "AGS(SG) Standard":
            st.session_state["ags_excel_filenames"] = {}

            # Load contractor config
            contractor_config = get_contract_config(contractor_selected)
            section_config = contractor_config["sections"]["Project_Borehole_Information"]

            with st.spinner("Identifying valid borehole data sheets...for {contractor_selected}"):

                for file in uploaded_files:
                    valid_borehole_sheets = get_valid_borehole_sheets(
                        ags_excel_file=file,
                        all_sheet_names=sheet_names,
                        config=section_config,
                        extract_borehole_number_fn=extract_borehole_number,
                        verbose=True
                    )

                    # Store results
                    if valid_borehole_sheets:
                        st.session_state["ags_excel_filenames"][file.name] = valid_borehole_sheets
                        st.session_state["valid_files"].append(file)

            if st.session_state["ags_excel_filenames"]:
                st.session_state["validity"] = True
                st.session_state["validated_contractor_config"] = contractor_config
                st.session_state["validated_contractor"] = contractor_selected
            else:
                st.warning("⚠️ No valid AGS file found.")
                st.session_state["validity"] = False
                st.session_state["validated_contractor_config"] = None
                st.session_state["validated_contractor"] = None
                st.session_state["ags_sg_file"] = False



if "validity" in st.session_state and st.session_state["validity"] == False and not new_files_uploaded:
    st.warning("⚠️ No valid AGS file found.")


# AGS(SG) File
if ("validity" in st.session_state and st.session_state["validity"] == True):
    st.success("Successfully identified AGS(SG) files")
    st.markdown("<hr style='border: 2px solid black; margin: 20px 0;>", unsafe_allow_html=True)
    st.subheader("✅ Valid AGS File(s) to be Transformed")
    filenames = [k for k,_ in st.session_state["ags_excel_filenames"].items()]
    ags_file_list_df = create_valid_ags_file_list_df(filenames)

    # Convert to HTML with custom CSS class
    ags_sg_html_table = ags_file_list_df.to_html(index=False, classes="custom-table")

    # Add text to inform user to review the list of identified valid boreholes before proceeding with data extraction and transformation
    # st.write(f"Please review the below list of the identified valid boreholes data sheet(s) in upload AGS File ({uploaded_filename})")
    st.markdown(f"""<p class="black-text">
                    ⚠️ Please review the below list of the AGS File(s) to be transformed
                </p>""", unsafe_allow_html=True)

    # Render the HTML table
    st.markdown(ags_sg_html_table, unsafe_allow_html=True)


# Add "Run AGS Extraction" button for user to execute the AGS data transformation pipeline
if "validity" in st.session_state and st.session_state["validity"] == True:

    if "final_merged_view_df" not in st.session_state:
    
        # Only executes the AGS extraction when "Run AGS Extraction" button is clicked
        if st.button("Run AGS Extraction", key="run_extraction"):

            st.info("AGS Extraction Started. ⚠️ Do Not Refresh Browser")
            # st.write(f"Fetcing SPT Details: {st.session_state["validated_contractor_config"]["sections"]["SPT"]}")

            if "ags_sg_file" in st.session_state and st.session_state["ags_sg_file"] == True:

                # Load AGS-SG config to get required sheets
                with open("ags_configs/ags_sg.json", "r") as f:
                    ags_sg_config = json.load(f)

                st.write(st.session_state["ags_excel_filenames"])

                raw_ags_files = [k for k,_ in st.session_state["ags_excel_filenames"].items()]   

                # add a placeholder to store the processed final view dataframe
                final_views_dfs = {}

                # raw_ags_files contains just the filenames (strings)
                for file_name in raw_ags_files:

                    sheet_names = st.session_state["ags_excel_filenames"][file_name]

                    st.write(f"📄 Processing: {file_name}")
                    
                    # Find the matching UploadedFile object
                    file_obj = next((f for f in uploaded_files if f.name == file_name), None)

                    if file_obj is not None:

                        ags_sg_transformer = AGSSgTransformer(file_obj, sheet_names, ags_sg_config)

                        ags_sg_transformer.transform()

                        transformed_dfs = ags_sg_transformer.transformed_dfs

                        final_view_df = ags_sg_transformer.final_view_df

                        if final_view_df is not None:
                            final_views_dfs[file_name] = final_view_df

                # union all final_views_dfs
                final_merged_view_df = create_final_view_df(final_views_dfs)

                st.session_state["final_merged_view_df"] = final_merged_view_df


            else:
                

                contractor_slug,transformer_name = contractor_map[st.session_state["validated_contractor"]]

                # Dynamically import the module and class
                module = importlib.import_module(f"ags_transformers.{contractor_slug}")
                TransformerClass = getattr(module, transformer_name)

                st.session_state["final_view_dict"] = {}  # reset
                st.session_state["transformation_result"] = {} # reset

                for sheet_name in st.session_state["validated_sheet_names"][:]:
                    st.write(f"Processing: {sheet_name}")

                    try:
                        
                        transformer = TransformerClass(
                            file=uploaded_file,
                            sheet_name=sheet_name,
                            config=st.session_state["validated_contractor_config"]
                        )
                    
                        # Runs the AGS data transformation pipeline
                        transformer.transform()

                        st.write(transformer.iteration_errors)
                        st.write(transformer.debug_df)

                    except Exception as e:
                        st.error(f"Error processing for {sheet_name}: {e}")

                    if transformer.result and transformer.result["transformation_result"]:
                        #st.write(transformer.mapped_specimen_spt_final_transformed_df)
                        st.session_state["final_view_dict"][sheet_name] = transformer.result["final_view_df"]
                        st.session_state["transformation_result"][sheet_name] = "✅ Completed"
                    
                    if transformer.result and not transformer.result["transformation_result"]:
                        st.session_state["transformation_result"][sheet_name] = "⚠️ Failed"

                st.success("✅ All boreholes processed.")

                completion_status_df = pd.DataFrame({"Borehole": [k for k in st.session_state["transformation_result"].keys()],
                                    "Data Extraction Status": [v for _,v in st.session_state["transformation_result"].items()]
                                    })
                
                # Convert to HTML with custom CSS class
                completion_status_html_table = completion_status_df.to_html(index=False, classes="custom-table")

                # Render the HTML table
                st.markdown(completion_status_html_table, unsafe_allow_html=True)

                try:
                    output_data = pd.concat([df for _,df in st.session_state["final_view_dict"].items() if isinstance(df,pd.DataFrame)],axis=0)
                except:
                    output_data = None

                if isinstance(output_data,pd.DataFrame):
                    st.subheader("Output Data")
                    st.write(pd.concat([df for _,df in st.session_state["final_view_dict"].items() if isinstance(df,pd.DataFrame)],axis=0))

                # st.dataframe(combined_df, height=600)  # You can increase this height


if "final_merged_view_df" in st.session_state:
    if isinstance(st.session_state["final_merged_view_df"], pd.DataFrame) and not st.session_state["final_merged_view_df"].empty:
        with st.expander("✅ Final View is ready to be downloaded"):

            # Let user choose columns to sort by
            sort_columns = st.multiselect(
                "Select column(s) to sort by before downloading",
                options=["soil_layer","spt_n_grouping","bh_no"],
                default=["spt_n_grouping","soil_layer"]
            )

            # Sort and display the DataFrame
            if sort_columns:
                st.session_state["final_merged_view_df"] = sort_df(st.session_state["final_merged_view_df"],sort_columns)
                st.write("### Sorted Data")
                st.dataframe(st.session_state["final_merged_view_df"])


                csv = convert_for_download(st.session_state["final_merged_view_df"])

                st.download_button(
                        label="Download Processed AGS Data",
                        data=csv,
                        file_name="data.csv",
                    mime="text/csv",
                    icon=":material/download:",
                )

            else:

                st.warning("Please select at least one column to sort by.")