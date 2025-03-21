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
                cursor.close()
                connection.close()
                return 'disabled'  # Usuario deshabilitado
            if bcrypt.checkpw(password.encode('utf-8'), user['password'].encode('utf-8')):
                cursor.close()
                connection.close()
                return user
        cursor.close()
        connection.close()
        return None

    @staticmethod
    def login_user(user):
        session['user'] = {
            'id': user['id'],
            'username': user['username'],
            'role': user['role'],  # Use role (varchar) from users table
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
    def insert_user(username, email, password, role_id):
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        connection = Config.get_db_connection()
        cursor = connection.cursor()
        # Fetch role name and consume result
        cursor.execute("SELECT name FROM roles WHERE id = %s", (role_id,))
        role_row = cursor.fetchone()
        role = role_row[0] if role_row else None
        # Ensure no unread results by consuming or using a new cursor
        cursor.execute("""
            INSERT INTO users (username, email, password, role, role_id)
            VALUES (%s, %s, %s, %s, %s)
        """, (username, email, hashed_password, role, role_id))  # Fixed placeholder count
        connection.commit()
        cursor.close()
        connection.close()

    @staticmethod
    def get_user():
        connection = Config.get_db_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE is_active = 1")
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
    def update_user(user_id, username, email, password, role_id):
        connection = Config.get_db_connection()
        cursor = connection.cursor()
        cursor.execute("SELECT name FROM roles WHERE id = %s", (role_id,))
        role_row = cursor.fetchone()
        role = role_row[0] if role_row else None
        if password:
            hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
            cursor.execute("""
                UPDATE users
                SET username = %s, email = %s, password = %s, role = %s, role_id = %s
                WHERE id = %s
            """, (username, email, hashed_password, role, role_id, user_id))
        else:
            cursor.execute("""
                UPDATE users
                SET username = %s, email = %s, role = %s, role_id = %s
                WHERE id = %s
            """, (username, email, role, role_id, user_id))
        connection.commit()
        cursor.close()
        connection.close()

    @staticmethod
    def get_disabled_users():
        connection = Config.get_db_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE is_active = 0")
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