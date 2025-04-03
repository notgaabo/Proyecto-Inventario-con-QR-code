from flask import Flask, request, jsonify, session, render_template, redirect, url_for
import os
from db import Config as db
from datetime import datetime, timedelta
from controllers.dashboard_controller import HomeController  
from controllers.auth_controller import AuthController
from controllers.user_controller import UserController
from controllers.statistic_controller import StatisticsController
from controllers.product_controller import ProductController
from controllers.qr_controller import QrController, LectorController
from controllers.sales_controller import SalesController
from controllers.company_controller import CompanyController
from controllers.order_controller import OrderController

class InventoryApp(Flask):
    def __init__(self):
        super().__init__(__name__)
        self.secret_key = 'StockBeam'
        self.config['STRIPE_PUBLIC_KEY'] = os.environ.get('STRIPE_PUBLIC_KEY', 'pk_test_xxx')
        self.config['STRIPE_SECRET_KEY'] = os.environ.get('STRIPE_SECRET_KEY', 'sk_test_xxx')
        self.permanent_session_lifetime = timedelta(days=7)
        self.register_error_handlers()
        self.register_routes()

    def forbidden_error(self, e=None):
        return render_template('errors/403.html'), 403
    
    def page_not_found(self, e):
        return render_template('errors/404.html'), 404

    def register_error_handlers(self):
        self.register_error_handler(403, self.forbidden_error)
        self.register_error_handler(404, self.page_not_found)

    def register_routes(self):
        # Rutas básicas
        self.add_url_rule('/', 'home', HomeController.home)
        self.add_url_rule('/login', 'login', AuthController.login, methods=['GET', 'POST'])
        self.add_url_rule('/logout', 'logout', AuthController.logout)

        # Rutas de administración (solo admin)
        self.add_url_rule('/admin', 'admin_dashboard', UserController.admin_dashboard)
        self.add_url_rule('/company/<int:company_id>', 'company_details', UserController.company_details, methods=['GET'])
        self.add_url_rule('/create_company', 'create_company', UserController.create_company, methods=['GET', 'POST'])
        self.add_url_rule('/company/<int:company_id>/create_users', 'create_users_for_company', UserController.create_users_for_company, methods=['GET', 'POST'])
        self.add_url_rule('/edit_user/<int:user_id>', 'edit_user', UserController.edit_user, methods=['GET', 'POST'])
        self.add_url_rule('/toggle_user_status/<int:user_id>', 'toggle_user_status', UserController.toggle_user_status, methods=['GET'])

        # Rutas de estadísticas (gerente y admin)
        self.add_url_rule('/statistics', 'statistics', StatisticsController.statistics)
        self.add_url_rule('/statistics/chart', 'statistics_chart', StatisticsController.statistics)
        self.add_url_rule('/filter-sales', 'filer_sales', StatisticsController.filter_sales, methods=['GET'])

        # Rutas de productos (encargado de almacén, gerente, admin)
        self.add_url_rule('/product', 'product_list', ProductController.get_product_list, methods=['GET'])
        self.add_url_rule('/add_product', 'add_product', ProductController.add_product, methods=['GET', 'POST'])
        self.add_url_rule('/edit_product/<int:product_id>', 'edit_product', ProductController.update_product, methods=['GET', 'POST'])
        self.add_url_rule('/delete_product/<int:product_id>', 'delete_product', ProductController.delete_product, methods=['POST'])

        # Rutas de inventario y QR (vendedor, encargado de almacén, gerente, admin)
        self.add_url_rule('/inventory', 'inventory', lambda: LectorController.inventory(stripe_public_key=self.config['STRIPE_PUBLIC_KEY']))
        self.add_url_rule('/escanear', 'escanear', LectorController.scan, methods=['POST'])
        self.add_url_rule('/carrito', 'carrito', LectorController.cart, methods=['GET'])
        self.add_url_rule('/actualizar_carrito', 'actualizar_carrito', LectorController.update_cart, methods=['POST'])
        self.add_url_rule('/products', 'products', LectorController.products)  # Añadida
        self.add_url_rule('/checkout', 'checkout', LectorController.checkout, methods=['POST'])  # Añadida
        self.add_url_rule('/generate_qr/<int:product_id>', 'generate_qr', QrController.generate_qr)  # Añadida

        # Ruta de las ordenes de empresas 
                # Assuming this is in your Flask app initialization (e.g., app.py or similar)
        self.add_url_rule('/create_order', 'create_order', OrderController.create_order, methods=['GET', 'POST'])
        self.add_url_rule('/orders', 'order_list', OrderController.order_list, methods=['GET'])
        self.add_url_rule('/orders/receive_multiple', 'receive_multiple_orders', OrderController.receive_multiple_orders, methods=['POST'])  # New route
        self.add_url_rule('/orders/<int:order_id>', 'view_order', OrderController.view_order, methods=['GET'])
        self.add_url_rule('/get_order_details/<int:order_id>', 'get_order_details', OrderController.get_order_details, methods=['GET'])
        # Optional: Keep this if you still need single-order receiving elsewhere
        self.add_url_rule('/receive_order', 'receive_order', OrderController.receive_order, methods=['GET', 'POST'])
        
        # Rutas de ventas (todos los roles autenticados)
        self.add_url_rule('/register_sale', 'register_sale', SalesController.register_sale, methods=['POST'])
        self.add_url_rule('/sales_history', 'sales_history', ProductController.sales_history, methods=['GET'])

        # Gestión de empresas (solo admin)
        self.add_url_rule('/manage_companies', 'manage_companies', CompanyController.manage_companies, methods=['GET'])
        self.add_url_rule('/edit_company', 'edit_company', CompanyController.edit_company, methods=['POST'])
        self.add_url_rule('/disable_company/<int:company_id>', 'disable_company', CompanyController.disable_company, methods=['GET'])
        self.add_url_rule('/enable_company/<int:company_id>', 'enable_company', CompanyController.enable_company, methods=['GET'])

    def disabled_user_error(self):
        return render_template('errors/disabled_user.html'), 403

app = InventoryApp()

@app.before_request
def check_user_status():
    session.permanent = True

    if request.endpoint is None:
        return redirect(url_for('login'))

    if 'user' not in session and request.endpoint not in ['login', 'disabled_user_error']:
        return redirect(url_for('login'))

    if 'user' in session:
        user = session['user']
        role = user.get('role', '').lower()  # Asegurar roles en minúscula

        if not role:
            return redirect(url_for('login'))

        admin_routes = [
            'admin_dashboard', 'company_details', 'create_company', 'create_users_for_company',
            'edit_user', 'toggle_user_status', 'manage_companies', 'edit_company',
            'disable_company', 'enable_company'
        ]
        product_routes = [
            'product_list', 'add_product', 'edit_product', 'delete_product'
        ]
        stats_routes = [
            'statistics', 'statistics_chart'
        ]
        inventory_routes = [
            'inventory', 'escanear', 'carrito', 'actualizar_carrito', 'products', 'checkout', 'generate_qr'
        ]

        if request.endpoint in admin_routes and role != 'admin':
            return app.forbidden_error()
        if request.endpoint in product_routes and role not in ['encargado de almacén', 'gerente', 'admin']:
            return app.forbidden_error()
        if request.endpoint in stats_routes and role not in ['gerente', 'admin']:
            return app.forbidden_error()
        if request.endpoint in inventory_routes and role not in ['vendedor', 'encargado de almacén', 'gerente', 'admin']:
            return app.forbidden_error()

        # Rutas de ventas no necesitan restricción adicional más allá de autenticación
        if request.endpoint == 'register_sale' and 'user' not in session:
            return app.forbidden_error()

        if request.endpoint == 'home':
            if role == 'vendedor':
                return redirect(url_for('inventory'))
            elif role == 'encargado de almacén':
                return redirect(url_for('product_list'))
            elif role == 'gerente':
                return redirect(url_for('statistics'))
            elif role == 'admin':
                return redirect(url_for('admin_dashboard'))

    return None

if __name__ == '__main__':
    app.run(debug=True)