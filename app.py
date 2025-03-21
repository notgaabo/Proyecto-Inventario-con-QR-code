from flask import Flask, request, jsonify, session, render_template, redirect, url_for
from db import Config as db
from datetime import datetime, timedelta
from controllers.dashboard_controller import HomeController  
from controllers.auth_controller import AuthController
from controllers.user_controller import UserController
from controllers.statistic_controller import StatisticsController
from controllers.product_controller import ProductController
from controllers.qr_controller import QrController
from controllers.qr_controller import LectorController
from controllers.sales_controller import SalesController

class InventoryApp(Flask):
    def __init__(self):
        super().__init__(__name__)
        self.secret_key = 'StockBeam'
        self.permanent_session_lifetime = timedelta(days=7)
        self.register_error_handlers()
        self.register_routes()

    def forbidden_error(self, e):
        return render_template('errors/403.html'), 403
    
    def page_not_found(self, e):
        return render_template('errors/404.html'), 404

    def register_error_handlers(self):
        self.register_error_handler(403, self.forbidden_error)
        self.register_error_handler(404, self.page_not_found)

    def register_routes(self):
        self.add_url_rule('/', 'home', HomeController.home)
        self.add_url_rule('/login', 'login', AuthController.login, methods=['GET', 'POST'])
        self.add_url_rule('/logout', 'logout', AuthController.logout)

        self.add_url_rule('/admin', 'admin_dashboard', UserController.admin_dashboard)
        self.add_url_rule('/create_user', 'create_user', UserController.create_user, methods=['GET', 'POST'])
        self.add_url_rule('/edit_user', 'edit_user', UserController.edit_user, methods=['POST'])
        self.add_url_rule('/disable_user/<int:user_id>', 'disable_user', UserController.disable_user, methods=['GET'])
        self.add_url_rule('/enable_user/<int:user_id>', 'enable_user', UserController.enable_user, methods=['GET'])
        
        self.add_url_rule('/statistics', 'statistics', StatisticsController.statistics)
        self.add_url_rule('/statistics/chart', 'statistics_chart', StatisticsController.statistics)

        self.add_url_rule('/disabled_error', 'disabled_user_error', self.disabled_user_error)
        self.add_url_rule('/403', 'forbidden_error', self.forbidden_error)

        self.add_url_rule('/product', 'product_list', ProductController.get_product_list, methods=['GET'])
        self.add_url_rule('/add_product', 'add_product', ProductController.add_product, methods=['GET', 'POST'])
        self.add_url_rule('/edit_product/<int:product_id>', 'edit_product', ProductController.update_product, methods=['GET', 'POST'])
        self.add_url_rule('/delete_product/<int:product_id>', 'delete_product', ProductController.delete_product, methods=['POST'])
        self.add_url_rule('/api/products', 'api_products', ProductController.filter_products, methods=['POST'])
        self.add_url_rule('/sales/history', 'sales_history', ProductController.sales_history, methods=['GET'])
        self.add_url_rule('/generate_qr/<int:product_id>', 'generate_qr', QrController.generate_qr, methods=['GET'])
      
        self.add_url_rule('/inventory', 'inventory', LectorController.inventory)
        self.add_url_rule('/escanear', 'escanear', LectorController.escanear, methods=['POST'])
        self.add_url_rule('/carrito', 'carrito', LectorController.carrito, methods=['GET'])
        self.add_url_rule('/actualizar_carrito', 'actualizar_carrito', LectorController.actualizar_carrito, methods=['POST'])
        self.add_url_rule('/dar_salida', 'dar_salida', LectorController.dar_salida, methods=['POST'])
        
        self.add_url_rule('/register_sale', 'register_sale', SalesController.register_sale, methods=['POST'])
        self.add_url_rule('/limpiar_carrito', 'limpiar_carrito', SalesController.limpiar_carrito, methods=['POST'])
        self.add_url_rule('/productos', 'productos', LectorController.productos, methods=['GET'])

    def disabled_user_error(self):
        return render_template('errors/disabled_user.html'), 403
    
    def statistic(self):
        """Renderiza la página de estadísticas con el gráfico generado"""
        stats = StatisticsController.get_sales_data()

        categories = ['Semana 1', 'Semana 2', 'Mes', 'Trimestre']
        values_sales = [float(stats["total_sales"])] * len(categories)
        values_transactions = [float(stats["total_transactions"])] * len(categories)
        values_profit = [float(stats["total_profit"])] * len(categories)

        chart_html = StatisticsController.generate_chart()

        return render_template("user/statistics.html", chart=chart_html, stats=stats)

    def register_sale(self):
        """Método para registrar una venta"""
        data = request.get_json()
        return jsonify({"message": "Venta registrada correctamente"}), 201


app = InventoryApp()

@app.before_request
def check_user_status():
    """Verifica el estado del usuario antes de cada solicitud"""
    session.permanent = True
    if 'user' in session:
        user = session['user']
        if user.get('is_active') == 0:
            return redirect(url_for('disabled_user_error'))

        admin_routes = ['admin_dashboard', 'create_user', 'edit_user', 'disable_user', 'enable_user']
        if request.endpoint in admin_routes and user.get('role') != 'admin':
            return render_template('errors/403.html'), 403

    return None

if __name__ == '__main__':
    app.run(debug=True)

