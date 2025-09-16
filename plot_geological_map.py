import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from folium.raster_layers import ImageOverlay
from folium.plugins import MarkerCluster
from PIL import Image
import socket
import streamlit as st

# Load Geological Map

def display_geological_map_with_boreholes(
    boreholes_coor_df,
    bounds=[[1.495116146,103.578843117], [1.114003920, 104.113838259]],
    map_center=[1.35, 103.82],
    zoom_start=17,
    map_width=900,
    map_height=800,
    checkbox_default=False
):
    # Remove duplicates 
    boreholes = boreholes_coor_df.drop_duplicates().reset_index(drop=True)

    # Remove null values
    boreholes = boreholes.dropna(subset=["lat","lon"],how="all")
    boreholes = boreholes.to_dict(orient='records')

    # Get local IP address for tile serving
    hostname = socket.gethostname()
    ip_add = socket.gethostbyname(hostname)
    url = "http://" + ip_add + ":8000"


    # find the centeroidz
    lats = [float(bh["lat"]) for bh in boreholes]
    lons = [float(bh["lon"]) for bh in boreholes]
    central_lat = sum(lats) / len(lats)
    central_lon = sum(lons) / len(lons)
    map_center = [central_lat,central_lon]
    
    m = folium.Map(location=map_center, zoom_start=zoom_start, tiles="OpenStreetMap")
    
    tiles_config = ("{z}","{x}","{y}")
    geology_tile_url = f"{url}/{tiles_config[0]}/{tiles_config[1]}/{tiles_config[2]}.png"
    
    geology_tiles = folium.TileLayer(
        tiles=geology_tile_url,
        attr="Singapore Geological Map (2021) (Source: BCA, and British Geological Survey)",
        name="Geological Map (Tiles)",
        overlay=True,
        control=True,
        opacity=0.8,
        max_zoom=20,
        min_zoom=6
    )
    
    borehole_group = folium.FeatureGroup(name="Boreholes", control=True)
    borehole_labels = folium.FeatureGroup(name="Boreholes_Labels", control=True)
    

    for bh in boreholes:
        folium.CircleMarker(
            location=[bh["lat"], bh["lon"]],
            radius=6,
            color='black',
            fill=True,
            fill_color='black',
            fill_opacity=1.0,
            popup=f"{bh['bh_no']}<br>Lat: {bh['lat']}<br>Lon: {bh['lon']}"
        ).add_to(borehole_group)
    
        # Label marker using DivIcon
        folium.Marker(
            location=[bh["lat"]-0.000005, bh["lon"]+0.000005],
            icon=folium.DivIcon(
                icon_size=(70, 36),
                icon_anchor=(0, 0),
                html=f'<div style="font-size: 12px; font-weight: bold; color: black; background-color: rgba(128,128,128,0.3); padding: 2px 5px; border-radius: 4px; white-space: nowrap;">{bh["bh_no"]}</div>'
            )
        ).add_to(borehole_labels)
    
    show_geology = st.checkbox("Show Geo Overlay", value=checkbox_default)
    if show_geology:
        geology_tiles.add_to(m)
    
    borehole_group.add_to(m)
    show_labes = st.checkbox("Show Borehole Labels", value=True)
    if show_labes:
        borehole_labels.add_to(m)
    folium.LayerControl().add_to(m)
    
    st.write(ip_add)
    st_folium(m, width=map_width, height=map_height)

