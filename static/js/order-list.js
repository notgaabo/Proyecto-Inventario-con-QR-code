
document.addEventListener('DOMContentLoaded', function() {
    const checkboxes = document.querySelectorAll('input[name="orderCheckbox"]');
    const selectAll = document.getElementById('selectAll');
    const receiveButton = document.getElementById('receiveButton');
    const orderIdsInput = document.getElementById('orderIdsInput');
    const todayOrdersDiv = document.getElementById('todayOrders');

    // Cargar órdenes de hoy
    function loadTodayOrders() {
        // Ensure the URL is properly escaped to avoid JavaScript errors
        const todayOrdersUrl = "{{ url_for('today_orders') | safe }}";
        
        fetch(todayOrdersUrl, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json'
            }
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            if (data.success && data.orders && data.orders.length > 0) {
                todayOrdersDiv.innerHTML = '';
                data.orders.forEach(order => {
                    const orderHtml = `
                        <div class="order-item bg-gray-50 p-4 rounded-md flex justify-between items-center" data-order-id="${order.id}">
                            <div>
                                <p class="text-sm font-medium text-gray-900">Orden #${order.id}</p>
                                <p class="text-xs text-gray-500">Proveedor: ${order.supplier_name || 'Sin proveedor'}</p>
                                <p class="text-xs text-gray-500">Fecha: ${order.order_date}</p>
                                <p class="text-xs text-gray-500">Creado por: ${order.created_by || 'Sin creador'}</p>
                            </div>
                            <form method="GET" action="{{ url_for('print_qr') | safe }}" class="print-qr-form">
                                <input type="hidden" name="order_id" value="${order.id}">
                                <button type="submit" class="bg-blue-500 hover:bg-blue-600 text-white py-1 px-3 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-opacity-50 transition-colors">
                                    Imprimir QR
                                </button>
                            </form>
                        </div>
                    `;
                    todayOrdersDiv.insertAdjacentHTML('beforeend', orderHtml);
                });

                // Añadir eventos a los formularios de impresión
                document.querySelectorAll('.print-qr-form').forEach(form => {
                    form.addEventListener('submit', function(e) {
                        e.preventDefault();
                        const orderId = form.querySelector('input[name="order_id"]').value;
                        const printQrUrl = "{{ url_for('print_qr') | safe }}?order_id=" + encodeURIComponent(orderId);
                        
                        fetch(printQrUrl, {
                            method: 'GET'
                        })
                        .then(response => {
                            if (response.ok) {
                                return response.blob();
                            }
                            throw new Error('Error al generar el PDF');
                        })
                        .then(blob => {
                            // Descargar el PDF
                            const url = window.URL.createObjectURL(blob);
                            const a = document.createElement('a');
                            a.href = url;
                            a.download = 'qr_codes.pdf';
                            document.body.appendChild(a);
                            a.click();
                            a.remove();
                            window.URL.revokeObjectURL(url);

                            // Eliminar la orden del apartado
                            const orderItem = form.closest('.order-item');
                            orderItem.remove();
                            // Si no quedan órdenes, mostrar mensaje
                            if (!todayOrdersDiv.querySelector('.order-item')) {
                                todayOrdersDiv.innerHTML = '<p class="text-gray-500">No hay órdenes para hoy</p>';
                            }
                        })
                        .catch(error => {
                            console.error('Error:', error);
                            alert('Error al generar el PDF de códigos QR');
                        });
                    });
                });
            } else {
                todayOrdersDiv.innerHTML = '<p class="text-gray-500">No hay órdenes para hoy</p>';
            }
        })
        .catch(error => {
            console.error('Error al cargar órdenes de hoy:', error);
            todayOrdersDiv.innerHTML = '<p class="text-gray-500">Error al cargar órdenes</p>';
        });
    }

    // Cargar órdenes al iniciar
    loadTodayOrders();

    // Manejo de selección de órdenes para marcar como entregadas
    function updateButtonState() {
        const checked = Array.from(checkboxes).some(cb => cb.checked);
        receiveButton.disabled = !checked;
    }

    checkboxes.forEach(checkbox => {
        checkbox.addEventListener('change', function() {
            updateButtonState();
            updateOrderIdsInput();
        });
    });

    if (selectAll) {
        selectAll.addEventListener('change', function() {
            checkboxes.forEach(cb => cb.checked = selectAll.checked);
            updateButtonState();
            updateOrderIdsInput();
        });
    }

    function updateOrderIdsInput() {
        const selectedOrderIds = Array.from(checkboxes)
            .filter(cb => cb.checked)
            .map(cb => cb.value);
        orderIdsInput.value = JSON.stringify(selectedOrderIds);
    }

    document.getElementById('receiveOrdersForm').addEventListener('submit', function(e) {
        if (!orderIdsInput.value) {
            e.preventDefault();
            alert('Por favor, seleccione al menos una orden para marcar como entregada.');
        }
    });
});