
document.addEventListener('DOMContentLoaded', () => {
    // --- Script para el modal de órdenes ---
    const printQRsButton = document.getElementById('printQRsButton');
    const qrModal = document.getElementById('qrModal');
    const closeModal = document.getElementById('closeModal');
    const ordersList = document.getElementById('ordersList');
    let activeQuantityInput = null; // Rastrea el componente de entrada activo

    // Abrir el modal al hacer clic en el botón
    printQRsButton.addEventListener('click', async () => {
        try {
            const response = await fetch('/last_delivered_products');
            const data = await response.json();
            if (data.success && data.orders.length > 0) {
                ordersList.innerHTML = '';
                data.orders.forEach(order => {
                    const orderDiv = document.createElement('div');
                    orderDiv.className = 'border p-4 rounded mb-4';
                    orderDiv.innerHTML = `
                        <h3 class="font-bold">Orden #${order.order_id} (${order.order_date})</h3>
                        <p>Proveedor: ${order.supplier_name}</p>
                        <ul class="list-disc ml-5">
                            ${order.products.map(product => `
                                <li class="flex items-center justify-between py-1" id="product-${product.id}">
                                    <span>${product.name} (x${product.quantity})</span>
                                    <span class="print-qr-toggle text-blue-500 hover:text-blue-700 cursor-pointer font-medium"
                                          data-product-id="${product.id}">
                                        Imprimir
                                    </span>
                                </li>
                            `).join('')}
                        </ul>
                        <button class="print-qr-order bg-blue-500 text-white px-3 py-1 rounded hover:bg-blue-600 mt-2"
                                data-order-id="${order.order_id}">
                            Imprimir QR's de la Orden
                        </button>
                    `;
                    ordersList.appendChild(orderDiv);
                });
                qrModal.style.display = 'block';
            } else {
                ordersList.innerHTML = '<p>No hay órdenes entregadas no impresas.</p>';
                qrModal.style.display = 'block';
            }
        } catch (error) {
            console.error('Error al cargar órdenes:', error);
            ordersList.innerHTML = '<p>Error al cargar las órdenes.</p>';
            qrModal.style.display = 'block';
        }
    });

    // Cerrar el modal
    closeModal.addEventListener('click', () => {
        qrModal.style.display = 'none';
        if (activeQuantityInput) {
            activeQuantityInput.style.display = 'inline';
            activeQuantityInput.parentElement.querySelector('.quantity-input-container')?.remove();
            activeQuantityInput = null;
        }
    });

    // Cerrar el modal al hacer clic fuera
    qrModal.addEventListener('click', (e) => {
        if (e.target === qrModal) {
            qrModal.style.display = 'none';
            if (activeQuantityInput) {
                activeQuantityInput.style.display = 'inline';
                activeQuantityInput.parentElement.querySelector('.quantity-input-container')?.remove();
                activeQuantityInput = null;
            }
        }
    });

    // Manejar clic en los textos "Imprimir" para mostrar el componente de entrada
    ordersList.addEventListener('click', (e) => {
        if (e.target.classList.contains('print-qr-toggle')) {
            const productId = e.target.getAttribute('data-product-id');
            const productLi = document.getElementById(`product-${productId}`);
            const toggleSpan = e.target;

            // Cerrar el componente activo si existe
            if (activeQuantityInput && activeQuantityInput !== toggleSpan) {
                activeQuantityInput.style.display = 'inline';
                activeQuantityInput.parentElement.querySelector('.quantity-input-container')?.remove();
                activeQuantityInput = null;
            }

            // Si el componente ya está abierto, no hacer nada
            if (toggleSpan.style.display === 'none') {
                return;
            }

            // Crear el componente de entrada
            const inputContainer = document.createElement('div');
            inputContainer.className = 'quantity-input-container flex items-center space-x-2 max-w-[10rem]';
            inputContainer.innerHTML = `
                <button type="button" class="decrement bg-gray-100 hover:bg-gray-200 border border-gray-300 rounded-l-lg p-2 h-9 focus:ring-gray-100 focus:ring-2 focus:outline-none">
                    <svg class="w-3 h-3 text-gray-900" aria-hidden="true" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 18 2">
                        <path stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M1 1h16"/>
                    </svg>
                </button>
                <input type="text" class="quantity-input bg-gray-50 border-x-0 border-gray-300 h-9 text-center text-gray-900 text-sm focus:ring-blue-500 focus:border-blue-500 w-12 py-2" value="1" required />
                <button type="button" class="increment bg-gray-100 hover:bg-gray-200 border border-gray-300 rounded-r-lg p-2 h-9 focus:ring-gray-100 focus:ring-2 focus:outline-none">
                    <svg class="w-3 h-3 text-gray-900" aria-hidden="true" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 18 18">
                        <path stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 1v16M1 9h16"/>
                    </svg>
                </button>
                <button type="button" class="print-qr-product bg-green-500 text-white px-3 py-1 rounded hover:bg-green-600">
                    Imprimir
                </button>
            `;
            toggleSpan.style.display = 'none';
            productLi.appendChild(inputContainer);
            activeQuantityInput = toggleSpan;

            const quantityInput = inputContainer.querySelector('.quantity-input');
            const decrementButton = inputContainer.querySelector('.decrement');
            const incrementButton = inputContainer.querySelector('.increment');

            // Validar entrada del teclado
            quantityInput.addEventListener('input', () => {
                quantityInput.value = quantityInput.value.replace(/[^0-9]/g, '');
                if (quantityInput.value === '' || parseInt(quantityInput.value) < 1) {
                    quantityInput.value = '1';
                }
            });

            // Decrementar
            decrementButton.addEventListener('click', () => {
                let value = parseInt(quantityInput.value);
                if (value > 1) {
                    quantityInput.value = value - 1;
                }
            });

            // Incrementar
            incrementButton.addEventListener('click', () => {
                let value = parseInt(quantityInput.value);
                quantityInput.value = value + 1;
            });
        }
    });

    // Manejar clic en los botones "Imprimir" de productos en el modal
    ordersList.addEventListener('click', async (e) => {
        if (e.target.classList.contains('print-qr-product')) {
            const inputContainer = e.target.closest('.quantity-input-container');
            const quantityInput = inputContainer.querySelector('.quantity-input');
            const productId = inputContainer.closest('li').id.replace('product-', '');
            const quantity = parseInt(quantityInput.value);

            if (isNaN(quantity) || quantity < 1) {
                showFlashMessage('Por favor, ingrese una cantidad válida mayor que 0', 'danger');
                return;
            }

            try {
                const response = await fetch(`/print_qr_for_product? precautionary_id=${productId}&quantity=${quantity}`);
                if (response.ok) {
                    const blob = await response.blob();
                    const url = window.URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.href = url;
                    a.download = `qr_codes_product_${productId}.pdf`;
                    document.body.appendChild(a);
                    a.click();
                    a.remove();
                    window.URL.revokeObjectURL(url);
                    // Cerrar el componente de entrada
                    const toggleSpan = inputContainer.previousElementSibling;
                    toggleSpan.style.display = 'inline';
                    inputContainer.remove();
                    activeQuantityInput = null;
                } else {
                    const data = await response.json();
                    showFlashMessage(`Error: ${data.message}`, 'danger');
                }
            } catch (error) {
                console.error('Error al descargar PDF:', error);
                showFlashMessage('Error al descargar el PDF', 'danger');
            }
        }
    });

    // Manejar clic en los botones "Imprimir QR's de la Orden"
    ordersList.addEventListener('click', async (e) => {
        if (e.target.classList.contains('print-qr-order')) {
            const orderId = e.target.getAttribute('data-order-id');
            try {
                const response = await fetch(`/print_qr_for_order?order_id=${orderId}`);
                if (response.ok) {
                    const blob = await response.blob();
                    const url = window.URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.href = url;
                    a.download = `qr_codes_order_${orderId}.pdf`;
                    document.body.appendChild(a);
                    a.click();
                    a.remove();
                    window.URL.revokeObjectURL(url);
                    // Eliminar la orden del modal
                    e.target.closest('.border.p-4.rounded.mb-4').remove();
                    if (!ordersList.children.length) {
                        ordersList.innerHTML = '<p>No hay órdenes entregadas no impresas.</p>';
                    }
                    // Cerrar cualquier componente de entrada activo
                    if (activeQuantityInput) {
                        activeQuantityInput.style.display = 'inline';
                        activeQuantityInput.parentElement.querySelector('.quantity-input-container')?.remove();
                        activeQuantityInput = null;
                    }
                } else {
                    const data = await response.json();
                    showFlashMessage(`Error: ${data.message}`, 'danger');
                }
            } catch (error) {
                console.error('Error al descargar PDF:', error);
                showFlashMessage('Error al descargar el PDF', 'danger');
            }
        }
    });

    // --- Script para el componente de impresión en tarjetas de producto ---
    // Manejar clics en las tarjetas de producto
    document.getElementById('productGrid').addEventListener('click', (e) => {
        if (e.target.classList.contains('decrement')) {
            const inputContainer = e.target.closest('.quantity-input-container');
            const quantityInput = inputContainer.querySelector('.quantity-input');
            let value = parseInt(quantityInput.value);
            if (value > 1) {
                quantityInput.value = value - 1;
            }
        }
        if (e.target.classList.contains('increment')) {
            const inputContainer = e.target.closest('.quantity-input-container');
            const quantityInput = inputContainer.querySelector('.quantity-input');
            let value = parseInt(quantityInput.value);
            quantityInput.value = value + 1;
        }
        if (e.target.classList.contains('print-qr-product')) {
            const inputContainer = e.target.closest('.quantity-input-container');
            const quantityInput = inputContainer.querySelector('.quantity-input');
            const productId = inputContainer.getAttribute('data-product-id');
            const quantity = parseInt(quantityInput.value);

            if (isNaN(quantity) || quantity < 1) {
                showFlashMessage('Por favor, ingrese una cantidad válida mayor que 0', 'danger');
                return;
            }

            fetch(`/print_qr_for_product?product_id=${productId}&quantity=${quantity}`)
                .then(response => {
                    if (response.ok) {
                        return response.blob();
                    }
                    return response.json().then(data => Promise.reject(data));
                })
                .then(blob => {
                    const url = window.URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.href = url;
                    a.download = `qr_codes_product_${productId}.pdf`;
                    document.body.appendChild(a);
                    a.click();
                    a.remove();
                    window.URL.revokeObjectURL(url);
                    showFlashMessage('Códigos QR generados exitosamente', 'success');
                })
                .catch(error => {
                    console.error('Error al descargar PDF:', error);
                    showFlashMessage(`Error: ${error.message || 'Error al descargar el PDF'}`, 'danger');
                });
        }
    });

    // Validar entradas de teclado en las tarjetas de producto
    document.getElementById('productGrid').addEventListener('input', (e) => {
        if (e.target.classList.contains('quantity-input')) {
            e.target.value = e.target.value.replace(/[^0-9]/g, '');
            if (e.target.value === '' || parseInt(e.target.value) < 1) {
                e.target.value = '1';
            }
        }
    });
});


document.addEventListener('DOMContentLoaded', function() {
        const filterButton = document.getElementById('filterButton');
        const filterArea = document.getElementById('filterArea');
        const searchInput = document.getElementById('searchInput');
        const categoryFilter = document.getElementById('categoryFilter');
        const minPriceInput = document.getElementById('minPrice');
        const maxPriceInput = document.getElementById('maxPrice');
        const availabilityFilter = document.getElementById('availabilityFilter');
        const clearFiltersButton = document.getElementById('clearFilters');
        const sortProducts = document.getElementById('sortProducts');
        const productGrid = document.getElementById('productGrid');
        const productCount = document.getElementById('productCount');
        const errorAlertContainer = document.getElementById('errorAlertContainer');
        const closeErrorAlertBtn = document.getElementById('closeErrorAlertBtn');
        const errorMessage = document.getElementById('errorMessage');

        // Mostrar la alerta si hay un mensaje de error (no vacío)
        if (errorMessage.textContent.trim() !== '') {
            errorAlertContainer.style.display = 'block';
            setTimeout(() => {
                errorAlertContainer.style.opacity = '0';
                setTimeout(() => {
                    errorAlertContainer.style.display = 'none';
                    errorAlertContainer.style.opacity = '1'; // Reset opacity for next use
                }, 300);
            }, 5000);
        }

        // Cerrar la alerta al hacer clic en el botón
        if (closeErrorAlertBtn) {
            closeErrorAlertBtn.addEventListener('click', function() {
                errorAlertContainer.style.opacity = '0';
                setTimeout(() => {
                    errorAlertContainer.style.display = 'none';
                    errorAlertContainer.style.opacity = '1';
                }, 300);
            });
        }

        // Mostrar/Ocultar filtros
        filterButton.addEventListener('click', function() {
            filterArea.classList.toggle('show');
        });
    
        // Cerrar filtros al hacer clic fuera
        document.addEventListener('click', function(event) {
            if (!filterArea.contains(event.target) && event.target !== filterButton && !filterButton.contains(event.target)) {
                filterArea.classList.remove('show');
            }
        });
    
        // Función para actualizar productos con AJAX
        function updateProducts() {
            const search = searchInput.value.toLowerCase();
            const category = categoryFilter.value;
            const minPrice = minPriceInput.value || '';
            const maxPrice = maxPriceInput.value || '';
            const availability = availabilityFilter.value;
            const sort = sortProducts.value;
    
            fetch('/api/products', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    search,
                    category,
                    minPrice,
                    maxPrice,
                    availability,
                    sort
                })
            })
            .then(response => response.json())
            .then(data => {
                if (!data.success) {
                    console.error('Error:', data.message);
                    productGrid.innerHTML = '<p class="text-center text-gray-500">Error al cargar productos.</p>';
                    productCount.textContent = '0';
                    return;
                }
    
                const products = data.productos;
                productGrid.innerHTML = '';
                productCount.textContent = products.length;
    
                if (products.length === 0) {
                    productGrid.innerHTML = '<p class="text-center text-gray-500">No hay productos disponibles.</p>';
                    return;
                }
    
                products.forEach(product => {
                    const stockClass = product.stock === 0 ? 'bg-red-600' : product.stock <= 15 ? 'bg-orange-500' : 'bg-green-500';
                    const stockText = product.stock === 0 ? 'Agotado' : product.stock <= 15 ? 'Stock Bajo' : 'En Stock';
                    const productHtml = `
                        <div class="group bg-white rounded-xl shadow-md hover:shadow-xl transition-all duration-300 overflow-hidden border border-gray-100">
                            <div class="h-48 bg-gray-100 relative overflow-hidden">
                                <img src="/static/uploads/${product.image || 'default.png'}" alt="${product.name}" class="w-full h-full object-cover transition-all duration-500">
                                <div class="absolute top-2 right-2 px-2 py-1 ${stockClass} text-white text-xs font-medium rounded-full">
                                    ${stockText}
                                </div>
                                <div class="absolute top-0 left-0 p-2">
                                    <span class="bg-black text-white text-xs px-3 py-1 rounded-full">${product.category}</span>
                                </div>
                                <div class="absolute -bottom-20 left-0 right-0 bg-orange-500 p-3 group-hover:bottom-0 transition-all duration-300">
                                    <div class="flex justify-between items-center">
                                        <span class="text-white font-bold">$${product.price}</span>
                                        <span class="text-white text-sm">Stock: ${product.stock}</span>
                                    </div>
                                </div>
                            </div>
                            <div class="p-5">
                                <h3 class="text-xl font-bold text-gray-900 mb-2 truncate">${product.name}</h3>
                                <!-- Componente para imprimir QR -->
                                <div class="quantity-input-container flex items-center space-x-2 max-w-[10rem] mb-4" data-product-id="${product.id}">
                                    <button type="button" class="decrement bg-gray-100 hover:bg-gray-200 border border-gray-300 rounded-l-lg p-2 h-9 focus:ring-gray-100 focus:ring-2 focus:outline-none">
                                        <svg class="w-3 h-3 text-gray-900" aria-hidden="true" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 18 2">
                                            <path stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M1 1h16"/>
                                        </svg>
                                    </button>
                                    <input type="text" class="quantity-input bg-gray-50 border-x-0 border-gray-300 h-9 text-center text-gray-900 text-sm focus:ring-blue-500 focus:border-blue-500 w-12 py-2" value="1" required />
                                    <button type="button" class="increment bg-gray-100 hover:bg-gray-200 border border-gray-300 rounded-r-lg p-2 h-9 focus:ring-gray-100 focus:ring-2 focus:outline-none">
                                        <svg class="w-3 h-3 text-gray-900" aria-hidden="true" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 18 18">
                                            <path stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 1v16M1 9h16"/>
                                        </svg>
                                    </button>
                                    <button type="button" class="print-qr-product bg-green-500 text-white px-3 py-1 rounded hover:bg-green-600">
                                        Imprimir
                                    </button>
                                </div>
                                <div class="flex justify-between items-center pt-4 border-t border-gray-100">
                                    <button type="button" data-modal-target="product-${product.id}" data-modal-toggle="product-${product.id}" class="text-gray-700 hover:text-orange-500 font-medium text-sm flex items-center transition-colors">
                                        <i class="fas fa-eye mr-2"></i> Ver más
                                    </button>
                                    <button type="button" data-modal-target="delete-modal-${product.id}" data-modal-toggle="delete-modal-${product.id}" class="text-gray-700 hover:text-red-500 font-medium text-sm flex items-center transition-colors">
                                        <i class="fas fa-trash-alt mr-2"></i> Eliminar
                                    </button>
                                </div>
                            </div>
                            <!-- Modales generados dinámicamente -->
                            <div id="product-${product.id}" tabindex="-1" aria-hidden="true" class="hidden fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50 backdrop-blur-sm overflow-y-auto overflow-x-hidden">
                                <div class="relative bg-white rounded-xl shadow-2xl w-full max-w-md m-4 overflow-hidden">
                                    <div class="h-40 bg-gradient-to-r from-gray-900 to-black relative">
                                        <img src="/static/uploads/${product.image || 'default.png'}" alt="${product.name}" class="w-full h-full object-cover transition-all duration-500">
                                        <div class="absolute top-4 right-4 flex space-x-2">
                                            <button type="button" class="bg-black rounded-full p-1.5 text-white hover:bg-red-600 transition-colors" data-modal-target="delete-modal-${product.id}" data-modal-toggle="delete-modal-${product.id}">
                                                <svg class="w-4 h-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                                                </svg>
                                            </button>
                                            <button type="button" class="text-white hover:text-gray-300 transition-colors" data-modal-hide="product-${product.id}">
                                                <svg class="w-6 h-6" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
                                                </svg>
                                            </button>
                                        </div>
                                        <div class="absolute -bottom-16 left-6">
                                            <div class="w-32 h-32 bg-white p-1 rounded-lg shadow-lg">
                                                <img src="/generate_qr/${product.id}" alt="Código QR" class="w-full h-full">
                                            </div>
                                        </div>
                                        <div class="absolute bottom-4 left-44 right-4">
                                            <h3 class="text-xl font-bold text-white truncate">${product.name}</h3>
                                            <span class="inline-block bg-orange-500 text-white text-xs px-3 py-1 rounded-full mt-1">${product.category}</span>
                                        </div>
                                    </div>
                                    <div class="p-6 pt-20">
                                        <div class="grid grid-cols-2 gap-4 text-sm">
                                            <div class="bg-gray-50 p-3 rounded-md">
                                                <p class="text-gray-500 mb-1">Stock</p>
                                                <p class="font-medium text-black text-lg">${product.stock} unidades</p>
                                            </div>
                                            <div class="bg-gray-50 p-3 rounded-md">
                                                <p class="text-gray-500 mb-1">Precio</p>
                                                <p class="font-medium text-black text-lg">$${product.price}</p>
                                            </div>
                                            <div class="bg-gray-50 p-3 rounded-md col-span-2">
                                                <p class="text-gray-500 mb-1">Precio de Costo</p>
                                                <div class="flex justify-between items-center">
                                                    <p class="font-medium text-black text-lg">$${product.cost_price}</p>
                                                    <div class="bg-gray-200 text-gray-800 text-xs px-2 py-1 rounded">
                                                        Margen: ${((product.price - product.cost_price) / product.price * 100).toFixed(2)}%
                                                    </div>
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                    <div class="bg-gray-50 px-6 py-4 flex justify-end">
                                        <button type="button" class="bg-black text-white py-2 px-6 rounded-full hover:bg-gray-800 transition-colors" data-modal-hide="product-${product.id}">
                                            Cerrar
                                        </button>
                                    </div>
                                </div>
                            </div>
                            <div id="delete-modal-${product.id}" tabindex="-1" class="hidden overflow-y-auto overflow-x-hidden fixed top-0 right-0 left-0 z-50 justify-center items-center w-full md:inset-0 h-[calc(100%-1rem)] max-h-full bg-black bg-opacity-50 backdrop-blur-sm">
                                <div class="relative p-4 w-full max-w-md max-h-full">
                                    <div class="relative bg-white rounded-xl shadow-xl">
                                        <div class="bg-gradient-to-r from-orange-500 to-orange-400 p-4 rounded-t-xl flex justify-between items-center">
                                            <h3 class="text-lg font-bold text-white">Eliminar Producto</h3>
                                            <button type="button" class="text-white hover:text-gray-200 transition-colors" data-modal-hide="delete-modal-${product.id}">
                                                <svg class="w-5 h-5" aria-hidden="true" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 14 14">
                                                    <path stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="m1 1 6 6m0 0 6 6M7 7l6-6M7 7l-6 6"/>
                                                </svg>
                                            </button>
                                        </div>
                                        <div class="p-6 text-center">
                                            <div class="w-16 h-16 mx-auto mb-4 bg-orange-100 rounded-full flex items-center justify-center">
                                                <svg class="w-8 h-8 text-orange-500" aria-hidden="true" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 20 20">
                                                    <path stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 11V6m0 8h.01M19 10a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z"/>
                                                </svg>
                                            </div>
                                            <h3 class="mb-5 text-lg font-medium text-gray-800">¿Estás seguro que quieres eliminar este producto?</h3>
                                            <form class="delete-product-form" data-product-id="${product.id}" class="flex flex-col sm:flex-row justify-center gap-3">
                                                <button type="submit" class="text-white bg-orange-500 hover:bg-orange-600 font-medium rounded-full text-sm px-5 py-2.5 transition-all duration-300 shadow-md hover:shadow-lg">
                                                    Sí, eliminar
                                                </button>
                                                <button type="button" data-modal-hide="delete-modal-${product.id}" class="py-2.5 px-5 text-sm font-medium text-gray-800 bg-white rounded-full border border-gray-300 hover:bg-gray-100 transition-all duration-300 shadow-md">
                                                    Cancelar
                                                </button>
                                            </form>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    `;
                    productGrid.insertAdjacentHTML('beforeend', productHtml);
                });
    
                // Re-inicializar eventos de modales después de cargar dinámicamente
                if (typeof window.initModals === 'function') {
                    window.initModals();
                }
            })
            .catch(error => {
                console.error('Error:', error);
                showFlashMessage('Error al cargar productos', 'danger');
            });
        }

        // Función para eliminar producto
        function deleteProduct(productId) {
            fetch(`/delete_product/${productId}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    const productElement = document.querySelector(`[data-product-id="${productId}"]`).closest('.group');
                    if (productElement) {
                        productElement.remove();
                        const productCount = document.getElementById('productCount');
                        const currentCount = parseInt(productCount.textContent);
                        productCount.textContent = currentCount - 1;
                        showFlashMessage('Producto eliminado exitosamente', 'success');
                    }
                } else {
                    showFlashMessage(data.message || 'Error al eliminar el producto', 'danger');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                showFlashMessage('Error al eliminar el producto', 'danger');
            });
        }

        // Función para mostrar mensajes flash
        function showFlashMessage(message, category) {
            const alertDiv = document.createElement('div');
            alertDiv.className = `alert alert-${category} alert-dismissible fade show`;
            alertDiv.role = 'alert';
            alertDiv.innerHTML = `
                ${message}
                <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
            `;
            document.querySelector('.bg-white.rounded-lg.shadow-xl.p-8').insertBefore(
                alertDiv,
                document.querySelector('.bg-white.rounded-lg.shadow-xl.p-8').children[1]
            );
            
            setTimeout(() => {
                alertDiv.classList.remove('show');
                setTimeout(() => alertDiv.remove(), 150);
            }, 3000);
        }

        // Manejar eliminación de productos
        document.addEventListener('submit', function(e) {
            if (e.target.classList.contains('delete-product-form')) {
                e.preventDefault();
                const productId = e.target.getAttribute('data-product-id');
                deleteProduct(productId);
                const modal = document.getElementById(`delete-modal-${productId}`);
                if (modal) {
                    modal.classList.add('hidden');
                }
            }
        });

        // Debounce para limitar las solicitudes mientras se escribe
        function debounce(func, wait) {
            let timeout;
            return function(...args) {
                clearTimeout(timeout);
                timeout = setTimeout(() => func.apply(this, args), wait);
            };
        }

        // Event listeners con debounce para búsqueda en tiempo real
        searchInput.addEventListener('input', debounce(updateProducts, 300));
        categoryFilter.addEventListener('change', updateProducts);
        minPriceInput.addEventListener('input', debounce(updateProducts, 300));
        maxPriceInput.addEventListener('input', debounce(updateProducts, 300));
        availabilityFilter.addEventListener('change', updateProducts);
        sortProducts.addEventListener('change', updateProducts);

        // Limpiar filtros
        clearFiltersButton.addEventListener('click', function() {
            searchInput.value = '';
            categoryFilter.value = 'all';
            minPriceInput.value = '';
            maxPriceInput.value = '';
            availabilityFilter.value = 'all';
            sortProducts.value = 'relevance';
            updateProducts();
        });

        // Cargar productos iniciales
        updateProducts();
    });

    