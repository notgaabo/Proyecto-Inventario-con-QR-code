let lastScannedCode = null;
let isProcessing = false;
let isPaused = false; // New flag for pause functionality

// Configuración del escáner QR
const html5QrCode = new Html5Qrcode("qr-reader");
const qrConfig = { 
    fps: 15,
    qrbox: { width: 200, height: 200 },
    aspectRatio: 1.0
};

// Crear el objeto de audio para el sonido "PI"
const beepSound = new Audio('https://www.soundjay.com/buttons/beep-01a.mp3');

// Iniciar escáner
html5QrCode.start(
    { facingMode: "environment" },
    qrConfig,
    async (decodedText) => {
        // Si está procesando, pausado o el código es el mismo que el último, ignorar
        if (isProcessing || isPaused || decodedText === lastScannedCode) return;

        isProcessing = true;
        lastScannedCode = decodedText;
        isPaused = true; // Pause scanning

        try {
            const response = await fetch('/escanear', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ codigo: decodedText })
            });
            const result = await response.json();

            if (result.success) {
                document.getElementById('qr-result').innerHTML = 
                    `<p class="text-green-600">Añadido: ${result.producto} (x${result.cantidad})</p>`;
                beepSound.play();
                loadProducts();
                updateCart();
            } else {
                document.getElementById('qr-result').innerHTML = 
                    `<p class="text-red-600">${result.message}</p>`;
            }
        } catch (error) {
            document.getElementById('qr-result').innerHTML = 
                `<p class="text-red-600">Error al procesar el QR: ${error.message}</p>`;
        } finally {
            // Reiniciar el estado después de procesar
            isProcessing = false;
            lastScannedCode = null; // Permitir escanear cualquier código nuevo

            // Pausar el escáner por 2 segundos antes de reanudar
            setTimeout(() => {
                isPaused = false; // Resume scanning after pause
            }, 2000); // 2-second pause
        }
    },
    (error) => {
        // Ignorar errores de escaneo en tiempo real (como cuando no hay QR visible)
    }
).catch(err => console.error("Error al iniciar el escáner:", err));

// Cargar lista de productos
async function loadProducts() {
    try {
        const response = await fetch('/productos');
        const result = await response.json();

        if (result.success && Array.isArray(result.productos)) {
            const productos = result.productos;
            let html = '';

            if (productos.length === 0) {
                html = `<p class="text-gray-600">No hay productos registrados</p>`;
            } else {
                productos.forEach(producto => {
                    html += `
                        <div class="border p-4 rounded-lg bg-gray-50 hover:bg-gray-100 transition duration-200">
                            <h3 class="font-semibold text-gray-800">${producto.nombre || 'Sin nombre'}</h3>
                            <p class="text-gray-600">Categoría: ${producto.categoria || 'N/A'}</p>
                            <p class="text-gray-600">Precio De Venta: $${producto.precio?.toFixed(2) || '0.00'}</p>
                            <p class="text-gray-600">Stock: ${producto.stock || 0}</p>
                            <p class="text-gray-600">Costo Compra: $${producto.costo?.toFixed(2) || '0.00'}</p>
                        </div>
                    `;
                });
            }

            document.getElementById('product_list').innerHTML = html;
        } else {
            document.getElementById('product_list').innerHTML = 
                `<p class="text-red-600">Error: ${result.message || 'No se pudieron cargar los productos'}</p>`;
        }
    } catch (error) {
        document.getElementById('product_list').innerHTML = 
            `<p class="text-red-600">Error al cargar productos: ${error.message}</p>`;
    }
}

// Actualizar carrito
async function updateCart() {
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
                const costo = item.price !== undefined ? item.price : 0;
                const cantidad = item.cantidad || 0;
                const subtotal = costo * cantidad;
                total += subtotal;

                html += `
                    <div class="border p-4 rounded-lg bg-gray-50 flex justify-between items-center">
                        <div>
                            <h3 class="font-semibold text-gray-800">${item.nombre || 'Sin nombre'}</h3>
                            <p class="text-gray-600">Precio: $${costo.toFixed(2)} x 
                                <input type="number" 
                                       class="w-16 border rounded p-1 text-center" 
                                       value="${cantidad}" 
                                       min="0" 
                                       onchange="updateQuantity('${id}', this.value)">
                            </p>
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
            document.getElementById('cart_total').textContent = `Total: $${total.toFixed(2)}`;
        } else {
            document.getElementById('cart_items').innerHTML = 
                `<p class="text-red-600">Error al cargar el registro: ${result.message}</p>`;
        }
    } catch (error) {
        document.getElementById('cart_items').innerHTML = 
            `<p class="text-red-600">Error al cargar el registro: ${error.message}</p>`;
    }
}

// Actualizar cantidad en el carrito
async function updateQuantity(productId, quantity) {
    try {
        const response = await fetch('/actualizar_carrito', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ codigo: productId, cantidad: parseInt(quantity) })
        });
        const result = await response.json();
        if (result.success) {
            updateCart();
            loadProducts();
        } else {
            alert(result.message);
            updateCart();
        }
    } catch (error) {
        alert('Error al actualizar el registro: ' + error.message);
        updateCart();
    }
}

// Completar salida
document.getElementById('checkout_btn').addEventListener('click', async () => {
    try {
        const response = await fetch('/dar_salida', { 
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });
        const result = await response.json();
        if (result.success) {
            alert('Salida registrada exitosamente');
            updateCart();
            loadProducts();
        } else {
            alert(result.message);
        }
    } catch (error) {
        alert('Error al procesar la salida: ' + error.message);
    }
});

// Cargar datos iniciales
window.onload = () => {
    loadProducts();
    updateCart();
};