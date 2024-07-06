import os
import sqlite3
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app

zero_bp = Blueprint('zero', __name__, template_folder='../static')

def get_database_path():
    return os.path.join(current_app.root_path, 'data', 'saisie.db')

def clear_tables():
    db_path = get_database_path()
    
    if not os.path.exists(db_path):
        flash("La base de données n'existe pas.", 'error')
        return False
    
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    try:
        # Vider le contenu des tables 'saisie' et 'notes'
        c.execute("DELETE FROM saisie")
        c.execute("DELETE FROM notes")
        c.execute("DELETE FROM liste")
        c.execute("DELETE FROM intervenant")
        conn.commit()
        return True
    except sqlite3.Error as e:
        flash(f"Erreur lors de la suppression des données : {e}", 'error')
        return False
    finally:
        conn.close()

@zero_bp.route('/')
def index():
    return render_template('zero.html')

@zero_bp.route('/clear', methods=['POST'])
def clear_data():
    password = request.form.get('password')
    if password == "AAFIA TAOUFIK":  # Remplacez par votre mot de passe réel
        if clear_tables():
            flash('تم مسح المعطيات السابقة بنجاح', 'success')
        else:
            flash('حدث خطأ أثناء مسح المعطيات', 'error')
    else:
        flash('كلمة المرور خاطئة', 'error')
    return redirect(url_for('zero.index'))