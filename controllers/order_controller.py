from flask import request, session, redirect, url_for, flash, render_template, jsonify, make_response
from db import Config as db
import json

class OrderController:
    @staticmethod
    def create_order():
        """Permite a admin o gerente registrar una orden con proveedor."""
        if 'user' not in session:
            return redirect(url_for('login'))

        if session['user'].get('role') not in ['admin', 'gerente']:
            flash("No tienes permiso para registrar órdenes", "error")
            return redirect(url_for('home'))

        company_id = session['user'].get('company_id')
        user_id = session['user'].get('id')

        if request.method == 'POST':
            data = request.form
            supplier_id = data.get('supplier_id')
            items = []
            for key in data.keys():
                if key.startswith('items['):
                    index = key.split('[')[1].split(']')[0]
                    if 'product_id' in key:
                        product_id = data.get(f'items[{index}][product_id]')
                        quantity = data.get(f'items[{index}][quantity]')
                        if product_id and quantity:
                            try:
                                items.append({'product_id': int(product_id), 'quantity': int(quantity)})
                            except ValueError:
                                flash("Datos inválidos en ítems (ID o cantidad)", "error")
                                return redirect(url_for('create_order'))

            if not supplier_id or not items:
                flash("Faltan datos: proveedor o ítems", "error")
                return redirect(url_for('create_order'))

            try:
                with db.get_db_connection() as connection:
                    with connection.cursor(dictionary=True) as cursor:
                        cursor.execute("SELECT id FROM suppliers WHERE id = %s AND company_id = %s", (supplier_id, company_id))
                        if not cursor.fetchone():
                            flash("Proveedor no válido", "error")
                            return redirect(url_for('create_order'))

                        cursor.execute(
                            """INSERT INTO orders (company_id, supplier_id, status, created_by)
                            VALUES (%s, %s, %s, %s)""",
                            (company_id, supplier_id, 'in_transit', user_id)
                        )
                        order_id = cursor.lastrowid

                        for item in items:
                            cursor.execute("SELECT id FROM products WHERE id = %s AND company_id = %s", (item['product_id'], company_id))
                            if not cursor.fetchone():
                                connection.rollback()
                                flash(f"Producto con ID {item['product_id']} no válido", "error")
                                return redirect(url_for('create_order'))

                            cursor.execute(
                                """INSERT INTO order_items (order_id, product_id, quantity)
                                VALUES (%s, %s, %s)""",
                                (order_id, item['product_id'], item['quantity'])
                            )
                        connection.commit()

                flash("Orden registrada como 'en camino' con éxito", "success")
                return redirect(url_for('order_list'))
            except Exception as e:
                flash(f"Error al registrar la orden: {str(e)}", "error")
                return redirect(url_for('create_order'))

        try:
            with db.get_db_connection() as connection:
                with connection.cursor(dictionary=True) as cursor:
                    cursor.execute("SELECT id, name FROM suppliers WHERE company_id = %s", (company_id,))
                    suppliers = cursor.fetchall() or []
                    cursor.execute("SELECT id, name FROM products WHERE company_id = %s", (company_id,))
                    products = cursor.fetchall() or []
            return render_template('orders/create_order.html', suppliers=suppliers, products=products)
        except Exception as e:
            flash(f"Error al cargar el formulario: {str(e)}", "error")
            return render_template('orders/create_order.html', suppliers=[], products=[])

    @staticmethod
    def receive_order(order_id=None):
        """Permite al encargado de almacén registrar una orden como entregada."""
        if 'user' not in session:
            return redirect(url_for('login'))

        if session['user'].get('role') not in ['encargado de almacén', 'gerente', 'admin']:
            flash("No tienes permiso para recibir órdenes", "error")
            return redirect(url_for('order_list'))

        company_id = session['user'].get('company_id')

        if request.method == 'POST' and order_id:
            try:
                with db.get_db_connection() as connection:
                    with connection.cursor(dictionary=True) as cursor:
                        cursor.execute(
                            "SELECT status FROM orders WHERE id = %s AND company_id = %s",
                            (order_id, company_id)
                        )
                        order = cursor.fetchone()
                        if not order or order['status'] != 'in_transit':
                            flash(f"La orden #{order_id} no está en tránsito", "error")
                            return redirect(url_for('order_list'))

                        cursor.execute(
                            """SELECT oi.product_id, oi.quantity
                            FROM order_items oi
                            WHERE oi.order_id = %s""",
                            (order_id,)
                        )
                        items = cursor.fetchall() or []

                        for item in items:
                            cursor.execute(
                                "UPDATE products SET stock = stock + %s WHERE id = %s AND company_id = %s",
                                (item['quantity'], item['product_id'], company_id)
                            )

                        cursor.execute(
                            "UPDATE orders SET status = 'delivered', delivered_at = NOW() WHERE id = %s",
                            (order_id,)
                        )
                        connection.commit()

                flash(f"Orden #{order_id} marcada como entregada correctamente", "success")
                return redirect(url_for('order_list'))
            except Exception as e:
                flash(f"Error al procesar la orden #{order_id}: {str(e)}", "error")
                return redirect(url_for('order_list'))

        return redirect(url_for('order_list'))

    @staticmethod
    def receive_multiple_orders():
        """Permite marcar múltiples órdenes en tránsito como entregadas."""
        if 'user' not in session:
            return redirect(url_for('login'))

        if session['user'].get('role') not in ['encargado de almacén', 'gerente', 'admin']:
            flash("No tienes permiso para recibir órdenes", "error")
            return redirect(url_for('order_list'))

        company_id = session['user'].get('company_id')

        if request.method == 'POST':
            order_ids_json = request.form.get('order_ids')
            if not order_ids_json:
                flash("No se han seleccionado órdenes para procesar", "error")
                return redirect(url_for('order_list'))

            try:
                order_ids = json.loads(order_ids_json)
                if not isinstance(order_ids, list) or not order_ids:
                    flash("No hay órdenes válidas para procesar", "error")
                    return redirect(url_for('order_list'))

                with db.get_db_connection() as connection:
                    with connection.cursor(dictionary=True) as cursor:
                        cursor.execute(
                            "SELECT id, status FROM orders WHERE id IN (%s) AND company_id = %s" % 
                            (','.join(['%s'] * len(order_ids)), '%s'),
                            order_ids + [company_id]
                        )
                        orders = cursor.fetchall() or []
                        invalid_orders = [o['id'] for o in orders if o['status'] != 'in_transit']
                        if invalid_orders:
                            flash(f"Las órdenes {', '.join(map(str, invalid_orders))} no están en tránsito", "error")
                            return redirect(url_for('order_list'))

                        if len(orders) != len(order_ids):
                            flash("Algunas órdenes seleccionadas no existen o no pertenecen a esta compañía", "error")
                            return redirect(url_for('order_list'))

                        for order_id in order_ids:
                            cursor.execute(
                                """SELECT oi.product_id, oi.quantity
                                FROM order_items oi
                                WHERE oi.order_id = %s""",
                                (order_id,)
                            )
                            items = cursor.fetchall() or []

                            for item in items:
                                cursor.execute(
                                    "UPDATE products SET stock = stock + %s WHERE id = %s AND company_id = %s",
                                    (item['quantity'], item['product_id'], company_id)
                                )

                            cursor.execute(
                                "UPDATE orders SET status = 'delivered', delivered_at = NOW() WHERE id = %s",
                                (order_id,)
                            )
                        connection.commit()

                flash(f"{len(order_ids)} órdenes marcadas como entregadas correctamente", "success")
                return redirect(url_for('order_list'))
            except Exception as e:
                flash(f"Error al procesar las órdenes: {str(e)}", "error")
                return redirect(url_for('order_list'))

        return redirect(url_for('order_list'))

    @staticmethod
    def order_list():
        """Lista órdenes pendientes o en tránsito con filtros y estadísticas."""
        if 'user' not in session:
            return redirect(url_for('login'))

        company_id = session['user'].get('company_id')
        user_role = session['user'].get('role')

        search = request.args.get('search', '')
        status_filter = request.args.get('status', '')
        date_from = request.args.get('date_from', '')
        date_to = request.args.get('date_to', '')

        orders = []
        order_stats = {'pending_count': 0, 'in_transit_count': 0}

        try:
            with db.get_db_connection() as connection:
                with connection.cursor(dictionary=True) as cursor:
                    base_query = """
                        FROM orders o
                        LEFT JOIN suppliers s ON o.supplier_id = s.id
                        LEFT JOIN users u ON o.created_by = u.id
                        WHERE o.company_id = %s AND o.status IN ('pending', 'in_transit')
                    """
                    params = [company_id]
                    
                    if search:
                        base_query += " AND (CAST(o.id AS CHAR) LIKE %s OR s.name LIKE %s OR u.username LIKE %s)"
                        search_param = f"%{search}%"
                        params.extend([search_param, search_param, search_param])
                    
                    if status_filter in ['pending', 'in_transit']:
                        base_query += " AND o.status = %s"
                        params.append(status_filter)
                    
                    if date_from:
                        base_query += " AND o.order_date >= %s"
                        params.append(date_from)
                    
                    if date_to:
                        base_query += " AND o.order_date <= %s"
                        params.append(date_to)
                    
                    cursor.execute(
                        "SELECT COUNT(*) as count FROM orders WHERE company_id = %s AND status = 'pending'",
                        (company_id,)
                    )
                    order_stats['pending_count'] = cursor.fetchone()['count'] or 0
                    
                    cursor.execute(
                        "SELECT COUNT(*) as count FROM orders WHERE company_id = %s AND status = 'in_transit'",
                        (company_id,)
                    )
                    order_stats['in_transit_count'] = cursor.fetchone()['count'] or 0
                    
                    query = f"""SELECT o.id, o.order_date, o.status, s.name AS supplier_name, u.username AS created_by
                        {base_query}
                        ORDER BY o.order_date DESC"""
                    
                    cursor.execute(query, params)
                    orders = cursor.fetchall() or []

            response = make_response(render_template(
                'orders/order_list.html', 
                orders=orders, 
                user_role=user_role, 
                **order_stats
            ))
            response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
            return response
        except Exception as e:
            flash(f"Error al listar órdenes: {str(e)}", "error")
            return render_template(
                'orders/order_list.html', 
                orders=orders, 
                user_role=user_role, 
                **order_stats
            )

    @staticmethod
    def view_order(order_id):
        """Muestra los detalles de una orden específica."""
        if 'user' not in session:
            return redirect(url_for('login'))

        company_id = session['user'].get('company_id')

        try:
            with db.get_db_connection() as connection:
                with connection.cursor(dictionary=True) as cursor:
                    cursor.execute(
                        """SELECT o.id, o.order_date, o.status, o.delivered_at, s.name AS supplier_name, u.username AS created_by
                        FROM orders o
                        LEFT JOIN suppliers s ON o.supplier_id = s.id
                        LEFT JOIN users u ON o.created_by = u.id
                        WHERE o.id = %s AND o.company_id = %s""",
                        (order_id, company_id)
                    )
                    order = cursor.fetchone()
                    
                    if not order:
                        flash("Orden no encontrada", "error")
                        return redirect(url_for('order_list'))
                    
                    cursor.execute(
                        """SELECT oi.product_id, oi.quantity, p.name AS product_name, p.sku, p.unit 
                        FROM order_items oi
                        JOIN products p ON oi.product_id = p.id
                        WHERE oi.order_id = %s""",
                        (order_id,)
                    )
                    items = cursor.fetchall() or []
                    
            return render_template('orders/view_order.html', order=order, items=items)
        except Exception as e:
            flash(f"Error al ver detalles de la orden: {str(e)}", "error")
            return redirect(url_for('order_list'))

    @staticmethod
    def get_pending_orders(company_id):
        """Obtiene las órdenes pendientes o en tránsito para la compañía."""
        try:
            with db.get_db_connection() as connection:
                with connection.cursor(dictionary=True) as cursor:
                    cursor.execute(
                        """SELECT id, status 
                        FROM orders 
                        WHERE company_id = %s AND status IN ('pending', 'in_transit')""",
                        (company_id,)
                    )
                    orders = cursor.fetchall() or []

                    for order in orders:
                        cursor.execute(
                            """SELECT oi.product_id, oi.quantity, p.name AS product_name 
                            FROM order_items oi 
                            JOIN products p ON oi.product_id = p.id 
                            WHERE oi.order_id = %s""",
                            (order['id'],)
                        )
                        order['items'] = cursor.fetchall() or []

                    return orders
        except Exception as e:
            flash(f"Error al cargar órdenes pendientes: {str(e)}", "error")
            return []

    @staticmethod
    def get_order_details(order_id):
        """Devuelve los detalles de una orden en formato JSON para AJAX."""
        if 'user' not in session:
            return jsonify({"success": False, "message": "No autenticado"}), 401

        company_id = session['user'].get('company_id')
        try:
            with db.get_db_connection() as connection:
                with connection.cursor(dictionary=True) as cursor:
                    cursor.execute(
                        "SELECT id, status FROM orders WHERE id = %s AND company_id = %s",
                        (order_id, company_id)
                    )
                    order = cursor.fetchone()
                    if not order or order['status'] not in ['pending', 'in_transit']:
                        return jsonify({"success": False, "message": "Orden no encontrada o no está pendiente/en tránsito"})

                    cursor.execute(
                        """SELECT oi.product_id, oi.quantity, p.name AS product_name 
                        FROM order_items oi 
                        JOIN products p ON oi.product_id = p.id 
                        WHERE oi.order_id = %s""",
                        (order_id,)
                    )
                    items = cursor.fetchall() or []

                    return jsonify({
                        "success": True,
                        "order": {
                            "id": order['id'],
                            "status": order['status'],
                            "items": items
                        }
                    })
        except Exception as e:
            return jsonify({"success": False, "message": f"Error al obtener detalles: {str(e)}"}), 500

            