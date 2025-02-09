import mysql.connector

class Config:
    @staticmethod
    def get_db_connection():
        return mysql.connector.connect(
            user='root',
            password='yoensi1881',
            host='localhost',
            database='final_project'
        )
