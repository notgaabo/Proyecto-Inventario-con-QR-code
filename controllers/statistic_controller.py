import plotly.graph_objs as go
import plotly.io as pio
from flask import render_template, session, redirect, url_for
from db.config import Config
from datetime import datetime, timedelta

class StatisticsController:
    @staticmethod
    def statistics():
        """Renderiza la página de estadísticas con el gráfico"""
        if 'user' not in session:
            return redirect(url_for('login'))

        stats = StatisticsController.get_sales_data()
        chart_html = StatisticsController.generate_chart(stats)
        top_products = StatisticsController.get_top_products()
        return render_template("user/statistics.html", chart=chart_html, stats=stats, products=top_products)

    @staticmethod
    def get_sales_data():
        """Consulta la base de datos y devuelve las estadísticas de ventas por períodos"""
        if 'user' not in session:
            return {
                "total_sales": 0,
                "total_transactions": 0,
                "total_profit": 0,
                "low_stock_items": 0,
                "all_items": 0,
                "all_categories": 0,
                "period_stats": {
                    "week1": {"sales": 0, "transactions": 0, "profit": 0},
                    "month": {"sales": 0, "transactions": 0, "profit": 0},
                    "quarter": {"sales": 0, "transactions": 0, "profit": 0}
                }
            }

        user_id = session['user']['id']
        db = Config()
        
        with db.get_db_connection() as connection:
            with connection.cursor() as cursor:
                query = """
                    SELECT 
                        s.sale_date,
                        COALESCE(s.quantity * p.price, 0) AS sale_amount,
                        COALESCE(s.quantity * (p.price - p.cost_price), 0) AS profit,
                        (SELECT COUNT(*) FROM products WHERE stock <= 25 AND user_id = %s) AS low_stock_items,
                        (SELECT COUNT(*) FROM products WHERE user_id = %s) AS all_items,
                        (SELECT COUNT(DISTINCT category) FROM products WHERE user_id = %s) AS all_categories
                    FROM sales s
                    JOIN products p ON s.product_id = p.id
                    WHERE p.user_id = %s
                    ORDER BY s.sale_date ASC
                """
                cursor.execute(query, (user_id, user_id, user_id, user_id))
                results = cursor.fetchall()

        period_stats = {
            "week1": {"sales": 0, "transactions": 0, "profit": 0},
            "month": {"sales": 0, "transactions": 0, "profit": 0},
            "quarter": {"sales": 0, "transactions": 0, "profit": 0}
        }
        
        total_unique_sales = 0
        total_unique_transactions = 0
        total_unique_profit = 0
        
        if results:
            first_date = results[0][0]
            
            for sale_date, sale_amount, profit in [(r[0], r[1], r[2]) for r in results]:
                days_diff = (sale_date - first_date).days
                
                # Acumular ventas únicas para el total
                total_unique_sales += sale_amount
                total_unique_transactions += 1
                total_unique_profit += profit
                
                if days_diff <= 7:
                    # Semana 1
                    period_stats["week1"]["sales"] += sale_amount
                    period_stats["week1"]["transactions"] += 1
                    period_stats["week1"]["profit"] += profit
                    # También se incluye en Mes
                    period_stats["month"]["sales"] += sale_amount
                    period_stats["month"]["transactions"] += 1
                    period_stats["month"]["profit"] += profit
                elif days_diff <= 85:
                    # Mes (incluye Semana 1 más lo que sigue hasta 85 días)
                    period_stats["month"]["sales"] += sale_amount
                    period_stats["month"]["transactions"] += 1
                    period_stats["month"]["profit"] += profit
                else:
                    # Trimestre
                    period_stats["quarter"]["sales"] += sale_amount
                    period_stats["quarter"]["transactions"] += 1
                    period_stats["quarter"]["profit"] += profit

        return {
            "total_sales": total_unique_sales,
            "total_transactions": total_unique_transactions,
            "total_profit": total_unique_profit,
            "low_stock_items": results[0][3] if results else 0,
            "all_items": results[0][4] if results else 0,
            "all_categories": results[0][5] if results else 0,
            "period_stats": period_stats
        }

    @staticmethod
    def generate_chart(stats):
        """Genera el gráfico de estadísticas con Plotly"""
        categories = ['Semana 1', 'Mes', 'Trimestre']
        period_stats = stats["period_stats"]

        values_sales = [
            period_stats["week1"]["sales"],
            period_stats["month"]["sales"],
            period_stats["quarter"]["sales"]
        ]
        values_transactions = [
            period_stats["week1"]["transactions"],
            period_stats["month"]["transactions"],
            period_stats["quarter"]["transactions"]
        ]
        values_profit = [
            period_stats["week1"]["profit"],
            period_stats["month"]["profit"],
            period_stats["quarter"]["profit"]
        ]

        fig = go.Figure()

        fig.add_trace(go.Bar(
            y=categories, x=values_sales, orientation='h',
            name='Ventas', marker=dict(color='#4CAF50')
        ))

        fig.add_trace(go.Bar(
            y=categories, x=values_transactions, orientation='h',
            name='Transacciones', marker=dict(color='#2196F3')
        ))

        fig.add_trace(go.Bar(
            y=categories, x=values_profit, orientation='h',
            name='Ganancias', marker=dict(color='#FF9800')
        ))

        fig.update_layout(
            title="Estadísticas de Ventas",
            xaxis_title="Cantidad",
            yaxis_title="Período",
            template="plotly",
            barmode='group'
        )

        return pio.to_html(fig, full_html=False)

    @staticmethod
    def get_top_products():
        """Obtiene los productos más vendidos"""
        if 'user' not in session:
            return []
        
        user_id = session['user']['id']
        db = Config()
        
        with db.get_db_connection() as connection:
            with connection.cursor() as cursor:
                query = """
                    SELECT 
                        p.name,
                        p.image,
                        SUM(s.quantity) as total_sales
                    FROM products p
                    LEFT JOIN sales s ON p.id = s.product_id
                    WHERE p.user_id = %s
                    GROUP BY p.id, p.name, p.image
                    ORDER BY total_sales DESC
                    LIMIT 3
                """
                cursor.execute(query, (user_id,))
                results = cursor.fetchall()
                
                return [
                    {
                        'name': row[0],
                        'image': row[1],
                        'sales_count': row[2] or 0
                    }
                    for row in results
                ]
                