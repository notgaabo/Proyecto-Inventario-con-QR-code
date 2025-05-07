document.addEventListener('DOMContentLoaded', function() {
    // Función para calcular el tiempo transcurrido
    function timeSince(dateStr) {
        const date = new Date(dateStr);
        const now = new Date();
        const seconds = Math.floor((now - date) / 1000);
        
        let interval = seconds / 31536000; // Años
        if (interval > 1) return Math.floor(interval) + "y";
        
        interval = seconds / 2592000; // Meses
        if (interval > 1) return Math.floor(interval) + "m";
        
        interval = seconds / 86400; // Días
        if (interval > 1) return Math.floor(interval) + "d";
        
        interval = seconds / 3600; // Horas
        if (interval > 1) return Math.floor(interval) + "h";
        
        interval = seconds / 60; // Minutos
        if (interval > 1) return Math.floor(interval) + "min";
        
        return Math.floor(seconds) + "s";
    }

    // Función para renderizar las notificaciones
    function renderNotifications(notifications) {
        const notificationsList = document.getElementById('notifications-list');
        if (!notificationsList) {
            console.error('Elemento notifications-list no encontrado en el DOM');
            return;
        }
        notificationsList.innerHTML = '';
        console.log('Renderizando notificaciones:', notifications); // Depuración

        notifications.forEach(notification => {
            // Determinar el icono y color según el tipo de notificación
            let iconClass, bgColor, iconColor;
            switch (notification.type) {
                case 'stock_low':
                    iconClass = 'fas fa-exclamation-triangle';
                    bgColor = 'bg-red-100';
                    iconColor = 'text-red-500';
                    break;
                case 'new_order':
                    iconClass = 'fas fa-file-invoice';
                    bgColor = 'bg-green-100';
                    iconColor = 'text-green-500';
                    break;
                case 'return':
                    iconClass = 'fas fa-undo';
                    bgColor = 'bg-yellow-100';
                    iconColor = 'text-yellow-500';
                    break;
                default:
                    iconClass = 'fas fa-bell';
                    bgColor = 'bg-gray-100';
                    iconColor = 'text-gray-500';
            }

            const li = document.createElement('li');
            li.className = 'notification-item';
            li.dataset.id = notification.id;
            li.dataset.read = notification.read ? 'true' : 'false';
            li.innerHTML = `
                <div class="flex p-3 border-b border-gray-100 hover:bg-gray-50 transition-colors duration-150">
                    <div class="flex-shrink-0 mr-3">
                        <div class="w-8 h-8 rounded-full ${bgColor} flex items-center justify-center">
                            <i class="${iconClass} ${iconColor} text-sm"></i>
                        </div>
                    </div>
                    <div class="flex-1">
                        <div class="flex items-center justify-between">
                            <p class="text-sm font-medium text-gray-900">${notification.title}</p>
                            <span class="text-xs text-gray-500">${timeSince(notification.created_at)}</span>
                        </div>
                        <p class="text-xs text-gray-600 mt-1">${notification.message}</p>
                        <div class="mt-2">
                            <button class="mark-read-btn text-xs text-blue-600 hover:text-blue-800">
                                Marcar como leída
                            </button>
                        </div>
                    </div>
                    <div class="ml-2 flex items-center">
                        <span class="unread-dot w-2 h-2 bg-orange-500 rounded-full ${notification.read ? 'hidden' : ''}"></span>
                    </div>
                </div>
            `;
            notificationsList.appendChild(li);
        });

        // Actualizar el estado después de renderizar
        updateUnreadIndicator();
        checkEmptyState();
    }

    // Función para obtener notificaciones del servidor
    function fetchNotifications() {
        console.log('Solicitando notificaciones desde /notifications'); // Depuración
        fetch('/notifications')
            .then(response => {
                console.log('Respuesta recibida:', response.status, response.statusText); // Depuración
                return response.json();
            })
            .then(data => {
                console.log('Datos recibidos:', data); // Depuración
                if (data.success) {
                    renderNotifications(data.notifications);
                } else {
                    console.error('Error al cargar notificaciones:', data.message);
                }
            })
            .catch(error => console.error('Error al obtener notificaciones:', error));
    }

    // Funcionalidad para marcar notificaciones individuales como leídas
    document.addEventListener('click', function(e) {
        if (e.target.classList.contains('mark-read-btn')) {
            e.preventDefault();
            e.stopPropagation();
            
            const notificationItem = e.target.closest('.notification-item');
            const notificationId = notificationItem.dataset.id;
            console.log('Marcando notificación como leída:', notificationId); // Depuración
            
            fetch(`/notifications/${notificationId}/read`, { method: 'POST' })
                .then(response => {
                    console.log('Respuesta de marcar como leída:', response.status, response.statusText); // Depuración
                    return response.json();
                })
                .then(data => {
                    console.log('Datos de marcar como leída:', data); // Depuración
                    if (data.success) {
                        fetchNotifications();
                    } else {
                        console.error('Error al marcar como leída:', data.message);
                    }
                })
                .catch(error => console.error('Error al marcar notificación:', error));
        }
    });

    // Funcionalidad para marcar todas como leídas
    document.getElementById('mark-all-read').addEventListener('click', function(e) {
        e.preventDefault();
        console.log('Marcando todas las notificaciones como leídas'); // Depuración
        
        const unreadNotifications = document.querySelectorAll('.notification-item[data-read="false"]');
        if (unreadNotifications.length === 0) {
            console.log('No hay notificaciones no leídas'); // Depuración
            return;
        }

        const promises = Array.from(unreadNotifications).map(item => {
            const notificationId = item.dataset.id;
            return fetch(`/notifications/${notificationId}/read`, { method: 'POST' })
                .then(response => response.json());
        });

        Promise.all(promises)
            .then(results => {
                console.log('Resultados de marcar todas como leídas:', results); // Depuración
                const allSuccessful = results.every(result => result.success);
                if (allSuccessful) {
                    fetchNotifications();
                } else {
                    console.error('Error al marcar todas las notificaciones como leídas');
                }
            })
            .catch(error => console.error('Error al marcar todas las notificaciones:', error));
    });

    // Función para actualizar el indicador global de no leídas
    function updateUnreadIndicator() {
        const unreadNotifications = document.querySelectorAll('.notification-item[data-read="false"]');
        const unreadIndicator = document.getElementById('unread-indicator');
        if (!unreadIndicator) {
            console.error('Elemento unread-indicator no encontrado en el DOM');
            return;
        }
        
        console.log('Notificaciones no leídas:', unreadNotifications.length); // Depuración
        if (unreadNotifications.length > 0) {
            unreadIndicator.classList.remove('hidden');
        } else {
            unreadIndicator.classList.add('hidden');
        }
    }

    // Verificar estado vacío
    function checkEmptyState() {
        const notificationsList = document.getElementById('notifications-list');
        const emptyState = document.getElementById('empty-state');
        if (!notificationsList || !emptyState) {
            console.error('Elementos notifications-list o empty-state no encontrados en el DOM');
            return;
        }
        
        if (notificationsList.children.length === 0) {
            emptyState.classList.remove('hidden');
        } else {
            emptyState.classList.add('hidden');
        }
    }

    // Cargar notificaciones al iniciar
    fetchNotifications();
});