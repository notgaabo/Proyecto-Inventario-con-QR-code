from flask import session, render_template, request, redirect, url_for, flash
from auth.auth import is_authenticated
from auth.auth import get_user, insert_user, update_user, delete_user
from auth.auth import get_db_connection

def admin_dashboard_controller():
    if not is_authenticated() or session['user']['role'] != 'admin':
        return redirect(url_for('login'))
    
    usuarios = get_user()
    return render_template('admin/dashboard.html', usuarios=usuarios)

def create_user_controller():
    if not is_authenticated() or session['user']['role'] != 'admin':
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        role = request.form['role']
        insert_user(username, password, role)
        flash('Usuario creado exitosamente', 'success')
        return redirect(url_for('admin_dashboard'))
    
    return render_template('admin/user_create.html')

def edit_user_controller(user_id, request):
    if not is_authenticated() or session['user']['role'] != 'admin':
        return redirect(url_for('login'))
    
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
    user = cursor.fetchone()
    
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        role = request.form['role']
        update_user(user_id, username, password, role)
        flash('Usuario actualizado exitosamente', 'success')
        return redirect(url_for('admin_dashboard'))
    
    return render_template('admin/edit_user.html', user=user)

def delete_user_controller(user_id):
    if not is_authenticated() or session['user']['role'] != 'admin':
        return redirect(url_for('login'))
    
    delete_user(user_id)
    flash('Usuario eliminado exitosamente', 'danger')
    return redirect(url_for('admin_dashboard'))
