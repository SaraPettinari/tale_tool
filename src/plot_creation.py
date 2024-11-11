import os
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

from src.utils import log_to_dataframe
from functools import reduce


def space_plot(activity_name, file_path):
    df = log_to_dataframe(file_path)
    if activity_name != '':
        filtered_df = df[df['activity'] == activity_name]
        fig = px.scatter_3d(filtered_df, x='x', y='y', z='z',
                            color='case',
                            symbol='activity',
                            title="Space for: " + activity_name,
                            range_x=[0, 10],
                            range_y=[0, 10],
                            range_z=[0, 2],
                            )
    else:
        activity_name = 'home'
        fig = px.scatter_3d(df, x='x', y='y', z='z',
                            color='activity',
                            symbol='resource',
                            title="Space for MRS",
                            range_x=[0, 10],
                            range_y=[0, 10],
                            range_z=[0, 2],
                            )
    
    fig.update_layout(scene=dict(
        yaxis=dict(
            backgroundcolor="rgb(227, 227, 250)",
            gridcolor="white",
            showbackground=True,
            zerolinecolor="white"),
        zaxis=dict(
            backgroundcolor="rgb(227, 227, 227)",
            gridcolor="white",
            showbackground=True,
            zerolinecolor="white",),),
    )
        
    out_file = "space_plot.html"
   
    plot_path =  os.path.join(os.getcwd(), "templates", activity_name)
    if not os.path.exists(plot_path):
        os.makedirs(plot_path)
    fig_path = os.path.join(plot_path, out_file)
    
    fig.write_html(fig_path)
    
    template_path = activity_name + '/' + out_file
    print(template_path)
    return template_path


def comm_plot(file_path):
    df = log_to_dataframe(file_path)