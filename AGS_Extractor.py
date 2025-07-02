import os,sys
import streamlit as st
import pandas as pd
import traceback
from streamlit_option_menu import option_menu
from st_pages import _get_pages_from_config
from utils import RYO_AGS_CONFIG
from utils import get_valid_borehole_sheets, extract_borehole_number
from utils import get_contrator_config_reference_json_file as get_contract_config
import importlib
from ags_transformers.ryo_engineering import RyoEngineeringTransformer

borehole_html_table = None

def load_css(file_path):
    with open(file_path) as f:
        st.html(f"""<style>
                {f.read()}
                </style>""")

def wide_space_default():
    st.set_page_config(layout="wide")

wide_space_default()
        

@st.cache_data
def create_valid_borehole_list_df(sheet_names):
    borehole_sheets_list_df = pd.DataFrame({"#":[*range(1,len(valid_sheets)+1)],"Borehole Data Sheetnames":[i for i in valid_sheets]})
    return borehole_sheets_list_df

# Load external CSS
CSS_PATH = os.path.join("assets/styles.css")
load_css(CSS_PATH)

pages = _get_pages_from_config()

contractor_map = {
    "Ryo Engineering": ("ryo_engineering","RyoEngineeringTransformer"),
    "SI Contractor B": ("contractor_b",None),
    "SI Contractor C": ("contractor_c",None)
}

st.title("⚙️ AGS Excel File Data Extractor")

uploaded_file = st.file_uploader("Upload AGS Excel file (.xlsx)", type=["xlsx"],key="ags-uploader")

contractor_selected = st.selectbox("Choose the SI Contractor who provided the AGS file", [*contractor_map.keys()], 
                                                                                          key="Contractor-Selection")

# Detect when user clears file upload
if uploaded_file is None and "ags_excel" in st.session_state:
    st.session_state.pop("ags_excel")
    st.session_state.pop("validity", None)
    st.session_state.pop("validated_sheet_names", None)
    st.session_state.pop("validated_contractor_config",None)


# Detect file name change or first upload
if uploaded_file:
    # Check if we already have a file and if it's the same
    prev_file = st.session_state.get("ags_excel")
    new_file_uploaded = (
        prev_file is None or uploaded_file.name != prev_file.name
    )

    if new_file_uploaded:
        st.session_state["ags_excel"] = uploaded_file

        # Read Excel
        excel = pd.ExcelFile(uploaded_file)
        sheet_names = excel.sheet_names

        # Load contractor config
        contractor_config = get_contract_config(contractor_selected)
        section_config = contractor_config["sections"]["Project_Borehole_Information"]

        with st.spinner("Identifying valid borehole data sheets..."):
            valid_sheets = get_valid_borehole_sheets(
                ags_excel_file=uploaded_file,
                all_sheet_names=sheet_names,
                config=section_config,
                extract_borehole_number_fn=extract_borehole_number,
                verbose=True
            )

        # Store results
        st.session_state["validity"] = bool(valid_sheets)
        st.session_state["validated_sheet_names"] = valid_sheets if valid_sheets else None
        st.session_state["validated_contractor_config"] = contractor_config
        st.session_state["validated_contractor"] = contractor_selected

        if not valid_sheets:
            st.warning("⚠️ No borehole records found in the AGS file.")


if "validity" in st.session_state and st.session_state["validity"] == False and not new_file_uploaded:
    st.warning("⚠️ No borehole records found in the AGS file.")


if "validity" in st.session_state and st.session_state["validity"] == True:
    st.success("Successfully identified borehole data sheets!")
    st.markdown("<hr style='border: 2px solid black; margin: 20px 0;>", unsafe_allow_html=True)
    st.subheader("✅ Valid Boreholes Records to be Transformed")
    borehole_sheets_list_df = create_valid_borehole_list_df(st.session_state["validated_sheet_names"])

    # Convert to HTML with custom CSS class
    borehole_html_table = borehole_sheets_list_df.to_html(index=False, classes="custom-table")

    # Add text to inform user to review the list of identified valid boreholes before proceeding with data extraction and transformation
    # st.write(f"Please review the below list of the identified valid boreholes data sheet(s) in upload AGS File ({uploaded_filename})")
    st.markdown(f"""<p class="black-text">
                    ⚠️ Please review the below list of the identified valid boreholes data sheet(s) in the uploaded AGS File ({st.session_state["ags_excel"].name})
                </p>""", unsafe_allow_html=True)

    # Render the HTML table
    st.markdown(borehole_html_table, unsafe_allow_html=True)


# Add "Run AGS Extraction" button for user to execute the AGS data transformation pipeline
if "validity" in st.session_state and st.session_state["validity"] == True:
    # Only executes the AGS extraction when "Run AGS Extraction" button is clicked
    if st.button("Run AGS Extraction", key="run_extraction"):

        st.info("AGS Extraction Started. ⚠️ Do Not Refresh Browser")
        # st.write(f"Fetcing SPT Details: {st.session_state["validated_contractor_config"]["sections"]["SPT"]}")

        contractor_slug,transformer_name = contractor_map[st.session_state["validated_contractor"]]

        # Dynamically import the module and class
        module = importlib.import_module(f"ags_transformers.{contractor_slug}")
        TransformerClass = getattr(module, transformer_name)

        # Instantiate and run
        # transformer = TransformerClass(file=uploaded_file, sheet_name=st.session_state["validated_sheet_names"][0], config=st.session_state["validated_contractor_config"])
        # transformer.transform()
        # # st.write(transformer.soil_layer_df_transformed)
        # # st.write(transformer.mapped_spt_soil_df_transformed)
        # # st.write(transformer.lab_test_df_transformed)
        # # st.write(transformer.triaxial_test_df_transformed)
        # # st.write(transformer.combined_lab_triaxial_test_transformed_df)
        # # st.write(transformer.mapped_specimen_spt_final_transformed_df)
        # if transformer.result and transformer.result["transformation_result"]:
        #     st.write(transformer.result["final_view_df"])

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