from flask import render_template, request, redirect, url_for, session, jsonify, make_response
from db import Config
import os
from werkzeug.utils import secure_filename

# Configuración para la carpeta de subidas
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

class ProductController:
    def __init__(self):
        self.connection = Config.get_db_connection()
        # Asegurarse de que la carpeta de subidas exista
        if not os.path.exists(UPLOAD_FOLDER):
            os.makedirs(UPLOAD_FOLDER)

    def allowed_file(self, filename):
        """Verifica si la extensión del archivo es permitida."""
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

    def get_product_list(self):
        """Lista los productos del usuario autenticado."""
        if 'user' not in session:
            return redirect(url_for('login'))
        
        user_id = session['user']['id']
        # Forzar una nueva conexión para asegurar datos frescos
        self.connection = Config.get_db_connection()
        try:
            with self.connection.cursor(dictionary=True) as cursor:
                cursor.execute("""
                    SELECT id, name, category, price, stock, cost_price, user_id, image 
                    FROM products 
                    WHERE user_id = %s
                """, (user_id,))
                products = cursor.fetchall()
            response = make_response(render_template('products/product_list.html', products=products))
            response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"
            return response
        except Exception as e:
            print(f"Error al cargar productos: {str(e)}")
            return render_template('products/product_list.html', error=f"Error al cargar productos: {str(e)}", products=[])

    def add_product(self):
        """Agrega un nuevo producto a la base de datos con imagen."""
        if 'user' not in session:
            return redirect(url_for('login'))
        
        if request.method == 'POST':
            try:
                name = request.form['name'].strip()
                category = request.form['category'].strip()
                price = float(request.form['price'])
                stock = int(request.form['stock'])
                cost_price = float(request.form['cost_price'])
                user_id = session['user']['id']
                image = None

                if 'image' in request.files:
                    file = request.files['image']
                    if file and file.filename != '' and self.allowed_file(file.filename):
                        filename = secure_filename(file.filename)
                        file.save(os.path.join(UPLOAD_FOLDER, filename))
                        image = f"{filename}"
                    elif file and file.filename != '':
                        raise ValueError("Formato de imagen no permitido. Usa PNG, JPG, JPEG o GIF.")

                if not name or not category:
                    raise ValueError("El nombre y la categoría no pueden estar vacíos.")
                if price <= 0 or cost_price <= 0:
                    raise ValueError("El precio y el costo deben ser mayores a cero.")
                if price < cost_price:
                    raise ValueError("El precio de venta no puede ser menor al costo.")
                if stock < 0:
                    raise ValueError("El stock no puede ser negativo.")
                
                with self.connection.cursor() as cursor:
                    cursor.execute("""
                        INSERT INTO products (name, category, price, stock, cost_price, user_id, image) 
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """, (name, category, price, stock, cost_price, user_id, image))
                    self.connection.commit()
                    print(f"Producto {name} agregado con ID: {cursor.lastrowid}")  # Depuración
                
                return redirect(url_for('product_list')) 

            except ValueError as ve:
                print(f"Validación fallida: {str(ve)}")  
                return render_template('products/product_list.html', error=str(ve), products=self._get_products(session['user']['id']))
            except Exception as e:
                print(f"Error al agregar producto: {str(e)}") 
                return render_template('products/product_list.html', error=f"Error al agregar producto: {str(e)}", products=self._get_products(session['user']['id']))
        return redirect(url_for('product_list')) 

    def _get_products(self, user_id):
        """Helper method to fetch products."""
        try:
            with self.connection.cursor(dictionary=True) as cursor:
                cursor.execute("""
                    SELECT id, name, category, price, stock, cost_price, user_id, image 
                    FROM products 
                    WHERE user_id = %s
                """, (user_id,))
                return cursor.fetchall()
        except Exception as e:
            print(f"Error en _get_products: {str(e)}")  
            return []

    def update_product(self, product_id):
        """Actualiza un producto existente con posibilidad de cambiar la imagen."""
        if 'user' not in session:
            return redirect(url_for('login'))
        
        if request.method == 'POST':
            try:
                name = request.form['name'].strip()
                category = request.form['category'].strip()
                price = float(request.form['price'])
                stock = int(request.form['stock'])
                cost_price = float(request.form['cost_price'])
                image = None

                if 'image' in request.files:
                    file = request.files['image']
                    if file and file.filename != '' and self.allowed_file(file.filename):
                        filename = secure_filename(file.filename)
                        file.save(os.path.join(UPLOAD_FOLDER, filename))
                        image = f"{filename}"
                    elif file and file.filename != '':
                        raise ValueError("Formato de imagen no permitido. Usa PNG, JPG, JPEG o GIF.")

                if not name or not category:
                    raise ValueError("El nombre y la categoría no pueden estar vacíos.")
                if price <= 0 or cost_price <= 0:
                    raise ValueError("El precio y el costo deben ser mayores a cero.")
                if price < cost_price:
                    raise ValueError("El precio de venta no puede ser menor al costo.")
                if stock < 0:
                    raise ValueError("El stock no puede ser negativo.")
                
                with self.connection.cursor() as cursor:
                    if image:  
                        cursor.execute("""
                            UPDATE products 
                            SET name = %s, category = %s, price = %s, stock = %s, cost_price = %s, image = %s 
                            WHERE id = %s AND user_id = %s
                        """, (name, category, price, stock, cost_price, image, product_id, session['user']['id']))
                    else:  
                        cursor.execute("""
                            UPDATE products 
                            SET name = %s, category = %s, price = %s, stock = %s, cost_price = %s 
                            WHERE id = %s AND user_id = %s
                        """, (name, category, price, stock, cost_price, product_id, session['user']['id']))
                    self.connection.commit()
                    if cursor.rowcount == 0:
                        return render_template('errors/404.html'), 404
                return self.get_product_list()
            except ValueError as ve:
                return render_template('products/edit_product.html', error=str(ve), product_id=product_id)
            except Exception as e:
                return render_template('products/edit_product.html', error=f"Error al actualizar: {str(e)}", product_id=product_id)
                
        try:
            with self.connection.cursor(dictionary=True) as cursor:
                cursor.execute("SELECT * FROM products WHERE id = %s AND user_id = %s", 
                              (product_id, session['user']['id']))
                product = cursor.fetchone()
                if not product:
                    return render_template('errors/404.html'), 404
            return render_template('products/edit_product.html', product=product)
        except Exception as e:
            return render_template('errors/404.html', error=f"Error al cargar producto: {str(e)}"), 404

    def delete_product(self, product_id):
        """Elimina un producto, su imagen de static/uploads y su QR de static/qr_codes si existen, luego redirige a la lista de productos."""
        if 'user' not in session:
            return redirect(url_for('login'))
        
        try:
            with self.connection.cursor(dictionary=True) as cursor:
                # Obtener el producto para verificar si tiene imagen
                cursor.execute("SELECT image FROM products WHERE id = %s AND user_id = %s", 
                            (product_id, session['user']['id']))
                product = cursor.fetchone()
                if not product:
                    return render_template('errors/404.html'), 404

                # Eliminar la imagen de static/uploads si existe
                if product['image']:
                    image_path = os.path.join(UPLOAD_FOLDER, product['image'])
                    if os.path.exists(image_path):
                        os.remove(image_path)
                        print(f"Imagen eliminada: {image_path}")  # Depuración
                    else:
                        print(f"Imagen no encontrada: {image_path}")  # Depuración

                # Eliminar el código QR de static/qr_codes si existe
                qr_path = os.path.join("static", "qr_codes", f"{product_id}.png")
                if os.path.exists(qr_path):
                    os.remove(qr_path)
                    print(f"Código QR eliminado: {qr_path}")  # Depuración
                else:
                    print(f"Código QR no encontrado: {qr_path}")  # Depuración

                # Eliminar el producto de la base de datos
                cursor.execute("DELETE FROM products WHERE id = %s AND user_id = %s", 
                            (product_id, session['user']['id']))
                self.connection.commit()
                if cursor.rowcount == 0:
                    return render_template('errors/404.html'), 404

            # Redirigir a la lista de productos actualizada
            return redirect(url_for('product_list'))

        except Exception as e:
            # En caso de error, redirigir con mensaje de error
            print(f"Error al eliminar producto, imagen o QR: {str(e)}")
            return redirect(url_for('product_list', error=f"Error al eliminar: {str(e)}"))

    def get_products_json(self):
        """Devuelve la lista de productos en formato JSON para actualizaciones dinámicas."""
        if 'user' not in session:
            return jsonify({"success": False, "message": "Not authenticated"}), 401
        user_id = session['user']['id']
        try:
            with self.connection.cursor(dictionary=True) as cursor:
                cursor.execute("""
                    SELECT id, name, category, price, stock, cost_price, image 
                    FROM products 
                    WHERE user_id = %s
                """, (user_id,))
                products = cursor.fetchall()
            return jsonify({"success": True, "productos": products})
        except Exception as e:
            print(f"Error al cargar productos en JSON: {str(e)}")
            return jsonify({"success": False, "message": f"Error al cargar productos: {str(e)}"}), 500