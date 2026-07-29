from backend.database.mysql_connection import get_connection

class MarketModel:
    @staticmethod
    def get_prices_by_crop(crop_name):
        conn, is_sqlite = get_connection()
        cursor = conn.cursor()
        try:
            if is_sqlite:
                cursor.execute("SELECT * FROM market_prices WHERE crop_name LIKE ?", (f"%{crop_name}%",))
            else:
                cursor.execute("SELECT * FROM market_prices WHERE crop_name LIKE %s", (f"%{crop_name}%",))
            rows = cursor.fetchall()
            if is_sqlite:
                return [dict(r) for r in rows]
            else:
                return [{
                    "id": r[0],
                    "crop_name": r[1],
                    "market_name": r[2],
                    "state": r[3],
                    "current_price": r[4],
                    "predicted_price": r[5],
                    "date": r[6]
                } for r in rows]
        finally:
            conn.close()

    @staticmethod
    def get_all_prices():
        conn, is_sqlite = get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT * FROM market_prices ORDER BY current_price DESC")
            rows = cursor.fetchall()
            if is_sqlite:
                return [dict(r) for r in rows]
            else:
                return [{
                    "id": r[0],
                    "crop_name": r[1],
                    "market_name": r[2],
                    "state": r[3],
                    "current_price": r[4],
                    "predicted_price": r[5],
                    "date": r[6]
                } for r in rows]
        finally:
            conn.close()
