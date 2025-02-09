from flask import session, redirect, url_for, flash, render_template, request
from auth.auth import Auth

class AuthController:
    @staticmethod
    def login():
        if request.method == 'POST':
            username = request.form.get('username')
            password = request.form.get('password')

            if not username or not password:
                flash('Por favor, completa ambos campos.', 'warning')
                return render_template('login.html')

            user = Auth.authenticate_user(username, password)

            if user == 'disabled': 
                flash('Tu cuenta está deshabilitada. Contacta al administrador.', 'warning')
                return render_template('errors/disabled_user.html')

            if user:  
                Auth.login_user(user)
                flash('Inicio de sesión exitoso', 'success')
                return redirect(url_for('admin_dashboard') if user.get('role') == 'admin' else url_for('statistics'))

            flash('Credenciales incorrectas. Intenta nuevamente.', 'danger')

        return render_template('login.html')

    @staticmethod
    def logout():
        Auth.logout_user()
        flash('Has cerrado sesión exitosamente', 'info')
        return redirect(url_for('login'))
