// #qr.js

document.addEventListener('DOMContentLoaded', () => {
    let lastScannedCode = null;
    let isProcessing = false;
    let isPaused = false;

    const html5QrCode = new Html5Qrcode("qr-reader");
    const qrConfig = { 
        fps: 15,
        qrbox: { width: 300, height: 300 },
        aspectRatio: 1.0
    };

    const beepSound = new Audio('https://www.soundjay.com/buttons/beep-01a.mp3');
    const qrResultDiv = document.getElementById('qr-result');
    const qrReaderDiv = document.getElementById('qr-reader');

    if (qrReaderDiv) qrReaderDiv.innerHTML = '';

    html5QrCode.start(
        { facingMode: "environment" },
        qrConfig,
        async (decodedText) => {
            if (isProcessing || isPaused || decodedText === lastScannedCode) return;

            isProcessing = true;
            lastScannedCode = decodedText;
            isPaused = true;

            try {
                const response = await fetch('/escanear', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ codigo: decodedText })
                });
                const result = await response.json();

                if (result.success) {
                    qrResultDiv.innerHTML = `<p class="text-green-600">Añadido: ${result.producto} (x${result.cantidad})</p>`;
                    beepSound.play();
                    await updateCart();
                } else {
                    qrResultDiv.innerHTML = `<p class="text-red-600">${result.message}</p>`;
                }
            } catch (error) {
                qrResultDiv.innerHTML = `<p class="text-red-600">Error al procesar el QR: ${error.message}</p>`;
            } finally {
                isProcessing = false;
                setTimeout(() => {
                    isPaused = false;
                    lastScannedCode = null;
                }, 2000);
            }
        },
        (error) => {
            console.warn(`Error de escaneo: ${error}`);
        }
    ).catch(err => {
        console.error("Error al iniciar el escáner:", err);
        qrResultDiv.innerHTML = `<p class="text-red-600">Error al iniciar la cámara: ${err.message}</p>`;
    });

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
                document.dispatchEvent(new Event('cartUpdated'));
            } else {
                document.getElementById('cart_items').innerHTML = `<p class="text-red-600">Error al cargar el registro: ${result.message}</p>`;
            }
        } catch (error) {
            document.getElementById('cart_items').innerHTML = `<p class="text-red-600">Error al cargar el registro: ${error.message}</p>`;
        }
    }

    async function updateQuantity(productId, quantity) {
        try {
            const response = await fetch('/actualizar_carrito', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ codigo: productId, cantidad: parseInt(quantity, 10) })
            });
            const result = await response.json();

            if (result.success) {
                await updateCart();
            } else {
                alert(result.message);
                await updateCart();
            }
        } catch (error) {
            alert('Error al actualizar el registro: ' + error.message);
            await updateCart();
        }
    }

    window.updateQuantity = updateQuantity; // Hacer accesible para onchange
    updateCart();
});
