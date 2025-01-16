from flask import Flask, render_template
from db.config import Config
import mysql.connector
import json

app = Flask(__name__)

@app.route('/')
def dashboard_1():
    # Conexión a la base de datos
    conn = Config()
    cursor = conn.cursor()

    # Consulta para obtener las ventas semanales
    cursor.execute('''
        SELECT WEEK(date) AS week, SUM(sale_amount) AS total_sales
        FROM sales
        GROUP BY WEEK(date)
        ORDER BY week;
    ''')
    sales_data = cursor.fetchall()

    # Consulta para obtener las ventas mensuales
    cursor.execute('''
        SELECT MONTH(date) AS month, SUM(sale_amount) AS total_sales
        FROM sales
        GROUP BY MONTH(date)
        ORDER BY month;
    ''')
    monthly_sales_data = cursor.fetchall()

    # Procesar los resultados en listas de Python
    weeks = [f'Semana {row[0]}' if row[0] is not None else 'Semana Desconocida' for row in sales_data]
    sales = [row[1] if row[1] is not None else 0 for row in sales_data]
    months = [f'Mes {row[0]}' if row[0] is not None else 'Mes Desconocido' for row in monthly_sales_data]
    monthly_sales = [row[1] if row[1] is not None else 0 for row in monthly_sales_data]

    cursor.close()
    conn.close()

    # Pasar los datos a la plantilla HTML
    return render_template('user/statistics.html', 
                           weeks=json.dumps(weeks),  # Convertir la lista de semanas a JSON
                           sales=json.dumps(sales),  # Convertir la lista de ventas semanales a JSON
                           months=json.dumps(months),  # Convertir la lista de meses a JSON
                           monthly_sales=json.dumps(monthly_sales))  # Convertir la lista de ventas mensuales a JSON

if __name__ == '__main__':
    app.run(debug=True)
