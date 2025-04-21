import os
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator
from sklearn.preprocessing import PolynomialFeatures
from sklearn.linear_model import LinearRegression
import numpy as np
from flask import send_from_directory, session
from db.config import Config
from datetime import datetime

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

        # Obtener company_id desde la sesión con validación explícita
        try:
            if 'user' not in session:
                print("Error: No se encontró 'user' en la sesión.")
                return None
            user = session['user']
            if not isinstance(user, dict) or 'company_id' not in user:
                print("Error: 'company_id' no está presente en session['user'].")
                return None
            company_id = user['company_id']
            if not isinstance(company_id, int) or company_id <= 0:
                print(f"Error: 'company_id' inválido en session['user']: {company_id}")
                return None
            print(f"company_id obtenido de la sesión: {company_id}")
        except Exception as e:
            print(f"Error al acceder a la sesión: {str(e)}")
            return None

        # Obtener datos de ventas y devoluciones filtrados por company_id
        try:
            connection = Config.get_db_connection()
            cursor = connection.cursor(dictionary=True)
            
            # Consulta de ventas filtrada por company_id
            cursor.execute("SELECT sale_date, quantity FROM sales WHERE company_id = %s", (company_id,))
            sales_results = cursor.fetchall()
            
            # Consulta de devoluciones filtrada por company_id
            cursor.execute("SELECT created_at, quantity FROM returns WHERE company_id = %s", (company_id,))
            returns_results = cursor.fetchall()
            
            cursor.close()
            connection.close()
            print(f"Datos cargados para company_id {company_id}: {len(sales_results)} ventas, {len(returns_results)} devoluciones")
        except Exception as e:
            print(f"Error al obtener datos para company_id {company_id}: {str(e)}")
            return None

        if not sales_results:
            print(f"No se encontraron datos de ventas para company_id {company_id}.")
            return None

        # Preprocesamiento de ventas
        df_sales = parade = pd.DataFrame(sales_results)
        df_sales['sale_date'] = pd.to_datetime(df_sales['sale_date'])
        df_sales['month'] = df_sales['sale_date'].dt.to_period('M')

        # Preprocesamiento de devoluciones
        df_returns = pd.DataFrame(returns_results) if returns_results else pd.DataFrame(columns=['created_at', 'quantity'])
        if not df_returns.empty:
            df_returns['created_at'] = pd.to_datetime(df_returns['created_at'])
            df_returns['month'] = df_returns['created_at'].dt.to_period('M')

        # Agrupar ventas por mes
        ventas_mensuales = df_sales.groupby('month')['quantity'].sum().reset_index()
        
        # Agrupar devoluciones por mes
        devoluciones_mensuales = df_returns.groupby('month')['quantity'].sum().reset_index() if not df_returns.empty else pd.DataFrame(columns=['month', 'quantity'])

        # Combinar ventas y devoluciones
        ventas_mensuales = ventas_mensuales.merge(devoluciones_mensuales, on='month', how='left', suffixes=('_sales', '_returns'))
        ventas_mensuales['quantity_returns'] = ventas_mensuales['quantity_returns'].fillna(0)
        ventas_mensuales['net_quantity'] = ventas_mensuales['quantity_sales'] - ventas_mensuales['quantity_returns']
        
        # Filtrar meses con ventas netas positivas o cero
        ventas_mensuales = ventas_mensuales[ventas_mensuales['net_quantity'] >= 0]
        if ventas_mensuales.empty:
            print(f"No hay datos de ventas netas válidos para company_id {company_id} después de descontar devoluciones.")
            return None

        ventas_mensuales['month_num'] = np.arange(len(ventas_mensuales))
        print(f"Datos procesados para company_id {company_id}: {len(ventas_mensuales)} meses con registros analizados")

        X = ventas_mensuales[['month_num']]
        y = ventas_mensuales['net_quantity']

        # Calcular tiempo desde la última venta
        last_sale_date = df_sales['sale_date'].max()
        months_since_last_sale = (datetime.now() - last_sale_date).days / 30.42  # Aproximación de meses
        decay_factor = max(0.5, 1 - 0.1 * months_since_last_sale)  # Reduce 10% por mes, mínimo 50%
        print(f"Tiempo desde última venta para company_id {company_id}: {months_since_last_sale:.2f} meses, factor de decaimiento: {decay_factor:.2f}")

        # Modelo polinomial
        n_points = len(ventas_mensuales)
        optimal_degree = min(3, n_points - 1)
        if n_points < 2:
            print(f"Datos insuficientes para una parábola para company_id {company_id}. Se necesita al menos 2 puntos.")
            return None
        print(f"Grado polinómico seleccionado para company_id {company_id}: {optimal_degree}")

        poly = PolynomialFeatures(degree=optimal_degree, include_bias=False)
        X_poly = poly.fit_transform(X)
        model = LinearRegression()
        model.fit(X_poly, y)

        y_pred = model.predict(X_poly)
        mse = np.mean((y - y_pred) ** 2)
        r2 = model.score(X_poly, y)
        print(f"Modelo entrenado para company_id {company_id} - MSE: {mse:.2f}, R²: {r2:.4f}")

        # Predicción para el próximo mes
        next_index = len(ventas_mensuales)
        X_future = np.array([[next_index]])
        X_future_poly = poly.transform(X_future)
        predicted = max(0, model.predict(X_future_poly)[0] * decay_factor)  # Aplicar decaimiento
        next_month = ventas_mensuales['month'].iloc[-1] + 1
        print(f"Predicción para {next_month} (company_id {company_id}): {predicted:.2f} (con decaimiento)")

        # Visualización
        plt.figure(figsize=(14, 8))
        ax = plt.gca()
        ax.set_facecolor(SalesPrediction.COLORS['background'])

        # Curva suave
        X_plot = np.linspace(0, next_index, 1000).reshape(-1, 1)
        X_plot_poly = poly.transform(X_plot)
        y_plot = model.predict(X_plot_poly)
        if decay_factor < 1:
            y_plot = y_plot * decay_factor  # Ajustar curva predicha

        plt.plot(X_plot, y_plot, color=SalesPrediction.COLORS['trend'], 
                 linewidth=3, label='Tendencia de ventas netas', alpha=0.8)

        idx_last = np.searchsorted(X_plot.flatten(), X['month_num'].iloc[-1])
        plt.plot(X_plot[idx_last:], y_plot[idx_last:], 
                 color=SalesPrediction.COLORS['prediction'],
                 linewidth=3.5, linestyle='--', alpha=0.9, 
                 label='Tendencia predicha')

        plt.scatter(X, y, color=SalesPrediction.COLORS['actual'], 
                    marker='o', s=120, edgecolors='white', 
                    linewidth=1.5, label='Ventas netas reales', zorder=3)

        plt.scatter(next_index, predicted, 
                    color=SalesPrediction.COLORS['prediction'],
                    marker='*', s=350, edgecolors='white', 
                    linewidth=2, label='Predicción', zorder=4)

        plt.title(f'Análisis de Tendencias de Ventas Netas y Predicción (Compañía {company_id})',
                  fontsize=20, pad=20, fontweight='bold', color='#333333')
        plt.xlabel('Meses con Registros', fontsize=14, labelpad=10)
        plt.ylabel('Volumen de Ventas Netas', fontsize=14, labelpad=10)

        month_labels = ventas_mensuales['month'].astype(str).tolist() + [str(next_month)]
        plt.xticks(range(len(month_labels)), month_labels, rotation=45, ha='right')

        plt.legend(loc='upper left', frameon=True, facecolor='white',
                   edgecolor='#dddddd', fontsize=12, 
                   bbox_to_anchor=(0.01, 0.99))

        plt.grid(True, linestyle='--', alpha=0.6, 
                 color=SalesPrediction.COLORS['grid'])

        # Anotación de predicción
        annotation_text = f'🔮 Predicción para {next_month}:\nSe estima una venta neta\naproximada de {predicted:.2f} productos'
        if decay_factor < 1:
            annotation_text += f'\n(Ajustado por {months_since_last_sale:.1f} meses sin ventas)'
        
        plt.annotate(
            annotation_text,
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
            print(f"Gráfico guardado correctamente como '{image_name}' para company_id {company_id}")
            return image_name
        except Exception as e:
            print(f"No se pudo guardar el gráfico para company_id {company_id}: {e}")
            plt.close()
            return None

    @staticmethod
    def send_image(filename):
        return send_from_directory('static', filename)