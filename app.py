from flask import Flask, render_template, redirect, url_for, session
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
        self.before_request(self.check_user_status)  # Verificación antes de cada solicitud
        self.register_error_handler(404, self.page_not_found)
        self.register_error_handler(403, self.forbidden_error)  # Manejador de error 403
        self.register_routes()

    def check_user_status(self):
        """Verifica el estado del usuario antes de cada solicitud"""
        session.permanent = True
        if 'user' in session:
            user = session['user']
            if user.get('is_active') == 0:
                # Si el usuario está deshabilitado, retorna el error 403
                return self.forbidden_error(None)

    def page_not_found(self, e):
        return render_template('errors/404.html'), 404

    def forbidden_error(self, e):
        """Manejador global de error 403 para cuando el usuario no tiene acceso"""
        return render_template('errors/403.html'), 403

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

    def disabled_user_error(self):
        """Página personalizada para usuarios deshabilitados"""
        return render_template('errors/disabled_user.html'), 403

if __name__ == '__main__':
    InventoryApp().run(debug=True)
