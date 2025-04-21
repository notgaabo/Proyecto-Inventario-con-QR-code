from flask import session, jsonify

class notificationsController:
    @staticmethod
    def get_notifications():
        if 'user' not in session:
            return jsonify({"success": False, "message": "No autenticado"}), 401

        user_role = session['user']['role']
        roles_to_notify_stock = ['gerente', 'admin', 'encargado de almacén']
        roles_to_notify_order = ['gerente', 'admin']
        roles_to_notify_return = ['gerente', 'admin', 'vendedor']

        notifications = session.get('notifications', [])
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

        return jsonify({"success": True, "notifications": filtered_notifications})

    @staticmethod
    def mark_notification_as_read(notification_id):
        if 'user' not in session:
            return jsonify({"success": False, "message": "No autenticado"}), 401

        notifications = session.get('notifications', [])
        for notification in notifications:
            if notification['id'] == int(notification_id):
                notification['read'] = True
                session.modified = True
                return jsonify({"success": True, "message": "Notificación marcada como leída"})

        return jsonify({"success": False, "message": "Notificación no encontrada"}), 404