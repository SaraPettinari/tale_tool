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
    '''
    fig_heatmap = px.density_heatmap(filtered_df,
                                        x="x",
                                        y="y", 
                                        title="Space for: " + activity_name,
                                        range_x=[0, 10],
                                        range_y=[0, 10],)
    '''
    
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
    #out_h = "space_plot_h.html"
   
    plot_path =  os.path.join(os.getcwd(), "templates", activity_name)
    if not os.path.exists(plot_path):
        os.makedirs(plot_path)
    fig_path = os.path.join(plot_path, out_file)
    #fig_h_path = os.path.join(plot_path, out_h)
    
    fig.write_html(fig_path)
    #fig_heatmap.write_html(fig_h_path)
    
    template_path = activity_name + '/' + out_file
    print(template_path)
    return template_path
    

def time_plot(activity_name, file_path):
    df = log_to_dataframe(file_path)
    filtered_df = df[df['activity'] == activity_name]
    filtered_df = filtered_df[filtered_df['lifecycle'] != 'inprogress']

    cases = filtered_df['case'].drop_duplicates()

    out_time = []

    for case in cases:
        temp_df = filtered_df[filtered_df['case'] == case]
        temp_df['deltatime'] = temp_df['timestamp'].diff()
        time_list = temp_df[temp_df['lifecycle']
                            == 'complete']['deltatime'].tolist()
        time_list = [t.total_seconds() for t in time_list]
        maxval = max(time_list)
        minval = min(time_list)
        avgval = reduce(lambda a, b: a + b, time_list) / len(time_list)
        minval = avgval-minval
        maxval = maxval-avgval
        out_time.append({'case': case, 'min': minval,
                        'max': maxval, 'avg': avgval})

    out_df = pd.DataFrame(out_time)

    fig = go.Figure(data=go.Bar(
        x=out_df['case'],
        y=out_df['avg'],
        error_y=dict(
            type='data',
            symmetric=False,
            array=out_df['max'],
            arrayminus=out_df['min'],
        )
    ))

    fig.update_layout(
        title="Time for: " + activity_name,
        xaxis_title="Case",
        yaxis_title="Time",
    )
    
    out_file = "time_plot.html"
    plot_path = os.getcwd() + "\\templates\\" + activity_name
    if not os.path.exists(plot_path):
        os.makedirs(plot_path)
    fig_path = plot_path + '\\' + out_file
    fig.write_html(fig_path)
    
    template_path = activity_name + '/' +out_file
    return template_path