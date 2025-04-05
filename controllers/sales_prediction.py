import os
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator
from sklearn.preprocessing import PolynomialFeatures
from sklearn.linear_model import LinearRegression  # Cambiamos a LinearRegression para ajuste exacto
import numpy as np
from flask import send_from_directory
from db.config import Config

class SalesPrediction:
    COLORS = {
        'background': '#f8f9fa',
        'trend': '#2c3e50',
        'actual': '#e74c3c',
        'prediction': '#27ae60',
        'grid': '#dcdcdc'
    }

    @staticmethod
    def get_sales_prediction():
        static_folder = 'static'
        image_name = 'ventas_prediccion.png'
        image_path = os.path.join(static_folder, image_name)

        if not os.path.exists(static_folder):
            os.makedirs(static_folder)
            print(f"Carpeta '{static_folder}' creada")

        # Obtener datos
        try:
            connection = Config.get_db_connection()
            cursor = connection.cursor(dictionary=True)
            cursor.execute("SELECT sale_date, quantity FROM sales")
            results = cursor.fetchall()
            cursor.close()
            connection.close()
            print(f"Datos cargados correctamente: {len(results)} registros")
        except Exception as e:
            print(f"Error al obtener datos de ventas: {str(e)}")
            return None

        if not results:
            print("No se encontraron datos de ventas.")
            return None

        # Preprocesamiento
        df = pd.DataFrame(results)
        df['sale_date'] = pd.to_datetime(df['sale_date'])
        df['month'] = df['sale_date'].dt.to_period('M')

        # Agrupar por mes, sin rellenar meses faltantes
        ventas_mensuales = df.groupby('month')['quantity'].sum().reset_index()
        ventas_mensuales['month_num'] = np.arange(len(ventas_mensuales))
        print(f"Datos procesados: {len(ventas_mensuales)} meses con registros analizados")

        X = ventas_mensuales[['month_num']]
        y = ventas_mensuales['quantity']

        # Usar un grado que permita ajuste exacto (n-1 para n puntos)
        n_points = len(ventas_mensuales)
        optimal_degree = min(3, n_points - 1)  # Grado 3 para 4 puntos, o menor si hay menos datos
        if n_points < 2:
            print("Datos insuficientes para una parábola. Se necesita al menos 2 puntos.")
            return None
        print(f"Grado polinómico seleccionado: {optimal_degree} (para ajuste exacto con {n_points} puntos)")

        # Modelo polinomial con LinearRegression (sin regularización)
        poly = PolynomialFeatures(degree=optimal_degree, include_bias=False)
        X_poly = poly.fit_transform(X)
        model = LinearRegression()
        model.fit(X_poly, y)

        y_pred = model.predict(X_poly)
        mse = np.mean((y - y_pred) ** 2)
        r2 = model.score(X_poly, y)
        print(f"Modelo entrenado - MSE: {mse:.2f}, R²: {r2:.4f}")

        # Verificar error en cada punto
        for i, (real, pred) in enumerate(zip(y, y_pred)):
            print(f"Mes {ventas_mensuales['month'].iloc[i]} - Real: {real:.2f}, Predicho: {pred:.2f}, Error: {real - pred:.2f}")

        # Predicción para el próximo mes
        next_index = len(ventas_mensuales)
        X_future = np.array([[next_index]])
        X_future_poly = poly.transform(X_future)
        predicted = max(0, model.predict(X_future_poly)[0])
        next_month = ventas_mensuales['month'].iloc[-1] + 1
        print(f"Predicción para {next_month}: {predicted:.2f}")

        # Visualización
        plt.figure(figsize=(14, 8))
        ax = plt.gca()
        ax.set_facecolor(SalesPrediction.COLORS['background'])

        # Curva suave con más puntos
        X_plot = np.linspace(0, next_index, 1000).reshape(-1, 1)
        X_plot_poly = poly.transform(X_plot)
        y_plot = model.predict(X_plot_poly)

        plt.plot(X_plot, y_plot, color=SalesPrediction.COLORS['trend'], 
                 linewidth=3, label='Tendencia de ventas (ajuste exacto)', alpha=0.8)

        idx_last = np.searchsorted(X_plot.flatten(), X['month_num'].iloc[-1])
        plt.plot(X_plot[idx_last:], y_plot[idx_last:], 
                 color=SalesPrediction.COLORS['prediction'],
                 linewidth=3.5, linestyle='--', alpha=0.9, 
                 label='Tendencia predicha')

        plt.scatter(X, y, color=SalesPrediction.COLORS['actual'], 
                    marker='o', s=120, edgecolors='white', 
                    linewidth=1.5, label='Ventas reales', zorder=3)

        plt.scatter(next_index, predicted, 
                    color=SalesPrediction.COLORS['prediction'],
                    marker='*', s=350, edgecolors='white', 
                    linewidth=2, label='Predicción', zorder=4)

        plt.title('Análisis de Tendencias de Ventas y Predicción (Ajuste Exacto)',
                  fontsize=20, pad=20, fontweight='bold', color='#333333')
        plt.xlabel('Meses con Registros', fontsize=14, labelpad=10)
        plt.ylabel('Volumen de Ventas', fontsize=14, labelpad=10)

        # Etiquetas del eje X con meses reales
        month_labels = ventas_mensuales['month'].astype(str).tolist() + [str(next_month)]
        plt.xticks(range(len(month_labels)), month_labels, rotation=45, ha='right')

        plt.legend(loc='upper left', frameon=True, facecolor='white',
                   edgecolor='#dddddd', fontsize=12, 
                   bbox_to_anchor=(0.01, 0.99))

        plt.grid(True, linestyle='--', alpha=0.6, 
                 color=SalesPrediction.COLORS['grid'])

        plt.annotate(
            f'🔮 Predicción para {next_month}:\nSe estima una venta\naproximada de {predicted:.2f} productos',
            xy=(next_index, predicted),
            xytext=(next_index, predicted * 0.65),
            arrowprops=dict(
                facecolor=SalesPrediction.COLORS['prediction'],
                shrink=0.05,
                width=2,
                alpha=0.8,
                connectionstyle="arc3,rad=0.3"
            ),
            fontsize=12,
            fontweight='bold',
            color=SalesPrediction.COLORS['prediction'],
            ha='center',
            bbox=dict(
                boxstyle="round,pad=0.5",
                fc="white",
                ec=SalesPrediction.COLORS['prediction'],
                alpha=0.8
            )
        )

        plt.axvspan(X['month_num'].iloc[-1], next_index,
                    alpha=0.1, color=SalesPrediction.COLORS['prediction'])

        plt.tight_layout()

        try:
            plt.savefig(image_path, dpi=300, bbox_inches='tight')
            plt.close()
            print(f"Gráfico guardado correctamente como '{image_name}'")
            return image_name
        except Exception as e:
            print(f"No se pudo guardar el gráfico: {e}")
            plt.close()
            return None

    @staticmethod
    def send_image(filename):
        return send_from_directory('static', filename)