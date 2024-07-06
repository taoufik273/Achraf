import os
import sys
from flask import request, jsonify, redirect, url_for, flash, render_template, send_from_directory
import sqlite3
from flask_cors import CORS
from functools import wraps

# Déterminer le chemin de base de l'application
if getattr(sys, 'frozen', False):
    application_path = sys._MEIPASS
else:
    application_path = os.path.dirname(os.path.abspath(__file__))

DATABASE = os.path.join(application_path, 'data', 'saisie.db')
PASSWORD = 'SBIH'  # Remplacez ceci par le mot de passe de votre choix

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def password_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'authenticated' not in request.cookies:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def init_app(app):
    CORS(app)

def login():
    if request.method == 'POST':
        if request.form['password'] == PASSWORD:
            response = redirect(url_for('setting_page'))
            response.set_cookie('authenticated', 'true')
            return response
        else:
            flash('كلمة المرور خاطئة', 'error')
    return render_template('login.html')

@password_required
def setting_page():
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

@password_required
def update():
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