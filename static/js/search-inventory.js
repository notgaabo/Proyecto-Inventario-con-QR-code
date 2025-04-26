
    document.addEventListener('DOMContentLoaded', () => {
        console.log('DOM completamente cargado');
        const searchInput = document.getElementById('product-search');
        const qrResultDiv = document.getElementById('qr-result');

        // Función para agregar producto por ID
        async function addProductById(productId) {
            try {
                // Verificar si el producto ya está en el carrito
                const cartItems = document.querySelectorAll('#cart_items div[data-product-id]');
                let productExists = false;

                cartItems.forEach(item => {
                    if (item.dataset.productId === productId) {
                        productExists = true;
                        const quantityInput = item.querySelector('input');
                        const currentQuantity = parseInt(quantityInput.value) || 0;
                        quantityInput.value = currentQuantity + 1; // Incrementar cantidad
                        updateQuantity(productId, currentQuantity + 1); // Actualizar en backend
                    }
                });

                // Si no existe, hacer la solicitud para añadirlo
                if (!productExists) {
                    const response = await fetch('/escanear', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ codigo: productId })
                    });
                    const result = await response.json();

                    if (result.success) {
                        qrResultDiv.innerHTML = `<p class="text-green-600">Añadido: ${result.producto} (x${result.cantidad})</p>`;
                        // Actualizar el carrito inmediatamente
                        await updateCartFromQR();
                    } else {
                        qrResultDiv.innerHTML = `<p class="text-red-600">${result.message}</p>`;
                    }
                } else {
                    qrResultDiv.innerHTML = `<p class="text-green-600">Cantidad incrementada para ID: ${productId}</p>`;
                }
            } catch (error) {
                qrResultDiv.innerHTML = `<p class="text-red-600">Error al procesar el ID: ${error.message}</p>`;
            }
        }

        // Función para actualizar el carrito (reutilizando la de qr.js)
        async function updateCartFromQR() {
            try {
                const response = await fetch('/carrito', {
                    method: 'GET',
                    headers: { 'Content-Type': 'application/json' }
                });
                const result = await response.json();

                if (result.success) {
                    const cart = result.carrito || {};
                    let html = '';
                    let total = 0;

                    Object.entries(cart).forEach(([id, item]) => {
                        const costo = item.price ?? 0;
                        const cantidad = item.cantidad ?? 0;
                        const subtotal = costo * cantidad;
                        total += subtotal;

                        html += `
                            <div data-product-id="${id}" class="border p-4 rounded-lg bg-gray-50 flex justify-between items-center">
                                <div>
                                    <span class="font-semibold text-gray-800">${item.nombre || 'Sin nombre'}</span>
                                    <span class="text-gray-600">$${costo.toFixed(2)}</span>
                                    <input type="number" 
                                           class="w-16 border rounded p-1 text-center" 
                                           value="${cantidad}" 
                                           min="0" 
                                           onchange="updateQuantity('${id}', this.value)">
                                </div>
                                <div class="flex items-center">
                                    <span class="text-gray-700 font-medium">$${subtotal.toFixed(2)}</span>
                                    <button onclick="updateQuantity('${id}', 0)" 
                                            class="ml-3 text-red-500 hover:text-red-700 transition duration-200">
                                        <i class="fas fa-trash"></i>
                                    </button>
                                </div>
                            </div>
                        `;
                    });

                    document.getElementById('cart_items').innerHTML = html || '<p class="text-gray-500">Registro vacío</p>';
                    document.getElementById('cart_total').textContent = `Total Registrado: $${total.toFixed(2)}`;
                    document.dispatchEvent(new Event('cartUpdated')); // Disparar evento para sales.js
                } else {
                    document.getElementById('cart_items').innerHTML = `<p class="text-red-600">Error al cargar el registro: ${result.message}</p>`;
                }
            } catch (error) {
                document.getElementById('cart_items').innerHTML = `<p class="text-red-600">Error al cargar el registro: ${error.message}</p>`;
            }
        }

        // Evento al presionar Enter
        searchInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                const productId = searchInput.value.trim();
                if (productId) {
                    addProductById(productId);
                    searchInput.value = ''; // Limpiar input
                }
            }
        });

        // Evento al salir del input (onblur)
        searchInput.addEventListener('blur', () => {
            const productId = searchInput.value.trim();
            if (productId) {
                addProductById(productId);
                searchInput.value = ''; // Limpiar input
            }
        });
    });