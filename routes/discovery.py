import os

from flask import render_template, request, session, Blueprint
from src.xes_handler import csv_to_xes
from src.utils import log_to_dataframe, create_dfg, get_file_path
import src.const as cn

discovery = Blueprint('discovery', __name__)

files_dict = {}
resp_list = []
resources_list = []

data_dict = {}
file_name = None

gui_interface = 'robotrace.html'
ROOT_DIR = os.path.abspath(os.curdir)


@discovery.route('/discovery', methods=['GET', 'POST'])
def init():
    # if there is a delete file request
    if request.method == 'POST':
        session['plot_file'] = {}
        file_name = request.form['file_name']
        if file_name in data_dict.keys():
            data_dict.pop(file_name)
            resp_list.remove(file_name)
            session['files'] = data_dict
            if 'response_data' in session.keys():
                session['response_data'] = ''
                
    #session['communication'] = ''
    #session['space'] = 'home/space_plot.html'
    session[cn.MEASURES] = {cn.ALL: {}}
                
    return render_template(gui_interface)


@discovery.route('/csv-processing', methods=['POST'])
def csv_processing():
    if 'csv-file' not in request.files:
        return render_template(gui_interface)
    
    file = request.files['csv-file']
    if file.filename == '':
        return render_template(gui_interface)
    if file:
        if file.filename.endswith('csv'):
            file_path = os.path.join(ROOT_DIR, 'docs', 'logs', 'csv', file.filename)
            file.save(file_path)
            dest_name = csv_to_xes(file_path)
        return render_template(gui_interface, message = "Saved as: {dest_name}", dest_name = dest_name)
    

@discovery.route('/select-logs', methods=['POST'])
def choose_path():
    files_list = request.files.getlist('file')
    for f in files_list:
        if f.filename.endswith('xes'):
            f.save(os.path.join(ROOT_DIR, 'docs', 'logs', f.filename))
            resp_list.append(f.filename)

        data_dict[f.filename] = {}

    session['files'] = resp_list
    session['fdata'] = data_dict[f.filename]
    
    return render_template(gui_interface)


@discovery.route('/discover-activity', methods=['GET', 'POST'])
def discover_dfg():    
    if request.method == 'GET':
        file_name = request.args.get('file_name')
        file_path = get_file_path(file_name)
        session['curr_path'] = file_path
        res_opt = request.args.get('resource_option')
        case_opt = request.args.get('case_option')
        
        if(res_opt == 'none' and case_opt == 'none'):
            filtering_conditions = {}
        else:
            filtering_conditions = {'org:resource': res_opt}
            session['resource_opt'] = res_opt
            if(case_opt != 'none'):
                session['case_opt'] = int(case_opt)

        (nodes, edges) = create_dfg(file_path,
                                    filtering_conditions)


        session['response_data'] = {'nodes': nodes, 'edges': edges}

        return render_template(gui_interface)

    elif request.method == 'POST':
        file_name = request.form['file_name']
        file_path = get_file_path(file_name)
        session['curr_path'] = file_path
        (nodes, edges) = create_dfg(file_path)
        session['response_data'] = {'nodes': nodes, 'edges': edges}

        session['plot_file'] = {}
        return render_template(gui_interface)


@discovery.route('/filter', methods=['POST'])
def get_filters():
    file_name = request.form['file_name']
    session['file_name'] = file_name

    file_path = get_file_path(file_name)
    df = log_to_dataframe(file_path)

    resources_list = []
    cases_list = []

    if 'resource' in df.keys():
        resources = df["resource"].unique()
        resources_list = list(resources.tolist())

    if 'case' in df.keys():
        cases = df['case'].unique()
        cases_list = list(cases.tolist())

    data_dict[file_name] = {
        'resources': resources_list, 'cases': cases_list}

    return render_template(gui_interface)

