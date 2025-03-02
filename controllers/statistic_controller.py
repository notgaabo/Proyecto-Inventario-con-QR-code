import plotly.graph_objs as go
import plotly.io as pio
from flask import render_template, session, redirect, url_for
from db.config import Config

class StatisticsController:
    @staticmethod
    def statistics():
        """Renderiza la página de estadísticas con el gráfico"""
        if 'user' not in session:
            return redirect(url_for('login'))  # Redirige si no hay sesión activa

        stats = StatisticsController.get_sales_data()
        chart_html = StatisticsController.generate_chart(stats)
        return render_template("user/statistics.html", chart=chart_html, stats=stats)

    @staticmethod
    def get_sales_data():
        """Consulta la base de datos y devuelve las estadísticas de ventas solo del usuario autenticado"""
        if 'user' not in session:
            return {
                "total_sales": 0,
                "total_transactions": 0,
                "total_profit": 0
            }

        user_id = session['user']['id']
        
        db = Config()
        connection = db.get_db_connection()
        cursor = connection.cursor()

        query = """
            SELECT 
                COALESCE(SUM(s.sale_price * s.quantity), 0) AS total_sales,
                COALESCE(COUNT(s.id), 0) AS total_transactions,
                COALESCE(SUM(s.profit), 0) AS total_profit
            FROM sales s
            JOIN products p ON s.product_id = p.id
            WHERE p.user_id = %s
        """
        cursor.execute(query, (user_id,))
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
        categories = ['Semana 1', 'Semana 2', 'Mes', 'Trimestre']

        values_sales = [float(stats["total_sales"])] * len(categories)
        values_transactions = [float(stats["total_transactions"])] * len(categories)
        values_profit = [float(stats["total_profit"])] * len(categories)

        fig = go.Figure(data=[ 
            go.Bar(
                y=categories,
                x=values_sales,
                type='bar',
                orientation='h',  
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

        fig.update_layout(
            title="Estadísticas de Ventas",
            xaxis_title="Cantidad",
            yaxis_title="Período",
            template="plotly_dark",  
            barmode='group'
        )

        chart_html = pio.to_html(fig, full_html=False)
        return chart_html
