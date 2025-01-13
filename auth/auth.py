from flask import session
import mysql.connector
import bcrypt

# Función para obtener la conexión a la base de datos
def get_db_connection():
    connection = mysql.connector.connect(
        host="localhost",
        user="root",
        password="yoensi1881",  # Cambia a tu contraseña
        database="final_project"  # Nombre de tu base de datos
    )
    return connection

# Función para verificar las credenciales del usuario
def authenticate_user(username, password):
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
    user = cursor.fetchone()
    
    if user and bcrypt.checkpw(password.encode('utf-8'), user['password'].encode('utf-8')):
        return user
    return None

# Función para guardar el usuario en la sesión
def login_user(user):
    # Guardar los datos necesarios del usuario en la sesión
    session['user'] = {
        'id': user['id'],
        'username': user['username'],
        'role': user['role'],
    }
    print(session)  # Depuración para verificar que los datos se guardan correctamente

# Función para verificar si un usuario está logueado
def is_authenticated():
    return 'user' in session

# Función para cerrar sesión
def logout_user():
    session.clear()  # Limpiar la sesión

# Función para insertar un usuario (hasheando la contraseña)
def insertar_usuario(username, password, role):
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())  # Hasheando la contraseña
    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute("""
        INSERT INTO users (username, password, role)
        VALUES (%s, %s, %s)
    """, (username, hashed_password, role))
    connection.commit()

# Función para obtener todos los usuarios
def obtener_usuarios():
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users")
    usuarios = cursor.fetchall()
    return usuarios

# Función para actualizar los datos de un usuario
def actualizar_usuario(user_id, username, password, role):
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())  # Hasheando la contraseña
    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute("""
        UPDATE users
        SET username = %s, password = %s, role = %s
        WHERE id = %s
    """, (username, hashed_password, role, user_id))
    connection.commit()

# Función para eliminar un usuario
def eliminar_usuario(user_id):
    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
    connection.commit()
