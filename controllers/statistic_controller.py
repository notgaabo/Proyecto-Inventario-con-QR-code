import plotly.graph_objs as go
import plotly.io as pio
from flask import render_template, session, redirect, url_for, abort, jsonify, request
from db.config import Config
from datetime import datetime, timedelta
from controllers.sales_prediction import SalesPrediction  # Import from controllers directory

class StatisticsController:
    @staticmethod
    def statistics():
        if 'user' not in session:
            return redirect(url_for('login'))

        if session['user']['role'] != 'gerente':
            return redirect(url_for('forbidden_error'))

        stats = StatisticsController.get_sales_data()
        chart_html = StatisticsController.generate_chart(stats)
        top_products = StatisticsController.get_top_products('month')

        sales_pred = SalesPrediction()
        prediction_img_path = sales_pred.get_sales_prediction()

        return render_template(
            "user/statistics.html",
            chart=chart_html,
            stats=stats,
            products=top_products,
            prediction_img_path=prediction_img_path
        )
    
    @staticmethod
    def get_sales_data():
        """Retrieve sales statistics by period from the database."""
        if 'user' not in session:
            return {
                "total_sales": 0,
                "total_transactions": 0,
                "total_profit": 0,
                "low_stock_items": 0,
                "all_items": 0,
                "all_categories": 0,
                "period_stats": {
                    "semana": {"sales": 0, "transactions": 0, "profit": 0},
                    "mes": {"sales": 0, "transactions": 0, "profit": 0},
                    "trimestre": {"sales": 0, "transactions": 0, "profit": 0}
                }
            }

        company_id = session['user']['company_id']
        try:
            with Config.get_db_connection() as connection:
                with connection.cursor(dictionary=True) as cursor:
                    query = """
                        SELECT 
                            s.sale_date,
                            COALESCE(s.quantity * p.price, 0) AS sale_amount,
                            COALESCE(s.quantity * (p.price - p.cost_price), 0) AS profit,
                            (SELECT COUNT(*) FROM products WHERE stock <= 25 AND company_id = %s) AS low_stock_items,
                            (SELECT COUNT(*) FROM products WHERE company_id = %s) AS all_items,
                            (SELECT COUNT(DISTINCT category) FROM products WHERE company_id = %s) AS all_categories
                        FROM sales s
                        JOIN products p ON s.product_id = p.id
                        WHERE s.company_id = %s
                        ORDER BY s.sale_date ASC
                    """
                    cursor.execute(query, (company_id, company_id, company_id, company_id))
                    results = cursor.fetchall()
        except Exception as e:
            print(f"Error fetching sales data: {str(e)}")
            return {
                "total_sales": 0,
                "total_transactions": 0,
                "total_profit": 0,
                "low_stock_items": 0,
                "all_items": 0,
                "all_categories": 0,
                "period_stats": {
                    "semana": {"sales": 0, "transactions": 0, "profit": 0},
                    "mes": {"sales": 0, "transactions": 0, "profit": 0},
                    "trimestre": {"sales": 0, "transactions": 0, "profit": 0}
                }
            }

        period_stats = {
            "semana": {"sales": 0, "transactions": 0, "profit": 0},
            "mes": {"sales": 0, "transactions": 0, "profit": 0},
            "trimestre": {"sales": 0, "transactions": 0, "profit": 0}
        }
        
        total_sales = 0
        total_transactions = 0
        total_profit = 0
        
        if results:
            now = datetime.now()
            for result in results:
                sale_date = result['sale_date']
                sale_amount = result['sale_amount']
                profit = result['profit']
                days_diff = (now - sale_date).days
                
                total_sales += sale_amount
                total_transactions += 1
                total_profit += profit
                
                if days_diff <= 7:
                    period_stats["semana"]["sales"] += sale_amount
                    period_stats["semana"]["transactions"] += 1
                    period_stats["semana"]["profit"] += profit
                if days_diff <= 30:
                    period_stats["mes"]["sales"] += sale_amount
                    period_stats["mes"]["transactions"] += 1
                    period_stats["mes"]["profit"] += profit
                if days_diff <= 90:
                    period_stats["trimestre"]["sales"] += sale_amount
                    period_stats["trimestre"]["transactions"] += 1
                    period_stats["trimestre"]["profit"] += profit

        return {
            "total_sales": total_sales,
            "total_transactions": total_transactions,
            "total_profit": total_profit,
            "low_stock_items": results[0]['low_stock_items'] if results else 0,
            "all_items": results[0]['all_items'] if results else 0,
            "all_categories": results[0]['all_categories'] if results else 0,
            "period_stats": period_stats
        }

    @staticmethod
    def generate_chart(stats):
        """Generate the statistics chart using Plotly."""
        categories = ['Última Semana', 'Último Mes', 'Último Trimestre']
        period_stats = stats["period_stats"]

        values_sales = [
            period_stats["semana"]["sales"],
            period_stats["mes"]["sales"],
            period_stats["trimestre"]["sales"]
        ]
        values_transactions = [
            period_stats["semana"]["transactions"],
            period_stats["mes"]["transactions"],
            period_stats["trimestre"]["transactions"]
        ]
        values_profit = [
            period_stats["semana"]["profit"],
            period_stats["mes"]["profit"],
            period_stats["trimestre"]["profit"]
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
            xaxis_title="Monto",
            yaxis_title="Período",
            template="plotly",
            barmode='group'
        )

        return pio.to_html(fig, full_html=False)

    @staticmethod
    def get_top_products(period='month'):
        """Retrieve the top-selling products based on a time period."""
        if 'user' not in session:
            return []

        company_id = session['user']['company_id']
        try:
            with Config.get_db_connection() as connection:
                with connection.cursor(dictionary=True) as cursor:
                    if period == 'week':
                        time_filter = "AND s.sale_date >= DATE_SUB(NOW(), INTERVAL 7 DAY)"
                    elif period == 'quarter':
                        time_filter = "AND s.sale_date >= DATE_SUB(NOW(), INTERVAL 3 MONTH)"
                    else:  # Default to month
                        time_filter = "AND s.sale_date >= DATE_SUB(NOW(), INTERVAL 1 MONTH)"

                    query = f"""
                        SELECT 
                            p.name,
                            p.image,
                            SUM(s.quantity) AS total_sales
                        FROM products p
                        LEFT JOIN sales s ON p.id = s.product_id
                        WHERE p.company_id = %s {time_filter}
                        GROUP BY p.id, p.name, p.image
                        ORDER BY total_sales DESC
                        LIMIT 3
                    """
                    cursor.execute(query, (company_id,))
                    results = cursor.fetchall()
                    
                    return [
                        {
                            'name': row['name'],
                            'image': row['image'],
                            'sales_count': row['total_sales'] or 0
                        }
                        for row in results
                    ]
        except Exception as e:
            print(f"Error fetching top products: {str(e)}")
            return []

    @staticmethod
    def filter_sales():
        """Endpoint to filter top-selling products by period."""
        if 'user' not in session:
            return redirect(url_for('login'))

        # Restrict access to managers only
        if session['user']['role'] != 'gerente':
            return redirect(url_for('forbidden_error'))

        period = request.args.get('period', 'month')
        top_products = StatisticsController.get_top_products(period)
        return jsonify({'products': top_products})