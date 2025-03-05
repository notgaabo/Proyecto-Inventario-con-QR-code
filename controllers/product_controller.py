#controllers/product_contorller.py

import mysql.connector
from flask import render_template, request, redirect, url_for, session
from db import Config
import os

class ProductController:
    def __init__(self):
        self.connection = Config.get_db_connection()

    def get_product_list(self):
        """Lista los productos del usuario autenticado."""
        if 'user' not in session:
            return redirect(url_for('login'))
        
        user_id = session['user']['id']
        
        with self.connection.cursor(dictionary=True) as cursor:
            cursor.execute("""
                SELECT id, name, category, price, stock, cost_price, user_id 
                FROM products 
                WHERE user_id = %s
            """, (user_id,))
            products = cursor.fetchall()
            
        return render_template('products/product_list.html', products=products)

    def add_product(self):
        """Agrega un nuevo producto a la base de datos."""
        if 'user' not in session:
            return redirect(url_for('login'))
        
        if request.method == 'POST':
            try:
                name = request.form['name']
                category = request.form['category']
                price = float(request.form['price'])
                stock = int(request.form['stock'])
                cost_price = float(request.form['cost_price'])
                user_id = session['user']['id']
                
                with self.connection.cursor() as cursor:
                    cursor.execute("""
                        INSERT INTO products (name, category, price, stock, cost_price, user_id) 
                        VALUES (%s, %s, %s, %s, %s, %s)
                    """, (name, category, price, stock, cost_price, user_id))
                    self.connection.commit()
                
                return redirect(url_for('product_list'))
            except Exception as e:
                return render_template('products/product_list.html', error=str(e))
        return render_template('products/add_product.html')

    def update_product(self, product_id):
        """Actualiza un producto existente."""
        if 'user' not in session:
            return redirect(url_for('login'))
        
        if request.method == 'POST':
            try:
                name = request.form['name']
                category = request.form['category']
                price = float(request.form['price'])
                stock = int(request.form['stock'])
                cost_price = float(request.form['cost_price'])
                
                with self.connection.cursor() as cursor:
                    cursor.execute("""
                        UPDATE products 
                        SET name = %s, category = %s, price = %s, stock = %s, cost_price = %s 
                        WHERE id = %s AND user_id = %s
                    """, (name, category, price, stock, cost_price, product_id, session['user']['id']))
                    self.connection.commit()
                    
                    if cursor.rowcount == 0:
                        return render_template('errors/404.html'), 404
                        
                return redirect(url_for('product_list'))
            except Exception as e:
                return render_template('products/edit_product.html', error=str(e), product_id=product_id)
                
        # GET request - show edit form
        with self.connection.cursor(dictionary=True) as cursor:
            cursor.execute("SELECT * FROM products WHERE id = %s AND user_id = %s", 
                         (product_id, session['user']['id']))
            product = cursor.fetchone()
            if not product:
                return render_template('errors/404.html'), 404
        return render_template('products/edit_product.html', product=product)

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
                    
            # Delete associated QR code if exists
            qr_path = f"static/qr_codes/{product_id}.png"
            if os.path.exists(qr_path):
                os.remove(qr_path)
                
            return redirect(url_for('product_list'))
        except Exception as e:
            return render_template('products/product_list.html', error=str(e))