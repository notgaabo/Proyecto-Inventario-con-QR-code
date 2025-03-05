#controllers/qr_controller.py

from flask import request, jsonify, send_file, session, redirect, url_for, render_template
import qrcode
import os
import io
import json  # Corregimos el typo: `jsonify` ya incluye dumps, pero usaremos json.loads para QR
from db import Config

class QrController:
    @staticmethod
    def generate_qr(product_id, save_locally=True):
        try:
            connection = Config.get_db_connection()
            cursor = connection.cursor(dictionary=True)
            cursor.execute("SELECT id, name, category, price, stock FROM products WHERE id = %s AND user_id = %s", 
                           (product_id, session['user']['id']))
            product = cursor.fetchone()
            cursor.close()
            connection.close()
            
            if not product:
                return jsonify({"success": False, "message": "Product not found"}), 404

            # Codificar más datos en el QR
            qr_data = json.dumps({  # Usamos json estándar en lugar de jsonify aquí
                "id": product["id"],
                "name": product["name"],
                "category": product["category"],
                "price": float(product["price"]),
                "stock": product["stock"]
            })
            
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(qr_data)
            qr.make(fit=True)
            qr_img = qr.make_image(fill_color="black", back_color="white")
            
            if save_locally:
                qr_dir = os.path.join("static", "qr_codes")
                os.makedirs(qr_dir, exist_ok=True)
                file_path = os.path.join(qr_dir, f"{product_id}.png")
                qr_img.save(file_path)
                return send_file(file_path, mimetype="image/png")
            
            img_io = io.BytesIO()
            qr_img.save(img_io, format="PNG")
            img_io.seek(0)
            return send_file(img_io, mimetype="image/png")
        except Exception as e:
            return jsonify({"success": False, "message": str(e)}), 500

class LectorController:
    @staticmethod
    def get_productos():
        """Obtiene los productos desde la base de datos."""
        conn = Config.get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""SELECT id, name, category, price, stock, cost_price, user_id FROM products WHERE user_id = %s""", 
                       (session['user']['id'],))
        productos = [
            {
                'id': str(row['id']),  # Convertimos a string para consistencia con el frontend
                'nombre': row['name'],
                'categoria': row['category'],  # Ajustamos clave a lo esperado por el frontend
                'precio': float(row['price']),  # Ajustamos clave
                'stock': row['stock'],
                'costo': float(row['cost_price'])  # Ajustamos clave
            } for row in cursor.fetchall()
        ]
        conn.close()
        return productos

    @staticmethod
    def inventory():
        """Renderiza la página de inventario."""
        if 'user' not in session:
            return redirect(url_for('login'))
        return render_template('user/inventory.html')

    @staticmethod
    def productos():
        """Devuelve la lista de productos en formato JSON."""
        if 'user' not in session:
            return jsonify({"success": False, "message": "Not authenticated"}), 401
        try:
            productos = LectorController.get_productos()
            return jsonify({"success": True, "productos": productos})
        except Exception as e:
            return jsonify({"success": False, "message": str(e)}), 500

    @staticmethod
    def carrito():
        """Devuelve el contenido del carrito en formato JSON."""
        if 'user' not in session:
            return jsonify({"success": False, "message": "Not authenticated"}), 401
        try:
            cart = session.get('cart', {})
            return jsonify({"success": True, "carrito": cart})
        except Exception as e:
            return jsonify({"success": False, "message": str(e)}), 500

    @staticmethod
    def escanear():
        if 'user' not in session:
            return jsonify({"success": False, "message": "Not authenticated"}), 401
        
        try:
            data = request.get_json()
            codigo = data.get('codigo')
            if not codigo:
                return jsonify({"success": False, "message": "No code provided"}), 400

            # Asumir que el código es el ID directamente como string
            codigo = str(codigo)

            inventario = {p['id']: p for p in LectorController.get_productos()}
            if codigo in inventario:
                cart = session.get('cart', {})
                if codigo in cart:
                    if cart[codigo]["cantidad"] + 1 <= inventario[codigo]["stock"]:
                        cart[codigo]["cantidad"] += 1
                    else:
                        return jsonify({"success": False, "message": "Insufficient stock"}), 400
                else:
                    cart[codigo] = {
                        "nombre": inventario[codigo]["nombre"],
                        "price": inventario[codigo]["precio"],
                        "stock": inventario[codigo]["stock"],
                        "cantidad": 1
                    }

                session['cart'] = cart
                session.modified = True
                return jsonify({
                    "success": True,
                    "producto": inventario[codigo]["nombre"],
                    "cantidad": cart[codigo]["cantidad"]
                })
            
            return jsonify({"success": False, "message": "Producto no encontrado"}), 404
        except Exception as e:
            return jsonify({"success": False, "message": str(e)}), 500

    @staticmethod
    def actualizar_carrito():
        if 'user' not in session:
            return jsonify({"success": False, "message": "Not authenticated"}), 401
            
        try:
            data = request.get_json()
            product_id = str(data['codigo'])
            cantidad = int(data['cantidad'])
            inventario = {p['id']: p for p in LectorController.get_productos()}
            
            cart = session.get('cart', {})
            if product_id in inventario:
                if cantidad <= inventario[product_id]["stock"]:
                    if cantidad == 0 and product_id in cart:
                        del cart[product_id]
                    elif cantidad > 0:
                        cart[product_id] = {
                            "nombre": inventario[product_id]["nombre"],
                            "price": inventario[product_id]["precio"],
                            "stock": inventario[product_id]["stock"],
                            "cantidad": cantidad
                        }
                    session['cart'] = cart
                    session.modified = True
                    return jsonify({"success": True})
                return jsonify({"success": False, "message": "Insufficient stock"})
            return jsonify({"success": False, "message": "Producto no encontrado"})
        except Exception as e:
            return jsonify({"success": False, "message": str(e)})

    @staticmethod
    def dar_salida():
        if 'user' not in session:
            return jsonify({"success": False, "message": "Not authenticated"}), 401
            
        try:
            cart = session.get('cart', {})
            if cart:
                conn = Config.get_db_connection()
                cursor = conn.cursor()
                for product_id, item in cart.items():
                    if item["cantidad"] > 0:
                        cursor.execute(
                            "UPDATE products SET stock = stock - %s WHERE id = %s AND user_id = %s",
                            (item["cantidad"], product_id, session['user']['id'])
                        )
                conn.commit()
                conn.close()
                session['cart'] = {}
                session.modified = True
                return jsonify({"success": True, "message": "Salida registrada"})
            return jsonify({"success": False, "message": "Carrito vacío"})
        except Exception as e:
            return jsonify({"success": False, "message": str(e)})