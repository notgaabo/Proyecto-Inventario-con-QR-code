from flask import render_template, request, redirect, url_for, flash, session
from datetime import datetime
from db import Config  # Importamos la clase Config del módulo db

class SupplierController:
    
    @staticmethod
    def add_supplier():
        if request.method == 'POST':
            # Obtener datos del formulario
            name = request.form['name']
            contact_info = request.form['contact_info']
            company_id = session.get('user', {}).get('company_id', 1)  # Obtener de la sesión, default a 1

            # Validaciones básicas
            if not name or not contact_info:
                flash('Todos los campos son obligatorios', 'error')
                return redirect(url_for('add_supplier'))

            if len(name) > 100:
                flash('El nombre no puede exceder 100 caracteres', 'error')
                return redirect(url_for('add_supplier'))

            if len(contact_info) > 255:
                flash('La información de contacto no puede exceder 255 caracteres', 'error')
                return redirect(url_for('add_supplier'))

            try:
                # Obtener conexión a la base de datos
                conn = Config.get_db_connection()
                cursor = conn.cursor()

                # Insertar el nuevo proveedor
                cursor.execute('''
                    INSERT INTO suppliers (name, contact_info, company_id, created_at)
                    VALUES (%s, %s, %s, %s)
                ''', (name, contact_info, company_id, datetime.now()))

                # Confirmar la transacción
                conn.commit()
                flash('Proveedor registrado exitosamente', 'success')

            except Exception as e:
                conn.rollback()
                flash(f'Error al registrar el proveedor: {str(e)}', 'error')

            finally:
                cursor.close()
                conn.close()

            return redirect(url_for('add_supplier'))

        # Si es GET, mostrar el formulario
        return render_template('suppliers/add_supplier.html')

    @staticmethod
    def supplier_list():
        try:
            # Obtener conexión a la base de datos
            conn = Config.get_db_connection()
            cursor = conn.cursor(dictionary=True)  # Usar dictionary=True para resultados como diccionarios

            # Consultar todos los proveedores
            cursor.execute('SELECT id, name, contact_info, company_id, created_at FROM suppliers WHERE company_id = %s', 
                           (session.get('user', {}).get('company_id', 1),))
            suppliers = cursor.fetchall()

        except Exception as e:
            flash(f'Error al obtener la lista de proveedores: {str(e)}', 'error')
            suppliers = []

        finally:
            cursor.close()
            conn.close()

        # Renderizar la plantilla con la lista de proveedores
        return render_template('suppliers/supplier_list.html', suppliers=suppliers)