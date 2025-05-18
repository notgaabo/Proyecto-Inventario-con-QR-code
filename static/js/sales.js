document.addEventListener('DOMContentLoaded', () => {
    const checkoutBtn = document.getElementById('checkout_btn');
    const confirmCheckoutBtn = document.getElementById('confirm_checkout');
    const checkoutModal = document.getElementById('checkout-modal');
    const cartContainer = document.getElementById('cart_items');
    const cartTotalElement = document.getElementById('cart_total');
    const transferForm = document.getElementById('transfer');
    const stripeForm = document.getElementById('stripe');

    let stripe = null;
    let elements = null;
    let card = null;

    console.log('sales.js cargado correctamente');

    const initializeStripe = () => {
        if (!stripe && stripePublicKey) {
            if (typeof Stripe === 'undefined') {
                console.error('Stripe library not loaded.');
                alert('Error: No se pudo cargar Stripe.');
                return;
            }
            stripe = Stripe(stripePublicKey);
            elements = stripe.elements();
            card = elements.create('card', {
                style: {
                    base: {
                        fontSize: '16px',
                        color: '#32325d',
                        '::placeholder': { color: '#aab7c4' }
                    },
                    invalid: {
                        color: '#fa755a',
                        iconColor: '#fa755a'
                    }
                }
            });
            card.mount('#card-element');
            card.on('change', (event) => {
                const displayError = document.getElementById('card-errors');
                displayError.textContent = event.error ? event.error.message : '';
            });
            console.log('Stripe inicializado');
        } else if (!stripePublicKey) {
            console.error('stripePublicKey is undefined.');
        }
    };

    const destroyStripe = () => {
        if (card) {
            card.unmount();
            card.destroy();
            card = null;
            stripe = null;
            elements = null;
            console.log('Stripe destruido');
        }
    };

    const getActivePaymentMethod = () => {
        if (!document.getElementById('cash').classList.contains('hidden')) {
            return 'cash';
        } else if (!document.getElementById('transfer').classList.contains('hidden')) {
            return 'transfer';
        } else if (!document.getElementById('stripe').classList.contains('hidden')) {
            return 'stripe';
        }
        return null;
    };

    // Initialize Stripe when Stripe tab is selected
    const tabButtons = document.querySelectorAll('.tab-button');
    tabButtons.forEach(button => {
        button.addEventListener('click', () => {
            const tabId = button.getAttribute('data-tab');
            if (tabId === 'stripe' && !card) {
                initializeStripe();
            } else if (tabId !== 'stripe' && card) {
                destroyStripe();
            }
        });
    });

    const calculateItemTotal = (price, quantity) => {
        const subtotal = (Number(price) || 0) * (Number(quantity) || 0);
        const itbisRate = 0.18;
        const itbis = subtotal * itbisRate;
        const total = subtotal + itbis;
        return { subtotal, itbis, total };
    };

    const updateCartTotal = () => {
        const items = cartContainer.querySelectorAll('div[data-product-id]');
        let subtotal = 0;
        let totalItbis = 0;
        let total = 0;

        items.forEach(item => {
            const price = parseFloat(item.querySelector('.text-gray-600')?.textContent.replace(/[^0-9.]/g, '') || '0');
            const quantity = parseInt(item.querySelector('input')?.value || '0');
            const { subtotal: itemSubtotal, itbis: itemItbis, total: itemTotal } = calculateItemTotal(price, quantity);
            subtotal += itemSubtotal;
            totalItbis += itemItbis;
            total += itemTotal;
        });

        cartTotalElement.textContent = `Total: $${total.toFixed(2)}`;
        console.log('Total del carrito actualizado:', { subtotal, totalItbis, total });
        return total;
    };

    const clearCart = () => {
        cartContainer.innerHTML = '<p class="text-gray-500">Registro vacío</p>';
        cartTotalElement.textContent = 'Total: $0.00';
        console.log('Carrito limpiado en el frontend');
    };

    const loadCartData = () => {
        const modalProducts = document.getElementById('modal_products');
        const modalTotal = document.getElementById('modal_total');
        
        if (!modalProducts || !modalTotal) {
            console.warn('modal_products o modal_total no encontrado');
            return;
        }

        modalProducts.innerHTML = '';
        let subtotal = 0;
        let totalItbis = 0;
        let total = 0;
        const cartItems = cartContainer.querySelectorAll('div[data-product-id]');

        if (!cartItems.length) {
            modalProducts.innerHTML = '<p class="text-gray-500">No hay productos en el carrito.</p>';
            modalTotal.innerHTML = `
                <div class="flex justify-between text-lg font-bold">
                    <span>Total a Pagar:</span>
                    <span class="text-orange-600">$0.00</span>
                </div>
            `;
        } else {
            cartItems.forEach(item => {
                const price = parseFloat(item.querySelector('.text-gray-600')?.textContent.replace(/[^0-9.]/g, '') || '0');
                const quantity = parseInt(item.querySelector('input')?.value || '0');
                const { subtotal: itemSubtotal, itbis: itemItbis, total: itemTotal } = calculateItemTotal(price, quantity);
                subtotal += itemSubtotal;
                totalItbis += itemItbis;
                total += itemTotal;

                const productName = item.querySelector('.font-semibold')?.textContent || 'Producto desconocido';
                modalProducts.innerHTML += `
                    <div class="flex justify-between items-center">
                        <span class="text-gray-800">${productName} (x${quantity})</span>
                        <span class="font-medium">$${itemTotal.toFixed(2)}</span>
                    </div>
                `;
            });

            modalTotal.innerHTML = `
                <div class="flex justify-between text-base font-medium">
                    <span>Subtotal:</span>
                    <span>$${subtotal.toFixed(2)}</span>
                </div>
                <div class="flex justify-between text-base font-medium mt-1">
                    <span>ITBIS (18%):</span>
                    <span>$${totalItbis.toFixed(2)}</span>
                </div>
                <div class="flex justify-between text-lg font-bold mt-2">
                    <span>Total a Pagar:</span>
                    <span class="text-orange-600">$${total.toFixed(2)}</span>
                </div>
            `;
        }

        console.log('Datos del carrito cargados en el modal:', { subtotal, totalItbis, total });
        return total;
    };

    if (checkoutBtn) {
        checkoutBtn.addEventListener('click', () => {
            loadCartData();
            const modal = new Flowbite.Modal(checkoutModal);
            modal.show();
            console.log('Modal de checkout abierto');
        });
    } else {
        console.warn('checkout_btn no encontrado');
    }

    if (confirmCheckoutBtn) {
        confirmCheckoutBtn.addEventListener('click', async () => {
            const paymentMethod = getActivePaymentMethod();
            const totalAmount = updateCartTotal();

            console.log('Botón Confirmar Pago clicado, método:', paymentMethod, 'total:', totalAmount);

            if (!paymentMethod) {
                alert('Por favor, selecciona un método de pago.');
                return;
            }

            if (totalAmount <= 0) {
                alert('El total debe ser mayor que cero para proceder con el pago.');
                return;
            }

            const itemsToSend = Array.from(cartContainer.querySelectorAll('div[data-product-id]'))
                .map(item => {
                    const productId = item.dataset.productId;
                    const quantity = parseInt(item.querySelector('input')?.value || '0');
                    const salePrice = parseFloat(item.querySelector('.text-gray-600')?.textContent.replace(/[^0-9.]/g, '') || '0');
                    const profit = salePrice * 0.20;
                    const { subtotal, itbis, total } = calculateItemTotal(salePrice, quantity);

                    return productId && quantity > 0 && salePrice > 0 ? {
                        product_id: productId,
                        quantity,
                        sale_price: salePrice,
                        profit,
                        subtotal,
                        itbis,
                        total
                    } : null;
                })
                .filter(item => item !== null);

            if (!itemsToSend.length) {
                alert('No hay productos válidos para registrar.');
                return;
            }

            let payload = { 
                items: itemsToSend, 
                payment_method: paymentMethod,
                amount: totalAmount
            };

            try {
                if (paymentMethod === 'stripe') {
                    if (!card) {
                        alert('Por favor, selecciona el método de pago Stripe y espera a que cargue.');
                        return;
                    }
                    const { token, error } = await stripe.createToken(card);
                    if (error) {
                        document.getElementById('card-errors').textContent = error.message;
                        console.error('Error en Stripe token:', error.message);
                        return;
                    }
                    payload.stripe_token = token.id;
                    console.log('Token de Stripe generado:', token.id);
                } else if (paymentMethod === 'transfer') {
                    const transferData = {
                        account_number: document.getElementById('account_number')?.value || '',
                        bank_name: document.getElementById('bank_name')?.value || '',
                        transfer_date: document.getElementById('transfer_date')?.value || '',
                        reference_number: document.getElementById('reference_number')?.value || ''
                    };
                    
                    if (Object.values(transferData).some(val => !val)) {
                        alert('Por favor, completa todos los campos de transferencia.');
                        return;
                    }
                    
                    payload.transfer_data = transferData;
                    console.log('Datos de transferencia:', transferData);
                }

                console.log('Enviando solicitud a /register_sale con payload:', payload);
                const response = await fetch('/register_sale', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Accept': 'application/json'
                    },
                    body: JSON.stringify(payload)
                });

                if (!response.ok) {
                    throw new Error(`Error en la solicitud: ${response.status} ${response.statusText}`);
                }

                const data = await response.json();
                console.log('Respuesta de /register_sale:', data);

                if (data.success) {
                    console.log('Venta registrada con éxito, limpiando carrito');
                    clearCart();
                    alert('Venta registrada con éxito');

                    const modalElement = document.getElementById('checkout-modal');
                    if (modalElement) {
                        modalElement.classList.add('hidden');
                        console.log('Modal cerrado manualmente');
                    } else {
                        console.warn('Modal element not found');
                    }

                    if (data.sale_ids && data.sale_ids.length > 0) {
                        const saleIdsParam = data.sale_ids.join(',');
                        const invoiceUrl = `/factura?ids=${saleIdsParam}`;
                        console.log('Generando descarga de factura con todos los IDs:', invoiceUrl);

                        const link = document.createElement('a');
                        link.href = invoiceUrl;
                        link.download = `factura_${data.sale_ids[0]}.pdf`;
                        document.body.appendChild(link);
                        link.click();
                        document.body.removeChild(link);
                        console.log('Descarga de factura iniciada');
                    } else {
                        console.warn('No se recibieron sale_ids en la respuesta');
                    }

                    if (paymentMethod === 'stripe' && data.receipt_url) {
                        console.log('Abriendo recibo de Stripe:', data.receipt_url);
                        window.open(data.receipt_url, '_blank');
                    }

                    destroyStripe();
                } else {
                    throw new Error(data.error || 'Error desconocido del servidor');
                }
            } catch (error) {
                console.error('Error al registrar la venta:', error);
                alert(`Error al registrar la venta: ${error.message}`);
            }
        });
    } else {
        console.warn('confirm_checkout no encontrado');
    }

    checkoutModal.addEventListener('hidden.flowbite.modal', () => {
        destroyStripe();
    });

    document.addEventListener('cartUpdated', updateCartTotal);
    updateCartTotal();
}); 