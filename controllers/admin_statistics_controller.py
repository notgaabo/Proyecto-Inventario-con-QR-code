from flask import session, redirect, url_for, render_template, flash
from db.config import Config

class AdminStatisticsController:
    @staticmethod
    def admin_dashboard():
        """Display the admin dashboard with a list of companies, their users, and general statistics."""
        if 'user' not in session:
            return redirect(url_for('login'))

        user_role = session['user'].get('role')
        user_company_id = session['user'].get('company_id')

        if user_role != 'admin':
            return redirect(url_for('forbidden_error'))

        try:
            with Config.get_db_connection() as connection:
                with connection.cursor(dictionary=True) as cursor:
                    # Obtener empresas
                    if user_company_id is None:
                        cursor.execute("SELECT * FROM companies")
                        companies = cursor.fetchall()
                    else:
                        cursor.execute("SELECT * FROM companies WHERE id = %s", (user_company_id,))
                        companies = cursor.fetchall()

                    # Clasificar empresas activas e inactivas
                    active_companies = [c for c in companies if c.get('is_active', 1) == 1]
                    disabled_companies = [c for c in companies if c.get('is_active', 1) == 0]

                    # Obtener usuarios por empresa
                    for company in companies:
                        cursor.execute(
                            "SELECT id, username, email, role, is_active FROM users WHERE company_id = %s",
                            (company['id'],)
                        )
                        company['users'] = cursor.fetchall()

                    # Usuarios sin empresa (solo para admin global)
                    global_users = []
                    if user_company_id is None:
                        cursor.execute(
                            "SELECT id, username, email, role, is_active FROM users WHERE company_id IS NULL"
                        )
                        global_users = cursor.fetchall()

                    # Estadísticas generales
                    cursor.execute("SELECT COUNT(*) AS total_active_companies FROM companies WHERE is_active = 1")
                    total_active_companies = cursor.fetchone()['total_active_companies']

                    cursor.execute("SELECT COUNT(*) AS total_disabled_companies FROM companies WHERE is_active = 0")
                    total_disabled_companies = cursor.fetchone()['total_disabled_companies']

                    cursor.execute("SELECT COUNT(*) AS total_users FROM users")
                    total_users = cursor.fetchone()['total_users']

                    cursor.execute("SELECT COUNT(*) AS total_active_users FROM users WHERE is_active = 1")
                    total_active_users = cursor.fetchone()['total_active_users']

        except Exception as e:
            flash(f"Error loading dashboard: {str(e)}", "error")
            return render_template(
                'admin/dashboard.html',
                active_companies=[],
                disabled_companies=[],
                global_users=[],
                total_active_companies=0,
                total_disabled_companies=0,
                total_users=0,
                total_active_users=0
            )

        return render_template(
            'admin/dashboard.html',
            active_companies=active_companies,
            disabled_companies=disabled_companies,
            global_users=global_users,
            total_active_companies=total_active_companies,
            total_disabled_companies=total_disabled_companies,
            total_users=total_users,
            total_active_users=total_active_users
        )
