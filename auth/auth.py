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
    def insert_user(username, email, password, role):
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        connection = Config.get_db_connection()
        cursor = connection.cursor()
        cursor.execute("""
            INSERT INTO users (username, email, password, role)
            VALUES (%s, %s, %s, %s)
        """, (username, email, hashed_password, role))
        connection.commit()
        cursor.close()
        connection.close()

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
    def get_user_by_id(user_id):
        connection = Config.get_db_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
        user = cursor.fetchone()
        cursor.close()
        connection.close()
        return user

    @staticmethod
    def update_user(user_id, username, email, password, role):
        connection = Config.get_db_connection()
        cursor = connection.cursor()
        if password:
            hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
            cursor.execute("""
                UPDATE users
                SET username = %s, email = %s, password = %s, role = %s
                WHERE id = %s
            """, (username, email, hashed_password, role, user_id))
        else:
            cursor.execute("""
                UPDATE users
                SET username = %s, role = %s
                WHERE id = %s
            """, (username, role, user_id))
        connection.commit()
        cursor.close()
        connection.close()

    @staticmethod
    def get_disabled_users():
        connection = Config.get_db_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE is_active = 0")  # Filtramos solo los usuarios desactivados
        disabled_users = cursor.fetchall()
        cursor.close()
        connection.close()
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
