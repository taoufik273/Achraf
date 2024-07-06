import os
import pandas as pd
import sqlite3
from flask import request, flash, redirect, url_for, current_app

def importer_donnees():
    if 'file' not in request.files:
        flash('No file part')
        return redirect(url_for('import_route'))
    file = request.files['file']
    if file.filename == '':
        flash('No selected file')
        return redirect(url_for('import_route'))
    
    try:
        df = pd.read_excel(file)
        
        db_path = get_database_path()
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS saisie (
            numero INTEGER,
            jour INTEGER,
            heure INTEGER,
            serie INTEGER,
            ordre INTEGER,
            massar TEXT UNIQUE,
            cin TEXT,
            nom TEXT,
            sexe TEXT,
            gym TEXT,
            course TEXT,
            poid TEXT,
            saut TEXT
        )
        ''')
        for col in ['gym', 'course', 'poid', 'saut']:
            if col not in df.columns:
                df[col] = ""
        insert_query = '''
        INSERT OR IGNORE INTO saisie (numero, jour, heure, serie, ordre, massar, cin, nom, sexe, gym, course, poid, saut)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        '''
        data_to_insert = df.values.tolist()
        cursor.executemany(insert_query, data_to_insert)
        conn.commit()
        cursor.close()
        conn.close()
        flash('تم الاستيراد بنجاح', 'ممتاز')
        return redirect(url_for('import_route'))
    except Exception as e:
        flash(f'Une erreur s\'est produite lors de l\'importation: {str(e)}', 'danger')
        return redirect(url_for('import_route'))


def get_database_path():
    # Chemin vers le dossier 'data' dans le répertoire du projet
    db_dir = os.path.join(current_app.root_path,  'data')
    db_path = os.path.join(db_dir, 'saisie.db')
    print(f"Chemin de la base de données : {db_path}")  # Pour vérification
    return db_path