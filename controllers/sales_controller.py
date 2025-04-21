# controllers/sales_controller.py
from flask import request, jsonify, session
from db import Config as db
from datetime import datetime
import os
import stripe

stripe.api_key = os.environ.get('STRIPE_SECRET_KEY')

class SalesController:
    @staticmethod
    def register_sale():
        """Registra una venta para usuarios autenticados con rol vendedor o superior."""
        try:
            if 'user' not in session:
                return jsonify({'success': False, 'error': 'Usuario no autenticado'}), 401

            # Permitir a 'vendedor', 'encargado de almacén', 'gerente', y 'admin'
            if session['user'].get('role') not in ['vendedor', 'encargado de almacén', 'gerente', 'admin']:
                return jsonify({'success': False, 'error': 'Solo vendedores pueden registrar ventas'}), 403

            company_id = session['user'].get('company_id')
            user_id = session['user'].get('id')  # Retain user_id for tracking the salesperson
            data = request.get_json()
            
            if not data or 'items' not in data or 'payment_method' not in data:
                return jsonify({'success': False, 'error': 'Faltan ítems o método de pago en la solicitud'}), 400

            items = data['items']
            payment_method = data['payment_method']
            amount = float(data.get('amount', 0))
            
            if not items or amount <= 0:
                return jsonify({'success': False, 'error': 'Ítems inválidos o monto menor o igual a cero'}), 400

            # Validar payment_method contra valores permitidos
            valid_payment_methods = ['cash', 'transfer', 'stripe']
            if payment_method not in valid_payment_methods:
                return jsonify({'success': False, 'error': 'Método de pago inválido'}), 400

            with db.get_db_connection() as connection:
                with connection.cursor(dictionary=True) as cursor:
                    payment_data = {}
                    
                    # Generar un sale_group_id único para esta venta
                    cursor.execute("SELECT MAX(sale_group_id) FROM sales WHERE company_id = %s", (company_id,))
                    last_group_id = cursor.fetchone()['MAX(sale_group_id)']
                    sale_group_id = (last_group_id or 0) + 1

                    if payment_method == 'stripe':
                        if 'stripe_token' not in data:
                            return jsonify({'success': False, 'error': 'Falta el token de Stripe'}), 400
                        
                        try:
                            charge = stripe.Charge.create(
                                amount=int(amount * 100),  # Convertir a centavos
                                currency='usd',
                                source=data['stripe_token'],
                                description=f'Venta de {len(items)} productos por usuario {user_id} para empresa {company_id}'
                            )
                            payment_data['stripe_charge_id'] = charge.id
                            payment_data['receipt_url'] = charge.receipt_url
                        except stripe.error.CardError as e:
                            return jsonify({
                                'success': False,
                                'error': f'Error de tarjeta: {e.user_message}'
                            }), 400
                        except stripe.error.StripeError as e:
                            return jsonify({
                                'success': False,
                                'error': f'Error de Stripe: {str(e)}'
                            }), 400
                            
                    elif payment_method == 'transfer':
                        if 'transfer_data' not in data:
                            return jsonify({'success': False, 'error': 'Faltan datos de transferencia'}), 400
                        
                        transfer_data = data['transfer_data']
                        required_fields = ['account_number', 'bank_name', 'transfer_date', 'reference_number']
                        
                        if not all(field in transfer_data for field in required_fields):
                            return jsonify({
                                'success': False,
                                'error': 'Faltan campos requeridos en los datos de transferencia'
                            }), 400
                            
                        payment_data['transfer_details'] = transfer_data

                    sale_ids = []
                    for item in items:
                        product_id = int(item.get('product_id', 0))
                        quantity = int(item.get('quantity', 0))
                        sale_price = float(item.get('sale_price', 0))
                        profit = float(item.get('profit', 0))
                        sale_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

                        # Verificar stock
                        cursor.execute(
                            "SELECT stock FROM products WHERE id = %s AND company_id = %s",
                            (product_id, company_id)
                        )
                        product = cursor.fetchone()
                        
                        if not product:
                            return jsonify({
                                'success': False,
                                'error': f'Producto {product_id} no encontrado'
                            }), 404
                            
                        if product['stock'] < quantity:
                            return jsonify({
                                'success': False,
                                'error': f'Stock insuficiente para el producto {product_id}'
                            }), 400

                        # Registrar la venta con company_id, user_id y sale_group_id
                        cursor.execute(
                            """INSERT INTO sales 
                            (company_id, user_id, product_id, quantity, sale_price, sale_date, profit, payment_method, sale_group_id)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                            (company_id, user_id, product_id, quantity, sale_price, sale_date, profit, payment_method, sale_group_id)
                        )
                        sale_id = cursor.lastrowid
                        sale_ids.append(sale_id)

                        # Actualizar stock
                        cursor.execute(
                            "UPDATE products SET stock = stock - %s WHERE id = %s AND company_id = %s",
                            (quantity, product_id, company_id)
                        )

                        # Registrar detalles de pago
                        if payment_method == 'transfer':
                            cursor.execute(
                                """INSERT INTO transfer_details 
                                (sale_id, account_number, bank_name, transfer_date, reference_number)
                                VALUES (%s, %s, %s, %s, %s)""",
                                (
                                    sale_id,
                                    transfer_data['account_number'],
                                    transfer_data['bank_name'],
                                    transfer_data['transfer_date'],
                                    transfer_data['reference_number']
                                )
                            )
                        elif payment_method == 'stripe':
                            cursor.execute(
                                "UPDATE sales SET stripe_payment_id = %s WHERE id = %s",
                                (payment_data['stripe_charge_id'], sale_id)
                            )

                    connection.commit()

            if 'cart' in session:
                session.pop('cart', None)
                session.modified = True

            return jsonify({
                'success': True,
                'message': 'Venta registrada con éxito',
                'sale_ids': sale_ids,
                'sale_group_id': sale_group_id,  # Incluimos el sale_group_id en la respuesta
                **payment_data
            }), 200

        except Exception as e:
            return jsonify({
                'success': False,
                'error': f'Error del servidor: {str(e)}'
            }), 500

    @staticmethod
    def clear_cart():
        """Limpia el carrito de compras para usuarios autenticados con rol vendedor o superior."""
        if 'user' not in session:
            return jsonify({'success': False, 'error': 'Usuario no autenticado'}), 401

        # Permitir a 'vendedor', 'encargado de almacén', 'gerente', y 'admin'
        if session['user'].get('role') not in ['vendedor', 'encargado de almacén', 'gerente', 'admin']:
            return jsonify({'success': False, 'error': 'Solo vendedores pueden limpiar el carrito'}), 403

        if 'cart' in session:
            session.pop('cart', None)
            session.modified = True
        return jsonify({'success': True, 'message': 'Carrito limpiado con éxito'}), 200
