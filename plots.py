import matplotlib.pyplot as plt
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import base64
import numpy as np

def get_base64_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")

def plot_plasticity_index_plotly(df, ll_col='ll', pl_col='pl', depth_col='depth', title="Plasticity Index vs Depth"):
    """
    Returns a modern-looking Plotly scatter plot for Plasticity Index vs Depth.
    
    Parameters:
        df (pd.DataFrame): DataFrame containing LL, PL, and Depth columns.
        ll_col (str): Column name for Liquid Limit.
        pl_col (str): Column name for Plastic Limit.
        depth_col (str): Column name for Depth (mBGL).
        title (str): Plot title.
    
    Returns:
        fig (plotly.graph_objs._figure.Figure): Plotly figure object.
    """
    df = df.copy()
    df.dropna(subset=[ll_col, pl_col, depth_col], inplace=True)
    df['pi'] = df[ll_col] - df[pl_col]

    if df["pi"].min() < 0:
        pi_range = [df["pi"].min()-10,df["pi"].max()+10]
    else:
        pi_range = [0,df["pi"].max()+10]

    fig = px.scatter(
        df,
        x='pi',
        y=depth_col,
        hover_data=['bh_no', 'sample_ref_no',"atterberg_limit_%_ll_%","atterberg_limit_%_pl_%"],
        labels={
            "soil_layer" : "Soil Type",
            "spt_n_grouping" : "SPT-N Value (Blow Count)",
            'pi': 'Plasticity Index (%)',
            "atterberg_limit_%_ll_%":"LL",
            "atterberg_limit_%_pl_%":"PL",
            depth_col: 'Sample Depth (mBGL)',
            'bh_no':"Borehole Number",
            "sample_ref_no":"Sample Ref. No.",
        },
        color_discrete_sequence=px.colors.qualitative.Set1,
        color = "soil_layer",
        symbol="spt_n_grouping"
    )

    fig.update_traces(marker=dict(size=10, opacity=0.9, line=dict(width=1, color='DarkSlateGrey')))
    fig.update_yaxes(
                # autorange='reversed',
                range=[df[depth_col].max()+1,0-0.5]
                     ) 
    fig.update_xaxes(
                range=pi_range
                     ) 
    fig.update_layout(
        legend_title = dict(
                            text="Soil Layer & SPT-N Grouping",
                            font=dict(size=16)
                        ),
        legend = dict(
            font=dict(size=14),
            orientation="h",         # horizontal legend
            yanchor="bottom",
            y=1.02,                  # slightly above the plot
            xanchor="left",
            x=0                 # centered horizontally
    ),
    shapes=[
        dict(
            type='line',
            xref='x',
            yref='y',
            x0=0,
            x1=0,
            y0=0-0.5,
            y1=df[depth_col].max()+1,
            line=dict(color='black', width=1, dash='solid')
        ),
        dict(
            type='line',
            xref='x',
            yref='y',
            x0=pi_range[0],
            x1=pi_range[1],
            y0=df[depth_col].max()+1,
            y1=df[depth_col].max()+1,
            line=dict(color='black', width=1, dash='solid')
        )
    ],
    xaxis=dict(
        title="Plasticity Index (%)",
        title_font=dict(size=18, family="Arial", color="black"),  # bold & bigger
        tickfont=dict(size=14),
        dtick=10,
        showgrid=True,
        gridcolor="black",
        minor=dict(
                    tick0=0,
                    dtick=2,         # Minor grid every 2 units
                    showgrid=True,   # ✅ Turn on minor gridlines
                    gridcolor="lightgray",
                    gridwidth=0.5
                )
    ),
    yaxis=dict(
        title="Sample Depth (mBGL)",
        title_font=dict(size=18, family="Arial", color="black"),
        tickfont=dict(size=14),
        showgrid=True,
        dtick=2,
        gridcolor="black",
        zeroline=True,
        zerolinewidth=3,
        zerolinecolor="black",
        minor=dict(
                    tick0=0,
                    dtick=1,         # Minor grid every 1 units
                    showgrid=True,   # ✅ Turn on minor gridlines
                    gridcolor="lightgray",
                    gridwidth=0.5
                )
    ),
        plot_bgcolor="#f9f9f9",
        paper_bgcolor="#ffffff",
        font=dict(size=14),
        height=900,
        margin=dict(l=80, r=60, t=40, b=80),  # Increase these as needed
    )

    return fig


def plot_undrained_shear_strength_plotly(df, uu_col='uu', depth_col='depth', title="Undrained Shear Strength vs Depth"):
    """
    Returns a modern-looking Plotly scatter plot for Undrained Shear Strength vs Depth.
    
    Parameters:
        df (pd.DataFrame): DataFrame containing LL, PL, and Depth columns.
        uu_col (str): Column name for Undrained Shear Strength.
        depth_col (str): Column name for Depth (mBGL).
        title (str): Plot title.
    
    Returns:
        fig (plotly.graph_objs._figure.Figure): Plotly figure object.
    """
    empty_data = False

    df = df.copy()
    df = df.dropna(subset=[uu_col, depth_col])
    
    if not len(df) >0:
        empty_data = True

    fig = px.scatter(
        df,
        x=uu_col,
        y=depth_col,
        hover_data=['bh_no', 'sample_ref_no','uu'],
        labels={
            "soil_layer" : "Soil Type",
            "spt_n_grouping" : "SPT-N Value (Blow Count)",
            uu_col: 'Undrained Shear Strength (kPa)',
            depth_col: 'Sample Depth (mBGL)',
            'bh_no':"Borehole Number",
            "sample_ref_no":"Sample Ref. No.",
        },
        color_discrete_sequence=px.colors.qualitative.Set1,
        color = "soil_layer",
        symbol="spt_n_grouping"
    )

    fig.update_traces(marker=dict(size=10, opacity=0.9, line=dict(width=1, color='DarkSlateGrey')))
    fig.update_yaxes(
                # autorange='reversed',
                range=[df[depth_col].max()+1,0-0.5]
                     ) 
    fig.update_xaxes(
                range=[0,df["uu"].max()+20]
                     ) 
    fig.update_layout(
    legend_title = dict(
                        text="Soil Layer & SPT-N Grouping",
                        font=dict(size=16)
                    ),
    legend = dict(
        font=dict(size=14),
        orientation="h",         # horizontal legend
        yanchor="bottom",
        y=1.02,                  # slightly above the plot
        xanchor="left",
        x=0                 # centered horizontally
    ),
        shapes=[
        dict(
            type='line',
            xref='x',
            yref='y',
            x0=0,
            x1=0,
            y0=0-0.5,
            y1=df[depth_col].max()+1,
            line=dict(color='black', width=1, dash='solid')
        ),
        dict(
            type='line',
            xref='x',
            yref='y',
            x0=0,
            x1=df["uu"].max()+20,
            y0=df[depth_col].max()+1,
            y1=df[depth_col].max()+1,
            line=dict(color='black', width=1, dash='solid')
        )
    ],
    xaxis=dict(
        title="Undrained Shear Strength (kPa)",
        title_font=dict(size=18, family="Arial", color="black"),  # bold & bigger
        tickfont=dict(size=14),
        dtick=10,
        showgrid=True,
        gridcolor="black",
        minor=dict(
                    tick0=0,
                    dtick=2,         # Minor grid every 2 units
                    showgrid=True,   # ✅ Turn on minor gridlines
                    gridcolor="lightgray",
                    gridwidth=0.5
                )
    ),
    yaxis=dict(
        title="Sample Depth (mBGL)",
        title_font=dict(size=18, family="Arial", color="black"),
        tickfont=dict(size=14),
        showgrid=True,
        dtick=2,
        gridcolor="black",
        zeroline=True,
        zerolinewidth=3,
        zerolinecolor="black",
        minor=dict(
                    tick0=0,
                    dtick=1,         # Minor grid every 1 units
                    showgrid=True,   # ✅ Turn on minor gridlines
                    gridcolor="lightgray",
                    gridwidth=0.5
                )
    ),
        plot_bgcolor="#f9f9f9",
        paper_bgcolor="#ffffff",
        font=dict(size=14),
        height=900,
        margin=dict(l=80, r=60, t=40, b=80),  # Increase these as needed
    )

    return fig,empty_data



def plot_undrained_shear_strength_sptn_plotly(df, uu_col='uu', spt_n='spt_n', title="SPT-N vs Undrained Shear Strength"):
    """
    Returns a modern-looking Plotly scatter plot for SPT-N vs Undrained Shear Strength.
    
    Parameters:
        df (pd.DataFrame): DataFrame containing LL, PL, and Depth columns.
        uu_col (str): Column name for Undrained Shear Strength.
        spt_n (str): Column name for SPT-N.
        title (str): Plot title.
    
    Returns:
        fig (plotly.graph_objs._figure.Figure): Plotly figure object.
    """
    empty_data = False

    df = df.copy()
    df = df.dropna(subset=[uu_col, spt_n])
    
    if not len(df) >0:
        empty_data = True

    fig = px.scatter(
        df,
        x=spt_n,
        y=uu_col,
        hover_data=['bh_no', 'sample_ref_no','uu'],
        labels={
            "soil_layer" : "Soil Type",
            "spt_n_grouping" : "SPT-N Value Grouping",
            uu_col: 'Undrained Shear Strength (kPa)',
            spt_n: 'SPTN-N Value',
            'bh_no':"Borehole Number",
            "sample_ref_no":"Sample Ref. No.",
        },
        color_discrete_sequence=px.colors.qualitative.Set1,
        color = "soil_layer",
        symbol="spt_n_grouping"
    )

    fig.update_traces(marker=dict(size=10, opacity=0.9, line=dict(width=1, color='DarkSlateGrey')))
    fig.update_yaxes(
                # autorange='reversed',
                range=[0,df["uu"].max()+20]
                     ) 
    fig.update_xaxes(
                range=[0,110]
                     ) 
    fig.update_layout(
    legend_title = dict(
                        text="Soil Layer & SPT-N Grouping",
                        font=dict(size=16)
                    ),
    legend = dict(
        font=dict(size=14),
        orientation="h",         # horizontal legend
        yanchor="bottom",
        y=1.02,                  # slightly above the plot
        xanchor="left",
        x=0                 # centered horizontally
    ),
        shapes=[
        dict(
            type='line',
            xref='x',
            yref='y',
            x0=0,
            x1=0,
            y0=0,
            y1=df["uu"].max()+20,
            line=dict(color='black', width=1, dash='solid')
        )
    ],
    xaxis=dict(
        title="SPT-N Value (Capped at 100)",
        title_font=dict(size=18, family="Arial", color="black"),  # bold & bigger
        tickfont=dict(size=14),
        dtick=10,
        showgrid=True,
        gridcolor="black",
        minor=dict(
                    tick0=0,
                    dtick=5,         # Minor grid every 5 units
                    showgrid=True,   # ✅ Turn on minor gridlines
                    gridcolor="lightgray",
                    gridwidth=0.5
                )
    ),
    yaxis=dict(
        title="Undrained Shear Strength",
        title_font=dict(size=18, family="Arial", color="black"),
        tickfont=dict(size=14),
        showgrid=True,
        dtick=10,
        gridcolor="black",
        zeroline=True,
        zerolinewidth=3,
        zerolinecolor="black",
        minor=dict(
                    tick0=0,
                    dtick=5,         # Minor grid every 1 units
                    showgrid=True,   # ✅ Turn on minor gridlines
                    gridcolor="lightgray",
                    gridwidth=0.5
                )
    ),
        plot_bgcolor="#f9f9f9",
        paper_bgcolor="#ffffff",
        font=dict(size=14),
        height=900,
        margin=dict(l=80, r=60, t=40, b=80),  # Increase these as needed
    )

    return fig,empty_data


def plot_partical_density_plotly(df, specific_gravity="specific_gravity", depth_col='depth', title="Plasticity Index vs Depth"):
    """
    Returns a modern-looking Plotly scatter plot for Plasticity Index vs Depth.
    
    Parameters:
        df (pd.DataFrame): DataFrame containing LL, PL, and Depth columns.
        specific_gravity (str): Column name for specific gravity
        depth_col (str): Column name for Depth (mBGL).
        title (str): Plot title.
    
    Returns:
        fig (plotly.graph_objs._figure.Figure): Plotly figure object.
    """
    df = df.copy()
    df.dropna(subset=[specific_gravity, depth_col], inplace=True)

    fig = px.scatter(
        df,
        x=specific_gravity,
        y=depth_col,
        hover_data=['bh_no', 'sample_ref_no'],
        labels={
            "soil_layer" : "Soil Type",
            "spt_n_grouping" : "SPT-N Value (Blow Count)",
            specific_gravity: 'Specific Gravity',
            depth_col: 'Sample Depth (mBGL)',
            'bh_no':"Borehole Number",
            "sample_ref_no":"Sample Ref. No.",
        },
        color_discrete_sequence=px.colors.qualitative.Set1,
        color = "soil_layer",
        symbol="spt_n_grouping"
    )

    fig.update_traces(marker=dict(size=10, opacity=0.9, line=dict(width=1, color='DarkSlateGrey')))
    fig.update_yaxes(
                # autorange='reversed',
                range=[df[depth_col].max()+1,0-0.5]
                     ) 
    fig.update_xaxes(
        range=[0,10]
    )
    fig.update_layout(
    legend_title = dict(
                        text="Soil Layer & SPT-N Grouping",
                        font=dict(size=16)
                    ),
    legend = dict(
        font=dict(size=14),
        orientation="h",         # horizontal legend
        yanchor="bottom",
        y=1.02,                  # slightly above the plot
        xanchor="left",
        x=0                 # centered horizontally
    ),
         shapes=[
        dict(
            type='line',
            xref='x',
            yref='y',
            x0=0,
            x1=0,
            y0=0-0.5,
            y1=df[depth_col].max()+1,
            line=dict(color='black', width=1, dash='solid')
        ),
        dict(
            type='line',
            xref='x',
            yref='y',
            x0=0,
            x1=10,
            y0=df[depth_col].max()+1,
            y1=df[depth_col].max()+1,
            line=dict(color='black', width=1, dash='solid')
        )
    ],
    xaxis=dict(
        title="Specific Gravity",
        title_font=dict(size=18, family="Arial", color="black"),  # bold & bigger
        tickfont=dict(size=14),
        dtick=1,
        showgrid=True,
        gridcolor="black",
        minor=dict(
                    tick0=0,
                    dtick=0.2,         # Minor grid every 2 units
                    showgrid=True,   # ✅ Turn on minor gridlines
                    gridcolor="lightgray",
                    gridwidth=0.5
                )
    ),
    yaxis=dict(
        title="Sample Depth (mBGL)",
        title_font=dict(size=18, family="Arial", color="black"),
        tickfont=dict(size=14),
        showgrid=True,
        dtick=2,
        gridcolor="black",
        zeroline=True,
        zerolinewidth=3,
        zerolinecolor="black",
        minor=dict(
                    tick0=0,
                    dtick=1,         # Minor grid every 1 units
                    showgrid=True,   # ✅ Turn on minor gridlines
                    gridcolor="lightgray",
                    gridwidth=0.5
                )
    ),
        plot_bgcolor="#f9f9f9",
        paper_bgcolor="#ffffff",
        font=dict(size=14),
        height=900,
        margin=dict(l=80, r=60, t=40, b=80),  # Increase these as needed
    )

    return fig


def plot_bulk_density_plotly(df, bulk_density="bulk_density", depth_col='depth', title="Plasticity Index vs Depth"):
    """
    Returns a modern-looking Plotly scatter plot for Bulk Desntiy vs Depth.
    
    Parameters:
        df (pd.DataFrame): DataFrame containing LL, PL, and Depth columns.
        bulk_density (str): Column name for bulk density
        depth_col (str): Column name for Depth (mBGL).
        title (str): Plot title.
    
    Returns:
        fig (plotly.graph_objs._figure.Figure): Plotly figure object.
    """
    df = df.copy()
    df.dropna(subset=[bulk_density, depth_col], inplace=True)

    fig = px.scatter(
        df,
        x=bulk_density,
        y=depth_col,
        hover_data=['bh_no', 'sample_ref_no'],
        labels={
            "soil_layer" : "Soil Type",
            "spt_n_grouping" : "SPT-N Value (Blow Count)",
            bulk_density: 'Bulk Density',
            depth_col: 'Sample Depth (mBGL)',
            'bh_no':"Borehole Number",
            "sample_ref_no":"Sample Ref. No.",
        },
        color_discrete_sequence=px.colors.qualitative.Set1,
        color = "soil_layer",
        symbol="spt_n_grouping"
    )

    fig.update_traces(marker=dict(size=10, opacity=0.9, line=dict(width=1, color='DarkSlateGrey')))
    fig.update_yaxes(
                # autorange='reversed',
                range=[df[depth_col].max()+1,0-0.5]
                     ) 
    fig.update_xaxes(
        range=[0,10]
    )
    fig.update_layout(
    legend_title = dict(
                        text="Soil Layer & SPT-N Grouping",
                        font=dict(size=16)
                    ),
    legend = dict(
        font=dict(size=14),
        orientation="h",         # horizontal legend
        yanchor="bottom",
        y=1.02,                  # slightly above the plot
        xanchor="left",
        x=0                 # centered horizontally
    ),
         shapes=[
        dict(
            type='line',
            xref='x',
            yref='y',
            x0=0,
            x1=0,
            y0=0-0.5,
            y1=df[depth_col].max()+1,
            line=dict(color='black', width=1, dash='solid')
        ),
        dict(
            type='line',
            xref='x',
            yref='y',
            x0=0,
            x1=10,
            y0=df[depth_col].max()+1,
            y1=df[depth_col].max()+1,
            line=dict(color='black', width=1, dash='solid')
        )
    ],
    xaxis=dict(
        title="Bulk Density (Mg/m<sup>3</sup>)",
        title_font=dict(size=18, family="Arial", color="black"),  # bold & bigger
        tickfont=dict(size=14),
        dtick=1,
        showgrid=True,
        gridcolor="black",
        minor=dict(
                    tick0=0,
                    dtick=0.2,         # Minor grid every 2 units
                    showgrid=True,   # ✅ Turn on minor gridlines
                    gridcolor="lightgray",
                    gridwidth=0.5
                )
    ),
    yaxis=dict(
        title="Sample Depth (mBGL)",
        title_font=dict(size=18, family="Arial", color="black"),
        tickfont=dict(size=14),
        showgrid=True,
        dtick=2,
        gridcolor="black",
        zeroline=True,
        zerolinewidth=3,
        zerolinecolor="black",
        minor=dict(
                    tick0=0,
                    dtick=1,         # Minor grid every 1 units
                    showgrid=True,   # ✅ Turn on minor gridlines
                    gridcolor="lightgray",
                    gridwidth=0.5
                )
    ),
        plot_bgcolor="#f9f9f9",
        paper_bgcolor="#ffffff",
        font=dict(size=14),
        height=900,
        margin=dict(l=80, r=60, t=40, b=80),  # Increase these as needed
    )

    return fig


def plot_plasticity_chart_plotly(df, ll_col='ll', pl_col='pl', depth_col='depth', title="Plasticity Chart - Plasticity Index, PI (%) vs Liquid Limit (%) "):
    """
    Returns a modern-looking Plotly scatter plot for Plasticity Index vs Depth.
    
    Parameters:
        df (pd.DataFrame): DataFrame containing LL, PL, and Depth columns.
        ll_col (str): Column name for Liquid Limit.
        pl_col (str): Column name for Plastic Limit.
        depth_col (str): Column name for Depth (mBGL).
        title (str): Plot title.
    
    Returns:
        fig (plotly.graph_objs._figure.Figure): Plotly figure object.
    """
    df = df.copy()
    df.dropna(subset=[ll_col, pl_col, depth_col], inplace=True)
    df['pi'] = df[ll_col] - df[pl_col]

    # Horizontal line (LL from 20 to 29, PI = 0)
    ll1 = np.linspace(0, 26, 50)
    pi1 = np.full_like(ll1, 6) 

    # Sloped line (LL from 26 to 110, PI = 0.73 * (LL - 20))
    ll2 = np.linspace(26, df[ll_col].max()+20, 100)
    pi2 = 6 + 0.73 * (ll2 - 26)

    # Combine both segments
    ll_full = np.concatenate((ll1, ll2))
    pi_full = np.concatenate((pi1, pi2))

    if df["pi"].min() < 0:
        pi_range = [df["pi"].min()-10,df["pi"].max()+10]
    else:
        pi_range = [0,df["pi"].max()+10]

    fig = px.scatter(
        df,
        x=df[ll_col],
        y="pi",
        hover_data=['bh_no', 'sample_ref_no',"atterberg_limit_%_ll_%","atterberg_limit_%_pl_%"],
        labels={
            "soil_layer" : "Soil Type",
            "spt_n_grouping" : "SPT-N Value (Blow Count)",
            'pi': 'Plasticity Index (%)',
            "atterberg_limit_%_ll_%":"LL",
            "atterberg_limit_%_pl_%":"PL",
            depth_col: 'Sample Depth (mBGL)',
            'bh_no':"Borehole Number",
            "sample_ref_no":"Sample Ref. No.",
        },
        color_discrete_sequence=px.colors.qualitative.Set1,
        color = "soil_layer",
        symbol="spt_n_grouping"
    )
    fig.add_trace(go.Scatter(x=ll_full, y=pi_full,name='A-Line', mode='lines', line=dict(color='black')))
    # fig.add_trace(go.Scatter(x=ll2, y=pi2, mode='lines', line=dict(color='black')))
    fig.update_traces(marker=dict(size=10, opacity=0.9, line=dict(width=1, color='DarkSlateGrey')))
    # Horizontal PI=7 line
    fig.update_yaxes(
                # # autorange='reversed',
                range=pi_range
                     ) 
    fig.update_xaxes(
                        range=[0,df[ll_col].max()+10]
                     ) 
    fig.update_layout(
    legend_title = dict(
                        text="Soil Layer & SPT-N Grouping",
                        font=dict(size=16)
                    ),
    legend = dict(
        font=dict(size=14),
        orientation="h",         # horizontal legend
        yanchor="bottom",
        y=1.02,                  # slightly above the plot
        xanchor="left",
        x=0                 # centered horizontally
    ),
    shapes=[
        dict(
            type='line',
            xref='x',
            yref='y',
            x0=0,
            x1=0,
            y0=pi_range[0],
            y1=pi_range[1],
            line=dict(color='black', width=1, dash='solid')
        )
    ],
    xaxis=dict(
        title="Liquid Limit, LL (%)",
        title_font=dict(size=18, family="Arial", color="black"),  # bold & bigger
        tickfont=dict(size=14),
        showgrid=True,
        gridcolor="black",
                minor=dict(
                    tick0=0,
                    dtick=2,         # Minor grid every 2 units
                    showgrid=True,   # ✅ Turn on minor gridlines
                    gridcolor="lightgray",
                    gridwidth=0.5
                )
    ),
    yaxis=dict(
        title="Plasticity Index, PI (%)",
        title_font=dict(size=18, family="Arial", color="black"),
        tickfont=dict(size=14),
        showgrid=True,
        dtick=10,
        gridcolor="black",
        zeroline=True,
        zerolinecolor='black',
        minor=dict(
                    tick0=0,
                    dtick=2,         # Minor grid every 2 units
                    showgrid=True,   # ✅ Turn on minor gridlines
                    gridcolor="lightgray",
                    gridwidth=0.5
                )
    ),
        plot_bgcolor="#f9f9f9",
        paper_bgcolor="#ffffff",
        font=dict(size=14),
        height=900,
        margin=dict(l=80, r=60, t=40, b=80),  # Increase these as needed
    )

    return fig


def plot_spt_n_vs_sample_depth_plotly(df, spt_n='spt_n', depth_col='spt_depth_to_top_of_test',title="SPT-N (Capped at 100) vs Depth"):
    """
    Returns a modern-looking Plotly scatter plot for SPT-N Vs Depth.
    
    Parameters:
        df (pd.DataFrame): DataFrame containing LL, PL, and Depth columns.
        depth_col (str): Column name for sample Depth (mBGL).
        sample_ref (str): Column name for sample/specimen
        title (str): Plot title.
    
    Returns:
        fig (plotly.graph_objs._figure.Figure): Plotly figure object.
    """
    df = df.copy()
    df.dropna(subset=[spt_n,depth_col], inplace=True)

    fig = px.scatter(
        df,
        x='spt_n',
        y=depth_col,
        hover_data=['bh_no',"spt_n"],
        labels={
            "soil_layer" : "Soil Type",
            "spt_n_grouping" : "SPT-N Group",
            'spt_n': 'SPT-N Value (Blow Count)',
            depth_col: 'SPT Depth (mBGL)',
            'bh_no':"Borehole Number"
        },
        color_discrete_sequence=px.colors.qualitative.Set1,
        color = "soil_layer",
        symbol="spt_n_grouping"
    )

    fig.update_traces(marker=dict(size=10, opacity=0.9, line=dict(width=1, color='DarkSlateGrey')))
    fig.update_yaxes(
                     range=[df[depth_col].max()+1,0-0.5] # inverse
    )
    fig.update_xaxes(
        range=[0,df[spt_n].max()+10]
    )
    fig.update_layout(
    legend_title = dict(
                        text="<span style='text-align:left'>Soil Layer & SPT-N Grouping</span>",
                        font=dict(size=16)

                 ),
    legend = dict(
        font=dict(size=14),
        orientation="h",         # horizontal legend
        yanchor="bottom",
        y=1.02,                  # slightly above the plot
        xanchor="left",
        x=0                 # centered horizontally
    ),
     shapes=[
        dict(
            type='line',
            xref='x',
            yref='y',
            x0=0,
            x1=0,
            y0=0-0.5,
            y1=df[depth_col].max()+1,
            line=dict(color='black', width=1, dash='solid')
        ),
        dict(
            type='line',
            xref='x',
            yref='y',
            x0=0,
            x1=df[spt_n].max()+10,
            y0=df[depth_col].max()+1,
            y1=df[depth_col].max()+1,
            line=dict(color='black', width=1, dash='solid')
        )
    ],
    xaxis=dict(
        title="SPT-N Values",
        title_font=dict(size=18, family="Arial", color="black"),  # bold & bigger
        tickfont=dict(size=14),
        showgrid=True,
        dtick=10,
        gridcolor="black",
                minor=dict(
                    tick0=0,
                    dtick=5,         # Minor grid every 2 units
                    showgrid=True,   # ✅ Turn on minor gridlines
                    gridcolor="lightgray",
                    gridwidth=0.5
                )
    ),
    yaxis=dict(
        title="SPT Depth (mBGL)",
        title_font=dict(size=18, family="Arial", color="black"),
        tickfont=dict(size=14),
        showgrid=True,
        dtick=2,
        gridcolor="lightgrey",
        zeroline=True,
        zerolinewidth=3,
        zerolinecolor="black",
        minor=dict(
                    tick0=0,
                    dtick=1,         # Minor grid every 2 units
                    showgrid=True,   # ✅ Turn on minor gridlines
                    gridcolor="lightgray",
                    gridwidth=0.5
                )
    ),
        plot_bgcolor="#f9f9f9",
        paper_bgcolor="#ffffff",
        font=dict(size=14),
        height=900,
        margin=dict(l=80, r=60, t=40, b=80),  # Increase these as needed
    )

    return fig


def plot_borehole_mapping(df, lat='latitude', lon='longtitude', title="Borehole Location on Map (Yellow Circles = Borehole Point)"):
    """
    Returns a modern-looking Plotly scatter plot for SPT-N Vs Depth.
    
    Parameters:
        df (pd.DataFrame): DataFrame containing lat, lon, borehole columns.
        lat (str): Column name for latitude.
        lon (str): olumn name for latitude.
    
    Returns:
        fig (plotly.graph_objs._figure.Figure): Plotly figure object.
    """

    # Get base64 string of your image
    # img_path = "assets/borehole.png" 
    #base64_str = get_base64_image(img_path)
    #image_uri = "data:image/png;base64," + base64_str

    # Use a light-themed map and highlight boreholes in yellow
    fig_map = px.scatter_mapbox(
        df,
        lat=lat,
        lon=lon,
        color_discrete_sequence=["black"],  # All boreholes appear yellow
        hover_name="bh_no",
        #hover_data={depth_col: True, soil_col: True, "drilling_depth_m": True},
        zoom=16,
        height=600
    )

    fig_map.update_traces(
        marker=dict(size=14, opacity=0.9, symbol="circle",color="black")
    )

    fig_map.update_layout(
        mapbox_style="carto-positron",  # Light theme
        margin=dict(l=10, r=10, b=10, t=40),
        title=title,
        uirevision="lock"
    )


    return fig_map #st.plotly_chart(fig_map, use_container_width=True)



def plot_moisture_content_pl_ll_range_plotly(df,mc_col="mc",ll_col='ll', pl_col='pl', depth_col='sample_depth',title=""):
    """
    Returns a modern-looking Plotly scatter plot for MC within PL-LL range against sample depth.
    
    Parameters:
        df (pd.DataFrame): DataFrame containing LL, PL, and Depth columns.
        bh_no (str) : Column name for borehole id
        depth_col (str): Column name for sample Depth (mBGL).
        sample_ref (str): Column name for sample/specimen
        title (str): Plot title.
    
    Returns:
        fig (plotly.graph_objs._figure.Figure): Plotly figure object.
    """
    df = df.copy()
    df.dropna(subset=[mc_col,ll_col,pl_col], how='all', inplace=True)
    # Sort by depth to create nice spacing
    df = df.sort_values(by=[depth_col],ascending=True)

    fig = go.Figure()

    # Step 1: Add depth jitter based on borehole number
    bh_list = df["bh_no"].unique()
    bh_offset_map = {bh: i * 0.03 for i, bh in enumerate(bh_list)}  # small offset per borehole
    df["depth_jitter"] = df[depth_col] + df["bh_no"].map(bh_offset_map)
    
    # Step 2: Loop through rows to draw PL–LL lines per sample
    for i, row in df.iterrows():
        fig.add_trace(go.Scatter(
            x=[row[pl_col], row[ll_col]],
            y=[row["depth_jitter"]] * 2,
            mode="lines+markers",
            line=dict(color='black', width=1),
            marker=dict(size=15, symbol="line-ns-open"),
            showlegend=False
        ))

    # Add PL marker
    fig.add_trace(go.Scatter(
        x=df[pl_col],
        y=df["depth_jitter"],
        mode='markers',
        marker=dict(color='blue', size=10, symbol='circle'),
        name="PL"
    ))


    # Add PL marker
    fig.add_trace(go.Scatter(
        x=df[ll_col],
        y=df["depth_jitter"],
        mode='markers',
        marker=dict(color='green', size=10, symbol='circle'),
        name="LL"
    ))

    # Plot Water Content as open square
    fig.add_trace(go.Scatter(
        x=df[mc_col],
        y=df["depth_jitter"],
        mode="markers+text",
        marker=dict(color='red', size=12, symbol='square-open',line=dict(width=2)),
        #text=df["bh_no"],  # optional: label points with borehole number
        name="Moisture Content",
        hovertemplate=
        "Borehole Number=%{customdata[0]}<br>" +
        "SPT-N Group=%{customdata[1]}<br>" +
        "Moisture Content (%)=%{x}<br>" +
        "Sample Depth (mBGL)=%{y}<br>" +
        "Soil Type=%{customdata[3]}<extra></extra>",
        customdata=df[["bh_no", "spt_n_grouping", "spt_n", "soil_layer"]]
    ))

    fig.update_xaxes(
                range=[0,np.max([df[mc_col].max(),df[ll_col].max()])]
                     ) 
    fig.update_yaxes(
                # autorange='reversed',
                range=[df[depth_col].max()+5,0-0.5]
                     ) 
    fig.update_layout(
    legend = dict(
        font=dict(size=14),
        orientation="h",         # horizontal legend
        yanchor="bottom",
        y=1.02,                  # slightly above the plot
        xanchor="left",
        x=0                 # centered horizontally
    ),
    xaxis=dict(
        title="Moisture Content (%) with PL-LL Range",
        title_font=dict(size=18, family="Arial", color="black"),  # bold & bigger
        tickfont=dict(size=14),
        dtick=10,
        showgrid=True,
        gridcolor="black",
        minor=dict(
                    tick0=0,
                    dtick=2,         # Minor grid every 2 units
                    showgrid=True,   # ✅ Turn on minor gridlines
                    gridcolor="lightgray",
                    gridwidth=0.5
                )
    ),
    yaxis=dict(
        title="Sample Depth (mBGL)",
        title_font=dict(size=18, family="Arial", color="black"),
        tickfont=dict(size=14),
        showgrid=True,
        dtick=1,
        gridcolor="lightgrey",
        minor=dict(
                    tick0=0,
                    dtick=1,         # Minor grid every 1 units
                    showgrid=True,   # ✅ Turn on minor gridlines
                    gridcolor="lightgray",
                    gridwidth=0.5
                )
    ),
        plot_bgcolor="#f9f9f9",
        paper_bgcolor="#ffffff",
        font=dict(size=14),
        height=1500,
        margin=dict(l=80, r=60, t=40, b=80),  # Increase these as needed
    )

    return fig