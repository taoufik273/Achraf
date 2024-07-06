# scripts/intervenant.py
import os
import pandas as pd
import sqlite3
from flask import flash, redirect, request

def importer_intervenant():
    if 'file' not in request.files:
        flash('Aucun fichier sélectionné', 'error')
        return redirect(request.url)
    
    file = request.files['file']
    
    if file.filename == '':
        flash('Aucun fichier sélectionné', 'error')
        return redirect(request.url)
    
    if file:
        try:
            # Lire le fichier Excel
            df = pd.read_excel(file)
            
            # Connexion à la base de données SQLite
            db_path = os.path.join(os.path.dirname(__file__), '../data/saisie.db')
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            # Préparation de la requête d'insertion
            insert_query = '''
            INSERT INTO intervenant (numero, nom, ppr, travail, code, mission)
            VALUES (?, ?, ?, ?, ?, ?)
            '''

            # Conversion des données du DataFrame en liste de tuples
            data_to_insert = df.values.tolist()

            # Vérifier et insérer les données une par une pour éviter les doublons
            for record in data_to_insert:
                ppr = record[2]  # Assuming ppr is the third column
                cursor.execute('SELECT COUNT(*) FROM intervenant WHERE ppr = ?', (ppr,))
                if cursor.fetchone()[0] == 0:
                    cursor.execute(insert_query, record)

            # Commit the transaction
            conn.commit()

            # Fermeture de la connexion
            cursor.close()
            conn.close()

            # Afficher un message de succès (utilisation de flash pour Flask)
            flash('تم الاستيراد بنجاح', 'ممتاز')

        except Exception as e:
            # Afficher un message d'erreur en cas de problème
            flash(f"Erreur lors de l'importation des intervenants : {str(e)}", 'error')

    # Rediriger vers la page d'importation ou toute autre page nécessaire
    return redirect('/intervenant')
