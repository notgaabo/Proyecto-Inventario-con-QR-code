# controllers/dashboard_controller.py

from flask import render_template, session, redirect, url_for
from auth.auth import Auth
from db import Config  # Added missing import

class HomeController:
    @staticmethod
    def home():
        if not Auth.is_authenticated():
            return redirect(url_for('login'))

        user = session['user']
        if user.get('role') == 'admin':  # Use .get() for safety
            return redirect(url_for('admin_dashboard'))
        elif user.get('role') == 'manager':  # Updated from 'gerente'
            return redirect(url_for('statistics'))
        elif user.get('role') == 'warehouse_manager':  # Updated from 'encargado_almacen'
            return redirect(url_for('product_list'))
        elif user.get('role') == 'salesperson':  # Updated from 'vendedor'
            return redirect(url_for('inventory'))
        else:
            # Handle unexpected roles (optional)
            return redirect(url_for('login'))  # Or a default page

class StatisticsController:
    @staticmethod
    def statistics():
        """Muestra las estadísticas del usuario si está autenticado."""
        if not Auth.is_authenticated():
            return redirect(url_for('login'))  # Si no está autenticado, lo redirige al login

        user = session['user']
        return render_template('user/statistics.html', user=user)  # Renderiza la plantilla de estadísticas
    
    @staticmethod
    def generator_statistic():
        """
        Generador de estadísticas del usuario.
        Devuelve estadísticas básicas del usuario autenticado.
        """
        if not Auth.is_authenticated():
            return redirect(url_for('login'))

        user = session['user']
        stats = {
            'user_id': user.get('id'),
            'username': user.get('username'),
            'login_count': 0,
            'last_login': None,
            'total_actions': 0
        }

        return render_template('user/statistics.html', stats=stats, user=user)

            # En un entorno de producción, usarías un logger aquí
        print(f"Error generating statistics: {str(e)}")
        return render_template(
            'user/statistics.html', 
            user=user, 
            error="Error al generar estadísticas"
        )