from flask import Flask, render_template, session, redirect, url_for
import functools

app = Flask(__name__)

# Simulación de sesión con un usuario logueado
session['user'] = {'id': 1, 'role': 'admin'}  # Este es un ejemplo; deberías obtener el rol de la base de datos.

# Decorador para verificar el rol del usuario
def role_required(roles):
    def decorator(f):
        @functools.wraps(f)
        def decorated_function(*args, **kwargs):
            user = session.get('user')
            if user and user['role'] in roles:
                return f(*args, **kwargs)
            return redirect(url_for('unauthorized'))
        return decorated_function
    return decorator

@app.route('/')
def home():
    # Dependiendo del rol, redirigir a la plantilla correspondiente
    user = session.get('user')
    if user:
        if user['role'] == 'admin':
            return redirect(url_for('admin_dashboard'))
        elif user['role'] == 'user':
            return redirect(url_for('user_dashboard'))
    return redirect(url_for('unauthorized'))

@app.route('/admin')
@role_required(['admin'])  # Solo acceso para admin
def admin_dashboard():
    return render_template('admin/dashboard.html')  # Aquí puedes renderizar la plantilla del administrador

@app.route('/user')
@role_required(['user'])  # Solo acceso para user
def user_dashboard():
    return render_template('user/dashboard.html')  # Aquí puedes renderizar la plantilla del usuario

@app.route('/unauthorized')
def unauthorized():
    return "You are not authorized to view this page."

if __name__ == '__main__':
    app.run(debug=True)
