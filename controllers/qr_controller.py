# controllers/qr_controller.py
from flask import request, jsonify, send_file, session, redirect, url_for, render_template
import qrcode
import os
import io
from db import Config
from PIL import Image
from datetime import datetime

class QrController:
    @staticmethod
    def generate_qr(product_id, save_locally=True):
        """Generate a QR code for a product."""
        try:
            if 'user' not in session:
                return jsonify({"success": False, "message": "User not authenticated"}), 401

            # Permitir a todos los roles que pueden acceder a inventory
            if session['user'].get('role') not in ['vendedor', 'encargado de almacén', 'gerente', 'admin']:
                return jsonify({"success": False, "message": "Unauthorized access"}), 403

            company_id = session['user'].get('company_id')
            with Config.get_db_connection() as connection:
                with connection.cursor(dictionary=True) as cursor:
                    cursor.execute(
                        "SELECT id, name FROM products WHERE id = %s AND company_id = %s",
                        (product_id, company_id)
                    )
                    product = cursor.fetchone()
                
                if not product:
                    return jsonify({"success": False, "message": "Product not found"}), 404

                qr_data = str(product["id"])
                qr = qrcode.QRCode(
                    version=1,
                    error_correction=qrcode.constants.ERROR_CORRECT_H,
                    box_size=10,
                    border=4,
                )
                qr.add_data(qr_data)
                qr.make(fit=True)
                qr_img = qr.make_image(fill_color="black", back_color="white").convert('RGBA')

                logo_path = os.path.join("static", "img", "logo.png")
                if not os.path.exists(logo_path):
                    return jsonify({"success": False, "message": "Logo file not found"}), 500
                
                logo = Image.open(logo_path).convert('RGBA')
                qr_width, qr_height = qr_img.size
                logo_size = qr_width // 4
                logo = logo.resize((logo_size, logo_size), Image.Resampling.LANCZOS)
                logo_position = ((qr_width - logo_size) // 2, (qr_height - logo_size) // 2)
                qr_img.paste(logo, logo_position, logo)

                if save_locally:
                    qr_dir = os.path.join("static", "qr_codes")
                    os.makedirs(qr_dir, exist_ok=True)
                    file_path = os.path.join(qr_dir, f"{product_id}.png")
                    qr_img.save(file_path, format="PNG")
                    return send_file(file_path, mimetype="image/png")
                
                img_io = io.BytesIO()
                qr_img.save(img_io, format="PNG")
                img_io.seek(0)
                return send_file(img_io, mimetype="image/png")
        except Exception as e:
            return jsonify({"success": False, "message": f"Server error: {str(e)}"}), 500

class LectorController:
    @staticmethod
    def get_products():
        """Retrieve products from the database."""
        if 'user' not in session:
            raise Exception("User not authenticated")
        
        company_id = session['user'].get('company_id')
        conn = Config.get_db_connection()
        try:
            with conn.cursor(dictionary=True) as cursor:
                cursor.execute(
                    """SELECT id, name, category, price, stock, cost_price 
                    FROM products 
                    WHERE company_id = %s""",
                    (company_id,)
                )
                products = [
                    {
                        'id': str(row['id']),
                        'name': row['name'],
                        'category': row['category'],
                        'price': float(row['price']),
                        'stock': row['stock'],
                        'cost': float(row['cost_price'])
                    } for row in cursor.fetchall()
                ]
        finally:
            conn.close()
        return products

    @staticmethod
    def inventory(stripe_public_key=None):
        """Render the inventory page."""
        if 'user' not in session:
            return redirect(url_for('login'))
        
        if session['user']['role'] not in ['vendedor', 'encargado de almacén', 'gerente', 'admin']:
            return redirect(url_for('forbidden_error'))
        
        fecha_actual = datetime.now().strftime('%Y-%m-%d')
        
        return render_template('user/inventory.html', fecha_actual=fecha_actual, stripe_public_key=stripe_public_key)

    @staticmethod
    def products():
        """Return the list of products in JSON format."""
        if 'user' not in session:
            return jsonify({"success": False, "message": "Not authenticated"}), 401
        
        if session['user']['role'] not in ['vendedor', 'encargado de almacén', 'gerente', 'admin']:
            return jsonify({"success": False, "message": "Unauthorized access"}), 403
        
        try:
            products = LectorController.get_products()
            return jsonify({"success": True, "products": products})
        except Exception as e:
            return jsonify({"success": False, "message": f"Server error: {str(e)}"}), 500

    @staticmethod
    def cart():
        """Return the cart contents in JSON format."""
        if 'user' not in session:
            return jsonify({"success": False, "message": "Not authenticated"}), 401
        
        if session['user']['role'] not in ['vendedor', 'encargado de almacén', 'gerente', 'admin']:
            return jsonify({"success": False, "message": "Unauthorized access"}), 403
        
        try:
            cart = session.get('cart', {})
            # Asegurar que el carrito sea compatible con qr.js
            formatted_cart = {
                str(k): {
                    "nombre": v["name"],
                    "price": v["price"],
                    "cantidad": v["quantity"]
                } for k, v in cart.items()
            }
            return jsonify({"success": True, "carrito": formatted_cart})
        except Exception as e:
            return jsonify({"success": False, "message": f"Server error: {str(e)}"}), 500

    @staticmethod
    def scan():
        """Scan a product and add it to the cart."""
        if 'user' not in session:
            return jsonify({"success": False, "message": "Not authenticated"}), 401
        
        if session['user']['role'] not in ['vendedor', 'encargado de almacén', 'gerente', 'admin']:
            return jsonify({"success": False, "message": "Unauthorized access"}), 403
        
        try:
            data = request.get_json()
            code = data.get('codigo')  # Ajustado a lo que envía qr.js
            if not code:
                return jsonify({"success": False, "message": "No code provided"}), 400

            code = str(code)
            inventory = {p['id']: p for p in LectorController.get_products()}
            if code in inventory:
                cart = session.get('cart', {})
                if code in cart:
                    if cart[code]["quantity"] + 1 <= inventory[code]["stock"]:
                        cart[code]["quantity"] += 1
                    else:
                        return jsonify({"success": False, "message": "Insufficient stock"}), 400
                else:
                    cart[code] = {
                        "name": inventory[code]["name"],
                        "price": inventory[code]["price"],
                        "stock": inventory[code]["stock"],
                        "quantity": 1
                    }

                session['cart'] = cart
                session.modified = True
                return jsonify({
                    "success": True,
                    "producto": inventory[code]["name"],  # Ajustado a qr.js
                    "cantidad": cart[code]["quantity"]    # Ajustado a qr.js
                })
            
            return jsonify({"success": False, "message": "Product not found"}), 404
        except Exception as e:
            return jsonify({"success": False, "message": f"Server error: {str(e)}"}), 500

    @staticmethod
    def update_cart():
        """Update the cart with a specified quantity."""
        if 'user' not in session:
            return jsonify({"success": False, "message": "Not authenticated"}), 401
            
        if session['user']['role'] not in ['vendedor', 'encargado de almacén', 'gerente', 'admin']:
            return jsonify({"success": False, "message": "Unauthorized access"}), 403
        
        try:
            data = request.get_json()
            product_id = str(data.get('codigo'))  # Ajustado a qr.js
            quantity = int(data.get('cantidad', 0))  # Ajustado a qr.js
            inventory = {p['id']: p for p in LectorController.get_products()}
            
            cart = session.get('cart', {})
            if product_id in inventory:
                if quantity <= inventory[product_id]["stock"]:
                    if quantity == 0 and product_id in cart:
                        del cart[product_id]
                    elif quantity > 0:
                        cart[product_id] = {
                            "name": inventory[product_id]["name"],
                            "price": inventory[product_id]["price"],
                            "stock": inventory[product_id]["stock"],
                            "quantity": quantity
                        }
                    session['cart'] = cart
                    session.modified = True
                    return jsonify({"success": True})
                return jsonify({"success": False, "message": "Insufficient stock"})
            return jsonify({"success": False, "message": "Product not found"})
        except Exception as e:
            return jsonify({"success": False, "message": f"Server error: {str(e)}"}), 500

    @staticmethod
    def checkout():
        """Process the cart and update stock."""
        if 'user' not in session:
            return jsonify({"success": False, "message": "Not authenticated"}), 401
            
        if session['user']['role'] not in ['vendedor', 'encargado de almacén', 'gerente', 'admin']:
            return jsonify({"success": False, "message": "Unauthorized access"}), 403
        
        try:
            cart = session.get('cart', {})
            if cart:
                company_id = session['user'].get('company_id')
                conn = Config.get_db_connection()
                try:
                    with conn.cursor() as cursor:
                        for product_id, item in cart.items():
                            if item["quantity"] > 0:
                                cursor.execute(
                                    "UPDATE products SET stock = stock - %s WHERE id = %s AND company_id = %s",
                                    (item["quantity"], product_id, company_id)
                                )
                        conn.commit()
                finally:
                    conn.close()
                session['cart'] = {}
                session.modified = True
                return jsonify({"success": True, "message": "Checkout processed successfully"})
            return jsonify({"success": False, "message": "Cart is empty"})
        except Exception as e:
            return jsonify({"success": False, "message": f"Server error: {str(e)}"}), 500