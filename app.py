#app.py

from flask import Flask, render_template, redirect, url_for, session, request
from datetime import timedelta
import os
from controllers.auth_controller import AuthController
from controllers.user_controller import UserController
from controllers.dashboard_controller import HomeController, StatisticsController

class InventoryApp(Flask):
    def __init__(self):
        super().__init__(__name__)
        self.secret_key = os.urandom(24)
        self.permanent_session_lifetime = timedelta(days=7)
        self.register_error_handlers()
        self.register_routes()

    def forbidden_error(self, e):
        """Manejador de error 403"""
        return render_template('errors/403.html'), 403
    
    def page_not_found(self, e):
        """Manejador de error 404"""
        return render_template('errors/404.html'), 404

    def register_error_handlers(self):
        """Registra los manejadores de errores"""
        self.register_error_handler(403, self.forbidden_error)
        self.register_error_handler(404, self.page_not_found)

    def register_routes(self):
        self.add_url_rule('/', 'home', HomeController.home)
        self.add_url_rule('/login', 'login', AuthController.login, methods=['GET', 'POST'])
        self.add_url_rule('/admin', 'admin_dashboard', UserController.admin_dashboard)
        self.add_url_rule('/create_user', 'create_user', UserController.create_user, methods=['GET', 'POST'])
        self.add_url_rule('/edit_user/<int:user_id>', 'edit_user', UserController.edit_user, methods=['GET', 'POST'])
        self.add_url_rule('/disable_user/<int:user_id>', 'disable_user', UserController.toggle_user_status, methods=['GET'])
        self.add_url_rule('/enable_user/<int:user_id>', 'enable_user', UserController.enable_user, methods=['GET'])
        self.add_url_rule('/statistics', 'statistics', StatisticsController.statistics)
        self.add_url_rule('/logout', 'logout', AuthController.logout)
        self.add_url_rule('/disabled_error', 'disabled_user_error', self.disabled_user_error)
        self.add_url_rule('/403', 'forbidden_error', self.forbidden_error)

    def disabled_user_error(self):
        """Página personalizada para usuarios deshabilitados"""
        return render_template('errors/disabled_user.html'), 403


app = InventoryApp()

@app.before_request
def check_user_status():
    """Verifica el estado del usuario antes de cada solicitud"""
    session.permanent = True
    if 'user' in session:
        user = session['user']
        
        # Verifica si el usuario está deshabilitado
        if user.get('is_active') == 0:
            return redirect(url_for('disabled_user_error'))

        # Verifica si intenta acceder a una ruta de admin sin ser admin
        admin_routes = ['admin_dashboard', 'create_user', 'edit_user', 'disable_user', 'enable_user']
        if request.endpoint in admin_routes and user.get('role') != 'admin':
            return render_template('errors/403.html'), 403  # Renderiza el error 403 sin redirigir

    return None

if __name__ == '__main__':
    app.run(debug=True)
