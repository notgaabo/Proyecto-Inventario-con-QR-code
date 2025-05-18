import os
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.preprocessing import PolynomialFeatures
from sklearn.linear_model import LinearRegression
import numpy as np
from flask import send_from_directory, session
from db.config import Config
from datetime import datetime, timedelta

class SalesPrediction:
    COLORS = {
        'background': '#f8f9fa',
        'trend': '#2c3e50',
        'actual': '#e74c3c',
        'prediction': '#27ae60',
        'grid': '#dcdcdc'
    }

    @staticmethod
    def fetch_sales_data(company_id):
        query = """
            SELECT 
                DATE_FORMAT(s.sale_date, '%Y-%m') AS month,
                COALESCE(SUM(s.quantity), 0) AS quantity_sales,
                COALESCE(SUM(r.quantity), 0) AS quantity_returns
            FROM sales s
            LEFT JOIN returns r 
                ON DATE_FORMAT(s.sale_date, '%Y-%m') = DATE_FORMAT(r.created_at, '%Y-%m')
                AND r.company_id = %s
            WHERE s.company_id = %s
                AND s.sale_date <= NOW()
            GROUP BY DATE_FORMAT(s.sale_date, '%Y-%m')
            ORDER BY month
        """
        last_sale_query = """
            SELECT MAX(sale_date) AS last_sale_date
            FROM sales
            WHERE company_id = %s
                AND sale_date <= NOW()
        """
        try:
            with Config.get_db_connection() as connection:
                cursor = connection.cursor(dictionary=True)
                cursor.execute(query, (company_id, company_id))
                results = cursor.fetchall()
                cursor.execute(last_sale_query, (company_id,))
                last_sale_result = cursor.fetchone()
                # Añadir mes actual si no está en los resultados
                current_month = datetime.now().strftime('%Y-%m')
                if not any(r['month'] == current_month for r in results):
                    results.append({
                        'month': current_month,
                        'quantity_sales': 0,
                        'quantity_returns': 0
                    })
            return results, last_sale_result
        except Exception as e:
            return None, None

    @staticmethod
    def train_model(df, last_sale_date):
        if df.empty or not last_sale_date:
            return None, None, None, None, None, None, None

        # Crear una copia explícita para evitar problemas con vistas
        df = df.copy()

        # Convertir 'month' a datetime y calcular net_quantity
        df['month'] = pd.to_datetime(df['month'])
        df['quantity_sales'] = df['quantity_sales'].astype(float)
        df['quantity_returns'] = df['quantity_returns'].astype(float)
        df['net_quantity'] = df['quantity_sales'] - df['quantity_returns']
        
        # Filtrar filas con net_quantity >= 0
        df = df[df['net_quantity'] >= 0].reset_index(drop=True)
        
        # Verificar si el DataFrame está vacío después de filtrar
        if df.empty:
            return None, None, None, None, None, None, None

        # Añadir month_num usando .loc para evitar SettingWithCopyWarning
        df.loc[:, 'month_num'] = np.arange(len(df))

        X = df[['month_num']]
        y = df['net_quantity']

        months_since_last_sale = (datetime.now() - last_sale_date).days / 30.42
        decay_factor = max(0.8, 1 - 0.05 * months_since_last_sale)

        n_points = len(df)
        optimal_degree = min(3, n_points - 1) if n_points > 1 else 1
        
        poly = PolynomialFeatures(degree=optimal_degree, include_bias=False)
        X_poly = poly.fit_transform(X)
        model = LinearRegression()
        model.fit(X_poly, y)

        y_pred = model.predict(X_poly)
        mse = np.mean((y - y_pred) ** 2)
        r2 = model.score(X_poly, y)

        next_index = len(df)
        X_future = np.array([[next_index]])
        X_future_poly = poly.transform(X_future)
        predicted = max(0, model.predict(X_future_poly)[0] * decay_factor)
        next_month = df['month'].iloc[-1] + pd.offsets.MonthBegin(1)

        return df, model, poly, predicted, next_month, decay_factor, next_index

    @staticmethod
    def generate_plot(df, model, poly, predicted, next_month, decay_factor, next_index, image_path):
        # Verificar que las columnas necesarias existan
        required_columns = ['month_num', 'net_quantity', 'month']
        if not all(col in df.columns for col in required_columns):
            return False

        plt.figure(figsize=(14, 8))
        ax = plt.gca()
        ax.set_facecolor(SalesPrediction.COLORS['background'])

        X = df[['month_num']]
        y = df['net_quantity']
        # Convertir X_plot a DataFrame para evitar la advertencia de sklearn
        X_plot = pd.DataFrame(np.linspace(0, next_index, 1000).reshape(-1, 1), columns=['month_num'])
        X_plot_poly = poly.transform(X_plot)
        y_plot = model.predict(X_plot_poly)
        if decay_factor < 1:
            y_plot = y_plot * decay_factor

        plt.plot(X_plot['month_num'], y_plot, color=SalesPrediction.COLORS['trend'], 
                 linewidth=3, label='Tendencia de ventas netas', alpha=0.8)
        idx_last = np.searchsorted(X_plot['month_num'], X['month_num'].iloc[-1])
        plt.plot(X_plot['month_num'][idx_last:], y_plot[idx_last:], 
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

        plt.title(f'Análisis de Tendencias de Ventas Netas y Predicción',
                 fontsize=20, pad=20, fontweight='bold', color='#333333')
        plt.xlabel('Meses con Registros', fontsize=14, labelpad=10)
        plt.ylabel('Volumen de Ventas Netas', fontsize=14, labelpad=10)

        month_labels = df['month'].dt.strftime('%Y-%m').tolist() + [next_month.strftime('%Y-%m')]
        plt.xticks(range(len(month_labels)), month_labels, rotation=45, ha='right')

        plt.legend(loc='upper left', frameon=True, facecolor='white',
                  edgecolor='#dddddd', fontsize=12, 
                  bbox_to_anchor=(0.01, 0.99))
        plt.grid(True, linestyle='--', alpha=0.6, 
                 color=SalesPrediction.COLORS['grid'])

        annotation_text = f'🔮 Predicción para {next_month.strftime("%Y-%m")}:\nSe estima una venta neta\naproximada de {predicted:.2f} productos'
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
            return True
        except Exception as e:
            plt.close()
            return False

    @staticmethod
    def get_sales_prediction():
        static_folder = 'static'
        image_name = f'ventas_prediccion_{session.get("user", {}).get("company_id", "unknown")}.png'
        image_path = os.path.join(static_folder, image_name)

        if not os.path.exists(static_folder):
            os.makedirs(static_folder)

        if os.path.exists(image_path):
            file_age = datetime.now() - datetime.fromtimestamp(os.path.getmtime(image_path))
            if file_age < timedelta(minutes=5):
                return image_name

        try:
            if 'user' not in session:
                return None
            user = session['user']
            if not isinstance(user, dict) or 'company_id' not in user:
                return None
            company_id = user['company_id']
            if not isinstance(company_id, int) or company_id <= 0:
                return None
        except Exception as e:
            return None

        session.pop('cached_sales_data', None)

        results, last_sale_result = SalesPrediction.fetch_sales_data(company_id)
        if not results or not last_sale_result:
            return None

        last_sale_date = last_sale_result['last_sale_date'] if last_sale_result and last_sale_result['last_sale_date'] else None
        if not last_sale_date:
            return None

        df = pd.DataFrame(results)
        result = SalesPrediction.train_model(df, last_sale_date)
        if result is None:
            return None

        df, model, poly, predicted, next_month, decay_factor, next_index = result

        success = SalesPrediction.generate_plot(df, model, poly, predicted, next_month, decay_factor, next_index, image_path)
        if not success:
            return None

        return image_name

    @staticmethod
    def send_image(filename):
        return send_from_directory('static', filename)