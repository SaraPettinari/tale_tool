import os
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

from src.utils import xes_to_df, process_battery
from functools import reduce
import src.const as cn

def get_plot(measure, file_path):
    df = xes_to_df(file_path)
    
    if measure == cn.SPACE:
        return get_space_plot(df)
    elif measure == cn.TIME:
        return ''
    elif measure == cn.COMM:
        return ''
    elif measure == cn.BATTERY:
        return get_battery_plot(df)

def get_space_plot(df, activity_name = None):
    if activity_name != None:
        filtered_df = df[df[cn.ACTIVITY] == activity_name]
        fig = px.scatter_3d(filtered_df, x='x', y='y', z='z',
                            color=cn.CASE,
                            symbol=cn.ACTIVITY,
                            title="Space for: " + activity_name,
                            range_x=[0, 10],
                            range_y=[0, 10],
                            range_z=[0, 2],
                            )
    else:
        activity_name = 'home'
        fig = px.scatter_3d(df, x='x', y='y', z='z',
                            color=cn.ACTIVITY,
                            symbol=cn.RESOURCE,
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
    df = xes_to_df(file_path)


def get_battery_plot(df, option = 'time'):

    
    if option == 'time':
        #process_battery(df)
        fig = px.line(df, 
                  x=cn.TIMESTAMP, 
                  y=cn.BATTERY, 
                  color=cn.RESOURCE,
                  hover_data=cn.ACTIVITY,
                  symbol=cn.RESOURCE,
                  animation_frame=cn.CASE,
                  animation_group=cn.TIMESTAMP,
                  title='Battery Depletion')
    elif option == 'activity':
        df = df.sort_values(by=[cn.CASE, cn.ACTIVITY, cn.TIMESTAMP])

        activity_battery = df.pivot_table(
            index=[cn.CASE, cn.ACTIVITY, cn.RESOURCE],
            columns=cn.LIFECYCLE,
            values=cn.BATTERY
        ).reset_index()
        activity_battery['battery_depletion'] = activity_battery['start'] - activity_battery['complete']

        # Step 2: Calculate the mean battery depletion for each activity and resource across all cases
        mean_activity_depletion = activity_battery.groupby([cn.ACTIVITY, cn.RESOURCE])['battery_depletion'].mean().reset_index()

        fig = px.bar(
            mean_activity_depletion,
            x=cn.ACTIVITY,
            y='battery_depletion',
            color=cn.RESOURCE,
            title="Mean Battery Depletion per Activity by Resource",
            labels={'battery_depletion': 'Mean Battery Depletion (%)', cn.ACTIVITY: 'Activity'},
            hover_data={cn.RESOURCE: True}
        )
        fig.update_layout(
            yaxis_title="Mean Battery Depletion (%)",
            xaxis_title="Activity",
        )

    
        

    out_file = option + "_battery_plot.html"
    
    plot_path =  os.path.join(os.getcwd(), "templates", 'home')

    
    fig_path = os.path.join(plot_path, out_file)
    
    fig.write_html(fig_path)
    
    template_path = 'home/' + out_file
    print(template_path)
    return template_path


