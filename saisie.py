import os
import sqlite3
from flask import request, jsonify, send_from_directory, current_app

def get_db_connection(app):
    db_path = os.path.join(app.root_path, 'data', 'saisie.db')
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def init_app(app):
    @app.route('/api/data', methods=['GET'])
    def get_data():
        conn = get_db_connection(app)
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT * FROM saisie")
            rows = cursor.fetchall()
            data = [{key: row[key] if row[key] is not None else '' for key in row.keys()} for row in rows]
            return jsonify(data)
        except Exception as e:
            app.logger.error(f"Error fetching data: {e}")
            return jsonify({"error": "Failed to fetch data"}), 500
        finally:
            conn.close()

    @app.route('/api/data', methods=['PUT'])
    def update_data():
        updates = request.json
        conn = get_db_connection(app)
        cursor = conn.cursor()
        try:
            for update in updates:
                cursor.execute('''
                    UPDATE saisie
                    SET gym = ?, course = ?, poid = ?, saut = ?
                    WHERE numero = ?
                ''', (update['gym'], update['course'], update['poid'], update['saut'], update['numero']))
            conn.commit()
            return jsonify({"success": "تم الحفظ بنجاح"})
        except Exception as e:
            app.logger.error(f"Error updating data: {e}")
            conn.rollback()
            return jsonify({"error": "Failed to update data"}), 500
        finally:
            conn.close()

    @app.route('/index')
    def index():
        try:
            return send_from_directory(os.path.join(app.root_path, 'static'), 'index.html')
        except Exception as e:
            app.logger.error(f"Error serving index.html: {e}")
            return jsonify({"error": "Failed to serve index.html"}), 500

    app.logger.info("Saisie module initialized")

if __name__ == '__main__':
    from flask import Flask
    app = Flask(__name__)
    init_app(app)
    app.run(debug=True)