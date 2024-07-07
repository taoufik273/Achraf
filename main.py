import os
import sys
import webbrowser
import subprocess
import sqlite3
from flask import Flask, send_from_directory, jsonify, request, render_template, redirect, flash

# Déterminer le chemin de base de l'application
if getattr(sys, 'frozen', False):
    application_path = sys._MEIPASS
else:
    application_path = os.path.dirname(os.path.abspath(__file__))

# Ajouter le chemin des scripts au sys.path
sys.path.append(os.path.join(application_path, 'scripts'))
sys.path.insert(0, application_path)

# Importer les modules locaux
import saisie
import setting 
from scripts import groups, stat, importer, intervenant, calculate

# Importer le blueprint zero
from scripts.zero import zero_bp

server = Flask(__name__, 
               static_folder=os.path.join(application_path, 'static'), 
               template_folder=os.path.join(application_path, 'web'))

server.secret_key = 'AAFIA'  # Nécessaire pour utiliser flash

# Enregistrer le blueprint zero
server.register_blueprint(zero_bp, url_prefix='/zero')

@server.route('/img/<path:filename>')
def serve_img(filename):
    return send_from_directory(os.path.join(application_path, 'img'), filename)

with server.app_context():
    saisie.init_app(server)
setting.init_app(server)

@server.route('/')
def start_page():
    db_path = os.path.join(application_path, 'data', 'saisie.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT section FROM index2")
    section = cursor.fetchone()
    conn.close()
    
    if section:
        section = section[0]
    else:
        section = "N/A"
    
    return render_template('start.html', section=section)

@server.route('/execute/<script_name>', methods=['POST'])
def execute_script(script_name):
    script_map = {
        'import': None,
        'saisie': None,
        'calculate': None,
        'NF': 'NF.py',
        'zero': None,
        'stat': 'stat.py',
        'dispence': 'dispence.py',
        'exportnote': 'exportnote.py',
        'trace': 'trace.py',
        'intervenant': None,
        'presence': 'presence.py',
        'liste': 'liste.py',
        'setting': None,
        'allnotes': 'allnotes.py',
        'groups': None
    }
    
    if script_name in script_map:
        # Gestion des redirections spécifiques
        if script_name == 'saisie':
            return jsonify({'redirect': '/index'}), 200
        elif script_name == 'setting':
            return jsonify({'redirect': '/login'}), 200
        elif script_name == 'groups':
            return jsonify({'redirect': '/groups'}), 200
        elif script_name == 'stat':
            return jsonify({'redirect': '/stat'}), 200
        elif script_name == 'calculate':
            return jsonify({'redirect': '/calculate'}), 200
        elif script_name == 'import':
            return jsonify({'redirect': '/import'}), 200
        elif script_name == 'intervenant':
            return jsonify({'redirect': '/intervenant'}), 200
        elif script_name == 'zero':
            return jsonify({'redirect': '/zero/'}), 200
        
        # Exécution du script via subprocess
        elif script_map[script_name]:
            try:
                subprocess.run([sys.executable, os.path.join(application_path, 'scripts', script_map[script_name])], 
                               capture_output=True, text=True, check=True)
                return jsonify({'message': f'{script_name} script executed successfully'}), 200
            except subprocess.CalledProcessError as e:
                server.logger.error(f"Error executing {script_name} script: {str(e)}")
                return jsonify({'error': str(e)}), 500
    
    return jsonify({}), 204


@server.route('/groups')
def groups_route():
    groups.generer_groups_html()
    return send_from_directory(server.static_folder, 'groups.html')

@server.route('/calculate')
def calculate_page():
    return render_template('calculate.html')

@server.route('/execute_calculate', methods=['POST'])
def execute_calculate():
    try:
        subprocess.run([sys.executable, os.path.join(application_path, 'scripts', 'calculate.py')], 
                       capture_output=True, text=True, check=True)
        return jsonify({'message': 'تم حساب المعدلات بنجاح.'}), 200
    except subprocess.CalledProcessError as e:
        server.logger.error(f"Error executing calculate.py: {str(e)}")
        return jsonify({'error': str(e)}), 500


@server.route('/stat')
def stat_route():
    stat.generer_statistiques_html()
    return send_from_directory(server.static_folder, 'statistiques.html')

@server.route('/import', methods=['GET', 'POST'])
def import_route():
    if request.method == 'POST':
        return importer.importer_donnees()
    return render_template('import.html')

@server.route('/intervenant', methods=['GET', 'POST'])
def intervenant_route():
    if request.method == 'POST':
        return intervenant.importer_intervenant()
    return render_template('intervenant.html')

@server.route('/save_data', methods=['POST'])
def save_data_route():
    return groups.handle_save_data()

@server.route('/about')
def about_page():
    return send_from_directory(server.static_folder, 'about.html')

@server.route('/download/<filename>')
def download_file(filename):
    return send_from_directory(os.path.join(application_path, 'INPUT'), filename, as_attachment=True)

# Routes pour le système de login et setting
@server.route('/login', methods=['GET', 'POST'])
def login():
    return setting.login()

@server.route('/setting')
def setting_page():
    return setting.setting_page()

@server.route('/api/data', methods=['POST'])
def update_setting():
    return setting.update()

def run_server():
    server.run(host='127.0.0.1', port=5000, debug=False)

if __name__ == '__main__':
    webbrowser.open('http://127.0.0.1:5000/')
    run_server()