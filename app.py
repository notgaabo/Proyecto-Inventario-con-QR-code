# app.py
from flask import Flask, request, session, render_template, redirect, url_for, flash
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
from controllers.sales_prediction import SalesPrediction
from controllers.invoice_controller import InvoiceGenerator
from controllers.returns_controller import returnsController
from controllers.supplier_controller import SupplierController
from controllers.notifications_controller import NotificationsController
from controllers.qr_print_controller import QRCodePrinter
from controllers.report_controller import ReportGenerator
from controllers.admin_statistics_controller import AdminStatisticsController
import time

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
    
    def page_not_found(self, e=None):
        return render_template('errors/404.html'), 404

    def disabled_user_error(self):
        return render_template('errors/disabled_user.html'), 403

    def register_error_handlers(self):
        self.register_error_handler(403, self.forbidden_error)
        self.register_error_handler(404, self.page_not_found)

    def register_routes(self):
        # Rutas básicas
        self.add_url_rule('/', 'home', HomeController.home)
        self.add_url_rule('/login', 'login', AuthController.login, methods=['GET', 'POST'])
        self.add_url_rule('/logout', 'logout', AuthController.logout)
        self.add_url_rule('/disabled_user', 'disabled_user_error', self.disabled_user_error)  # Ruta para disabled_user_error

        # Rutas de administración (solo admin)
        self.add_url_rule('/admin', 'admin_dashboard', AdminStatisticsController.admin_dashboard)
        self.add_url_rule('/company/<int:company_id>', 'company_details', UserController.company_details, methods=['GET'])
        self.add_url_rule('/create_company', 'create_company', UserController.create_company, methods=['GET', 'POST'])
        self.add_url_rule('/company/<int:company_id>/create_users', 'create_users_for_company', UserController.create_users_for_company, methods=['GET', 'POST'])
        self.add_url_rule('/edit_user/<int:user_id>', 'edit_user', UserController.edit_user, methods=['GET', 'POST'])
        self.add_url_rule('/toggle_user_status/<int:user_id>', 'toggle_user_status', UserController.toggle_user_status, methods=['GET'])

        # Rutas de estadísticas (gerente y admin)
        self.add_url_rule('/statistics', 'statistics', StatisticsController.statistics)
        self.add_url_rule('/statistics/chart', 'statistics_chart', StatisticsController.statistics)
        self.add_url_rule('/filter-sales', 'filer_sales', StatisticsController.filter_sales, methods=['GET'])
        self.add_url_rule('/sales_prediction', 'sales_prediction', SalesPrediction.get_sales_prediction)
        self.add_url_rule('/static/<path:filename>', 'send_image', SalesPrediction.send_image)

        # Rutas de productos (encargado de almacén, gerente, admin)
        self.add_url_rule('/product', 'product_list', ProductController.get_product_list, methods=['GET'])
        self.add_url_rule('/product/<int:product_id>', 'get_product_by_id', ProductController.get_product_by_id, methods=['GET'])
        self.add_url_rule('/add_product', 'add_product', ProductController.add_product, methods=['GET', 'POST'])
        self.add_url_rule('/edit_product/<int:product_id>', 'edit_product', ProductController.update_product, methods=['GET', 'POST'])
        self.add_url_rule('/delete_product/<int:product_id>', 'delete_product', ProductController.delete_product, methods=['POST'])

        # Rutas de inventario y QR (vendedor, encargado de almacén, gerente, admin)
        self.add_url_rule('/inventory', 'inventory', lambda: LectorController.inventory(stripe_public_key=self.config['STRIPE_PUBLIC_KEY']))
        self.add_url_rule('/escanear', 'escanear', LectorController.scan, methods=['POST'])
        self.add_url_rule('/carrito', 'carrito', LectorController.cart, methods=['GET'])
        self.add_url_rule('/actualizar_carrito', 'actualizar_carrito', LectorController.update_cart, methods=['POST'])
        self.add_url_rule('/products', 'products', LectorController.products)
        self.add_url_rule('/checkout', 'checkout', LectorController.checkout, methods=['POST'])
        self.add_url_rule('/generate_qr/<int:product_id>', 'generate_qr', QrController.generate_qr)

        # Rutas de órdenes de empresas 
        self.add_url_rule('/create_order', 'create_order', OrderController.create_order, methods=['GET', 'POST'])
        self.add_url_rule('/orders', 'order_list', OrderController.order_list, methods=['GET'])
        self.add_url_rule('/orders/receive_multiple', 'receive_multiple_orders', OrderController.receive_multiple_orders, methods=['POST'])
        self.add_url_rule('/orders/<int:order_id>', 'view_order', OrderController.view_order, methods=['GET'])
        self.add_url_rule('/receive_order', 'receive_order', OrderController.receive_order, methods=['GET', 'POST'])
        
        # Rutas de ventas (todos los roles autenticados)
        self.add_url_rule('/register_sale', 'register_sale', SalesController.register_sale, methods=['POST'])
        self.add_url_rule('/sales_history', 'sales_history', ProductController.sales_history, methods=['GET'])

        # Reportes
        self.add_url_rule('/factura', 'get_factura', InvoiceGenerator.get_factura, methods=['GET'])
        self.add_url_rule('/last_delivered_products', 'last_delivered_products', QRCodePrinter.get_last_delivered_products, methods=['GET'])
        self.add_url_rule('/print_qr_for_order', 'print_qr_for_order', QRCodePrinter.print_qr_for_order, methods=['GET'])
        self.add_url_rule('/print_qr_for_product', 'print_qr_for_product', QRCodePrinter.print_qr_for_product, methods=['GET'])
        self.add_url_rule('/', 'index', ReportGenerator.index, methods=['GET'])
        self.add_url_rule('/generate_report/<report_type>', 'generate_report', ReportGenerator.generate_report, methods=['GET'])  
        self.add_url_rule('/report', 'report', ReportGenerator.report, methods=['GET'])

        # Devoluciones
        self.add_url_rule('/return', 'returns_list', returnsController.return_list)
        self.add_url_rule('/return/<int:return_id>', 'view_return', returnsController.view_return)
        self.add_url_rule('/return', 'returns_list', returnsController.return_list)
        self.add_url_rule('/return/new', 'returns_new', returnsController.add_return, methods=['GET', 'POST'])
        self.add_url_rule('/api/sale/<int:sale_group_id>', 'get_sale_data', returnsController.get_sale_data, methods=['GET'])

        # Suplidores
        self.add_url_rule('/add_supplier', 'add_supplier', SupplierController.add_supplier, methods=['GET', 'POST'])
        self.add_url_rule('/suppliers', 'supplier_list', SupplierController.supplier_list)
        self.add_url_rule('/suppliers/edit/<int:supplier_id>', 'edit_supplier', SupplierController.edit_supplier, methods=['GET', 'POST'])

        # Notificaciones
        self.add_url_rule('/notifications', 'get_notifications_route', NotificationsController.get_notifications, methods=['GET'])
        self.add_url_rule('/notifications/<notification_id>/read', 'mark_notification_as_read_route', NotificationsController.mark_notification_as_read, methods=['POST'])

        # Gestión de empresas (solo admin)  
        self.add_url_rule('/manage_companies', 'manage_companies', CompanyController.manage_companies, methods=['GET'])
        self.add_url_rule('/edit_company', 'edit_company', CompanyController.edit_company, methods=['POST'])
        self.add_url_rule('/disable_company/<int:company_id>', 'disable_company', CompanyController.disable_company, methods=['GET'])
        self.add_url_rule('/enable_company/<int:company_id>', 'enable_company', CompanyController.enable_company, methods=['GET'])

app = InventoryApp()

@app.before_request
def check_user_status():
    session.permanent = True

    if request.endpoint is None:
        return app.page_not_found(e=None)

    # Ignorar rutas específicas para evitar verificaciones innecesarias
    if request.endpoint in ['login', 'disabled_user_error', 'static']:
        return None

    # Redirigir al login si no hay usuario en la sesión
    if 'user' not in session:
        return redirect(url_for('login'))

    # Obtener datos del usuario
    user = session['user']
    role = user.get('role', '').lower()  # Asegurar roles en minúscula
    company_id = user.get('company_id')  # Obtener company_id

    # Verificar si el usuario tiene un rol válido
    if not role:
        session.pop('user', None)
        flash("Sesión inválida. Por favor, inicia sesión nuevamente.", "error")
        return redirect(url_for('login'))

    # Verificar el estado de la empresa
    if company_id:
        try:
            with db.get_db_connection() as connection:
                with connection.cursor(dictionary=True) as cursor:
                    cursor.execute("SELECT is_active FROM companies WHERE id = %s", (company_id,))
                    company = cursor.fetchone()
                    if company and not company['is_active']:
                        # Empresa desactivada: cerrar sesión y mostrar mensaje
                        session.pop('user', None)
                        flash("Tu empresa ha sido desactivada. Contacta al administrador.", "error")
                        return redirect(url_for('disabled_user_error'))
        except Exception as e:
            session.pop('user', None)
            flash(f"Error al verificar el estado de la empresa: {str(e)}", "error")
            return redirect(url_for('disabled_user_error'))

    # Verificación de permisos por rol
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
    if request.endpoint in product_routes and role not in ['gerente', 'admin']:
        return app.forbidden_error()
    if request.endpoint in stats_routes and role not in ['gerente', 'admin']:
        return app.forbidden_error()
    if request.endpoint in inventory_routes and role not in ['vendedor', 'gerente', 'admin']:
        return app.forbidden_error()

    # Rutas de ventas no necesitan restricción adicional más allá de autenticación
    if request.endpoint == 'register_sale' and 'user' not in session:
        return app.forbidden_error()

    # Redirección según el rol en la ruta 'home'
    if request.endpoint == 'home':
        if role == 'vendedor':
            return redirect(url_for('inventory'))
        elif role == 'encargado de almacén':
            return redirect(url_for('order_list'))
        elif role == 'gerente':
            return redirect(url_for('statistics'))
        elif role == 'admin':
            return redirect(url_for('admin_dashboard'))

    return None

if __name__ == '__main__':
    app.run(debug=True)