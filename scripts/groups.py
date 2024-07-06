import sqlite3
import pandas as pd
from flask import Flask, request, jsonify, send_from_directory
import logging
import math
import os

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

app = Flask(__name__)

def generer_groups_html():
    # Chemin absolu à la base de données
    db_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'saisie.db')
    
    with sqlite3.connect(db_path) as conn:
        query = """
            SELECT 
                s.jour as jour, 
                s.heure as heure, 
                COUNT(DISTINCT s.massar) as nombre_candidats
            FROM 
                saisie s
            GROUP BY 
                s.jour, s.heure
            ORDER BY 
                s.jour, s.heure
        """
        df = pd.read_sql_query(query, conn)

    def generate_html_table(df):
        html = '<form id="statsForm">\n'
        html += '<table dir="rtl">\n'
        html += '<tr><th>يوم الامتحان</th><th>ساعة الامتحان</th><th>عدد المترشحين</th><th>عدد المجموعات</th></tr>\n'
        
        current_jour = None
        color_index = 0
        colors = ['lightblue', 'lightgreen']
        
        for index, row in df.iterrows():
            if row['jour'] != current_jour:
                current_jour = row['jour']
                color = colors[color_index % 2]
                color_index += 1
            
            html += f'<tr style="background-color: {color};">'
            html += f'<td>{row["jour"]}</td>'
            html += f'<td>{row["heure"]}</td>'
            html += f'<td><strong>{row["nombre_candidats"]}</strong></td>'
            html += f'<td><input type="number" name="groupes_{row["jour"]}_{row["heure"]}" min="1" max="{row["nombre_candidats"]}" required></td>'
            html += '</tr>\n'
        
        html += '</table>\n'
        html += '<button type="submit" style="margin-top: 20px;">حفظ</button>\n'
        html += '</form>\n'
        
        html += '''
        <script>
        document.getElementById('statsForm').onsubmit = function(e) {
            e.preventDefault();
            var formData = new FormData(this);
            var result = {};
            for (var [key, value] of formData.entries()) {
                result[key] = value;
            }
            fetch('/save_data', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(result),
            })
            .then(response => response.json())
            .then(data => {
                if(data.success) {
                    alert('تم حفظ البيانات بنجاح');
                } else {
                    alert('حدث خطأ أثناء حفظ البيانات: ' + data.error);
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('حدث خطأ أثناء حفظ البيانات');
            });
        }
        </script>
        '''
        return html

    html_content = """
    <html lang="ar" dir="rtl">
    <head>
        <meta charset="UTF-8">
        <title>توزيع المترشحين</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                direction: rtl;
            }}
            table {{
                border-collapse: collapse;
                width: 100%;
            }}
            th, td {{
                border: 1px solid black;
                padding: 8px;
                text-align: center;
            }}
            th {{
                background-color: #f2f2f2;
            }}
            input[type="number"] {{
                width: 60px;
            }}
            button {{
                padding: 10px 20px;
                font-size: 16px;
            }}
        </style>
    </head>
    <body>
        <h1>توزيع المترشحين</h1>
        {table}
    </body>
    </html>
    """

    table_html = generate_html_table(df)
    html_complet = html_content.format(table=table_html)

    # Chemin absolu pour le fichier HTML
    html_path = os.path.join(os.path.dirname(__file__), '..', 'static', 'groups.html')
    
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(html_complet)

    print("Le fichier groups.html a été généré avec succès.")

@app.route('/')
def index():
    generer_groups_html()
    # Retourner le fichier HTML depuis le dossier 'static'
    static_path = os.path.join(os.path.dirname(__file__), '..', 'static')
    return send_from_directory(static_path, 'groups.html')

def save_data(data):
    logging.info("Début de la fonction save_data")
    try:
        # Chemin absolu à la base de données
        db_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'saisie.db')
        
        with sqlite3.connect(db_path) as conn:
            conn.execute("BEGIN TRANSACTION")
            cursor = conn.cursor()
            
            logging.debug("Connexion à la base de données établie")
            
            # Vide la table liste
            cursor.execute("DELETE FROM liste")
            logging.info("Table 'liste' vidée avec succès")
            
            for key, value in data.items():
                logging.debug(f"Traitement de la clé : {key}, valeur : {value}")
                if key.startswith('groupes_'):
                    _, jour, heure = key.split('_')
                    nombre_groupes = int(value)
                    
                    logging.info(f"Traitement des données pour le jour {jour} à {heure}")
                    
                    # Récupère les candidats pour ce jour et cette heure
                    cursor.execute("""
                        SELECT serie, ordre, massar, nom
                        FROM saisie
                        WHERE jour = ? AND heure = ?
                        ORDER BY numero
                    """, (jour, heure))
                    
                    candidats = cursor.fetchall()
                    nombre_candidats = len(candidats)
                    logging.debug(f"Nombre de candidats trouvés : {nombre_candidats}")
                    
                    if nombre_groupes < 1 or nombre_groupes > nombre_candidats:
                        raise ValueError(f"Le nombre de groupes ({nombre_groupes}) est invalide pour {nombre_candidats} candidats le {jour} à {heure}.")
                    
                    taille_groupe = math.ceil(nombre_candidats / nombre_groupes)
                    
                    for i, candidat in enumerate(candidats):
                        serie, ordre, massar, nom = candidat
                        numliste = (i // taille_groupe) + 1
                        # Récupère le numéro à partir de la première colonne de saisie
                        cursor.execute("""
                            SELECT numero
                            FROM saisie
                            WHERE jour = ? AND heure = ? AND serie = ? AND ordre = ? AND massar = ?
                        """, (jour, heure, serie, ordre, massar))
                        numero = cursor.fetchone()[0]

                        logging.debug(f"Insertion : jour={jour}, heure={heure}, serie={serie}, ordre={ordre}, massar={massar}, nom={nom}, numliste={numliste}, numero={numero}")
                        cursor.execute("""
                            INSERT INTO liste (jour, heure, serie, ordre, massar, nom, numliste, numero)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        """, (jour, heure, serie, ordre, massar, nom, numliste, numero))
            
            conn.commit()
            logging.info("Données enregistrées avec succès.")
        return "Données enregistrées avec succès."
    except sqlite3.Error as e:
        conn.rollback()
        logging.error(f"Erreur SQLite lors de l'enregistrement des données : {str(e)}")
        return f"Erreur SQLite lors de l'enregistrement des données : {str(e)}"
    except ValueError as e:
        conn.rollback()
        logging.error(f"Erreur de validation des données : {str(e)}")
        return f"Erreur de validation des données : {str(e)}"
    except Exception as e:
        conn.rollback()
        logging.error(f"Erreur inattendue lors de l'enregistrement des données : {str(e)}", exc_info=True)
        return f"Erreur inattendue lors de l'enregistrement des données : {str(e)}"

@app.route('/save_data', methods=['POST'])
def handle_save_data():
    logging.info("Requête reçue sur /save_data")
    try:
        data = request.json
        logging.debug(f"Données reçues : {data}")
        result = save_data(data)
        if result.startswith("Erreur"):
            logging.error(f"Erreur retournée : {result}")
            return jsonify({"success": False, "error": result}), 500
        else:
            logging.info("Données sauvegardées avec succès")
            return jsonify({"success": True, "message": result}), 200
    except Exception as e:
        logging.error(f"Erreur inattendue lors de la gestion des données : {str(e)}", exc_info=True)
        return jsonify({"success": False, "error": f"Erreur inattendue : {str(e)}"}), 500

@app.route('/groups')
def groups_page():
    generer_groups_html()
    # Retourner le fichier HTML depuis le dossier 'static'
    static_path = os.path.join(os.path.dirname(__file__), '..', 'static')
    return send_from_directory(static_path, 'groups.html')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
