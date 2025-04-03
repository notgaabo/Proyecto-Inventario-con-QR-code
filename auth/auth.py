# auth/auth.py
from flask import session
import bcrypt
from db.config import Config

class Auth:
    @staticmethod
    def authenticate_user(username, password):
        """
        Autentica a un usuario verificando su nombre de usuario y contraseña.
        Devuelve el usuario como diccionario si es válido, 'disabled' si está inactivo, o None si falla.
        """
        try:
            with Config.get_db_connection() as connection:
                with connection.cursor(dictionary=True) as cursor:
                    cursor.execute(
                        "SELECT u.id, u.username, u.email, u.password, u.role, u.is_active, u.company_id "
                        "FROM users u "
                        "WHERE u.username = %s",
                        (username,)
                    )
                    user = cursor.fetchone()
                    if not user:
                        return None
                    # Verificar contraseña con bcrypt
                    if not bcrypt.checkpw(password.encode('utf-8'), user['password'].encode('utf-8')):
                        return None
                    if user['is_active'] == 0:
                        return 'disabled'
                    return user  # Devuelve el diccionario con 'role' como string
        except Exception as e:
            print(f"Error authenticating user: {e}")
            return None

    @staticmethod
    def login_user(user):
        """
        Configura la sesión del usuario tras autenticación exitosa.
        """
        session['user'] = {
            'id': user['id'],
            'username': user['username'],
            'email': user.get('email', ''),
            'role': user['role'],  # 'vendedor', 'encargado de almacén', 'gerente', o 'admin'
            'company_id': user.get('company_id'),
            'is_active': user.get('is_active', 1)
        }

    @staticmethod
    def is_authenticated():
        """
        Verifica si hay un usuario autenticado en la sesión.
        """
        return 'user' in session

    @staticmethod
    def logout_user():
        """
        Cierra la sesión del usuario eliminando todos los datos de la sesión.
        """
        session.clear()

class Company:
    @staticmethod
    def insert_company(name, industry, address, phone):
        """
        Inserta una nueva empresa en la base de datos y devuelve su ID.
        """
        try:
            with Config.get_db_connection() as connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        "INSERT INTO companies (name, industry, address, phone, is_active) "
                        "VALUES (%s, %s, %s, %s, %s)",
                        (name, industry, address, phone, 1)
                    )
                    connection.commit()
                    cursor.execute("SELECT LAST_INSERT_ID()")
                    return cursor.fetchone()[0]
        except Exception as e:
            print(f"Error en insert_company: {str(e)}")
            raise

    @staticmethod
    def get_company_by_id(company_id):
        """
        Obtiene los detalles de una empresa por su ID.
        """
        try:
            with Config.get_db_connection() as connection:
                with connection.cursor(dictionary=True) as cursor:
                    cursor.execute(
                        "SELECT id, name, industry, address, phone, is_active "
                        "FROM companies WHERE id = %s",
                        (company_id,)
                    )
                    return cursor.fetchone()
        except Exception as e:
            print(f"Error en get_company_by_id: {str(e)}")
            return None

class User:
    @staticmethod
    def insert_user(username, email, password, role, company_id):
        """
        Inserta un nuevo usuario en la base de datos con una contraseña hasheada usando bcrypt.
        """
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        try:
            with Config.get_db_connection() as connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        "INSERT INTO users (username, email, password, role, company_id, is_active) "
                        "VALUES (%s, %s, %s, %s, %s, %s)",
                        (username, email, hashed_password, role, company_id, 1)
                    )
                    connection.commit()
        except Exception as e:
            print(f"Error en insert_user: {str(e)}")
            raise

    @staticmethod
    def get_users_by_company(company_id):
        """
        Obtiene todos los usuarios activos de una empresa específica.
        """
        try:
            with Config.get_db_connection() as connection:
                with connection.cursor(dictionary=True) as cursor:
                    cursor.execute(
                        "SELECT id, username, email, role, is_active "
                        "FROM users WHERE company_id = %s AND is_active = 1",
                        (company_id,)
                    )
                    return cursor.fetchall()
        except Exception as e:
            print(f"Error en get_users_by_company: {str(e)}")
            return []

    @staticmethod
    def get_user_by_id(user_id):
        """
        Obtiene los detalles de un usuario por su ID.
        """
        try:
            with Config.get_db_connection() as connection:
                with connection.cursor(dictionary=True) as cursor:
                    cursor.execute(
                        "SELECT id, username, email, role, company_id, is_active "
                        "FROM users WHERE id = %s",
                        (user_id,)
                    )
                    return cursor.fetchone()
        except Exception as e:
            print(f"Error en get_user_by_id: {str(e)}")
            return None

    @staticmethod
    def update_user(user_id, username, email, password, role):
        """
        Actualiza los detalles de un usuario, con opción de cambiar la contraseña.
        """
        try:
            with Config.get_db_connection() as connection:
                with connection.cursor() as cursor:
                    if password:
                        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
                        cursor.execute(
                            "UPDATE users "
                            "SET username = %s, email = %s, password = %s, role = %s "
                            "WHERE id = %s",
                            (username, email, hashed_password, role, user_id)
                        )
                    else:
                        cursor.execute(
                            "UPDATE users "
                            "SET username = %s, email = %s, role = %s "
                            "WHERE id = %s",
                            (username, email, role, user_id)
                        )
                    connection.commit()
        except Exception as e:
            print(f"Error en update_user: {str(e)}")
            raise

    @staticmethod
    def toggle_user_status(user_id):
        """
        Cambia el estado activo/inactivo de un usuario.
        """
        try:
            with Config.get_db_connection() as connection:
                with connection.cursor(dictionary=True) as cursor:
                    cursor.execute("SELECT is_active FROM users WHERE id = %s", (user_id,))
                    user = cursor.fetchone()
                    if user:
                        new_status = 0 if user["is_active"] == 1 else 1
                        cursor.execute(
                            "UPDATE users SET is_active = %s WHERE id = %s",
                            (new_status, user_id)
                        )
                        connection.commit()
        except Exception as e:
            print(f"Error en toggle_user_status: {str(e)}")
            raise