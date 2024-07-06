import os
import sys
from tkinter import Tk, filedialog, messagebox
import pandas as pd
import sqlite3

def resource_path(relative_path):
    """ Obtenir le chemin absolu vers la ressource, fonctionne pour dev et pour PyInstaller """
    try:
        # PyInstaller crée une variable temporaire pour stocker le chemin d'accès aux fichiers.
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def importer_donnees():
    # Créer une fenêtre principale Tkinter cachée
    root = Tk()
    root.withdraw()  # Masquer la fenêtre principale
    
    # Ouvrir une boîte de dialogue pour sélectionner le fichier Excel
    filename = filedialog.askopenfilename(filetypes=[("Excel files", "*.xlsx;*.xls")], parent=root)
    
    # Si aucun fichier n'est sélectionné, retourner
    if not filename:
        return
    
    try:
        # Lire le fichier Excel
        df = pd.read_excel(filename)
        
        # Connexion à la base de données SQLite
        db_path = resource_path('data/saisie.db')
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
            cursor.execute('SELECT COUNT(*) FROM intervenant WHERE ppr = ?', (record[2],))
            if cursor.fetchone()[0] == 0:
                cursor.execute(insert_query, record)

        # Commit the transaction
        conn.commit()

        # Fermeture de la connexion
        cursor.close()
        conn.close()

        # Afficher un message de succès
        messagebox.showinfo("ممتاز", "تم الاستيراد بنجاح", parent=root)

    except Exception as e:
        # Afficher un message d'erreur en cas de problème
        messagebox.showerror("Erreur", "Une erreur s'est produite lors de l'importation: " + str(e), parent=root)

    # Détruire la fenêtre principale après utilisation
    root.destroy()

# Appel de la fonction importer_donnees() au démarrage du script
if __name__ == "__main__":
    importer_donnees()
