from flask import request, render_template, redirect, url_for, session, flash, jsonify
from db.config import Config as db
from datetime import datetime, date

class returnsController:
    @staticmethod
    def return_list():
        try:
            conn = db.get_db_connection()
            cursor = conn.cursor(dictionary=True)
            company_id = session['user']['company_id']
            
            # Obtener parámetros de búsqueda
            search = request.args.get('search', '')
            date_from = request.args.get('date_from', '')
            date_to = request.args.get('date_to', '')
            
            # Construir la consulta base
            query = """
                SELECT r.*, p.name as product_name 
                FROM returns r 
                LEFT JOIN products p ON r.product_id = p.id 
                WHERE r.company_id = %s
            """
            params = [company_id]
            
            # Añadir filtros si se proporcionan
            if search:
                query += " AND (r.product_id LIKE %s OR r.reason LIKE %s)"
                search_param = f"%{search}%"
                params.extend([search_param, search_param])
            
            if date_from:
                query += " AND r.created_at >= %s"
                params.append(date_from)
            
            if date_to:
                query += " AND r.created_at <= %s"
                params.append(date_to + " 23:59:59")
            
            query += " ORDER BY r.created_at DESC"
            
            # Ejecutar la consulta para obtener las devoluciones filtradas
            cursor.execute(query, tuple(params))
            devoluciones = cursor.fetchall()
            
            # Calcular el total de devoluciones (sin filtros)
            cursor.execute("SELECT COUNT(*) as total FROM returns WHERE company_id = %s", (company_id,))
            devoluciones_total = cursor.fetchone()['total']
            
            # Calcular la cantidad total devuelta (suma de cantidades)
            cursor.execute("SELECT SUM(quantity) as total_quantity FROM returns WHERE company_id = %s", (company_id,))
            result = cursor.fetchone()
            total_quantity = result['total_quantity'] if result['total_quantity'] else 0
            
            # Calcular devoluciones del mes actual
            current_date = datetime.now()
            first_day = date(current_date.year, current_date.month, 1)
            last_day = date(current_date.year, current_date.month + 1, 1) if current_date.month < 12 else date(current_date.year + 1, 1, 1)
            
            cursor.execute("""
                SELECT COUNT(*) as monthly_count
                FROM returns 
                WHERE company_id = %s 
                AND created_at >= %s 
                AND created_at < %s
            """, (company_id, first_day, last_day))
            result = cursor.fetchone()
            monthly_returns_count = result['monthly_count'] if result['monthly_count'] else 0
            
        except Exception as e:
            flash(f'Error al obtener la lista de devoluciones: {str(e)}', 'error')
            devoluciones = []
            devoluciones_total = 0
            total_quantity = 0
            monthly_returns_count = 0
        
        finally:
            cursor.close()
            conn.close()
        
        return render_template('returns/returns.html', 
                              devoluciones=devoluciones,
                              devoluciones_total=devoluciones_total,
                              total_quantity=total_quantity,
                              monthly_returns_count=monthly_returns_count)

    @staticmethod
    def view_return(return_id):
        try:
            conn = db.get_db_connection()
            cursor = conn.cursor(dictionary=True)
            company_id = session['user']['company_id']
            
            # Consulta para obtener los detalles básicos de la devolución
            cursor.execute("""
                SELECT r.*, p.name as product_name 
                FROM returns r 
                LEFT JOIN products p ON r.product_id = p.id 
                WHERE r.id = %s AND r.company_id = %s
            """, (return_id, company_id))
            devolucion = cursor.fetchone()
            
            if not devolucion:
                flash('La devolución solicitada no existe o no tienes permiso para verla', 'error')
                return redirect(url_for('returns_list'))
            
            return render_template('returns/view_return.html', devolucion=devolucion)
        
        except Exception as e:
            flash(f'Error al obtener los detalles de la devolución: {str(e)}', 'error')
            return redirect(url_for('returns_list'))
        
        finally:
            cursor.close()
            conn.close()
            
    @staticmethod
    def add_return():
        if request.method == 'POST':
            sale_group_id = request.form.get('sale_group_id')
            reason = request.form.get('reason')
            company_id = session['user']['company_id']
            fecha = datetime.now()

            if not sale_group_id or not sale_group_id.isdigit():
                flash('ID de grupo de venta inválido', 'error')
                return redirect(url_for('returns_new'))

            if not reason:
                flash('Debe proporcionar un motivo para la devolución', 'error')
                return redirect(url_for('returns_new'))

            try:
                conn = db.get_db_connection()
                cursor = conn.cursor(dictionary=True)
                
                # Verificar si el sale_group_id existe
                cursor.execute("""
                    SELECT 1 
                    FROM sales 
                    WHERE sale_group_id = %s AND company_id = %s LIMIT 1
                """, (sale_group_id, company_id))
                if not cursor.fetchone():
                    flash('El grupo de venta especificado no existe', 'error')
                    return redirect(url_for('returns_new'))

                # Obtener todos los productos de la venta
                cursor.execute("""
                    SELECT id, product_id, quantity 
                    FROM sales 
                    WHERE sale_group_id = %s AND company_id = %s
                """, (sale_group_id, company_id))
                sale_products = cursor.fetchall()

                if not sale_products:
                    flash('No se encontraron productos para este grupo de venta', 'error')
                    return redirect(url_for('returns_new'))

                # Inicializar notificaciones
                if 'notifications' not in session:
                    session['notifications'] = []
                if 'notification_counter' not in session:
                    session['notification_counter'] = 0

                user_role = session['user']['role']
                roles_to_notify_return = ['gerente', 'admin', 'vendedor']
                roles_to_notify_stock = ['gerente', 'admin', 'encargado de almacén']

                for sale in sale_products:
                    product_id = sale['product_id']
                    quantity = sale['quantity']

                    # Insertar devolución para cada producto
                    cursor.execute("""
                        INSERT INTO returns (sale_id, product_id, quantity, reason, company_id, created_at) 
                        VALUES (%s, %s, %s, %s, %s, %s)
                    """, (sale['id'], product_id, quantity, reason, company_id, fecha))
                    return_id = cursor.lastrowid

                    # Actualizar stock
                    cursor.execute("SELECT stock, name FROM products WHERE id = %s AND company_id = %s", (product_id, company_id))
                    product = cursor.fetchone()
                    if not product:
                        flash(f'Producto con ID {product_id} no encontrado', 'error')
                        continue

                    new_stock = product['stock'] + quantity
                    cursor.execute("UPDATE products SET stock = %s WHERE id = %s", (new_stock, product_id))

                    # Notificación de stock bajo
                    threshold = 5
                    if new_stock <= threshold and user_role in roles_to_notify_stock:
                        session['notification_counter'] += 1
                        notification = {
                            'id': session['notification_counter'],
                            'title': 'Stock Bajo',
                            'message': f"El producto \"{product['name']}\" tiene {new_stock} unidades en stock.",
                            'type': 'stock_low',
                            'reference_id': product_id,
                            'created_at': fecha.isoformat(),
                            'read': False
                        }
                        session['notifications'].append(notification)
                        session.modified = True

                    # Notificación de devolución
                    if user_role in roles_to_notify_return:
                        session['notification_counter'] += 1
                        notification = {
                            'id': session['notification_counter'],
                            'title': 'Devolución Procesada',
                            'message': f"Se ha procesado la devolución #{return_id} de \"{product['name']}\" por {reason}.",
                            'type': 'return',
                            'reference_id': return_id,
                            'created_at': fecha.isoformat(),
                            'read': False
                        }
                        session['notifications'].append(notification)
                        session.modified = True
                
                conn.commit()
                flash('Devolución registrada correctamente', 'success')
            
            except Exception as e:
                conn.rollback()
                flash(f'Error al registrar la devolución: {str(e)}', 'error')
            
            finally:
                cursor.close()
                conn.close()
            
            return redirect(url_for('returns_list'))

        return render_template('returns/new_return.html', sale_group_id=None)

    @staticmethod
    def get_sale_data(sale_group_id):
        try:
            conn = db.get_db_connection()
            cursor = conn.cursor(dictionary=True)
            company_id = session['user']['company_id']
            
            cursor.execute("""
                SELECT 1 
                FROM sales 
                WHERE sale_group_id = %s AND company_id = %s LIMIT 1
            """, (sale_group_id, company_id))
            exists = cursor.fetchone()

            if not exists:
                return jsonify({'error': 'El grupo de venta no existe'}), 404

            cursor.execute("""
                SELECT s.id, s.product_id as product_id, p.name, s.quantity 
                FROM sales s 
                JOIN products p ON p.id = s.product_id 
                WHERE s.sale_group_id = %s AND s.company_id = %s
            """, (sale_group_id, company_id))
            sale_products = cursor.fetchall()
            
            if not sale_products:
                return jsonify({'error': 'No se encontraron productos para este grupo de venta'}), 404
            
            return jsonify({
                'products': [{'id': p['product_id'], 'name': p['name'], 'quantity': p['quantity'], 'sale_id': p['id']} for p in sale_products]
            })
            
        except Exception as e:
            return jsonify({'error': f'Error al obtener datos de la venta: {str(e)}'}), 500
            
        finally:
            cursor.close()
            conn.close()