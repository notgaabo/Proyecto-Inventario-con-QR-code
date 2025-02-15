import plotly.graph_objs as go
import plotly.io as pio
from flask import render_template
from db.config import Config

class StatisticsController:
    @staticmethod
    def statistics():
        """Renderiza la página de estadísticas con el gráfico"""
        # Obtenemos las estadísticas de ventas
        stats = StatisticsController.get_sales_data()

        # Llamamos al gráfico generado
        chart_html = StatisticsController.generate_chart(stats)  # Ahora pasamos stats a la función

        # Pasamos las estadísticas y el gráfico a la plantilla
        return render_template("user/statistics.html", chart=chart_html, stats=stats)

    @staticmethod
    def get_sales_data():
        """Consulta la base de datos y devuelve las estadísticas de ventas en formato diccionario"""
        db = Config()
        connection = db.get_db_connection()
        cursor = connection.cursor()

        query = """
            SELECT 
                COALESCE(SUM(sale_price * quantity), 0) AS total_sales,
                COALESCE(COUNT(id), 0) AS total_transactions,
                COALESCE(SUM(profit), 0) AS total_profit
            FROM sales
        """
        cursor.execute(query)
        result = cursor.fetchone()
        cursor.close()
        connection.close()

        if result:
            return {
                "total_sales": result[0],
                "total_transactions": result[1],
                "total_profit": result[2]
            }
        else:
            return {
                "total_sales": 0,
                "total_transactions": 0,
                "total_profit": 0
            }

    @staticmethod
    def generate_chart(stats):
        """Genera el gráfico de estadísticas con Plotly"""
        # Define las categorías de las barras (en este caso, categorías fijas como ejemplo)
        categories = ['Semana 1', 'Semana 2', 'Mes', 'Trimestre']

        # Usamos los valores de ventas, transacciones y ganancias
        values_sales = [float(stats["total_sales"])] * len(categories)
        values_transactions = [float(stats["total_transactions"])] * len(categories)
        values_profit = [float(stats["total_profit"])] * len(categories)

        # Crea el gráfico de barras
        fig = go.Figure(data=[
            go.Bar(
                y=categories,
                x=values_sales,
                type='bar',
                orientation='h',  # Barra horizontal
                name='Ventas',
                marker=dict(color='#4CAF50')
            ),
            go.Bar(
                y=categories,
                x=values_transactions,
                type='bar',
                orientation='h',
                name='Transacciones',
                marker=dict(color='#2196F3')
            ),
            go.Bar(
                y=categories,
                x=values_profit,
                type='bar',
                orientation='h',
                name='Ganancias',
                marker=dict(color='#FF9800')
            )
        ])

        # Configuraciones adicionales del gráfico
        fig.update_layout(
            title="Estadísticas de Ventas",
            xaxis_title="Cantidad",
            yaxis_title="Período",
            template="plotly_dark",  # Tema oscuro para el gráfico
            barmode='group'  # Para agrupar las barras
        )

        # Convierte el gráfico a HTML para insertarlo en la plantilla
        chart_html = pio.to_html(fig, full_html=False)
        return chart_html
