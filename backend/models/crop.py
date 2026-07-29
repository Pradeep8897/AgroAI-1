from backend.database.mysql_connection import get_connection

class CropModel:
    @staticmethod
    def save_recommendation(user_id, name, N, P, K, ph, temp, hum, rain, prediction):
        conn, is_sqlite = get_connection()
        cursor = conn.cursor()
        try:
            if is_sqlite:
                cursor.execute(
                    "INSERT INTO crops (user_id, name, N, P, K, ph, temperature, humidity, rainfall, prediction) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (user_id, name, N, P, K, ph, temp, hum, rain, prediction)
                )
            else:
                cursor.execute(
                    "INSERT INTO crops (user_id, name, N, P, K, ph, temperature, humidity, rainfall, prediction) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                    (user_id, name, N, P, K, ph, temp, hum, rain, prediction)
                )
            conn.commit()
            return cursor.lastrowid
        except Exception as e:
            print(f"Error saving crop recommendation: {e}")
            return None
        finally:
            conn.close()

    @staticmethod
    def get_history_by_user(user_id):
        conn, is_sqlite = get_connection()
        cursor = conn.cursor()
        try:
            if is_sqlite:
                cursor.execute("SELECT * FROM crops WHERE user_id = ? ORDER BY created_at DESC", (user_id,))
            else:
                cursor.execute("SELECT * FROM crops WHERE user_id = %s ORDER BY created_at DESC", (user_id,))
            rows = cursor.fetchall()
            if is_sqlite:
                return [dict(r) for r in rows]
            else:
                return [{
                    "id": r[0],
                    "user_id": r[1],
                    "name": r[2],
                    "N": r[3],
                    "P": r[4],
                    "K": r[5],
                    "ph": r[6],
                    "temperature": r[7],
                    "humidity": r[8],
                    "rainfall": r[9],
                    "prediction": r[10],
                    "created_at": r[11]
                } for r in rows]
        finally:
            conn.close()
