from flask import session, jsonify
from datetime import datetime
from uuid import uuid4

class NotificationsController:
    @staticmethod
    def get_notifications():
        if 'user' not in session:
            print("Error: No hay usuario en la sesión para get_notifications")  # Depuración
            return jsonify({"success": False, "message": "No autenticado"}), 401

        user_role = session['user']['role']
        print(f"Usuario autenticado con rol: {user_role}, sesión: {session['user']}")  # Depuración
        roles_to_notify_stock = ['gerente', 'admin', 'encargado de almacén']
        roles_to_notify_order = ['gerente', 'admin']
        roles_to_notify_return = ['gerente', 'admin', 'vendedor']

        notifications = session.get('notifications', [])
        print(f"Notificaciones en sesión: {notifications}")  # Depuración
        filtered_notifications = []

        for notification in notifications:
            if notification['read']:
                continue  # Skip read notifications
            if notification['type'] == 'stock_low' and user_role in roles_to_notify_stock:
                filtered_notifications.append(notification)
            elif notification['type'] == 'new_order' and user_role in roles_to_notify_order:
                filtered_notifications.append(notification)
            elif notification['type'] == 'return' and user_role in roles_to_notify_return:
                filtered_notifications.append(notification)

        print(f"Notificaciones filtradas para {user_role}: {filtered_notifications}")  # Depuración
        return jsonify({"success": True, "notifications": filtered_notifications})

    @staticmethod
    def mark_notification_as_read(notification_id):
        if 'user' not in session:
            print("Error: No hay usuario en la sesión para marcar notificación")  # Depuración
            return jsonify({"success": False, "message": "No autenticado"}), 401

        notifications = session.get('notifications', [])
        print(f"Intentando marcar notificación {notification_id} como leída")  # Depuración
        for notification in notifications:
            if notification['id'] == notification_id:  # Comparar como string
                notification['read'] = True
                session.modified = True
                print(f"Notificación {notification_id} marcada como leída")  # Depuración
                return jsonify({"success": True, "message": "Notificación marcada como leída"})

        print(f"Notificación {notification_id} no encontrada")  # Depuración
        return jsonify({"success": False, "message": "Notificación no encontrada"}), 404

    @staticmethod
    def check_low_stock(products):
        if 'user' not in session:
            print("Usuario no autenticado, no se verifican notificaciones")  # Depuración
            return

        user_role = session['user']['role']
        print(f"Verificando bajo stock para rol: {user_role}, productos: {products}")  # Depuración
        if user_role not in ['gerente', 'admin', 'encargado de almacén']:
            print(f"Rol {user_role} no recibe notificaciones de stock_low")  # Depuración
            return

        notifications = session.get('notifications', [])
        new_notifications = False
        
        for product in products:
            if not isinstance(product.get('stock'), (int, float)):
                print(f"Stock inválido para producto {product.get('id')}: {product.get('stock')}")  # Depuración
                continue
            if product['stock'] < 25:
                existing_notification = next((n for n in notifications if n['type'] == 'stock_low' and n['product_id'] == product['id']), None)
                if not existing_notification:
                    notification = {
                        'id': str(uuid4()),
                        'type': 'stock_low',
                        'product_id': product['id'],
                        'title': f'Bajo stock: {product["name"]}',
                        'message': f'El producto {product["name"]} tiene solo {product["stock"]} unidades en inventario.',
                        'created_at': datetime.utcnow().isoformat(),
                        'read': False
                    }
                    notifications.append(notification)
                    new_notifications = True
                    print(f"Nueva notificación creada: {notification}")  # Depuración

        if new_notifications:
            session['notifications'] = notifications
            session.modified = True
            print(f"Notificaciones actualizadas en sesión: {notifications}")  # Depuración
        else:
            print("No se crearon nuevas notificaciones")  # Depuración