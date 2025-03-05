import mysql.connector
from flask import render_template, request, redirect, url_for, session, jsonify
from db import Config

class ProductController:
    def __init__(self):
        # Mantener la conexión abierta como solicitaste
        self.connection = Config.get_db_connection()

    def get_product_list(self):
        """Lista los productos del usuario autenticado."""
        if 'user' not in session:
            return redirect(url_for('login'))
        
        user_id = session['user']['id']
        try:
            with self.connection.cursor(dictionary=True) as cursor:
                cursor.execute("""
                    SELECT id, name, category, price, stock, cost_price, user_id 
                    FROM products 
                    WHERE user_id = %s
                """, (user_id,))
                products = cursor.fetchall()
                print(f"Productos encontrados para user_id {user_id}: {products}")  # Depuración
            return render_template('products/product_list.html', products=products)
        except Exception as e:
            print(f"Error al cargar productos: {str(e)}")  # Depuración
            return render_template('products/product_list.html', error=f"Error al cargar productos: {str(e)}", products=[])

    def add_product(self):
        """Agrega un nuevo producto a la base de datos."""
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

                print(f"Datos recibidos: {request.form}")  # Depuración

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
                        INSERT INTO products (name, category, price, stock, cost_price, user_id) 
                        VALUES (%s, %s, %s, %s, %s, %s)
                    """, (name, category, price, stock, cost_price, user_id))
                    self.connection.commit()
                    print(f"Producto {name} agregado para user_id {user_id}")  # Depuración
                
                # Renderizar la lista actualizada directamente
                return self.get_product_list()
            except ValueError as ve:
                print(f"Validación fallida: {str(ve)}")  # Depuración
                return render_template('products/product_list.html', error=str(ve), products=self._get_products(user_id))
            except Exception as e:
                print(f"Error al agregar producto: {str(e)}")  # Depuración
                return render_template('products/product_list.html', error=f"Error al agregar producto: {str(e)}", products=self._get_products(user_id))
        return redirect(url_for('product_list'))  # Si es GET, redirige a la lista

    def _get_products(self, user_id):
        """Helper method to fetch products."""
        try:
            with self.connection.cursor(dictionary=True) as cursor:
                cursor.execute("""
                    SELECT id, name, category, price, stock, cost_price, user_id 
                    FROM products 
                    WHERE user_id = %s
                """, (user_id,))
                return cursor.fetchall()
        except Exception as e:
            print(f"Error en _get_products: {str(e)}")  # Depuración
            return []

    def update_product(self, product_id):
        """Actualiza un producto existente."""
        if 'user' not in session:
            return redirect(url_for('login'))
        
        if request.method == 'POST':
            try:
                name = request.form['name'].strip()
                category = request.form['category'].strip()
                price = float(request.form['price'])
                stock = int(request.form['stock'])
                cost_price = float(request.form['cost_price'])
                
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
                        UPDATE products 
                        SET name = %s, category = %s, price = %s, stock = %s, cost_price = %s 
                        WHERE id = %s AND user_id = %s
                    """, (name, category, price, stock, cost_price, product_id, session['user']['id']))
                    self.connection.commit()
                    if cursor.rowcount == 0:
                        return render_template('errors/404.html'), 404
                return self.get_product_list()  # Renderizar lista actualizada
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
        """Elimina un producto."""
        if 'user' not in session:
            return redirect(url_for('login'))
        
        try:
            with self.connection.cursor() as cursor:
                cursor.execute("DELETE FROM products WHERE id = %s AND user_id = %s", 
                              (product_id, session['user']['id']))
                self.connection.commit()
                if cursor.rowcount == 0:
                    return render_template('errors/404.html'), 404
            return self.get_product_list()  # Renderizar lista actualizada
        except Exception as e:
            return render_template('products/product_list.html', error=f"Error al eliminar: {str(e)}", products=self._get_products(session['user']['id']))

    def get_products_json(self):
        """Devuelve la lista de productos en formato JSON para actualizaciones dinámicas."""
        if 'user' not in session:
            return jsonify({"success": False, "message": "Not authenticated"}), 401
        user_id = session['user']['id']
        try:
            with self.connection.cursor(dictionary=True) as cursor:
                cursor.execute("""
                    SELECT id, name, category, price, stock, cost_price 
                    FROM products 
                    WHERE user_id = %s
                """, (user_id,))
                products = cursor.fetchall()
            return jsonify({"success": True, "productos": products})
        except Exception as e:
            print(f"Error al cargar productos en JSON: {str(e)}")
            return jsonify({"success": False, "message": f"Error al cargar productos: {str(e)}"}), 500