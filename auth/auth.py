 # auth/auth.py


from flask import session
import bcrypt
from db.config import Config 

class Auth:
    @staticmethod
    def authenticate_user(username, password):
        connection = Config.get_db_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
        user = cursor.fetchone()
        
        if user:
            if user['is_active'] == 0:
                return 'disabled'  # Usuario deshabilitado
            if bcrypt.checkpw(password.encode('utf-8'), user['password'].encode('utf-8')):
                return user
        return None

    @staticmethod
    def login_user(user):
        session['user'] = {
            'id': user['id'],
            'username': user['username'],
            'role': user['role'],
        }
        print(session)

    @staticmethod
    def is_authenticated():
        return 'user' in session

    @staticmethod
    def logout_user():
        session.clear()

class User:
    @staticmethod
    def insert_user(username, password, role):
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        connection = Config.get_db_connection()
        cursor = connection.cursor()
        cursor.execute("""
            INSERT INTO users (username, password, role)
            VALUES (%s, %s, %s)
        """, (username, hashed_password, role))
        connection.commit()

    @staticmethod
    def get_user():
        connection = Config.get_db_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE is_active = 1")  # Filtramos solo los usuarios activos
        users = cursor.fetchall()
        cursor.close()
        connection.close()
        return users


    @staticmethod
    def update_user(user_id, username, password, role):
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        connection = Config.get_db_connection()
        cursor = connection.cursor()
        cursor.execute("""
            UPDATE users
            SET username = %s, password = %s, role = %s
            WHERE id = %s
        """, (username, hashed_password, role, user_id))
        connection.commit()

    @staticmethod
    def get_disabled_users():
        connection = Config.get_db_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE is_active = 0")  # Filtramos solo los usuarios desactivados
        disabled_users = cursor.fetchall()
        cursor.close()  # Cerrar cursor
        connection.close()  # Cerrar conexión
        return disabled_users


    @staticmethod
    def deactivate_user(user_id):
        connection = Config.get_db_connection()
        cursor = connection.cursor()
        cursor.execute("UPDATE users SET is_active = 0 WHERE id = %s", (user_id,))
        connection.commit()
        cursor.close()
        connection.close()

    @staticmethod
    def activate_user(user_id):
        connection = Config.get_db_connection()
        cursor = connection.cursor()
        cursor.execute("UPDATE users SET is_active = 1 WHERE id = %s", (user_id,))
        connection.commit()
        cursor.close()
        connection.close()

    @staticmethod
    def toggle_user_status(user_id):
        connection = Config.get_db_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT is_active FROM users WHERE id = %s", (user_id,))
        user = cursor.fetchone()

        if user:
            new_status = 0 if user["is_active"] == 1 else 1
            cursor.execute("UPDATE users SET is_active = %s WHERE id = %s", (new_status, user_id))
            connection.commit()
        cursor.close()
        connection.close()

    @staticmethod
    def enable_user_in_db(user_id):
        connection = Config.get_db_connection()
        cursor = connection.cursor()
        cursor.execute("UPDATE users SET is_active = 1 WHERE id = %s", (user_id,))
        connection.commit()
        cursor.close()
        connection.close()
