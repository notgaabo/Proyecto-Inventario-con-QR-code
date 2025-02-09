 # controllers/user_controller.py



from flask import session, render_template, request, redirect, url_for, flash
from auth.auth import Auth, User  # Importamos la clase User

class UserController:
    @staticmethod
    def admin_dashboard():
        if 'user' not in session or session['user'].get('role') != 'admin':
            return redirect(url_for('login'))
        
        # Obtener usuarios activos e inactivos
        usuarios_activos = User.get_user()  # Debes asegurarte de que 'get_user' obtenga todos los usuarios
        disabled_users = User.get_disabled_users()  # Usamos get_disabled_users() para obtener los deshabilitados
        
        # Renderizamos el template pasando ambos grupos de usuarios
        return render_template('admin/dashboard.html', usuarios_activos=usuarios_activos, disabled_users=disabled_users)

    @staticmethod
    def create_user():
        if 'user' not in session or session['user'].get('role') != 'admin':
            return redirect(url_for('login'))
        
        if request.method == 'POST':
            username = request.form['username']
            password = request.form['password']
            role = request.form['role']
            User.insert_user(username, password, role)  # Usamos insert_user() de la clase User
            flash('Usuario creado exitosamente', 'success')
            return redirect(url_for('admin_dashboard'))
        
        return render_template('admin/user_create.html')

    @staticmethod
    def edit_user(user_id):
        if 'user' not in session or session['user'].get('role') != 'admin':
            return redirect(url_for('login'))
        
        user = User.get_user_by_id(user_id)  # Usamos una nueva función para obtener un usuario por ID
        
        if request.method == 'POST':
            username = request.form['username']
            password = request.form['password']
            role = request.form['role']
            User.update_user(user_id, username, password, role)  # Usamos update_user() de la clase User
            flash('Usuario actualizado exitosamente', 'success')
            return redirect(url_for('admin_dashboard'))
        
        return render_template('admin/edit_user.html', user=user)

    @staticmethod
    def toggle_user_status(user_id):
        """Activa o desactiva un usuario según su estado actual."""
        if 'user' not in session or session['user'].get('role') != 'admin':
            return redirect(url_for('login'))
        
        User.toggle_user_status(user_id)  # Usamos toggle_user_status() de la clase User
        flash('Estado del usuario actualizado correctamente', 'warning')
        return redirect(url_for('admin_dashboard'))

    @staticmethod
    def enable_user(user_id):
        if 'user' not in session or session['user'].get('role') != 'admin':
            return redirect(url_for('login'))
        
        User.enable_user_in_db(user_id)  # Usamos enable_user_in_db() de la clase User
        flash("Usuario activado correctamente.", "success")
        return redirect(url_for('admin_dashboard'))
    
    @staticmethod
    def disable_user(user_id):
        if 'user' not in session or session['user'].get('role') != 'admin':
            return redirect(url_for('login'))
        
        User.disable_user_in_db(user_id)  # Usamos disable_user_in_db() de la clase User
        flash("Usuario desactivado correctamente.", "danger")
        return redirect(url_for('admin_dashboard'))  # Redirigimos al dashboard

    @staticmethod
    def get_active_users():
        active_users = User.get_active_users()  # Usamos get_active_users() de la clase User
        return active_users

    @staticmethod
    def get_disabled_users():
        disabled_users = User.get_disabled_users()  # Usamos get_disabled_users() de la clase User
        return disabled_users
