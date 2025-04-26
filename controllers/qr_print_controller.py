from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.colors import Color
import io
import os
from db import Config as db
from flask import make_response, request, jsonify
from datetime import date
from controllers.qr_controller import QrController

class QRCodePrinter:
    def __init__(self):
        self.qr_size = 25 * mm
        self.margin = 10 * mm
        self.spacing = 3 * mm
        self.max_qr_per_page = 20
        self.qr_dir = os.path.join("static", "qr_codes")

    def get_qr_image_path(self, product_id):
        qr_path = os.path.join(self.qr_dir, f"{product_id}.png")
        if not os.path.exists(qr_path):
            response = QrController.generate_qr(product_id=product_id, save_locally=True, internal_call=True)
            if isinstance(response, tuple) and response[1] != 200:
                print(f"Error generando QR para product_id {product_id}: {response[0].get_json()['message']}")
                return None
        return qr_path

    def validate_input(self, product_data=None, order_item_ids=None, order_id=None):
        if not product_data and not order_item_ids and not order_id:
            print("Se deben proporcionar product_data, order_item_ids o order_id")
            return False
        if product_data and (not isinstance(product_data, list) or not product_data):
            print(f"product_data inválido: {product_data}")
            return False
        if order_item_ids and (not isinstance(order_item_ids, (list, tuple)) or not order_item_ids):
            print(f"order_item_ids inválido: {order_item_ids}")
            return False
        if order_id and not isinstance(order_id, int):
            print(f"order_id inválido: {order_id}")
            return False
        return True

    def fetch_product_data(self, order_item_ids=None, order_id=None):
        connection = db.get_db_connection()
        cursor = connection.cursor(dictionary=True)
        try:
            if order_id:
                query = """
                    SELECT status FROM orders WHERE id = %s
                """
                cursor.execute(query, (order_id,))
                order = cursor.fetchone()
                if not order or order['status'] != 'delivered':
                    print(f"La orden {order_id} no está en estado 'delivered'")
                    return None

                query = """
                    SELECT p.id, p.name, p.price, p.category, oi.quantity
                    FROM order_items oi
                    JOIN products p ON oi.product_id = p.id
                    WHERE oi.order_id = %s
                """
                cursor.execute(query, (order_id,))
            elif order_item_ids:
                query = """
                    SELECT p.id, p.name, p.price, p.category, oi.quantity
                    FROM order_items oi
                    JOIN products p ON oi.product_id = p.id
                    WHERE oi.id IN ({})
                """.format(','.join(['%s'] * len(order_item_ids)))
                cursor.execute(query, tuple(order_item_ids))
            else:
                print("No se proporcionaron order_item_ids ni order_id")
                return None

            products = cursor.fetchall()
            if not products:
                print(f"No se encontraron productos para order_id: {order_id} o order_item_ids: {order_item_ids}")
                return None

            product_data = [
                {
                    'id': p['id'],
                    'name': p['name'],
                    'price': p['price'],
                    'category': p['category'],
                    'quantity': p['quantity']
                } for p in products
            ]
            return product_data

        except Exception as e:
            print(f"Error al consultar la base de datos: {str(e)}")
            return None
        finally:
            cursor.close()
            connection.close()

    def generate_pdf(self, product_data):
        buffer = io.BytesIO()
        p = canvas.Canvas(buffer, pagesize=A4)
        width, height = A4
        black = Color(0, 0, 0)
        gray = Color(0.6, 0.6, 0.6)
        orange = Color(0.9, 0.5, 0.3)

        def draw_page(products_subset, start_idx):
            y = height - self.margin - self.qr_size
            x = self.margin
            col = 0
            row = 0

            for idx, item in enumerate(products_subset):
                product = item['product']
                count = item['count']
                qr_path = self.get_qr_image_path(product['id'])
                if not qr_path:
                    continue

                p.drawImage(qr_path, x, y, self.qr_size, self.qr_size)
                p.setFillColor(black)
                p.setFont("Helvetica-Bold", 8)
                p.drawString(x, y - 5 * mm, f"ID: {product['id']}")
                p.setFont("Helvetica", 7)
                name = product['name'][:30] + "..." if len(product['name']) > 30 else product['name']
                p.drawString(x, y - 10 * mm, name)
                p.setFillColor(gray)
                p.drawString(x, y - 15 * mm, f"${product['price']:.2f}")
                p.setFillColor(orange)
                p.drawString(x, y - 20 * mm, f"{product['category'] or 'Sin categoría'} (x{count})")

                col += 1
                x += self.qr_size + self.spacing
                if col >= 5:
                    col = 0
                    row += 1
                    x = self.margin
                    y -= self.qr_size + self.spacing + 20 * mm
                    if row >= 4:
                        break

            p.setFillColor(gray)
            p.setFont("Helvetica", 8)
            p.drawString(self.margin, self.margin, f"Página {start_idx // self.max_qr_per_page + 1}")
            p.showPage()

        expanded_products = []
        for product in product_data:
            for i in range(product['quantity']):
                expanded_products.append({
                    'product': {
                        'id': product['id'],
                        'name': product['name'],
                        'price': product['price'],
                        'category': product['category']
                    },
                    'count': i + 1
                })

        for i in range(0, len(expanded_products), self.max_qr_per_page):
            draw_page(expanded_products[i:i + self.max_qr_per_page], i)

        p.save()
        pdf_data = buffer.getvalue()
        buffer.close()
        return pdf_data

    def generate(self, product_data=None, order_item_ids=None, order_id=None):
        if not self.validate_input(product_data, order_item_ids, order_id):
            return None

        if order_id or order_item_ids:
            product_data = self.fetch_product_data(order_item_ids=order_item_ids, order_id=order_id)
            if not product_data:
                return None

        print("Productos para códigos QR:")
        for p in product_data:
            print(f"- ID: {p['id']}, Nombre: {p['name']}, Precio: {p['price']}, Cantidad: {p['quantity']}")

        pdf_data = self.generate_pdf(product_data)
        print(f"PDF de códigos QR generado exitosamente para {'order_id' if order_id else 'order_item_ids' if order_item_ids else 'product_data'}")
        return pdf_data

    @staticmethod
    def get_qr_pdf():
        product_ids = request.args.get('product_ids')
        order_item_ids = request.args.get('order_item_ids')
        order_id = request.args.get('order_id')

        if not product_ids and not order_item_ids and not order_id:
            return jsonify({"success": False, "message": "No se proporcionaron product_ids, order_item_ids ni order_id"}), 400

        printer = QRCodePrinter()
        try:
            if order_id:
                pdf_data = printer.generate(order_id=int(order_id))
            elif product_ids:
                product_ids = [int(id.strip()) for id in product_ids.split(',')]
                connection = db.get_db_connection()
                cursor = connection.cursor(dictionary=True)
                try:
                    query = """
                        SELECT id, name, price, category
                        FROM products
                        WHERE id IN ({})
                    """.format(','.join(['%s'] * len(product_ids)))
                    cursor.execute(query, tuple(product_ids))
                    products = cursor.fetchall()
                    product_data = [
                        {
                            'id': p['id'],
                            'name': p['name'],
                            'price': p['price'],
                            'category': p['category'],
                            'quantity': 1
                        } for p in products
                    ]
                    if not product_data:
                        return jsonify({"success": False, "message": "No se encontraron productos para los product_ids proporcionados"}), 404
                    pdf_data = printer.generate(product_data=product_data)
                finally:
                    cursor.close()
                    connection.close()
            else:
                order_item_ids = [int(id.strip()) for id in order_item_ids.split(',')]
                pdf_data = printer.generate(order_item_ids=order_item_ids)

            if pdf_data:
                response = make_response(pdf_data)
                response.headers['Content-Type'] = 'application/pdf'
                response.headers['Content-Disposition'] = 'attachment; filename=qr_codes.pdf'
                return response
            return jsonify({"success": False, "message": "Error generando el PDF de códigos QR"}), 500

        except ValueError:
            return jsonify({"success": False, "message": "Formato inválido de IDs"}), 400

    @staticmethod
    def get_last_delivered_products():
        """Maneja la ruta /last_delivered_products para obtener los productos de órdenes entregadas no impresas."""
        connection = db.get_db_connection()
        cursor = connection.cursor(dictionary=True)
        try:
            query = """
                SELECT o.id AS order_id, o.order_date, s.name AS supplier_name,
                       p.id AS product_id, p.name, p.price, p.category, oi.quantity
                FROM orders o
                JOIN order_items oi ON o.id = oi.order_id
                JOIN products p ON oi.product_id = p.id
                LEFT JOIN suppliers s ON o.supplier_id = s.id
                WHERE o.status = 'delivered' AND o.is_printed = FALSE
                ORDER BY o.order_date DESC
                LIMIT 50
            """
            cursor.execute(query)
            products = cursor.fetchall()
            if not products:
                print("No se encontraron productos de órdenes entregadas no impresas")
                return jsonify({'success': True, 'orders': []})

            # Agrupar por orden para el frontend
            orders = {}
            for p in products:
                order_id = p['order_id']
                if order_id not in orders:
                    orders[order_id] = {
                        'order_id': order_id,
                        'order_date': p['order_date'].strftime('%Y-%m-%d'),
                        'supplier_name': p['supplier_name'] or 'Sin proveedor',
                        'products': []
                    }
                orders[order_id]['products'].append({
                    'id': p['product_id'],
                    'name': p['name'],
                    'price': p['price'],
                    'category': p['category'],
                    'quantity': p['quantity']
                })
            return jsonify({'success': True, 'orders': list(orders.values())})

        except Exception as e:
            print(f"Error al obtener productos de órdenes entregadas: {str(e)}")
            return jsonify({'success': False, 'message': f"Error al obtener órdenes: {str(e)}"}), 500
        finally:
            cursor.close()
            connection.close()

    @staticmethod
    def print_qr_for_order():
        """Maneja la ruta /print_qr_for_order para generar un PDF de códigos QR para un order_id y marcar como impreso."""
        order_id = request.args.get('order_id')
        if not order_id:
            return jsonify({"success": False, "message": "No se proporcionó order_id"}), 400

        printer = QRCodePrinter()
        try:
            pdf_data = printer.generate(order_id=int(order_id))
            if pdf_data:
                # Marcar la orden como impresa
                connection = db.get_db_connection()
                cursor = connection.cursor()
                try:
                    query = """
                        UPDATE orders SET is_printed = TRUE WHERE id = %s
                    """
                    cursor.execute(query, (int(order_id),))
                    connection.commit()
                except Exception as e:
                    print(f"Error al marcar la orden como impresa: {str(e)}")
                    return jsonify({"success": False, "message": f"Error al marcar la orden como impresa: {str(e)}"}), 500
                finally:
                    cursor.close()
                    connection.close()

                response = make_response(pdf_data)
                response.headers['Content-Type'] = 'application/pdf'
                response.headers['Content-Disposition'] = f'attachment; filename=qr_codes_order_{order_id}.pdf'
                return response
            return jsonify({"success": False, "message": "Error generando el PDF de códigos QR"}), 500
        except ValueError:
            return jsonify({"success": False, "message": "Formato inválido de order_id"}), 400

    @staticmethod
    def print_qr_for_product():
        """Maneja la ruta /print_qr_for_product para generar un PDF de códigos QR para un product_id con cantidad especificada."""
        product_id = request.args.get('product_id')
        quantity = request.args.get('quantity')

        if not product_id or not quantity:
            return jsonify({"success": False, "message": "No se proporcionaron product_id o quantity"}), 400

        try:
            product_id = int(product_id)
            quantity = int(quantity)
            if quantity < 1:
                return jsonify({"success": False, "message": "La cantidad debe ser mayor que 0"}), 400

            connection = db.get_db_connection()
            cursor = connection.cursor(dictionary=True)
            try:
                query = """
                    SELECT id, name, price, category
                    FROM products
                    WHERE id = %s
                """
                cursor.execute(query, (product_id,))
                product = cursor.fetchone()
                if not product:
                    return jsonify({"success": False, "message": "Producto no encontrado"}), 404

                product_data = [{
                    'id': product['id'],
                    'name': product['name'],
                    'price': product['price'],
                    'category': product['category'],
                    'quantity': quantity
                }]

                printer = QRCodePrinter()
                pdf_data = printer.generate(product_data=product_data)
                if pdf_data:
                    response = make_response(pdf_data)
                    response.headers['Content-Type'] = 'application/pdf'
                    response.headers['Content-Disposition'] = f'attachment; filename=qr_codes_product_{product_id}.pdf'
                    return response
                return jsonify({"success": False, "message": "Error generando el PDF de códigos QR"}), 500

            finally:
                cursor.close()
                connection.close()

        except ValueError:
            return jsonify({"success": False, "message": "Formato inválido de product_id o quantity"}), 400