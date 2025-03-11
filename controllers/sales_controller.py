from flask import Flask, request, jsonify
from db import Config as db  # Import your Config class
from datetime import datetime

class SalesController:
    @staticmethod
    def register_sale():
        connection = None
        cursor = None
        try:
            # Get JSON data from the request
            data = request.get_json()
            if not data or 'items' not in data:
                return jsonify({'error': 'No items provided'}), 400

            items = data['items']
            if not items:
                return jsonify({'error': 'Empty items list'}), 400

            # Establish database connection
            connection = db.get_db_connection()
            cursor = connection.cursor()

            for item in items:
                product_id = item.get('product_id')
                quantity = int(item.get('quantity', 0))
                sale_price = float(item.get('sale_price', 0))
                profit = float(item.get('profit', 0))
                sale_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

                if not product_id or quantity <= 0 or sale_price <= 0:
                    continue  # Skip invalid items

                # Insert into sales table
                insert_query = """
                    INSERT INTO sales (product_id, quantity, sale_price, sale_date, profit)
                    VALUES (%s, %s, %s, %s, %s)
                """
                values = (product_id, quantity, sale_price, sale_date, profit)
                cursor.execute(insert_query, values)

                # Update product stock
                update_query = """
                    UPDATE products 
                    SET stock = stock - %s 
                    WHERE id = %s
                """
                cursor.execute(update_query, (quantity, product_id))

            # Commit the transaction
            connection.commit()
            return jsonify({'message': 'Sale registered successfully'}), 200

        except Exception as e:
            # Rollback on error
            if connection and connection.is_connected():
                connection.rollback()
            print(f"Error al registrar la venta: {e}")
            return jsonify({'error': str(e)}), 500

        finally:
            # Clean up resources
            if cursor:
                cursor.close()
            if connection and connection.is_connected():
                connection.close()

# Register the rout
