from flask import session, redirect, url_for, flash, render_template, request
from auth.auth import authenticate_user, login_user, logout_user, is_authenticated

def login_controller():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if not username or not password:
            flash('Por favor, completa ambos campos.', 'warning')
            return render_template('login.html')
        
        user = authenticate_user(username, password)
        if user:
            login_user(user)
            flash('Inicio de sesión exitoso', 'success')
            if user.get('role') == 'admin':
                return redirect(url_for('admin_dashboard'))
            else:
                return redirect(url_for('statistics'))
        else:
            flash('Credenciales incorrectas. Intenta nuevamente.', 'danger')
            return render_template('login.html')

    # Retorna la plantilla de login para solicitudes GET o si hay errores
    return render_template('login.html')

def logout_controller():
    logout_user()
    flash('Has cerrado sesión exitosamente', 'info')
    return redirect(url_for('login'))
