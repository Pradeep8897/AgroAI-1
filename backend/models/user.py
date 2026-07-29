from backend.database.mysql_connection import get_connection
from werkzeug.security import generate_password_hash, check_password_hash

class UserModel:
    @staticmethod
    def create_user(username, email, password, role='farmer'):
        conn, is_sqlite = get_connection()
        cursor = conn.cursor()
        hashed_password = generate_password_hash(password)
        try:
            if is_sqlite:
                cursor.execute(
                    "INSERT INTO users (username, email, password, role) VALUES (?, ?, ?, ?)",
                    (username, email, hashed_password, role)
                )
            else:
                cursor.execute(
                    "INSERT INTO users (username, email, password, role) VALUES (%s, %s, %s, %s)",
                    (username, email, hashed_password, role)
                )
            conn.commit()
            user_id = cursor.lastrowid
            return user_id
        except Exception as e:
            print(f"Error creating user: {e}")
            return None
        finally:
            conn.close()

    @staticmethod
    def get_user_by_email(email):
        conn, is_sqlite = get_connection()
        cursor = conn.cursor()
        try:
            if is_sqlite:
                cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
            else:
                cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
            row = cursor.fetchone()
            if row:
                return dict(row) if is_sqlite else {
                    "id": row[0],
                    "username": row[1],
                    "email": row[2],
                    "password": row[3],
                    "role": row[4],
                    "phone": row[5],
                    "location": row[6],
                    "state": row[7],
                    "farm_size": row[8],
                    "language": row[9],
                    "created_at": row[10]
                }
            return None
        finally:
            conn.close()

    @staticmethod
    def get_user_by_id(user_id):
        conn, is_sqlite = get_connection()
        cursor = conn.cursor()
        try:
            if is_sqlite:
                cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
            else:
                cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
            row = cursor.fetchone()
            if row:
                return dict(row) if is_sqlite else {
                    "id": row[0],
                    "username": row[1],
                    "email": row[2],
                    "password": row[3],
                    "role": row[4],
                    "phone": row[5],
                    "location": row[6],
                    "state": row[7],
                    "farm_size": row[8],
                    "language": row[9],
                    "created_at": row[10]
                }
            return None
        finally:
            conn.close()

    @staticmethod
    def update_profile(user_id, username, email, phone, location, state, farm_size, language):
        conn, is_sqlite = get_connection()
        cursor = conn.cursor()
        try:
            if is_sqlite:
                cursor.execute(
                    "UPDATE users SET username = ?, email = ?, phone = ?, location = ?, state = ?, farm_size = ?, language = ? WHERE id = ?",
                    (username, email, phone, location, state, farm_size, language, user_id)
                )
            else:
                cursor.execute(
                    "UPDATE users SET username = %s, email = %s, phone = %s, location = %s, state = %s, farm_size = %s, language = %s WHERE id = %s",
                    (username, email, phone, location, state, farm_size, language, user_id)
                )
            conn.commit()
            return True
        except Exception as e:
            print(f"Error updating user: {e}")
            return False
        finally:
            conn.close()

    @staticmethod
    def update_password(user_id, new_password):
        conn, is_sqlite = get_connection()
        cursor = conn.cursor()
        hashed = generate_password_hash(new_password)
        try:
            if is_sqlite:
                cursor.execute("UPDATE users SET password = ? WHERE id = ?", (hashed, user_id))
            else:
                cursor.execute("UPDATE users SET password = %s WHERE id = %s", (hashed, user_id))
            conn.commit()
            return True
        except Exception as e:
            print(f"Error updating password: {e}")
            return False
        finally:
            conn.close()
