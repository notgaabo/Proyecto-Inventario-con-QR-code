import os
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression
from flask import send_from_directory
from db.config import Config  # Asegúrate de tener get_db_connection()

class SalesPrediction:
    @staticmethod
    def get_sales_prediction():
        static_folder = 'static'
        image_name = 'ventas_prediccion.png'
        image_path = os.path.join(static_folder, image_name)

        if not os.path.exists(static_folder):
            os.makedirs(static_folder)

        try:
            connection = Config.get_db_connection()
            cursor = connection.cursor(dictionary=True)
            cursor.execute("SELECT sale_date, quantity FROM sales")
            results = cursor.fetchall()
            cursor.close()
            connection.close()
        except Exception as e:
            print(f"Error al obtener datos de ventas: {str(e)}")
            return None

        if not results:
            print("No se encontraron datos de ventas.")
            return None

        df = pd.DataFrame(results)
        df['sale_date'] = pd.to_datetime(df['sale_date'])
        df['month'] = df['sale_date'].dt.to_period('M')

        ventas_mensuales = df.groupby('month')['quantity'].sum().reset_index()
        ventas_mensuales['month_num'] = range(len(ventas_mensuales))

        X = ventas_mensuales[['month_num']]
        y = ventas_mensuales['quantity']

        model = LinearRegression()
        model.fit(X, y)

        next_month = [[len(ventas_mensuales)]]
        predicted = max(0, model.predict(next_month)[0])

        fig, ax = plt.subplots(figsize=(10, 6))

        ax.plot(X, y, color='blue', marker='o', label='Datos reales')
        ax.plot(
            [X['month_num'].iloc[-1], X['month_num'].iloc[-1] + 1],
            [y.iloc[-1], predicted],
            color='orange', linestyle='--', marker='o', label='Predicción próxima'
        )
        ax.scatter(X['month_num'].iloc[-1] + 1, predicted, color='orange')

        ax.set_title('Predicción de ventas mensuales')
        ax.set_xlabel('Mes (índice)')
        ax.set_ylabel('Cantidad vendida')
        ax.legend()
        ax.grid(True)

        plt.savefig(image_path)
        plt.close()

        return image_name  # <- Retorna solo el nombre del archivo

    @staticmethod
    def send_image(filename):
        return send_from_directory('static', filename)
