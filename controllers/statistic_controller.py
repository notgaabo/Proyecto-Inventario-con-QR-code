# controllers/statistic_controller.py

import plotly.graph_objs as go
import plotly.io as pio
from flask import render_template, session, redirect, url_for
from db.config import Config
from datetime import datetime, timedelta

class StatisticsController:
    @staticmethod
    def statistics():
        """Render the statistics page with charts, accessible only to managers."""
        if 'user' not in session:
            return redirect(url_for('login'))

        # Restrict access to managers only
        if session['user']['role'] != 'manager':
            return redirect(url_for('forbidden_error'))

        stats = StatisticsController.get_sales_data()
        chart_html = StatisticsController.generate_chart(stats)
        top_products = StatisticsController.get_top_products()
        return render_template("user/statistics.html", chart=chart_html, stats=stats, products=top_products)

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
                    "week1": {"sales": 0, "transactions": 0, "profit": 0},
                    "month": {"sales": 0, "transactions": 0, "profit": 0},
                    "quarter": {"sales": 0, "transactions": 0, "profit": 0}
                }
            }

        company_id = session['user']['company_id']  # Matches users.company_id
        try:
            with Config.get_db_connection() as connection:
                with connection.cursor(dictionary=True) as cursor:  # Updated to dictionary=True
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
                        WHERE s.company_id = %s  -- Updated to filter sales by company_id
                        ORDER BY s.sale_date ASC
                    """
                    cursor.execute(query, (company_id, company_id, company_id, company_id))
                    results = cursor.fetchall()
        except Exception as e:
            print(f"Error fetching sales data: {str(e)}")  # Replace with proper logging in production
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

        period_stats = {
            "week1": {"sales": 0, "transactions": 0, "profit": 0},
            "month": {"sales": 0, "transactions": 0, "profit": 0},
            "quarter": {"sales": 0, "transactions": 0, "profit": 0}
        }
        
        total_sales = 0
        total_transactions = 0
        total_profit = 0
        
        if results:
            first_date = results[0]['sale_date']  # Updated to dictionary access
            for result in results:
                sale_date = result['sale_date']
                sale_amount = result['sale_amount']
                profit = result['profit']
                days_diff = (sale_date - first_date).days
                
                total_sales += sale_amount
                total_transactions += 1
                total_profit += profit
                
                if days_diff <= 7:
                    period_stats["week1"]["sales"] += sale_amount
                    period_stats["week1"]["transactions"] += 1
                    period_stats["week1"]["profit"] += profit
                    period_stats["month"]["sales"] += sale_amount
                    period_stats["month"]["transactions"] += 1
                    period_stats["month"]["profit"] += profit
                elif days_diff <= 85:
                    period_stats["month"]["sales"] += sale_amount
                    period_stats["month"]["transactions"] += 1
                    period_stats["month"]["profit"] += profit
                else:
                    period_stats["quarter"]["sales"] += sale_amount
                    period_stats["quarter"]["transactions"] += 1
                    period_stats["quarter"]["profit"] += profit

        return {
            "total_sales": total_sales,
            "total_transactions": total_transactions,
            "total_profit": total_profit,
            "low_stock_items": results[0]['low_stock_items'] if results else 0,  #\intUpdated to dictionary access
            "all_items": results[0]['all_items'] if results else 0,  # Updated to dictionary access
            "all_categories": results[0]['all_categories'] if results else 0,  # Updated to dictionary access
            "period_stats": period_stats
        }

    @staticmethod
    def generate_chart(stats):
        """Generate the statistics chart using Plotly."""
        categories = ['Week 1', 'Month', 'Quarter']
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
            name='Sales', marker=dict(color='#4CAF50')
        ))

        fig.add_trace(go.Bar(
            y=categories, x=values_transactions, orientation='h',
            name='Transactions', marker=dict(color='#2196F3')
        ))

        fig.add_trace(go.Bar(
            y=categories, x=values_profit, orientation='h',
            name='Profit', marker=dict(color='#FF9800')
        ))

        fig.update_layout(
            title="Sales Statistics",
            xaxis_title="Amount",
            yaxis_title="Period",
            template="plotly",
            barmode='group'
        )

        return pio.to_html(fig, full_html=False)

    @staticmethod
    def get_top_products():
        """Retrieve the top-selling products."""
        if 'user' not in session:
            return []
        
        company_id = session['user']['company_id']  # Matches users.company_id
        try:
            with Config.get_db_connection() as connection:
                with connection.cursor(dictionary=True) as cursor:  # Updated to dictionary=True
                    query = """
                        SELECT 
                            p.name,
                            p.image,
                            SUM(s.quantity) AS total_sales
                        FROM products p
                        LEFT JOIN sales s ON p.id = s.product_id
                        WHERE p.company_id = %s
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
            print(f"Error fetching top products: {str(e)}")  # Replace with proper logging in production
            return []