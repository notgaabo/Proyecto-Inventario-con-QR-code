# db/__init__.py

import mysql.connector

def get_db_connection():
    connection = mysql.connector.connect(
        host='localhost',  # Cambia estos valores según tu configuración
        user='root',
        password='yoensi1881',
        database='final_project'
    )
    return connection
