 # controllers/dashboard_controller.py

from flask import render_template, session, redirect, url_for
from auth.auth import Auth

class HomeController:
    @staticmethod
    def home():
        """Redirige al usuario a su dashboard según su rol."""
        if not Auth.is_authenticated():
            return redirect(url_for('login'))  # Si no está autenticado, lo redirige al login

        user = session['user']
        if user['role'] == 'admin':
            return redirect(url_for('admin_dashboard'))  # Redirige al dashboard de admin
        else:
            return redirect(url_for('statistics'))  # Redirige al dashboard de usuario

class StatisticsController:
    @staticmethod
    def statistics():
        """Muestra las estadísticas del usuario si está autenticado."""
        if not Auth.is_authenticated():
            return redirect(url_for('login'))  # Si no está autenticado, lo redirige al login

        user = session['user']
        return render_template('user/statistics.html', user=user)  # Renderiza la plantilla de estadísticas
    
    @staticmethod
    def generator_statisticI():
        """Generador de estadísticas del usuario."""
        # Implementación del código para generar las estadísticas del usuario
        
        