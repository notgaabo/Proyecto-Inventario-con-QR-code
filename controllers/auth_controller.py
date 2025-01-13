from flask import session, redirect, url_for, flash
from auth.auth import authenticate_user, login_user, logout_user, is_authenticated

def login_controller(request):
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user = authenticate_user(username, password)
        if user:
            login_user(user)
            flash('Login exitoso', 'success')
            if user['role'] == 'admin':
                return redirect(url_for('admin_dashboard'))
            else:
                return redirect(url_for('statistics'))
        else:
            flash('Credenciales incorrectas. Intenta nuevamente.', 'danger')

    return None  # Para ser manejado en el archivo app.py

def logout_controller():
    logout_user()
    flash('Has cerrado sesión exitosamente', 'info')
    return redirect(url_for('login'))
