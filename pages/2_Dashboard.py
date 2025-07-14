import streamlit as st
import os,sys
import pyproj
import pandas as pd
import datetime as dt
from plots import plot_plasticity_index_plotly
from plots import plot_spt_n_vs_sample_depth_plotly
from plots import plot_borehole_mapping
from plots import plot_plasticity_chart_plotly
from plots import plot_moisture_content_pl_ll_range_plotly
from plots import plot_partical_density_plotly
from plots import plot_undrained_shear_strength_plotly
from plots import plot_undrained_shear_strength_sptn_plotly
from plots import plot_bulk_density_plotly
from utils import export_plotly_charts_to_pdf
import re


st.title("Borehole & Geotechnical Analysis Dashboard")

def load_css(file_path):
    with open(file_path) as f:
        st.html(f"""<style>
                {f.read()}
                </style>""")

def wide_space_default():
    st.set_page_config(layout="wide")

# Set wide as the default layout
# wide_space_default()

st.title("📈 Dashboard")
    

# Load external CSS
CSS_PATH = os.path.join("assets/styles.css")
load_css(CSS_PATH)


# Create 2 cols dashboard
col_1, col_2 = st.columns([1,3],gap="large")

# =====================================================================================
#                         Column 1 (Left Sidebar for inputs and filters)
# =====================================================================================

col_1.subheader("Data Upload")

dashboard_uploaded_file = col_1.file_uploader("Upload Borehole Data For Analysis (.xlsx or .csv)", type=["xlsx","csv"],key="ags-uploader")

col_1.subheader("Filter Selection")

chart_options = {
    "Show Chart 1": "Plasticity Index Vs Depth",
    "Show Chart 2": "SPT-N Vs Depth",
    "Show Chart 3": "Borehole Mapping",
    "Show Chart 4": "Plasticity Chart",
    "Show Chart 5": "MC PL-LL",
    "Show Chart 6": "Specific Gravity vs Depth",
    "Show Chart 7": "Bulk Density vs Depth",
    "Show Chart 8": "Undrained Shear Strength vs Depth",
    "Show Chart 9": "SPT-N vs Undrained Shear Strength"
}


# Multiselect widget
selected_charts = col_1.multiselect("Choose charts to display",options=[v for k,v in chart_options.items()], default=[v for k,v in chart_options.items()])


# =====================================================================================
#                            Column 2 (Main Chart Area)
# =====================================================================================

# st.write(st.session_state)


@st.cache_data
def extract_relevant_cols(uploaded_file,ext):
    df = pd.read_csv(uploaded_file)
    # df = df[["project","client","easting_m", "northing_m", "depth_m", "soil_type","bh_no",
    #          "drilling_depth_m","g_elevation_m",
    #          "spt_n",
    #          "spt_n_grouping",
    #          "soil_layer",
    #          "spt_depth_to_top_of_test",
    #          "bulk_density_mg_m3",
    #          "partical_density",
    #          "water_content_%",
    #          "atterberg_limit_%_ll_%",
    #          "atterberg_limit_%_pl_%",
    #          "uu",
    #          "sample_depth",
    #          "sample_ref_no"
    #          ]]
    df = create_lat_long(df)
    return df



def create_lat_long(df):
    # Convert Easting/Northing to Lat/Lon
    svy21 = pyproj.Transformer.from_crs("EPSG:3414", "EPSG:4326", always_xy=True)
    df["Longitude"], df["Latitude"] = svy21.transform(df["easting_m"].values, df["northing_m"].values)
    return df


# Create today's date
if "dashboard_date_today" not in st.session_state:
    date_today = dt.datetime.today().date()
    st.session_state["dashboard_date_today"] = date_today.strftime("%Y%m%d")

# Detect file name change or first upload
if dashboard_uploaded_file:

    # Check if we already have a file and if it's the same
    prev_file_dashboard = st.session_state.get("dashboard_file") # if dashboard_file key is none existent, then None is return
    new_file_uploaded = (
        prev_file_dashboard is None or dashboard_uploaded_file.name != prev_file_dashboard.name
    )

    if new_file_uploaded:

        st.session_state["dashboard_file"] = dashboard_uploaded_file

        file_name = dashboard_uploaded_file.name.lower()

        try:

            if file_name.endswith(".csv") or file_name.endswith(".xlsx"):
                df = extract_relevant_cols(dashboard_uploaded_file, ".csv")
                st.session_state["df"] = df  

            else:
                col_2.error("Unsupported file format. Please upload a CSV or Excel file.")
                df = None

            col_2.write(df)

            if df is not None:
                st.session_state["project_title"] = df["project"].unique()[0]
                st.session_state["total_borehole"] = df["bh_no"].nunique()
                st.session_state["client_name"] = df["client"].unique()[0]


            col_2.success(f"{dashboard_uploaded_file.name} loaded successfully ✅")

        except Exception as e:
            col_2.error(f"❌ Failed to load file {dashboard_uploaded_file.name}")
            df = None

    else:
         
         df = st.session_state.get("df")

# col_2.write(st.session_state)

if "project_title" in st.session_state:
    proj_id = st.session_state["project_title"]    
else:
    proj_id = None

if "client_name" in st.session_state:
    client_name = st.session_state["client_name"]    
else:
    client_name = None

if "total_borehole" in st.session_state:
    total_borehole = st.session_state["total_borehole"]    
else:
    total_borehole = 0


with col_2:

    shared_card_style = """
        background-color: #ffffff;
        border-radius: 12px;
        padding: 20px;
        height: 180px;
        margin-bottom:20px;
        box-shadow: 2px 2px 10px rgba(0,0,0,0.1);
        display: flex;
        flex-direction: column;
        justify-content: flex-start;
    """

    title_style = "margin: 0 0 8px 0; font-weight: bold; color: #555; font-size: 25px;"
    value_style_1 = "margin: 0; font-size: 26px; color: #C70039 !important;"
    value_style_2 = "margin: 0; font-size: 45px; color: #C70039 !important;"  # larger text for borehole count

    col_2.markdown(
        f"""
        <div style="{shared_card_style}">
            <p style="{title_style}">Project Name:</p>
            <h2 style="{value_style_1}">{proj_id}</h1>
        </div>
        """,
        unsafe_allow_html=True
    )


    subcol1, subcol2 = st.columns([2,1])

    subcol1.markdown(
        f"""
        <div style="{shared_card_style}">
            <p style="{title_style}">Client:</p>
            <h2 style="{value_style_1}">{client_name}</h1>
        </div>
        """,
        unsafe_allow_html=True
    )

    subcol2.markdown(
        f"""
        <div style="{shared_card_style}">
            <p style="{title_style}">Total Boreholes:</p>
            <h2 style="{value_style_2}">{total_borehole}</h1>
        </div>
        """,
        unsafe_allow_html=True
    )


if "df" in locals():  # make sure df exists
    if "Borehole Mapping" in selected_charts:
        col_2.subheader("Borehole Location Map (Black Circles = Borehole Point)" )
        try:
            fig = plot_borehole_mapping(df, lat='Latitude', lon="Longitude",title="")
            col_2.plotly_chart(fig, use_container_width=False)
        except Exception as e:
            col_2.error(f"Error plotting Borehole Location Map: {e}")


if "df" in locals(): # make sure df exists

    # Step 1: Extract unique filter options
    soil_layer_options = df['soil_layer'].dropna().unique().tolist()
    spt_group_options = df['spt_n_grouping'].dropna().unique().tolist()

    # Step 2: Create dropdowns
    selected_soils = col_1.multiselect("Choose Soil Type", options=soil_layer_options, default=soil_layer_options)
    selected_spt_groups = col_1.multiselect("Choose SPT-N Group", options=spt_group_options, default=spt_group_options)

    # Step 3: Initialize filtered DataFrame
    filtered_df = df.copy()

    if set(selected_soils) != set(soil_layer_options):
        pattern = "|".join([re.escape(s) for s in selected_soils])
        filtered_df = filtered_df[filtered_df["soil_layer"].fillna("").str.contains(pattern, regex=True)]

    if set(selected_spt_groups) != set(spt_group_options):
        pattern = "|".join([re.escape(s) for s in selected_spt_groups])
        filtered_df = filtered_df[filtered_df["spt_n_grouping"].fillna("").str.contains(pattern, regex=True)]

    # Step 5: Prepare subheader text
    soil_text = "All Soil Types" if set(selected_soils) == set(soil_layer_options) else "; ".join(selected_soils)
    spt_text = "All SPT-N Groups" if set(selected_spt_groups) == set(spt_group_options) else "; ".join(selected_spt_groups)

    sub_header_text_soil_layer_selection = f"Soil Layer = {soil_text}"
    sub_header_text_spt_n_selection = f"SPT-N Group = {spt_text}"

# create a placeholder to store charts 
figures_list_placehoder = []
figures_title_placeholders = []
figures_subheader_soil_placeholders = []
figures_subheader_spt_n_placeholders = []

export_placeholder = col_1.empty()  # Create a placeholder at the top

if "df" in locals():  # make sure df exists

    if "Plasticity Index Vs Depth" in selected_charts:
        title = "Plasticity Index vs Depth"
        col_2.subheader(title)
        col_2.markdown(f"###### {sub_header_text_soil_layer_selection}")
        col_2.markdown(f"###### {sub_header_text_spt_n_selection}")
        # Filter based on soil type 
        try:
            fig = plot_plasticity_index_plotly(filtered_df, ll_col='atterberg_limit_%_ll_%', pl_col='atterberg_limit_%_pl_%', depth_col='sample_depth')
            
            col_2.plotly_chart(fig, use_container_width=False)

            figures_list_placehoder.append(fig)
            figures_title_placeholders.append(title)
            figures_subheader_soil_placeholders.append(sub_header_text_soil_layer_selection)
            figures_subheader_spt_n_placeholders.append(sub_header_text_spt_n_selection)

        except Exception as e:

            col_2.error(f"Error plotting Plasticity Index: {e}")


if "df" in locals():  # make sure df exists

    if "Plasticity Chart" in selected_charts:
        title = "Plasticity Chart - Plasticity Index, PI (%) vs Liquid Limit, LL (%)"
        col_2.subheader(title)
        col_2.markdown(f"###### {sub_header_text_soil_layer_selection}")
        col_2.markdown(f"###### {sub_header_text_spt_n_selection}")
        # Filter based on soil type 
        try:
            fig = plot_plasticity_chart_plotly(filtered_df, ll_col='atterberg_limit_%_ll_%', pl_col='atterberg_limit_%_pl_%', depth_col='sample_depth')
            
            col_2.plotly_chart(fig, use_container_width=False)

            figures_list_placehoder.append(fig)
            figures_title_placeholders.append(title)
            figures_subheader_soil_placeholders.append(sub_header_text_soil_layer_selection)
            figures_subheader_spt_n_placeholders.append(sub_header_text_spt_n_selection)

        except Exception as e:

            col_2.error(f"Error plotting Plasticity Chart: {e}")

if "df" in locals():  # make sure df exists

    if "SPT-N Vs Depth" in selected_charts:
        title = "SPT-N (Capped at 100) vs Depth"
        col_2.subheader(title)
        col_2.markdown(f"###### {sub_header_text_soil_layer_selection}")
        col_2.markdown(f"###### {sub_header_text_spt_n_selection}")
        try:
            fig = plot_spt_n_vs_sample_depth_plotly(filtered_df,spt_n="spt_n",depth_col='spt_depth_to_top_of_test')
            col_2.plotly_chart(fig, use_container_width=False)

            figures_list_placehoder.append(fig)
            figures_title_placeholders.append(title)
            figures_subheader_soil_placeholders.append(sub_header_text_soil_layer_selection)
            figures_subheader_spt_n_placeholders.append(sub_header_text_spt_n_selection)

        except Exception as e:
            col_2.error(f"Error plotting SPT-N vs Depth: {e}")


if "df" in locals():  # make sure df exists

    if "MC PL-LL" in selected_charts:
        
        borehole_options = filtered_df['bh_no'].dropna().unique().tolist()

        filtered_df_mc = filtered_df.copy()

        title = "Moisture Content PL-LL Range vs Depth"
        col_2.subheader(title)
        # Add a placeholder 
        borehole_select_placeholder = col_2.empty()
        # Add the dropdown multiselect
        selected_borehole_ids = borehole_select_placeholder.multiselect(label="Choose Borehole IDs",options=borehole_options,default=borehole_options)
        col_2.markdown(f"###### {sub_header_text_soil_layer_selection}")
        col_2.markdown(f"###### {sub_header_text_spt_n_selection}")

        if set(selected_borehole_ids) != set(borehole_options):
            pattern = "|".join([re.escape(s) for s in selected_borehole_ids])
            filtered_df_mc = filtered_df_mc[filtered_df_mc["bh_no"].fillna("").str.contains(pattern, regex=True)]
        try:
            fig = plot_moisture_content_pl_ll_range_plotly(filtered_df_mc,mc_col="water_content_%",ll_col="atterberg_limit_%_ll_%"
                                                           ,pl_col="atterberg_limit_%_pl_%",
                                                           depth_col='sample_depth')
            
            col_2.plotly_chart(fig, use_container_width=False)

            figures_list_placehoder.append(fig)
            figures_title_placeholders.append(title)
            figures_subheader_soil_placeholders.append(sub_header_text_soil_layer_selection)
            figures_subheader_spt_n_placeholders.append(sub_header_text_spt_n_selection)

        except Exception as e:
            col_2.error(f"Error plotting moisture content vs Depth: {e}")


if "df" in locals():  # make sure df exists

    if "Specific Gravity vs Depth" in selected_charts:
        title = "Specific Gravity vs Depth"
        col_2.subheader("Specific Gravity vs Depth")
        col_2.markdown(f"###### {sub_header_text_soil_layer_selection}")
        col_2.markdown(f"###### {sub_header_text_spt_n_selection}")
        try:
            fig = plot_partical_density_plotly(filtered_df,specific_gravity="partical_density",depth_col='sample_depth')
            
            col_2.plotly_chart(fig, use_container_width=False)

            figures_list_placehoder.append(fig)
            figures_title_placeholders.append(title)
            figures_subheader_soil_placeholders.append(sub_header_text_soil_layer_selection)
            figures_subheader_spt_n_placeholders.append(sub_header_text_spt_n_selection)
        except Exception as e:
            col_2.error(f"Error plotting Specific Gravity vs Depth: {e}")


if "df" in locals():  # make sure df exists

    if "Bulk Density vs Depth" in selected_charts:
        title = "Bulk Density vs Depth"
        col_2.subheader("Bulk Density vs Depth")
        col_2.markdown(f"###### {sub_header_text_soil_layer_selection}")
        col_2.markdown(f"###### {sub_header_text_spt_n_selection}")
        try:
            fig = plot_bulk_density_plotly(filtered_df,bulk_density='bulk_density_mg_m3',depth_col='sample_depth')
            
            col_2.plotly_chart(fig, use_container_width=False)

            figures_list_placehoder.append(fig)
            figures_title_placeholders.append(title)
            figures_subheader_soil_placeholders.append(sub_header_text_soil_layer_selection)
            figures_subheader_spt_n_placeholders.append(sub_header_text_spt_n_selection)
        except Exception as e:
            col_2.error(f"Error plotting Specific Gravity vs Depth: {e}")


if "df" in locals():  # make sure df exists

    if "Undrained Shear Strength vs Depth" in selected_charts:
        title = "Undrained Shear Strength vs Depth"
        col_2.subheader("Undrained Shear Strength vs Depth")
        col_2.markdown(f"###### {sub_header_text_soil_layer_selection}")
        col_2.markdown(f"###### {sub_header_text_spt_n_selection}")
        try:
            fig,empty_data = plot_undrained_shear_strength_plotly(filtered_df,uu_col="uu",depth_col='sample_depth')
            #col_2.write(empty_data)

            if not empty_data:

                col_2.plotly_chart(fig, use_container_width=False)

                figures_list_placehoder.append(fig)
                figures_title_placeholders.append(title)
                figures_subheader_soil_placeholders.append(sub_header_text_soil_layer_selection)
                figures_subheader_spt_n_placeholders.append(sub_header_text_spt_n_selection)
            else:
                col_2.error(f"No data to plot.")
        except Exception as e:
            col_2.error(f"Error plotting Undrained Shear Strength vs Depth: {e}")


if "df" in locals():  # make sure df exists

    if "SPT-N vs Undrained Shear Strength" in selected_charts:
        title = "Undrained Shear Strength vs SPT-N"
        col_2.subheader("Undrained Shear Strength vs SPT-N")
        col_2.markdown(f"###### {sub_header_text_soil_layer_selection}")
        col_2.markdown(f"###### {sub_header_text_spt_n_selection}")
        try:
            fig,empty_data = plot_undrained_shear_strength_sptn_plotly(filtered_df,uu_col="uu",spt_n='spt_n')
            #col_2.write(empty_data)

            if not empty_data:

                col_2.plotly_chart(fig, use_container_width=False)

                figures_list_placehoder.append(fig)
                figures_title_placeholders.append(title)
                figures_subheader_soil_placeholders.append(sub_header_text_soil_layer_selection)
                figures_subheader_spt_n_placeholders.append(sub_header_text_spt_n_selection)
            else:
                col_2.error(f"No data to plot.")
        except Exception as e:
            col_2.error(f"Error plotting Undrained Shear Strength vs SPT-N: {e}")


# Export Button
if figures_list_placehoder:
    with export_placeholder:  # Render the button in the top placeholder
        try:
            if st.button("Download All Charts as PDF"):
                with st.spinner("Exporting charts... please wait ⏳"):
                    pdf_path = export_plotly_charts_to_pdf(figures_list_placehoder,
                                                           figures_title_placeholders,
                                                           figures_subheader_soil_placeholders,
                                                           figures_subheader_spt_n_placeholders)

                st.success("✅ Export successful! Your PDF is ready to download.")

                if len(selected_soils) == 1:
                    soil_name_term = selected_soils[0].title()
                elif len(selected_soils) >0:
                    soil_name_term = "Multiple_Soils_Types"

                with open(pdf_path, "rb") as f:
                    st.download_button(
                        label="Click to Download PDF",
                        data=f,
                        file_name=f"Site_Investigation_Charts_{soil_name_term}_{st.session_state["dashboard_date_today"]}.pdf",
                        mime="application/pdf"
                    )
        except Exception as e:
            st.error(f"❌ Export failed: {e}")
