import mysql.connector
from flask import render_template, request, redirect, url_for, session
from db import Config 

class ProductController:
    def __init__(self):
        self.connection = Config.get_db_connection() 

    @staticmethod
    def get_product_list():
        """Lista los productos del usuario autenticado."""
        if 'user' not in session:
            return redirect(url_for('login'))
        
        user_id = session['user']['id']
        connection = Config.get_db_connection()

        with connection.cursor(dictionary=True) as cursor:
            cursor.execute("SELECT * FROM products WHERE user_id = %s", (user_id,))
            products = cursor.fetchall()
        connection.close()
        return render_template('products/product_list.html', products=products)
    
    def add_product(self):
        """Agrega un nuevo producto a la base de datos."""
        if 'user' not in session:
            return redirect(url_for('login'))
        
        name = request.form['name']
        stock = request.form['stock']
        user_id = session['user']['id']
        
        with self.connection.cursor() as cursor:
            cursor.execute("INSERT INTO products (name, stock, user_id) VALUES (%s, %s, %s)", (name, stock, user_id))
            self.connection.commit()
        
        return redirect(url_for('products.product_list'))  
    
    def update_product(self, product_id):
        """Actualiza un producto existente."""
        if 'user' not in session:
            return redirect(url_for('login'))
        
        name = request.form['name']
        stock = request.form['stock']
        
        with self.connection.cursor() as cursor:
            cursor.execute("UPDATE products SET name = %s, stock = %s WHERE id = %s AND user_id = %s", (name, stock, product_id, session['user']['id']))
            self.connection.commit()
        
        return redirect(url_for('products.product_list'))
    
    def delete_product(self, product_id):
        """Elimina un producto."""
        if 'user' not in session:
            return redirect(url_for('login'))
        
        with self.connection.cursor() as cursor:
            cursor.execute("DELETE FROM products WHERE id = %s AND user_id = %s", (product_id, session['user']['id']))
            self.connection.commit()
        
        return redirect(url_for('products.product_list'))
