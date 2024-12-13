import os

from flask import render_template, request, session, Blueprint

from src.utils import *
from src.plot_creation import *
import src.const as cn

enhancement = Blueprint('enhancement', __name__)

gui_interface = 'enhancement.html'
ROOT_DIR = os.path.abspath(os.curdir)

@enhancement.route('/measurements_gui')
def measurements_gui():
    return render_template(gui_interface)


@enhancement.route('/measurements_gui/measure', methods=['GET'])
def get_global_plot():
    file_path = session[cn.PATH]
    args_keys = request.args.keys()
    for key in args_keys:
        if key == 'graph':
            if request.args[key] == cn.PERFORMANCE: # reconstruct the frequency DFG
                (nodes, edges) = create_performance_dfg(file_path)
                session[cn.RESP] = {'nodes': nodes, 'edges': edges}
            elif request.args[key] == cn.FREQUENCY: # reconstruct the performance DFG
                (nodes, edges) = create_dfg(file_path)
                session[cn.RESP] = {'nodes': nodes, 'edges': edges}
        else: # Create measures plot
            df = xes_to_df(file_path)
                
            fig_path = get_plot(key, df)
            session[cn.MEASURES][cn.ALL][key] = fig_path
    return render_template(gui_interface)


@enhancement.route('/view/activity', methods=['GET'])
def see_plot():
    args = request.args
    activity_name = args.get('activity_id')
    file_name = session[cn.FILE]
    file_path = get_file_path(file_name)
    session['current_activity'] = activity_name
    # space plot generation
    if args.get(cn.SPACE):
        fig_path = get_space_plot(activity_name, file_path)       
        if not cn.MEASURES in session.keys():
            session[cn.MEASURES] = {activity_name: {cn.SPACE: fig_path}}
        elif not activity_name in session[cn.MEASURES].keys():
            session[cn.MEASURES][activity_name] = {cn.SPACE: fig_path}
        else:
            session[cn.MEASURES][activity_name][cn.SPACE] = fig_path
    
    return render_template(gui_interface)
