# controllers/auth_controller.py
from flask import session, redirect, url_for, flash, render_template, request
from auth.auth import Auth

class AuthController:
    @staticmethod
    def login():
        """Handle user login and redirect based on role."""
        if request.method == 'POST':
            username = request.form.get('username')
            password = request.form.get('password')

            if not username or not password:
                flash('Por favor, completa ambos campos.', 'warning')
                return render_template('login.html')

            user = Auth.authenticate_user(username, password)
            print(f"User from DB: {user}")  # Debug: Verifica qué devuelve la BD

            if user == 'disabled':
                flash('Tu cuenta está deshabilitada. Contacta al administrador.', 'warning')
                return render_template('errors/disabled_user.html')

            if user:
                Auth.login_user(user)
                print(f"Session after login: {session['user']}")  # Debug: Verifica la sesión
                role = user.get('role')
                print(f"Role extracted: {role}")  # Debug: Verifica el rol específico
                
                # Mensaje de bienvenida según rol
                if role == 'admin':
                    flash('Bienvenido, administrador!', 'success')
                elif role in ['vendedor', 'encargado de almacén', 'gerente']:
                    flash(f'Bienvenido, {role}!', 'success')
                else:
                    flash(f'Rol no reconocido: {role}. Contacta al administrador.', 'warning')
                    return redirect(url_for('login'))

                # Redirección según rol
                if role == 'admin':
                    return redirect(url_for('admin_dashboard'))
                elif role == 'vendedor':
                    return redirect(url_for('inventory'))
                elif role == 'encargado de almacén':
                    return redirect(url_for('product_list'))
                elif role == 'gerente':
                    return redirect(url_for('statistics'))

            flash('Credenciales incorrectas. Intenta nuevamente.', 'danger')

        return render_template('login.html')

    @staticmethod
    def logout():
        """Maneja el cierre de sesión de usuarios"""
        Auth.logout_user()
        flash('Has cerrado sesión exitosamente', 'info')
        return redirect(url_for('login'))