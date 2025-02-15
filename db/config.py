import mysql.connector

class Config:
    @staticmethod
    def get_db_connection():
        """Obtiene la conexión a la base de datos"""
        return mysql.connector.connect(
            user='root',
            password='yoensi1881',
            host='localhost',
            database='final_project'
        )

    @staticmethod
    def get_sales_date():
        """Consulta las ventas por fecha"""
        connection = Config.get_db_connection()
        cursor = connection.cursor()

        query = """
        SELECT DATE(sale_date) as date, SUM(sale_price) as total_sales
        FROM sales
        GROUP BY DATE(sale_date)
        ORDER BY date ASC;
        """
        cursor.execute(query)
        result = cursor.fetchall()

        cursor.close()
        connection.close()
        return result
