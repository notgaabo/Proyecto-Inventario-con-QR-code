
    let accumulatedOrders = [];

    // Cargar órdenes seleccionadas al iniciar
    document.addEventListener('DOMContentLoaded', function() {
        displayOrders();
    });

    function toggleOrderSelection(orderId, isChecked) {
        fetch(`/get_order_details/${orderId}`, {
            method: 'GET',
            headers: { 'Content-Type': 'application/json' }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                if (isChecked) {
                    accumulatedOrders.push(data.order);
                } else {
                    accumulatedOrders = accumulatedOrders.filter(order => order.id != orderId);
                }
                displayOrders();
            } else {
                alert(data.message || "Error al cargar la orden.");
                document.getElementById(`order_${orderId}`).checked = false;
            }
        })
        .catch(error => {
            console.error("Error:", error);
            alert("Error al conectar con el servidor: " + error.message);
            document.getElementById(`order_${orderId}`).checked = false;
        });
    }

    function displayOrders() {
        const ordersList = document.getElementById('ordersList');
        ordersList.innerHTML = '';

        accumulatedOrders.forEach((order) => {
            const orderDiv = document.createElement('div');
            orderDiv.className = 'border p-6 rounded bg-white shadow-md';
            orderDiv.innerHTML = `
                <h4 class="font-semibold text-lg text-gray-800">Orden #${order.id}</h4>
                <ul class="list-disc pl-6 mt-2 text-gray-700">
                    ${order.items.map(item => `
                        <li>${item.product_name} - Cantidad: ${item.quantity}</li>
                    `).join('')}
                </ul>
                <button type="button" onclick="removeOrder('${order.id}')" 
                        class="text-red-500 mt-4 hover:underline">
                    Eliminar
                </button>
            `;
            ordersList.appendChild(orderDiv);
        });

        document.getElementById('receiveOrdersBtn').style.display = accumulatedOrders.length > 0 ? 'block' : 'none';
        updateHiddenInput();
    }

    function removeOrder(orderId) {
        accumulatedOrders = accumulatedOrders.filter(order => order.id != orderId);
        document.getElementById(`order_${orderId}`).checked = false;
        displayOrders();
    }

    function updateHiddenInput() {
        document.getElementById('ordersInput').value = JSON.stringify(accumulatedOrders);
    }

    document.getElementById('submitOrdersForm').addEventListener('submit', async function(e) {
        e.preventDefault();

        if (accumulatedOrders.length === 0) {
            alert("No hay órdenes para recibir.");
            return;
        }

        try {
            const response = await fetch('{{ url_for("receive_order") }}', {
                method: 'POST',
                headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
                body: new URLSearchParams({
                    'orders': JSON.stringify(accumulatedOrders)
                })
            });

            if (response.ok) {
                accumulatedOrders = [];
                displayOrders();
                location.reload(); // Recargar para mostrar el mensaje flash
            } else {
                alert("Error al procesar las órdenes.");
            }
        } catch (error) {
            alert("Error al conectar con el servidor: " + error);
        }
    });