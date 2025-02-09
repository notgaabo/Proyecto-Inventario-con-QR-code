import mysql.connector
from db.config import Config

class Database:
    def __init__(self):
        self.connection = None

    def connect(self):
        if not self.connection or not self.connection.is_connected():
            self.connection = mysql.connector.connect(
                host=Config.MYSQL_HOST,
                user=Config.MYSQL_USER,
                password=Config.MYSQL_PASSWORD,
                database=Config.MYSQL_DB
            )
        return self.connection

    def close(self):
        if self.connection and self.connection.is_connected():
            self.connection.close()

db = Database()
