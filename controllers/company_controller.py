# controllers/company_controller.py
from flask import session, render_template, request, redirect, url_for, flash
from auth.auth import User, Company
from db.config import Config

class CompanyController:
    @staticmethod
    def manage_companies():
        """Muestra la lista de empresas activas y deshabilitadas"""
        if 'user' not in session or session['user'].get('role') != 'admin':
            return redirect(url_for('login'))

        try:
            with Config.get_db_connection() as connection:
                with connection.cursor(dictionary=True) as cursor:
                    cursor.execute("SELECT id, name, industry, address, phone FROM companies WHERE is_active = 1")
                    active_companies = cursor.fetchall()
                    cursor.execute("SELECT id, name, industry, address, phone FROM companies WHERE is_active = 0")
                    disabled_companies = cursor.fetchall()
            return render_template('admin/dashboard.html', 
                                 active_companies=active_companies, 
                                 disabled_companies=disabled_companies)
        except Exception as e:
            flash(f"Error al cargar empresas: {str(e)}", "error")

    @staticmethod
    def create_company():
        """Crea una nueva empresa"""
        if 'user' not in session or session['user'].get('role') != 'admin':
            return redirect(url_for('login'))

        if request.method == 'POST':
            name = request.form.get('name')
            industry = request.form.get('industry', '')
            address = request.form.get('address', '')
            phone = request.form.get('phone', '')

            if not name:
                flash("El nombre es obligatorio", "error")
                return redirect(url_for('manage_companies'))
            if not industry:
                flash("El sector es obligatorio", "error")
                return redirect(url_for('manage_companies'))
            if not address:
                flash("La dirección es obligatoria", "error")
                return redirect(url_for('manage_companies'))
            if not phone:
                flash("El teléfono es obligatorio", "error")
                return redirect(url_for('manage_companies'))
                
            try:
                with Config.get_db_connection() as connection:
                    with connection.cursor() as cursor:
                        cursor.execute("""
                            INSERT INTO companies (name, industry, address, phone, is_active)
                            VALUES (%s, %s, %s, %s, %s)
                        """, (name, industry, address, phone, 1))
                        connection.commit()
                flash("Empresa creada exitosamente", "success")
            except Exception as e:
                flash(f"Error al crear empresa: {str(e)}", "error")
            return redirect(url_for('manage_companies'))
        return redirect(url_for('manage_companies'))

    @staticmethod
    def edit_company():
        """Edita una empresa existente"""
        if 'user' not in session or session['user'].get('role') != 'admin':
            return redirect(url_for('login'))

        if request.method == 'POST':
            company_id = request.form.get('company_id')
            name = request.form.get('name')
            industry = request.form.get('industry', '')
            address = request.form.get('address', '')
            phone = request.form.get('phone', '')

            if not company_id or not name:
                flash("ID y nombre son obligatorios", "error")
                return redirect(url_for('manage_companies'))

            try:
                with Config.get_db_connection() as connection:
                    with connection.cursor() as cursor:
                        cursor.execute("""
                            UPDATE companies 
                            SET name = %s, industry = %s, address = %s, phone = %s
                            WHERE id = %s AND is_active = 1
                        """, (name, industry, address, phone, company_id))
                        connection.commit()
                        if cursor.rowcount == 0:
                            flash("Empresa no encontrada o no activa", "error")
                        else:
                            flash("Empresa actualizada exitosamente", "success")
            except Exception as e:
                flash(f"Error al actualizar empresa: {str(e)}", "error")
            return redirect(url_for('manage_companies'))
        return redirect(url_for('manage_companies'))

    @staticmethod
    def disable_company(company_id):
        """Deshabilita una empresa"""
        if 'user' not in session or session['user'].get('role') != 'admin':
            return redirect(url_for('login'))

        try:
            with Config.get_db_connection() as connection:
                with connection.cursor() as cursor:
                    cursor.execute("UPDATE companies SET is_active = 0 WHERE id = %s", (company_id,))
                    connection.commit()
                    if cursor.rowcount == 0:
                        flash("Empresa no encontrada", "error")
                    else:
                        flash("Empresa desactivada exitosamente", "success")
        except Exception as e:
            flash(f"Error al desactivar empresa: {str(e)}", "error")
        return redirect(url_for('manage_companies'))

    @staticmethod
    def enable_company(company_id):
        """Habilita una empresa"""
        if 'user' not in session or session['user'].get('role') != 'admin':
            return redirect(url_for('login'))

        try:
            with Config.get_db_connection() as connection:
                with connection.cursor() as cursor:
                    cursor.execute("UPDATE companies SET is_active = 1 WHERE id = %s", (company_id,))
                    connection.commit()
                    if cursor.rowcount == 0:
                        flash("Empresa no encontrada", "error")
                    else:
                        flash("Empresa activada exitosamente", "success")
        except Exception as e:
            flash(f"Error al activar empresa: {str(e)}", "error")
        return redirect(url_for('manage_companies'))

    @staticmethod
    def manage_company_roles(company_id):
        """Gestionar roles específicos de una empresa"""
        if 'user' not in session or session['user'].get('role') != 'admin':
            return redirect(url_for('login'))

        company = Company.get_company_by_id(company_id)
        if not company:
            flash("Company not found", "error")
            return redirect(url_for('admin_dashboard'))

        if request.method == 'POST':
            role_name = request.form.get('role_name')
            permissions = request.form.getlist('permissions')  # Lista de permisos
            
            if not role_name:
                flash("Role name is required", "error")
            else:
                try:
                    with Config.get_db_connection() as connection:
                        with connection.cursor() as cursor:
                            cursor.execute(
                                "INSERT INTO company_roles (company_id, role_name, permissions) VALUES (%s, %s, %s)",
                                (company_id, role_name, str(permissions))
                            )
                            connection.commit()
                            flash("Role created successfully", "success")
                except Exception as e:
                    flash(f"Error creating role: {str(e)}", "error")

        with Config.get_db_connection() as connection:
            with connection.cursor(dictionary=True) as cursor:
                cursor.execute(
                    "SELECT * FROM company_roles WHERE company_id = %s",
                    (company_id,)
                )
                roles = cursor.fetchall()

        return render_template('admin/company/company_roles.html', company=company, roles=roles)

    @staticmethod
    def manage_company_products(company_id):
        """Gestionar productos y QR de una empresa"""
        if 'user' not in session or session['user'].get('role') != 'admin':
            return redirect(url_for('login'))

        company = Company.get_company_by_id(company_id)
        if not company:
            flash("Company not found", "error")
            return redirect(url_for('admin_dashboard'))

        if request.method == 'POST':
            name = request.form.get('name')
            description = request.form.get('description')
            stock = request.form.get('stock', 0)

            if not name:
                flash("Product name is required", "error")
            else:
                try:
                    with Config.get_db_connection() as connection:
                        with connection.cursor() as cursor:
                            cursor.execute(
                                "INSERT INTO products (company_id, name, description, stock) VALUES (%s, %s, %s, %s)",
                                (company_id, name, description, stock)
                            )
                            product_id = cursor.lastrowid
                            qr_code = f"qr_{company_id}_{product_id}.png"
                            cursor.execute(
                                "UPDATE products SET qr_code = %s WHERE id = %s",
                                (qr_code, product_id)
                            )
                            connection.commit()
                            flash("Product created successfully", "success")
                except Exception as e:
                    flash(f"Error creating product: {str(e)}", "error")

        with Config.get_db_connection() as connection:
            with connection.cursor(dictionary=True) as cursor:
                cursor.execute(
                    "SELECT * FROM products WHERE company_id = %s",
                    (company_id,)
                )
                products = cursor.fetchall()

        return render_template('products/product_list.html', company=company, products=products)