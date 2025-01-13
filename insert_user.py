import bcrypt
import mysql.connector

# Función para obtener la conexión a la base de datos
def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="yoensi1881",  # Cambia a tu contraseña
        database="final_project"  # Cambia al nombre de tu base de datos
    )

# Función para encriptar la contraseña
def hash_password(password):
    # Generamos el salt
    salt = bcrypt.gensalt()
    # Encriptamos la contraseña
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed_password

# Función para insertar un usuario con contraseña encriptada
def insert_user(username, password, role):
    connection = get_db_connection()
    cursor = connection.cursor()

    # Hasheamos la contraseña antes de insertarla
    hashed_password = hash_password(password)

    # Ejecutamos el query para insertar el usuario
    query = """
    INSERT INTO users (username, password, role)
    VALUES (%s, %s, %s)
    """
    cursor.execute(query, (username, hashed_password, role))

    # Confirmamos los cambios en la base de datos
    connection.commit()

    # Cerramos la conexión
    cursor.close()
    connection.close()

    print(f"Usuario '{username}' insertado correctamente con la contraseña hasheada.")

# Inserta un usuario (puedes cambiar estos valores para probar)
insert_user('admini', 'adminpassword', 'admin')
insert_user('userr1', 'userpassword', 'user')
