from flask import render_template, request, redirect, url_for, session, jsonify, make_response
from db import Config
import os
import mysql.connector
from werkzeug.utils import secure_filename

# Configuración para la carpeta de subidas
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

class ProductController:
    @staticmethod
    def allowed_file(filename):
        """Verifica si la extensión del archivo es permitida."""
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

    @staticmethod
    def get_product_list():
        """Lista los productos del usuario autenticado."""
        if 'user' not in session:
            return redirect(url_for('login'))
        
        user_id = session['user']['id']
        connection = Config.get_db_connection()
        try:
            with connection.cursor(dictionary=True) as cursor:
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
        finally:
            connection.close()

    @staticmethod
    def add_product():
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
                    if file and file.filename != '' and ProductController.allowed_file(file.filename):
                        filename = secure_filename(file.filename)
                        if not os.path.exists(UPLOAD_FOLDER):
                            os.makedirs(UPLOAD_FOLDER)
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
                
                connection = Config.get_db_connection()
                try:
                    with connection.cursor() as cursor:
                        cursor.execute("""
                            INSERT INTO products (name, category, price, stock, cost_price, user_id, image) 
                            VALUES (%s, %s, %s, %s, %s, %s, %s)
                        """, (name, category, price, stock, cost_price, user_id, image))
                        connection.commit()
                        print(f"Producto {name} agregado con ID: {cursor.lastrowid}")
                    return redirect(url_for('product_list'))
                finally:
                    connection.close()
            except ValueError as ve:
                print(f"Validación fallida: {str(ve)}")
                return render_template('products/product_list.html', error=str(ve), products=ProductController._get_products(user_id))
            except Exception as e:
                print(f"Error al agregar producto: {str(e)}")
                return render_template('products/product_list.html', error=f"Error al agregar producto: {str(e)}", products=ProductController._get_products(user_id))
        return render_template('products/add_product.html')

    @staticmethod
    def _get_products(user_id):
        """Método auxiliar para obtener productos."""
        connection = Config.get_db_connection()
        try:
            with connection.cursor(dictionary=True) as cursor:
                cursor.execute("""
                    SELECT id, name, category, price, stock, cost_price, user_id, image 
                    FROM products 
                    WHERE user_id = %s
                """, (user_id,))
                return cursor.fetchall()
        finally:
            connection.close()

    @staticmethod
    def update_product(product_id):
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
                user_id = session['user']['id']
                image = None

                if 'image' in request.files:
                    file = request.files['image']
                    if file and file.filename != '' and ProductController.allowed_file(file.filename):
                        filename = secure_filename(file.filename)
                        if not os.path.exists(UPLOAD_FOLDER):
                            os.makedirs(UPLOAD_FOLDER)
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
                
                connection = Config.get_db_connection()
                try:
                    with connection.cursor() as cursor:
                        if image:
                            cursor.execute("""
                                UPDATE products 
                                SET name = %s, category = %s, price = %s, stock = %s, cost_price = %s, image = %s 
                                WHERE id = %s AND user_id = %s
                            """, (name, category, price, stock, cost_price, image, product_id, user_id))
                        else:
                            cursor.execute("""
                                UPDATE products 
                                SET name = %s, category = %s, price = %s, stock = %s, cost_price = %s 
                                WHERE id = %s AND user_id = %s
                            """, (name, category, price, stock, cost_price, product_id, user_id))
                        connection.commit()
                        if cursor.rowcount == 0:
                            return render_template('errors/404.html'), 404
                    return redirect(url_for('product_list'))
                finally:
                    connection.close()
            except ValueError as ve:
                return render_template('products/edit_product.html', error=str(ve), product_id=product_id)
            except Exception as e:
                return render_template('products/edit_product.html', error=f"Error al actualizar: {str(e)}", product_id=product_id)
        
        connection = Config.get_db_connection()
        try:
            with connection.cursor(dictionary=True) as cursor:
                cursor.execute("SELECT * FROM products WHERE id = %s AND user_id = %s", 
                              (product_id, session['user']['id']))
                product = cursor.fetchone()
                if not product:
                    return render_template('errors/404.html'), 404
            return render_template('products/edit_product.html', product=product)
        except Exception as e:
            return render_template('errors/404.html', error=f"Error al cargar producto: {str(e)}"), 404
        finally:
            connection.close()

    
    @staticmethod
    def delete_product(product_id):
        """Elimina un producto, su imagen de static/uploads y su QR de static/qr_codes si existen."""
        if 'user' not in session:
            return jsonify({"success": False, "message": "Not authenticated"}), 401
        
        connection = Config.get_db_connection()
        try:
            with connection.cursor(dictionary=True) as cursor:
                cursor.execute("SELECT image FROM products WHERE id = %s AND user_id = %s", 
                            (product_id, session['user']['id']))
                product = cursor.fetchone()
                if not product:
                    return jsonify({"success": False, "message": "Product not found"}), 404

                if product['image']:
                    image_path = os.path.join(UPLOAD_FOLDER, product['image'])
                    if os.path.exists(image_path):
                        os.remove(image_path)
                        print(f"Imagen eliminada: {image_path}")
                    else:
                        print(f"Imagen no encontrada: {image_path}")

                qr_path = os.path.join("static", "qr_codes", f"{product_id}.png")
                if os.path.exists(qr_path):
                    os.remove(qr_path)
                    print(f"Código QR eliminado: {qr_path}")
                else:
                    print(f"Código QR no encontrado: {qr_path}")

                cursor.execute("DELETE FROM products WHERE id = %s AND user_id = %s", 
                            (product_id, session['user']['id']))
                connection.commit()
                if cursor.rowcount == 0:
                    return jsonify({"success": False, "message": "Product not found"}), 404

            return jsonify({"success": True})
        except Exception as e:
            print(f"Error al eliminar producto, imagen o QR: {str(e)}")
            return jsonify({"success": False, "message": f"Error al eliminar: {str(e)}"}), 500
        finally:
            connection.close()

    @staticmethod
    def filter_products():
        """Filtra productos dinámicamente según los parámetros enviados desde el frontend."""
        if 'user' not in session:
            return jsonify({"success": False, "message": "Not authenticated"}), 401
        
        user_id = session['user']['id']
        data = request.get_json()
        
        search = data.get('search', '')
        category = data.get('category', 'all')
        min_price = data.get('minPrice', '')
        max_price = data.get('maxPrice', '')
        availability = data.get('availability', 'all')
        sort = data.get('sort', 'relevance')

        query = """
            SELECT id, name, category, price, stock, cost_price, image 
            FROM products 
            WHERE user_id = %s
        """
        params = [user_id]

        if search:
            query += " AND name LIKE %s"
            params.append(f"%{search}%")

        if category != 'all':
            query += " AND category = %s"
            params.append(category)

        if min_price:
            query += " AND price >= %s"
            params.append(float(min_price))
        if max_price:
            query += " AND price <= %s"
            params.append(float(max_price))

        if availability == 'inStock':
            query += " AND stock > 0"
        elif availability == 'outOfStock':
            query += " AND stock = 0"

        if sort == 'priceAsc':
            query += " ORDER BY price ASC"
        elif sort == 'priceDesc':
            query += " ORDER BY price DESC"
        else:  # relevance
            query += " ORDER BY name ASC"

        connection = Config.get_db_connection()
        try:
            with connection.cursor(dictionary=True) as cursor:
                cursor.execute(query, params)
                products = cursor.fetchall()
            return jsonify({"success": True, "productos": products})
        except Exception as e:
            print(f"Error al filtrar productos: {str(e)}")
            return jsonify({"success": False, "message": f"Error al filtrar productos: {str(e)}"}), 500
        finally:
            connection.close()

    @staticmethod
    def sales_history():
        """Muestra el historial de ventas con paginación."""
        if 'user' not in session:
            return redirect(url_for('login'))
        
        user_id = session['user']['id']
        connection = Config.get_db_connection()
        
        sales = []
        total_sales = 0
        total_profit = 0
        avg_per_sale = 0
        profit_margin = 0
        total_rows = 0
        
        # Pagination parameters
        rows_per_page = 10
        page = request.args.get('page', 1, type=int)
        offset = (page - 1) * rows_per_page
        
        try:
            product_filter = request.args.get('product', 'all')
            start_date = request.args.get('start_date')
            end_date = request.args.get('end_date')
            
            count_query = "SELECT COUNT(*) as total FROM sales WHERE user_id = %s"
            params_count = [user_id]
            
            query = """
                SELECT s.*, p.cost_price 
                FROM sales s
                JOIN products p ON s.product_id = p.id
                WHERE s.user_id = %s
            """
            params = [user_id]
            
            if product_filter != 'all':
                query += " AND s.product_id = %s"
                count_query += " AND product_id = %s"
                params.append(product_filter)
                params_count.append(product_filter)
            if start_date:
                query += " AND s.sale_date >= %s"
                count_query += " AND sale_date >= %s"
                params.append(start_date)
                params_count.append(start_date)
            if end_date:
                query += " AND s.sale_date <= %s"
                count_query += " AND sale_date <= %s"
                params.append(end_date)
                params_count.append(end_date)
            
            query += " LIMIT %s OFFSET %s"
            params.extend([rows_per_page, offset])
            
            with connection.cursor(dictionary=True) as cursor:
                cursor.execute(count_query, params_count)
                total_rows = cursor.fetchone()['total']
                
                cursor.execute(query, params)
                sales = cursor.fetchall()
                
                for sale in sales:
                    sale_price = float(sale['sale_price'])
                    cost_price = float(sale['cost_price'])
                    quantity = float(sale['quantity'])
                    sale_total = sale_price * quantity
                    profit = (sale_price - cost_price) * quantity
                    sale['profit'] = profit
                    total_sales += sale_total
                    total_profit += profit
                
                avg_per_sale = total_sales / len(sales) if sales else 0
                profit_margin = (total_profit / total_sales * 100) if total_sales > 0 else 0
            
            total_pages = (total_rows + rows_per_page - 1) // rows_per_page
            
            return render_template(
                'products/sales_history.html',
                sales=sales,
                total_sales=total_sales,
                total_profit=total_profit,
                avg_per_sale=avg_per_sale,
                profit_margin=profit_margin,
                page=page,
                total_pages=total_pages,
                total_rows=total_rows
            )
        except mysql.connector.Error as db_err:
            print(f"Database Error: {str(db_err)}")
            return render_template(
                'products/sales_history.html',
                error=f"Database Error: {str(db_err)}",
                sales=sales,
                total_sales=total_sales,
                total_profit=total_profit,
                avg_per_sale=avg_per_sale,
                profit_margin=profit_margin,
                page=page,
                total_pages=1,
                total_rows=total_rows
            )
        except Exception as e:
            print(f"Error: {str(e)}")
            return render_template(
                'products/sales_history.html',
                error=f"Error: {str(e)}",
                sales=sales,
                total_sales=total_sales,
                total_profit=total_profit,
                avg_per_sale=avg_per_sale,
                profit_margin=profit_margin,
                page=page,
                total_pages=1,
                total_rows=total_rows
            )
        finally:
            connection.close()