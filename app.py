import os
import sys
from flask import Flask, request, jsonify, send_from_directory, render_template
import sqlite3
from flask_cors import CORS

# Déterminer le chemin de base de l'application
if getattr(sys, 'frozen', False):
    application_path = sys._MEIPASS
else:
    application_path = os.path.dirname(os.path.abspath(__file__))

DATABASE = os.path.join(application_path, 'data', 'saisie.db')

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_app(app):
    CORS(app)

    @app.route('/api/data', methods=['GET'])
    def get_data():
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM saisie")
        rows = cursor.fetchall()
        conn.close()

        data = [{key: row[key] if row[key] is not None else '' for key in row.keys()} for row in rows]

        return jsonify(data)

    @app.route('/api/data', methods=['PUT'])
    def update_data():
        updates = request.json
        conn = get_db_connection()
        cursor = conn.cursor()
        for update in updates:
            cursor.execute('''
                UPDATE saisie
                SET gym = ?, course = ?, poid = ?, saut = ?
                WHERE numero = ?
            ''', (update['gym'], update['course'], update['poid'], update['saut'], update['numero']))
        conn.commit()
        conn.close()
        return jsonify({"ممتاز": "تم الحفظ بنجاح"})

    @app.route('/index')
    def index():
        return send_from_directory(os.path.join(application_path, 'static'), 'index.html')

    @app.route('/setting')
    def saisie():
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM 'index2' LIMIT 1")
        row = cur.fetchone()
        conn.close()
        
        if row:
            data = ['' if item is None else str(item) for item in row]
        else:
            data = [''] * 6
        
        return render_template('setting.html', data=data)

    @app.route('/api/data', methods=['POST'])
    def saisie_updait():
        conn = get_db_connection()
        cur = conn.cursor()
        
        try:
            annee = request.form.get('annee', '')
            centre = request.form.get('centre', '')
            inspecteur = request.form.get('inspecteur', '')
            membre = request.form.get('membre', '')
            membre1 = request.form.get('membre1', '')
            section = request.form.get('section', '')
            
            cur.execute("SELECT COUNT(*) FROM 'index2'")
            count = cur.fetchone()[0]
            
            if count == 0:
                cur.execute("INSERT INTO 'index2' (annee, centre, inspecteur, membre, membre1, section) VALUES (?, ?, ?, ?, ?, ?)",
                            (annee, centre, inspecteur, membre, membre1, section))
            else:
                cur.execute("UPDATE 'index2' SET annee=?, centre=?, inspecteur=?, membre=?, membre1=?, section=?",
                            (annee, centre, inspecteur, membre, membre1, section))
            
            conn.commit()
            return jsonify({'success': True, 'message': 'تم تحديث البيانات بنجاح'})
        except Exception as e:
            conn.rollback()
            return jsonify({'success': False, 'error': str(e)})
        finally:
            conn.close()

    return app

if __name__ == '__main__':
    app = Flask(__name__, static_folder=os.path.join(application_path, 'static'))
    init_app(app)
    app.run(debug=False)