import os
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

from src.utils import xes_to_df
from functools import reduce
import src.const as cn

def get_plot(measure, file_path):
    df = xes_to_df(file_path)
    
    if measure == cn.SPACE:
        return get_space_plot(df)
    elif measure == cn.TIME:
        return ''
    elif measure == cn.COMM:
        return get_communication_graph(df)
    elif measure == cn.BATTERY:
        return get_battery_plot(df)

def get_space_plot(df, activity_name = None):
    plot_list = []
    out_file_3d = "space_plot_3d.html"
    out_file_heat = "space_plot_heat.html"
    
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
        # Create the heatmap
        fig_heatmap = px.density_heatmap(
            df,
            x='x',
            y='y',
            title="Space for MRS - Heatmap",
            color_continuous_scale="Viridis",
            hover_data={cn.RESOURCE: True},
            range_x=[0, 10],
            range_y=[0, 10]
        )
    else:
        activity_name = 'home'
        fig = px.scatter_3d(df, x='x', y='y', z='z',
                            color=cn.ACTIVITY,
                            symbol=cn.RESOURCE,
                            title="Space for MRS - 3D",
                            range_x=[0, 10],
                            range_y=[0, 10],
                            range_z=[0, 2],
                            )
        # Create the heatmap
        fig_heatmap = px.density_heatmap(
            df,
            x='x',
            y='y',
            title="Space for MRS - Heatmap",
            color_continuous_scale="Viridis",
            range_x=[0, 10],
            range_y=[0, 10]
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
        
    
   
    plot_path =  os.path.join(os.getcwd(), "templates", activity_name)
    if not os.path.exists(plot_path):
        os.makedirs(plot_path)
        
    fig_path_3d = os.path.join(plot_path, out_file_3d)
    fig_path_heat = os.path.join(plot_path, out_file_heat)
    
    
    fig.write_html(fig_path_3d)
    fig_heatmap.write_html(fig_path_heat)
    
    plot_list.append(activity_name + '/' + out_file_3d)
    plot_list.append(activity_name + '/' + out_file_heat)
    
    return plot_list



def get_battery_plot(df):
    template_path = []
    plot_path =  os.path.join(os.getcwd(), "templates", 'home')
    
    # Create time plot
    out_file = "time_battery_plot.html"
    fig_time = px.line(df, 
                x=cn.TIMESTAMP, 
                y=cn.BATTERY, 
                color=cn.RESOURCE,
                hover_data={cn.ACTIVITY : True},
                animation_frame=cn.CASE,
                animation_group=cn.TIMESTAMP,
                title='Battery Discharge')
    
    fig_path = os.path.join(plot_path, out_file)
    
    fig_time.write_html(fig_path)
    
    t_path = 'home/' + out_file
    template_path.append(t_path)

    # Create activity plot
    df = df.sort_values(by=[cn.CASE, cn.ACTIVITY, cn.TIMESTAMP])

    activity_battery = df.pivot_table(
        index=[cn.CASE, cn.ACTIVITY, cn.RESOURCE],
        columns=cn.LIFECYCLE,
        values=cn.BATTERY
    ).reset_index()
    activity_battery['battery_depletion'] = activity_battery['start'] - activity_battery['complete']

    # Calculate the mean battery depletion for each activity and resource across all cases
    mean_activity_depletion = activity_battery.groupby([cn.ACTIVITY, cn.RESOURCE])['battery_depletion'].mean().reset_index()

    fig = px.bar(
        mean_activity_depletion,
        x=cn.ACTIVITY,
        y='battery_depletion',
        color=cn.RESOURCE,
        facet_col=cn.RESOURCE,
        title="Mean Battery Discharge per Activity by Resource",
        labels={'battery_depletion': 'Mean Battery Discharge (%)', cn.ACTIVITY: 'Activity'},
    )
    fig.update_layout(
        yaxis_title="Mean Battery Depletion (%)",
        xaxis_title="Activity",
    )

    out_file = "activity_battery_plot.html"
    
    fig_path = os.path.join(plot_path, out_file)
    fig.write_html(fig_path)
    
    a_path = 'home/' + out_file

    template_path.append(a_path)
    
    return template_path


def get_communication_graph(this_df):
    df = pd.DataFrame(generate_comm_data(this_df))
    # Assuming 'start_time' and 'complete_time' are in string format, convert them to datetime
    df['start_time'] = pd.to_datetime(df['start_time'])
    df['complete_time'] = pd.to_datetime(df['complete_time'])

    # Calculate performance metrics
    df['duration'] = df['complete_time'] - df['start_time']
    df['success_rate'] = 1 - (df['lost_msgs'] / df['attempts'])

    print(df['attempts'].mean())

    # Calculate duration
    df['duration'] = (df['complete_time'] - df['start_time']).dt.total_seconds()
    
    df[cn.ACTIVITY] = [x[0] for x in df[cn.ACTIVITY]]
    
    activities_counts = df[cn.ACTIVITY].value_counts().reset_index()
    activities_counts.columns = [cn.ACTIVITY, 'received_msgs']

    # Grouping data by activities and calculating sum of messages sent, lost, and total duration
    grouped_data = df.groupby(cn.ACTIVITY).agg({'msg_id': 'count', 'lost_msgs': 'sum', 'duration': 'mean', 'attempts': 'mean'}).reset_index()


    # Merge the counts of rows for each activities into the grouped data DataFrame
    grouped_data = pd.merge(grouped_data, activities_counts, on=cn.ACTIVITY)
    
    fig = px.bar(grouped_data, x="activity", y=["received_msgs", "lost_msgs"], text_auto=True)

    fig.update_layout(xaxis_title="activity", yaxis_title="Messages Count",
                    title="Communication Metrics")


    out_file = "commumication_plot.html"
    
    plot_path =  os.path.join(os.getcwd(), "templates", "home")
    if not os.path.exists(plot_path):
        os.makedirs(plot_path)
    fig_path = os.path.join(plot_path, out_file)
    
    fig.write_html(fig_path)
    
    template_path = "home" + '/' + out_file
    print(template_path)
    return(template_path)


def generate_comm_data(df : pd.DataFrame):
    
    grouped_df = df.groupby('msg_id')
    lost_msgs = 0
    tentativi = 0
    results = []
    # Iterate over each group and store it in the dictionary
    for msg_id, group in grouped_df:
        lost_msgs = 0
        tentativi = 0
        activity = group[cn.ACTIVITY].iloc[0]
        receive_rows = group[group['msg_role'] == 'receive']
        
            
        # Find the first row with 'lifecycle' equal to 'start'
        start_rows = group[(group[cn.LIFECYCLE] == 'start')]
        if not start_rows.empty:
            start_row = start_rows.iloc[0]
            tentativi = len(start_rows)
            if receive_rows.empty:
                lost_msgs += 1
        else:
            continue
        
        # Find the last row with 'lifecycle' equal to 'complete'
        complete_rows = group[(group[cn.LIFECYCLE] == 'complete')]
        if not complete_rows.empty:
            complete_row = complete_rows.iloc[-1]
        else:
            continue
        
        # Calculate timestamp difference
        timestamp_diff = pd.to_datetime(complete_row[cn.TIMESTAMP]) - pd.to_datetime(start_row[cn.TIMESTAMP])
        
        # Store results
        results.append({
            'msg_id': msg_id,
            cn.ACTIVITY: activity,
            'start_time': start_row[cn.TIMESTAMP],
            'complete_time': complete_row[cn.TIMESTAMP],
            'timestamp_diff': timestamp_diff,
            'lost_msgs': lost_msgs,
            'attempts': tentativi
        })
        # Store both send and receive rows in a dictionary


    dff = pd.DataFrame(results)

    return dff