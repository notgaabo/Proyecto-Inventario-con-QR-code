from flask import session, render_template, request, redirect, url_for, flash
from auth.auth import User, Company
from db.config import Config

class UserController:
    @staticmethod
    def company_details(company_id):
        """Display detailed view of a company with its users."""
        if 'user' not in session or session['user'].get('role') != 'admin':
            return redirect(url_for('login'))

        try:
            with Config.get_db_connection() as connection:
                with connection.cursor(dictionary=True) as cursor:
                    # Obtener detalles de la empresa
                    cursor.execute("SELECT * FROM companies WHERE id = %s", (company_id,))
                    company = cursor.fetchone()
                    if not company:
                        flash("Company not found", "error")
                        return redirect(url_for('admin_dashboard'))

                    # Obtener usuarios de la empresa
                    cursor.execute(
                        "SELECT id, username, email, role, is_active FROM users WHERE company_id = %s",
                        (company_id,)
                    )
                    users = cursor.fetchall()

                    # Separar usuarios habilitados y deshabilitados
                    active_users = [u for u in users if u['is_active'] == 1]
                    disabled_users = [u for u in users if u['is_active'] == 0]

        except Exception as e:
            flash(f"Error loading company details: {str(e)}", "error")
            return redirect(url_for('admin_dashboard'))

        return render_template(
            'admin/company/company_details.html',  # Ajustado a la nueva ubicación
            company=company,
            active_users=active_users,
            disabled_users=disabled_users,
            valid_roles=['salesperson', 'warehouse_manager', 'manager']
        )

    @staticmethod
    def create_company():
        """Create a new company and redirect to user creation for that company."""
        if 'user' not in session or session['user'].get('role') != 'admin':
            return redirect(url_for('login'))

        if request.method == 'POST':
            name = request.form.get('name')
            industry = request.form.get('industry', '')
            address = request.form.get('address', '')
            phone = request.form.get('phone', '')
            
            if not name:
                flash("Company name is required", "error")
                return render_template('admin/company/company_create.html')

            try:
                company_id = Company.insert_company(name, industry, address, phone)
                flash("Company created successfully", "success")
                return redirect(url_for('create_users_for_company', company_id=company_id))
            except Exception as e:
                flash(f"Error creating company: {str(e)}", "error")
                return render_template('admin/company/company_create.html')

        return render_template('admin/company/company_create.html')

    @staticmethod
    def create_users_for_company(company_id):
        """Create users for a specific company."""
        if 'user' not in session or session['user'].get('role') != 'admin':
            return redirect(url_for('login'))

        company = Company.get_company_by_id(company_id)
        if not company:
            flash("Company not found", "error")
            return redirect(url_for('admin_dashboard'))

        try:
            with Config.get_db_connection() as connection:
                with connection.cursor(dictionary=True) as cursor:
                    # Obtener roles desde la tabla company_roles
                    cursor.execute("SELECT role_name FROM company_roles")
                    roles_data = cursor.fetchall()
                    valid_roles = [role['role_name'] for role in roles_data]  # Lista de role_name en español

        except Exception as e:
            flash(f"Error loading roles: {str(e)}", "error")
            valid_roles = []  # En caso de error, usar lista vacía

        if request.method == 'POST':
            username = request.form.get('username')
            email = request.form.get('email')
            password = request.form.get('password')
            role = request.form.get('role')

            if not all([username, email, password, role]):
                flash("All fields are required", "error")
                users = User.get_users_by_company(company_id)
                return render_template('admin/user_create.html', company=company, roles=valid_roles, users=users)

            if role not in valid_roles:
                flash("Invalid role selected", "error")
                users = User.get_users_by_company(company_id)
                return render_template('admin/user_create.html', company=company, roles=valid_roles, users=users)

            try:
                User.insert_user(username, email, password, role, company_id)
                flash("User created successfully", "success")
                return redirect(url_for('company_details', company_id=company_id))
            except Exception as e:
                flash(f"Error creating user: {str(e)}", "error")

        users = User.get_users_by_company(company_id)
        return render_template('admin/user_create.html', company=company, roles=valid_roles, users=users)

    @staticmethod
    def edit_user(user_id):
        """Edit an existing user's details."""
        if 'user' not in session or session['user'].get('role') != 'admin':
            return redirect(url_for('login'))

        user = User.get_user_by_id(user_id)
        if not user:
            flash("User not found", "error")
            return redirect(url_for('admin_dashboard'))

        if request.method == 'POST':
            username = request.form.get('username')
            email = request.form.get('email')
            password = request.form.get('password')  # Optional
            role = request.form.get('role')

            if not all([username, email, role]):
                flash("Username, email, and role are required", "error")
                roles = ['salesperson', 'warehouse_manager', 'manager']
                return render_template('admin/edit_user.html', user=user, roles=roles)

            valid_roles = ['salesperson', 'warehouse_manager', 'manager']
            if role not in valid_roles:
                flash("Invalid role selected", "error")
                roles = valid_roles
                return render_template('admin/edit_user.html', user=user, roles=roles)

            try:
                User.update_user(user_id, username, email, password, role)
                flash("User updated successfully", "success")
                return redirect(url_for('company_details', company_id=user['company_id']))
            except Exception as e:
                flash(f"Error updating user: {str(e)}", "error")

        roles = ['salesperson', 'warehouse_manager', 'manager']
        return render_template('admin/edit_user.html', user=user, roles=roles)

    @staticmethod
    def toggle_user_status(user_id):
        """Toggle the active status of a user."""
        if 'user' not in session or session['user'].get('role') != 'admin':
            return redirect(url_for('login'))

        try:
            user = User.get_user_by_id(user_id)
            if not user:
                flash("User not found", "error")
                return redirect(url_for('admin_dashboard'))

            User.toggle_user_status(user_id)
            flash("User status updated successfully", "warning")
            return redirect(url_for('company_details', company_id=user['company_id']))
        except Exception as e:
            flash(f"Error updating user status: {str(e)}", "error")
            return redirect(url_for('admin_dashboard'))