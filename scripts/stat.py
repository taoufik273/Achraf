import sqlite3
import pandas as pd
from flask import Flask, send_from_directory
import logging
import os

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

app = Flask(__name__)

def format_float(value):
    if pd.isnull(value):
        return "-"
    return f"{value:.2f}"

def generer_statistiques_html():
    db_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'saisie.db')
    
    with sqlite3.connect(db_path) as conn:
        query = """
            SELECT 
                s.jour as 'يوم الامتحان',
                s.heure as 'ساعة الامتحان',
                s.serie as 'المسلك',
                COUNT(DISTINCT s.massar) as 'عدد المترشحين',
                SUM(CASE WHEN s.moyen NOT IN ('إعفاء', 'غياب') THEN 1 ELSE 0 END) as 'عدد الممتحنين',
                SUM(CASE WHEN s.moyen = 'إعفاء' THEN 1 ELSE 0 END) as 'عدد المعفيين',
                SUM(CASE WHEN s.moyen = 'غياب' THEN 1 ELSE 0 END) as 'عدد الغائبين',
                MAX(CASE WHEN s.moyen NOT IN ('إعفاء', 'غياب') THEN CAST(s.moyen AS FLOAT) ELSE NULL END) as 'أعلى نقطة',
                MIN(CASE WHEN s.moyen NOT IN ('إعفاء', 'غياب') THEN CAST(s.moyen AS FLOAT) ELSE NULL END) as 'أدنى نقطة',
                AVG(CASE WHEN s.moyen NOT IN ('إعفاء', 'غياب') THEN CAST(s.moyen AS FLOAT) ELSE NULL END) as 'متوسط النقط',
                SUM(CASE WHEN s.moyen NOT IN ('إعفاء', 'غياب') AND CAST(s.moyen AS FLOAT) < 5 THEN 1 ELSE 0 END) as 'عدد المترشحين أقل من 5',
                SUM(CASE WHEN s.moyen NOT IN ('إعفاء', 'غياب') AND CAST(s.moyen AS FLOAT) >= 5 AND CAST(s.moyen AS FLOAT) < 10 THEN 1 ELSE 0 END) as 'عدد المترشحين بين 5 و 10',
                SUM(CASE WHEN s.moyen NOT IN ('إعفاء', 'غياب') AND CAST(s.moyen AS FLOAT) >= 10 AND CAST(s.moyen AS FLOAT) < 15 THEN 1 ELSE 0 END) as 'عدد المترشحين بين 10 و 15',
                SUM(CASE WHEN s.moyen NOT IN ('إعفاء', 'غياب') AND CAST(s.moyen AS FLOAT) >= 15 THEN 1 ELSE 0 END) as 'عدد المترشحين 15 فما فوق'
            FROM 
                notes s
            GROUP BY 
                s.jour, s.heure, s.serie
            ORDER BY 
                s.jour, s.heure, s.serie
        """
        df = pd.read_sql_query(query, conn)

    # Trier le DataFrame par jour, heure, et série
    df = df.sort_values(['يوم الامتحان', 'ساعة الامتحان', 'المسلك'])

    # Création du DataFrame résumé
    df_resume = df.groupby('المسلك').agg({
        'عدد المترشحين': 'sum',
        'عدد الممتحنين': 'sum',
        'أعلى نقطة': 'max',
        'أدنى نقطة': 'min',
        'متوسط النقط': 'mean',
        'عدد المترشحين أقل من 5': 'sum',
        'عدد المترشحين بين 5 و 10': 'sum',
        'عدد المترشحين بين 10 و 15': 'sum',
        'عدد المترشحين 15 فما فوق': 'sum',
        'عدد المعفيين': 'sum',
        'عدد الغائبين': 'sum'
    }).reset_index()

    # Calcul des totaux
    total_row = pd.DataFrame(df_resume[['عدد المترشحين', 'عدد الممتحنين', 'عدد المعفيين', 'عدد الغائبين', 'عدد المترشحين أقل من 5', 'عدد المترشحين بين 5 و 10', 'عدد المترشحين بين 10 و 15', 'عدد المترشحين 15 فما فوق']].sum()).transpose()
    total_row['المسلك'] = 'مجموع'
    total_row['أعلى نقطة'] = df_resume['أعلى نقطة'].max()
    total_row['أدنى نقطة'] = df_resume['أدنى نقطة'].min()
    total_row['متوسط النقط'] = df_resume['متوسط النقط'].mean()

    # Ajouter la ligne de total au DataFrame résumé
    df_resume = pd.concat([df_resume, total_row], ignore_index=True)

    # Trier le DataFrame résumé par nombre de candidats décroissant
    df_resume = df_resume.sort_values('عدد المترشحين', ascending=False)

    def generate_html_table(df, include_date_time=True):
        html = '<table dir="rtl">\n'
        if include_date_time:
            headers = ['يوم الامتحان', 'ساعة الامتحان', 'المسلك', 'عدد المترشحين', 'عدد الممتحنين', 'عدد المعفيين', 'عدد الغائبين', 'أعلى نقطة', 'أدنى نقطة', 'متوسط النقط', 
                       'عدد المترشحين أقل من 5', 'عدد المترشحين بين 5 و 10', 
                       'عدد المترشحين بين 10 و 15', 'عدد المترشحين 15 فما فوق']
        else:
            headers = ['المسلك', 'عدد المترشحين', 'عدد الممتحنين', 'عدد المعفيين', 'عدد الغائبين', 'أعلى نقطة', 'أدنى نقطة', 'متوسط النقط', 
                       'عدد المترشحين أقل من 5', 'عدد المترشحين بين 5 و 10', 
                       'عدد المترشحين بين 10 و 15', 'عدد المترشحين 15 فما فوق']
        
        html += '<tr>' + ''.join(f'<th>{header}</th>' for header in headers) + '</tr>\n'
        
        if include_date_time:
            colors = ['lightblue', 'lightgreen']
        else:
            colors = ['lightpink', 'lavender']
        
        color_index = 0
        current_day = None
        rowspan_counts = df['يوم الامتحان'].value_counts().to_dict() if 'يوم الامتحان' in df.columns else {}

        for index, row in df.iterrows():
            if include_date_time and row.get('يوم الامتحان') != current_day:
                current_day = row.get('يوم الامتحان')
                color_index = (color_index + 1) % 2
            elif not include_date_time:
                color_index = (color_index + 1) % 2
            
            color = colors[color_index]

            if row.get('المسلك') == 'مجموع':
                color = 'lightblue'
                bold = 'font-weight: bold;'
            else:
                bold = ''
            
            html += f'<tr style="background-color: {color}; {bold}">'
            if include_date_time:
                if rowspan_counts.get(row.get('يوم الامتحان'), 0) > 0:
                    html += f'<td rowspan="{rowspan_counts.get(row.get("يوم الامتحان"), 0)}">{row.get("يوم الامتحان")}</td>'
                    rowspan_counts[row.get('يوم الامتحان')] = 0
                html += f'<td>{row.get("ساعة الامتحان")}</td>'
            html += f'<td>{row.get("المسلك")}</td>'
            html += f'<td><strong>{row.get("عدد المترشحين")}</strong></td>'
            html += f'<td><strong>{row.get("عدد الممتحنين")}</strong></td>'
            html += f'<td><strong>{row.get("عدد المعفيين")}</strong></td>'
            html += f'<td><strong>{row.get("عدد الغائبين")}</strong></td>'
            html += f'<td>{format_float(row.get("أعلى نقطة"))}</td>'
            html += f'<td>{format_float(row.get("أدنى نقطة"))}</td>'
            html += f'<td>{format_float(row.get("متوسط النقط"))}</td>'
            html += f'<td>{row.get("عدد المترشحين أقل من 5")}</td>'
            html += f'<td>{row.get("عدد المترشحين بين 5 و 10")}</td>'
            html += f'<td>{row.get("عدد المترشحين بين 10 و 15")}</td>'
            html += f'<td>{row.get("عدد المترشحين 15 فما فوق")}</td>'
            html += '</tr>\n'
        
        html += '</table>\n'
        return html

    html_content = """
    <html lang="ar" dir="rtl">
    <head>
        <meta charset="UTF-8">
        <title>إحصائيات</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                direction: rtl;
            }}
            table {{
                border-collapse: collapse;
                width: 100%;
                margin-bottom: 20px;
            }}
            th, td {{
                border: 1px solid black;
                padding: 8px;
                text-align: center;
            }}
            th {{
                background-color: #f2f2f2;
            }}
            h2 {{
                margin-top: 30px;
            }}
        </style>
    </head>
    <body>
        <h1>إحصائيات</h1>
        <h2>إحصائيات مفصلة</h2>
        {table_detailed}
        <h2>ملخص الإحصائيات</h2>
        {table_summary}
    </body>
    </html>
    """

    table_detailed = generate_html_table(df, include_date_time=True)
    table_summary = generate_html_table(df_resume, include_date_time=False)
    html_complet = html_content.format(table_detailed=table_detailed, table_summary=table_summary)

    html_path = os.path.join(os.path.dirname(__file__), '..', 'static', 'statistiques.html')
    
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(html_complet)

    print("Le fichier statistiques.html a été généré avec succès.")

@app.route('/')
def index():
    generer_statistiques_html()
    static_path = os.path.join(os.path.dirname(__file__), '..', 'static')
    return send_from_directory(static_path, 'statistiques.html')

if __name__ == '__main__':
    app.run(debug=True)
