from flask import render_template, request, redirect, url_for, flash, session
from datetime import datetime
import time
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
    def edit_supplier(supplier_id=None):
        # Obtener conexión a la base de datos
        conn = Config.get_db_connection()
        cursor = conn.cursor(dictionary=True)

        try:
            if request.method == 'POST':
                # Obtener datos del formulario
                name = request.form['name'].strip()
                contact_info = request.form['contact_info'].strip()
                company_id = session.get('user', {}).get('company_id', 1)

                # Validaciones
                if not name or not contact_info:
                    flash('Todos los campos son obligatorios', 'error')
                    return redirect(url_for('edit_supplier', supplier_id=supplier_id))

                if len(name) > 100:
                    flash('El nombre no puede exceder 100 caracteres', 'error')
                    return redirect(url_for('edit_supplier', supplier_id=supplier_id))

                if len(contact_info) > 255:
                    flash('La información de contacto no puede exceder 255 caracteres', 'error')
                    return redirect(url_for('edit_supplier', supplier_id=supplier_id))

                # Actualizar el proveedor
                cursor.execute('''
                    UPDATE suppliers 
                    SET name = %s, contact_info = %s, updated_at = %s
                    WHERE id = %s AND company_id = %s
                ''', (name, contact_info, datetime.now(), supplier_id, company_id))

                # Confirmar la transacción
                conn.commit()

                if cursor.rowcount == 0:
                    flash('No se encontró el proveedor o no tiene permiso para editarlo', 'error')
                else:
                    flash('Proveedor actualizado exitosamente', 'success')

                return redirect(url_for('supplier_list'))

            else:
                # Obtener datos del proveedor
                cursor.execute('SELECT id, name, contact_info FROM suppliers WHERE id = %s AND company_id = %s', 
                              (supplier_id, session.get('user', {}).get('company_id', 1)))
                supplier = cursor.fetchone()

                if not supplier:
                    flash('Proveedor no encontrado', 'error')
                    return redirect(url_for('supplier_list'))

                return render_template('suppliers/edit_supplier.html', supplier=supplier)

        except Exception as e:
            conn.rollback()
            flash(f'Error al procesar la solicitud: {str(e)}', 'error')
            return redirect(url_for('supplier_list'))

        finally:
            cursor.close()
            conn.close()

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