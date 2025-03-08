from flask import session, render_template, request, redirect, url_for, flash
from auth.auth import User

class UserController:
    @staticmethod
    def admin_dashboard():
        if 'user' not in session:
            return redirect(url_for('login'))
        
        if session['user'].get('role') != 'admin':
            return redirect(url_for('forbidden_error'))

        usuarios_activos = User.get_user()
        disabled_users = User.get_disabled_users()
        
        return render_template('admin/dashboard.html', usuarios_activos=usuarios_activos, disabled_users=disabled_users)

    @staticmethod
    def create_user():
        if 'user' not in session:
            return redirect(url_for('login'))
        
        if session['user'].get('role') != 'admin':
            return redirect(url_for('forbidden_error'))
        
        if request.method == 'POST':
            username = request.form['username']
            email = request.form['email']
            password = request.form['password']
            role = request.form['role']
            User.insert_user(username, password, role)
            flash('Usuario creado exitosamente', 'success')
            return redirect(url_for('admin_dashboard'))
        
        return render_template('admin/user_create.html')

    @staticmethod
    def edit_user(user_id):
        if 'user' not in session:
            return redirect(url_for('login'))
        
        if session['user'].get('role') != 'admin':
            return redirect(url_for('forbidden_error'))

        user = User.get_user_by_id(user_id)
        if not user:
            flash('Usuario no encontrado', 'error')
            return redirect(url_for('admin_dashboard'))

        if request.method == 'POST':
            username = request.form['username']
            role = request.form['role']
            password = request.form['password'] if request.form['password'] else None
            User.update_user(user_id, username, password, role)
            flash('Usuario actualizado exitosamente', 'success')
            return redirect(url_for('admin_dashboard'))
        
        return render_template('admin/edit_user.html', user=user)

    @staticmethod
    def toggle_user_status(user_id):
        if 'user' not in session:
            return redirect(url_for('login'))
        
        if session['user'].get('role') != 'admin':
            return redirect(url_for('forbidden_error'))
        
        User.toggle_user_status(user_id)
        flash('Estado del usuario actualizado correctamente', 'warning')
        return redirect(url_for('admin_dashboard'))

    @staticmethod
    def enable_user(user_id):
        if 'user' not in session:
            return redirect(url_for('login'))
        
        if session['user'].get('role') != 'admin':
            return redirect(url_for('forbidden_error'))
        
        User.activate_user(user_id)
        flash("Usuario activado correctamente.", "success")
        return redirect(url_for('admin_dashboard'))
    
    @staticmethod
    def disable_user(user_id):
        if 'user' not in session:
            return redirect(url_for('login'))
        
        if session['user'].get('role') != 'admin':
            return redirect(url_for('forbidden_error'))
        
        User.deactivate_user(user_id)
        flash("Usuario desactivado correctamente.", "danger")
        return redirect(url_for('admin_dashboard'))
