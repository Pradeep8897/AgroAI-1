from backend.database.mysql_connection import get_connection

class DiseaseModel:
    @staticmethod
    def get_disease_by_name(name):
        conn, is_sqlite = get_connection()
        cursor = conn.cursor()
        try:
            if is_sqlite:
                cursor.execute("SELECT * FROM diseases WHERE name = ?", (name,))
            else:
                cursor.execute("SELECT * FROM diseases WHERE name = %s", (name,))
            row = cursor.fetchone()
            if row:
                return dict(row) if is_sqlite else {
                    "id": row[0],
                    "name": row[1],
                    "severity": row[2],
                    "cause": row[3],
                    "chemical_cure": row[4],
                    "organic_cure": row[5]
                }
            return None
        finally:
            conn.close()

    @staticmethod
    def save_report(user_id, crop_name, disease_name, severity, image_path):
        conn, is_sqlite = get_connection()
        cursor = conn.cursor()
        try:
            if is_sqlite:
                cursor.execute(
                    "INSERT INTO disease_reports (user_id, crop_name, disease_name, severity, image_path, status) VALUES (?, ?, ?, ?, ?, 'completed')",
                    (user_id, crop_name, disease_name, severity, image_path)
                )
            else:
                cursor.execute(
                    "INSERT INTO disease_reports (user_id, crop_name, disease_name, severity, image_path, status) VALUES (%s, %s, %s, %s, %s, 'completed')",
                    (user_id, crop_name, disease_name, severity, image_path)
                )
            conn.commit()
            return cursor.lastrowid
        except Exception as e:
            print(f"Error saving disease report: {e}")
            return None
        finally:
            conn.close()

    @staticmethod
    def get_reports_by_user(user_id):
        conn, is_sqlite = get_connection()
        cursor = conn.cursor()
        try:
            if is_sqlite:
                cursor.execute("SELECT * FROM disease_reports WHERE user_id = ? ORDER BY created_at DESC", (user_id,))
            else:
                cursor.execute("SELECT * FROM disease_reports WHERE user_id = %s ORDER BY created_at DESC", (user_id,))
            rows = cursor.fetchall()
            if is_sqlite:
                return [dict(r) for r in rows]
            else:
                return [{
                    "id": r[0],
                    "user_id": r[1],
                    "crop_name": r[2],
                    "disease_name": r[3],
                    "severity": r[4],
                    "image_path": r[5],
                    "status": r[6],
                    "created_at": r[7]
                } for r in rows]
        finally:
            conn.close()
