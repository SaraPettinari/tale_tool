import os

from flask import render_template, request, session, Blueprint
from src.xes_handler import csv_to_xes
from src.utils import xes_to_df, create_dfg, get_file_path, create_performance_dfg
import src.const as cn

discovery = Blueprint('discovery', __name__)

files_dict = {}
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
        file_name = request.form[cn.FILE]
        if file_name in data_dict.keys():
            data_dict.pop(file_name)
            session['files'] = data_dict
            if cn.RESP in session.keys():
                session[cn.RESP] = ''
            if session[cn.FILE] == file_name:
                session[cn.FILE] = ''
                
    session[cn.MEASURES] = {cn.ALL: {}}
    session[cn.RESP] = ''
                
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
    f = request.files.get('file')
    
    if f.filename.endswith('xes'):
        file_path = os.path.join(ROOT_DIR, 'docs', 'logs', f.filename)
        f.save(file_path)
        session['fdata'] = {}
        session[cn.FILE] = f.filename
        data_dict[f.filename] = {}
        
        
        df = xes_to_df(file_path)

        resources_list = []
        cases_list = []

        if cn.RESOURCE in df.keys():
            resources = df[cn.RESOURCE].unique()
            resources_list = list(resources.tolist())

        if cn.CASE in df.keys():
            cases = df[cn.CASE].unique()
            cases_list = list(cases.tolist())

        session['fdata'] = { 
                'filters':{
                'resources': resources_list, 'cases': cases_list}
            }
                           
    return render_template(gui_interface)


@discovery.route('/discover-activity', methods=['GET', 'POST'])
def discover_dfg():    
    if request.method == 'GET':
        file_name = request.args.get(cn.FILE)
        file_path = get_file_path(file_name)
        session[cn.PATH] = file_path
        res_opt = request.args.get('resource_option')
        case_opt = request.args.get('case_option')
        
        if (res_opt == 'none' and case_opt == 'none'):
            filtering_conditions = {}
        else:
            filtering_conditions = {}
            if res_opt != 'none':
                filtering_conditions[cn.RESOURCE] = res_opt
                session['resource_opt'] = res_opt
            if case_opt != 'none':
                selected_case = int(case_opt)
                filtering_conditions[cn.CASE] = selected_case
                session['case_opt'] = int(case_opt)

        (nodes, edges) = create_dfg(file_path,
                                    filtering_conditions)


        session[cn.RESP] = {'nodes': nodes, 'edges': edges}

        return render_template(gui_interface, button_pressed='btn1')

    elif request.method == 'POST':
        file_name = request.form[cn.FILE]
        file_path = get_file_path(file_name)
        session[cn.PATH] = file_path
        (nodes, edges) = create_dfg(file_path)
        session[cn.RESP] = {'nodes': nodes, 'edges': edges}

        session['plot_file'] = {}
        return render_template(gui_interface, button_pressed='btn1')


@discovery.route('/discover-performance', methods=['GET', 'POST'])
def discover_performance():    
    if request.method == 'GET':
        file_name = request.args.get(cn.FILE)
        file_path = get_file_path(file_name)
        session[cn.PATH] = file_path
        res_opt = request.args.get('resource_option')
        case_opt = request.args.get('case_option')
        
        if (res_opt == 'none' and case_opt == 'none'):
            filtering_conditions = {}
        else:
            filtering_conditions = {}
            if res_opt != 'none':
                filtering_conditions[cn.RESOURCE] = res_opt
                session['resource_opt'] = res_opt
            if case_opt != 'none':
                selected_case = int(case_opt)
                filtering_conditions[cn.CASE] = selected_case
                session['case_opt'] = int(case_opt)

        (nodes, edges) = create_performance_dfg(file_path,
                                    filtering_conditions)


        session[cn.RESP] = {'nodes': nodes, 'edges': edges}

        return render_template(gui_interface, button_pressed='btn2')

    elif request.method == 'POST':
        file_name = request.form[cn.FILE]
        file_path = get_file_path(file_name)
        session[cn.PATH] = file_path
        (nodes, edges) = create_performance_dfg(file_path)
        session[cn.RESP] = {'nodes': nodes, 'edges': edges}

        session['plot_file'] = {}
        return render_template(gui_interface, button_pressed='btn2')

