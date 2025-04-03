# controllers/product_controller.py
from flask import render_template, request, redirect, url_for, session, jsonify, make_response, flash
from db import Config
import os
from werkzeug.utils import secure_filename
from datetime import datetime

# Configuración de archivos
UPLOAD_FOLDER = 'static/uploads'
QR_FOLDER = 'static/qr_codes'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB

class ProductController:
    @staticmethod
    def _allowed_file(filename):
        """Verifica si la extensión del archivo es permitida."""
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

    @staticmethod
    def _validate_product_data(name, category, price, stock, cost_price, supplier_id=None):
        """Valida los datos del producto antes de procesarlos."""
        errors = []
        if not name or not name.strip():
            errors.append("El nombre es obligatorio")
        if not category or not category.strip():
            errors.append("La categoría es obligatoria")
        if not isinstance(price, (int, float)) or price <= 0:
            errors.append("El precio debe ser mayor a cero")
        if not isinstance(stock, int) or stock < 0:
            errors.append("El stock no puede ser negativo")
        if not isinstance(cost_price, (int, float)) or cost_price <= 0:
            errors.append("El costo debe ser mayor a cero")
        if price <= cost_price:
            errors.append("El precio debe ser mayor al costo")
        if supplier_id is not None and not isinstance(supplier_id, int):
            errors.append("El ID del proveedor debe ser un número entero")
        return errors

    @staticmethod
    def _get_db_connection():
        """Obtiene una conexión a la base de datos con manejo de errores."""
        try:
            return Config.get_db_connection()
        except Exception as e:
            print(f"Error al conectar a la base de datos: {str(e)}")
            raise

    @staticmethod
    def get_product_list():
        """Lista los productos de la compañía del usuario autenticado con información del proveedor."""
        if 'user' not in session:
            return redirect(url_for('login'))

        company_id = session['user'].get('company_id')
        if not company_id:
            flash("No se encontró la compañía del usuario", "error")
            return redirect(url_for('login'))

        try:
            connection = ProductController._get_db_connection()
            with connection.cursor(dictionary=True) as cursor:
                cursor.execute("""
                    SELECT p.id, p.name, p.category, p.price, p.stock, p.cost_price, p.image, 
                           p.supplier_id, p.company_id, s.name as supplier_name
                    FROM products p
                    LEFT JOIN suppliers s ON p.supplier_id = s.id
                    WHERE p.company_id = %s
                    ORDER BY p.id DESC
                """, (company_id,))
                products = cursor.fetchall()
            
            response = make_response(render_template('products/product_list.html', products=products))
            response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
            return response
        except Exception as e:
            print(f"Error al listar productos: {str(e)}")
            flash(f"Error al cargar productos: {str(e)}", "error")
            return render_template('products/product_list.html', products=[])
        finally:
            if 'connection' in locals():
                connection.close()

    @staticmethod
    def add_product():
        """Agrega un nuevo producto con validación, imagen y proveedor."""
        if 'user' not in session:
            return redirect(url_for('login'))

        company_id = session['user'].get('company_id')
        user_id = session['user'].get('id')

        if request.method == 'POST':
            try:
                # Obtener datos del formulario
                name = request.form.get('name', '').strip()
                category = request.form.get('category', '').strip()
                price = float(request.form.get('price', 0))
                stock = int(request.form.get('stock', 0))
                cost_price = float(request.form.get('cost_price', 0))
                supplier_id = request.form.get('supplier_id', type=int)

                # Validar datos
                errors = ProductController._validate_product_data(name, category, price, stock, cost_price, supplier_id)
                if errors:
                    for error in errors:
                        flash(error, "error")
                    return redirect(url_for('product_list'))

                # Manejar imagen
                image_filename = None
                if 'image' in request.files:
                    file = request.files['image']
                    if file and file.filename:
                        if not ProductController._allowed_file(file.filename):
                            flash("Formato de imagen no permitido", "error")
                            return redirect(url_for('product_list'))
                        if file.content_length > MAX_FILE_SIZE:
                            flash("La imagen excede el tamaño máximo de 5MB", "error")
                            return redirect(url_for('product_list'))
                        
                        filename = secure_filename(f"{company_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{file.filename}")
                        os.makedirs(UPLOAD_FOLDER, exist_ok=True)
                        file.save(os.path.join(UPLOAD_FOLDER, filename))
                        image_filename = filename

                # Insertar en la base de datos
                connection = ProductController._get_db_connection()
                with connection.cursor() as cursor:
                    cursor.execute("""
                        INSERT INTO products (name, category, price, stock, cost_price, image, supplier_id, company_id)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    """, (name, category, price, stock, cost_price, image_filename, supplier_id, company_id))
                    connection.commit()
                    product_id = cursor.lastrowid
                    print(f"Producto {name} (ID: {product_id}) agregado por usuario {user_id}")
                
                flash("Producto agregado exitosamente", "success")
                return redirect(url_for('product_list'))
            except ValueError as ve:
                flash(f"Error en los datos: {str(ve)}", "error")
                return redirect(url_for('product_list'))
            except Exception as e:
                print(f"Error al agregar producto: {str(e)}")
                flash(f"Error al agregar producto: {str(e)}", "error")
                return redirect(url_for('product_list'))
            finally:
                if 'connection' in locals():
                    connection.close()
        return redirect(url_for('product_list'))

    @staticmethod
    def update_product(product_id):
        """Actualiza un producto existente con validación y manejo de imagen."""
        if 'user' not in session:
            return redirect(url_for('login'))

        company_id = session['user'].get('company_id')
        
        if request.method == 'POST':
            try:
                name = request.form.get('name', '').strip()
                category = request.form.get('category', '').strip()
                price = float(request.form.get('price', 0))
                stock = int(request.form.get('stock', 0))
                cost_price = float(request.form.get('cost_price', 0))
                supplier_id = request.form.get('supplier_id', type=int)

                errors = ProductController._validate_product_data(name, category, price, stock, cost_price, supplier_id)
                if errors:
                    for error in errors:
                        flash(error, "error")
                    return redirect(url_for('update_product', product_id=product_id))

                image_filename = None
                if 'image' in request.files:
                    file = request.files['image']
                    if file and file.filename:
                        if not ProductController._allowed_file(file.filename):
                            flash("Formato de imagen no permitido", "error")
                            return redirect(url_for('update_product', product_id=product_id))
                        if file.content_length > MAX_FILE_SIZE:
                            flash("La imagen excede el tamaño máximo de 5MB", "error")
                            return redirect(url_for('update_product', product_id=product_id))
                        
                        filename = secure_filename(f"{company_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{file.filename}")
                        os.makedirs(UPLOAD_FOLDER, exist_ok=True)
                        file.save(os.path.join(UPLOAD_FOLDER, filename))
                        image_filename = filename

                connection = ProductController._get_db_connection()
                with connection.cursor() as cursor:
                    if image_filename:
                        cursor.execute("""
                            UPDATE products 
                            SET name = %s, category = %s, price = %s, stock = %s, cost_price = %s, 
                                image = %s, supplier_id = %s
                            WHERE id = %s AND company_id = %s
                        """, (name, category, price, stock, cost_price, image_filename, supplier_id, product_id, company_id))
                    else:
                        cursor.execute("""
                            UPDATE products 
                            SET name = %s, category = %s, price = %s, stock = %s, cost_price = %s, supplier_id = %s
                            WHERE id = %s AND company_id = %s
                        """, (name, category, price, stock, cost_price, supplier_id, product_id, company_id))
                    connection.commit()
                    if cursor.rowcount == 0:
                        flash("Producto no encontrado", "error")
                        return redirect(url_for('product_list'))
                
                flash("Producto actualizado exitosamente", "success")
                return redirect(url_for('product_list'))
            except Exception as e:
                print(f"Error al actualizar producto {product_id}: {str(e)}")
                flash(f"Error al actualizar: {str(e)}", "error")
                return redirect(url_for('update_product', product_id=product_id))
            finally:
                if 'connection' in locals():
                    connection.close()

        try:
            connection = ProductController._get_db_connection()
            with connection.cursor(dictionary=True) as cursor:
                cursor.execute("""
                    SELECT p.*, s.name as supplier_name 
                    FROM products p 
                    LEFT JOIN suppliers s ON p.supplier_id = s.id 
                    WHERE p.id = %s AND p.company_id = %s
                """, (product_id, company_id))
                product = cursor.fetchone()
                if not product:
                    flash("Producto no encontrado", "error")
                    return redirect(url_for('product_list'))
            return render_template('products/edit_product.html', product=product)
        except Exception as e:
            print(f"Error al cargar producto {product_id}: {str(e)}")
            flash(f"Error al cargar producto: {str(e)}", "error")
            return redirect(url_for('product_list'))
        finally:
            if 'connection' in locals():
                connection.close()

    @staticmethod
    def delete_product(product_id):
        """Elimina un producto y sus archivos asociados."""
        if 'user' not in session:
            return jsonify({"success": False, "message": "No autenticado"}), 401

        company_id = session['user'].get('company_id')
        try:
            connection = ProductController._get_db_connection()
            with connection.cursor(dictionary=True) as cursor:
                # Obtener información del producto
                cursor.execute("SELECT image FROM products WHERE id = %s AND company_id = %s", 
                             (product_id, company_id))
                product = cursor.fetchone()
                if not product:
                    return jsonify({"success": False, "message": "Producto no encontrado"}), 404

                # Eliminar archivos asociados
                if product['image']:
                    image_path = os.path.join(UPLOAD_FOLDER, product['image'])
                    if os.path.exists(image_path):
                        os.remove(image_path)
                        print(f"Imagen eliminada: {image_path}")

                qr_path = os.path.join(QR_FOLDER, f"{product_id}.png")
                if os.path.exists(qr_path):
                    os.remove(qr_path)
                    print(f"QR eliminado: {qr_path}")

                # Eliminar de la base de datos
                cursor.execute("DELETE FROM products WHERE id = %s AND company_id = %s", 
                             (product_id, company_id))
                connection.commit()
                
                print(f"Producto {product_id} eliminado exitosamente")
                return jsonify({"success": True, "message": "Producto eliminado"})
        except Exception as e:
            print(f"Error al eliminar producto {product_id}: {str(e)}")
            return jsonify({"success": False, "message": f"Error al eliminar: {str(e)}"}), 500
        finally:
            if 'connection' in locals():
                connection.close()

    @staticmethod
    def filter_products():
        """Filtra productos dinámicamente con parámetros del frontend."""
        if 'user' not in session:
            return jsonify({"success": False, "message": "No autenticado"}), 401

        company_id = session['user'].get('company_id')
        data = request.get_json() or {}

        try:
            search = data.get('search', '').lower()
            category = data.get('category', 'all')
            min_price = float(data.get('minPrice', 0)) if data.get('minPrice') else None
            max_price = float(data.get('maxPrice', float('inf'))) if data.get('maxPrice') else None
            availability = data.get('availability', 'all')
            sort = data.get('sort', 'relevance')

            query = """
                SELECT id, name, category, price, stock, cost_price, image, supplier_id 
                FROM products 
                WHERE company_id = %s
            """
            params = [company_id]

            if search:
                query += " AND LOWER(name) LIKE %s"
                params.append(f"%{search}%")
            if category != 'all':
                query += " AND category = %s"
                params.append(category)
            if min_price is not None:
                query += " AND price >= %s"
                params.append(min_price)
            if max_price is not None:
                query += " AND price <= %s"
                params.append(max_price)
            if availability == 'inStock':
                query += " AND stock > 0"
            elif availability == 'outOfStock':
                query += " AND stock = 0"

            query += " ORDER BY "
            if sort == 'priceAsc':
                query += "price ASC"
            elif sort == 'priceDesc':
                query += "price DESC"
            else:
                query += "id DESC"

            connection = ProductController._get_db_connection()
            with connection.cursor(dictionary=True) as cursor:
                cursor.execute(query, params)
                products = cursor.fetchall()
            return jsonify({"success": True, "productos": products})
        except Exception as e:
            print(f"Error al filtrar productos: {str(e)}")
            return jsonify({"success": False, "message": f"Error al filtrar: {str(e)}"}), 500
        finally:
            if 'connection' in locals():
                connection.close()

    @staticmethod
    def sales_history():
        """Muestra el historial de ventas con estadísticas y paginación."""
        if 'user' not in session:
            return redirect(url_for('login'))

        company_id = session['user'].get('company_id')
        page = request.args.get('page', 1, type=int)
        rows_per_page = 10
        offset = (page - 1) * rows_per_page

        try:
            connection = ProductController._get_db_connection()
            with connection.cursor(dictionary=True) as cursor:
                # Contar total de registros
                count_query = "SELECT COUNT(*) as total FROM sales WHERE company_id = %s"
                cursor.execute(count_query, (company_id,))
                total_rows = cursor.fetchone()['total']
                total_pages = (total_rows + rows_per_page - 1) // rows_per_page

                # Obtener ventas con filtros
                query = """
                    SELECT s.*, p.name, p.cost_price 
                    FROM sales s
                    JOIN products p ON s.product_id = p.id
                    WHERE s.company_id = %s
                    ORDER BY s.sale_date DESC
                    LIMIT %s OFFSET %s
                """
                cursor.execute(query, (company_id, rows_per_page, offset))
                sales = cursor.fetchall()

                # Calcular estadísticas
                total_sales = sum(float(sale['sale_price']) * float(sale['quantity']) for sale in sales)
                total_profit = sum((float(sale['sale_price']) - float(sale['cost_price'])) * float(sale['quantity']) 
                                 for sale in sales)
                avg_per_sale = total_sales / len(sales) if sales else 0
                profit_margin = (total_profit / total_sales * 100) if total_sales > 0 else 0

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
        except Exception as e:
            print(f"Error al cargar historial de ventas: {str(e)}")
            flash(f"Error al cargar historial: {str(e)}", "error")
            return render_template(
                'products/sales_history.html',
                sales=[],
                total_sales=0,
                total_profit=0,
                avg_per_sale=0,
                profit_margin=0,
                page=page,
                total_pages=1,
                total_rows=0
            )
        finally:
                connection.close()