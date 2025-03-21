from flask import Flask, request, jsonify, session, render_template
from db import Config as db
from datetime import datetime

class SalesController:
    @staticmethod
    def register_sale():
        try:
            # Verificar si el usuario está autenticado
            if 'user' not in session:
                return jsonify({'success': False, 'error': 'User not authenticated'}), 401

            user_id = session['user'].get('id')
            if not user_id:
                return jsonify({'success': False, 'error': 'User ID not found in session'}), 401

            # Obtener los datos del request
            data = request.get_json()
            if not data or 'items' not in data:
                return jsonify({'success': False, 'error': 'No items provided'}), 400

            items = data['items']
            if not items:
                return jsonify({'success': False, 'error': 'Empty items list'}), 400

            # Conectar a la base de datos
            with db.get_db_connection() as connection:
                with connection.cursor() as cursor:
                    for item in items:
                        product_id = int(item.get('product_id', 0))
                        quantity = int(item.get('quantity', 0))
                        sale_price = float(item.get('sale_price', 0))
                        sale_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

                        if not product_id or quantity <= 0 or sale_price <= 0:
                            return jsonify({
                                'success': False,
                                'error': f'Invalid data for product {product_id}'
                            }), 400

                        # Obtener el cost_price del producto
                        cursor.execute("SELECT cost_price, stock FROM products WHERE id = %s", (product_id,))
                        result = cursor.fetchone()
                        if not result:
                            return jsonify({
                                'success': False,
                                'error': f'Product with ID {product_id} not found'
                            }), 404
                        cost_price, stock = result
                        
                        if stock < quantity:
                            return jsonify({
                                'success': False,
                                'error': f'Insufficient stock for product {product_id}'
                            }), 400

                        # Convertir cost_price a float para que coincida con sale_price
                        cost_price = float(cost_price)

                        # Calcular el profit como sale_price - cost_price por unidad
                        profit = (sale_price - cost_price) * quantity

                        # Insertar la venta con user_id y profit calculado
                        insert_query = """
                            INSERT INTO sales (user_id, product_id, quantity, sale_price, sale_date, profit)
                            VALUES (%s, %s, %s, %s, %s, %s)
                        """
                        cursor.execute(insert_query, (user_id, product_id, quantity, sale_price, sale_date, profit))

                        # Actualizar el stock
                        update_query = """
                            UPDATE products 
                            SET stock = stock - %s 
                            WHERE id = %s
                        """
                        cursor.execute(update_query, (quantity, product_id))

                        if cursor.rowcount == 0:
                            return jsonify({
                                'success': False,
                                'error': f'Product with ID {product_id} not found or stock not updated'
                            }), 500

                    connection.commit()

            # Limpiar el carrito
            if 'carrito' in session:
                session.pop('carrito', None)
                session.modified = True

            return jsonify({'success': True, 'message': 'Sale registered successfully'}), 200

        except Exception as e:
            return jsonify({'success': False, 'error': f'Server error: {str(e)}'}), 500

    @staticmethod
    def limpiar_carrito():
        if 'carrito' in session:
            session.pop('carrito', None)
            session.modified = True
        return jsonify({'success': True, 'message': 'Carrito limpiado correctamente'}), 200

    @staticmethod
    def top_selling_products():
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'success': False, 'error': 'User not authenticated'}), 401

        connection = db.get_db_connection()
        cursor = connection.cursor()

        query = """
            SELECT 
                p.id, 
                p.name, 
                p.price, 
                p.stock, 
                p.category, 
                p.image, 
                p.cost_price, 
                SUM(s.quantity) AS sales_count
            FROM sales s
            JOIN products p ON s.product_id = p.id
            WHERE p.user_id = %s
            GROUP BY p.id, p.name, p.price, p.stock, p.category, p.image, p.cost_price
            ORDER BY sales_count DESC
            LIMIT 3
        """
        cursor.execute(query, (user_id,))
        products = cursor.fetchall()

        cursor.close()
        connection.close()
        return render_template('user/statistics.html', products=products)