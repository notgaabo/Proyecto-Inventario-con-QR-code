from flask import Flask, render_template, request, redirect, url_for, flash, session
from datetime import timedelta
from controllers.auth_controller import login_controller, logout_controller
from controllers.user_controller import admin_dashboard_controller, crear_usuario_controller, editar_usuario_controller, eliminar_usuario_controller
from controllers.dashboard_controller import home_controller, statistics_controller
import os

app = Flask(__name__)
app.secret_key = os.urandom(24)
app.permanent_session_lifetime = timedelta(days=7)

@app.before_request
def make_session_permanent():
    session.permanent = True

@app.route('/')
def home():
    return home_controller()

@app.route('/login', methods=['GET', 'POST'])
def login():
    return login_controller(request)

@app.route('/admin_dashboard')
def admin_dashboard():
    return admin_dashboard_controller()

@app.route('/crear_usuario', methods=['GET', 'POST'])
def crear_usuario():
    return crear_usuario_controller(request)

@app.route('/editar_usuario/<int:user_id>', methods=['GET', 'POST'])
def editar_usuario(user_id):
    return editar_usuario_controller(user_id, request)

@app.route('/eliminar_usuario/<int:user_id>', methods=['GET'])
def eliminar_usuario_route(user_id):
    return eliminar_usuario_controller(user_id)

@app.route('/statistics')
def statistics():
    return statistics_controller()

@app.route('/logout')
def logout():
    return logout_controller()

if __name__ == '__main__':
    app.run(debug=True)
