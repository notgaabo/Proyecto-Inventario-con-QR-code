// #sales.js

document.addEventListener('DOMContentLoaded', () => {
    const checkoutBtn = document.getElementById('checkout_btn');
    const confirmCheckoutBtn = document.getElementById('confirm_checkout');
    const checkoutModal = document.getElementById('checkout-modal');
    const cartContainer = document.getElementById('cart_items');
    const cartTotalElement = document.getElementById('cart_total');
    const paymentMethodSelect = document.getElementById('payment_method');
    const transferForm = document.getElementById('transfer_form');
    const stripeForm = document.getElementById('stripe_form');

    let stripe = null;
    let elements = null;
    let card = null;

    console.log('sales.js cargado correctamente');

    const initializeStripe = () => {
        if (!stripe) {
            stripe = Stripe(stripePublicKey); // Asegúrate de definir stripePublicKey en tu HTML
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

    paymentMethodSelect.addEventListener('change', (e) => {
        transferForm.classList.add('hidden');
        stripeForm.classList.add('hidden');
        destroyStripe();
        if (e.target.value === 'transfer') {
            transferForm.classList.remove('hidden');
        } else if (e.target.value === 'stripe') {
            stripeForm.classList.remove('hidden');
            initializeStripe();
        }
        console.log('Método de pago cambiado a:', e.target.value);
    });

    const calculateItemTotal = (price, quantity) => (Number(price) || 0) * (Number(quantity) || 0);

    const updateCartTotal = () => {
        const items = cartContainer.querySelectorAll('div[data-product-id]');
        let total = 0;
        items.forEach(item => {
            const price = parseFloat(item.querySelector('.text-gray-600')?.textContent.replace(/[^0-9.]/g, '') || '0');
            const quantity = parseInt(item.querySelector('input')?.value || '0');
            total += calculateItemTotal(price, quantity);
        });
        cartTotalElement.textContent = `Total: $${total.toFixed(2)}`;
        console.log('Total del carrito actualizado:', total);
        return total;
    };

    const clearCart = () => {
        cartContainer.innerHTML = '<p class="text-gray-500">Registro vacío</p>';
        cartTotalElement.textContent = 'Total: $0.00';
        console.log('Carrito limpiado en el frontend');
    };

    const loadCartData = () => {
        const modalProducts = document.getElementById('modal_products');
        if (!modalProducts) {
            console.warn('modal_products no encontrado');
            return;
        }

        modalProducts.innerHTML = '';
        let total = 0;
        const cartItems = cartContainer.querySelectorAll('div[data-product-id]');

        if (!cartItems.length) {
            modalProducts.innerHTML = '<p class="text-gray-500">No hay productos en el carrito.</p>';
        } else {
            cartItems.forEach(item => {
                const price = parseFloat(item.querySelector('.text-gray-600')?.textContent.replace(/[^0-9.]/g, '') || '0');
                const quantity = parseInt(item.querySelector('input')?.value || '0');
                const itemTotal = calculateItemTotal(price, quantity);
                total += itemTotal;

                const productName = item.querySelector('.font-semibold')?.textContent || 'Producto desconocido';
                modalProducts.innerHTML += `
                    <div class="flex justify-between items-center">
                        <span class="text-gray-800">${productName} (x${quantity})</span>
                        <span class="font-medium">$${itemTotal.toFixed(2)}</span>
                    </div>
                `;
            });
        }

        document.getElementById('modal_total').textContent = `$${total.toFixed(2)}`;
        console.log('Datos del carrito cargados en el modal, total:', total);
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
            const paymentMethod = paymentMethodSelect.value;
            const totalAmount = updateCartTotal();

            console.log('Botón Confirmar Pago clicado, método:', paymentMethod, 'total:', totalAmount);

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

                    return productId && quantity > 0 && salePrice > 0 ? {
                        product_id: productId,
                        quantity,
                        sale_price: salePrice,
                        profit
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
                        account_number: document.getElementById('account_number').value,
                        bank_name: document.getElementById('bank_name').value,
                        transfer_date: document.getElementById('transfer_date').value,
                        reference_number: document.getElementById('reference_number').value
                    };
                    
                    if (!transferData.account_number || !transferData.bank_name || 
                        !transferData.transfer_date || !transferData.reference_number) {
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

                    // Close the modal manually
                    const modalElement = document.getElementById('checkout-modal');
                    if (modalElement) {
                        modalElement.classList.add('hidden');
                        console.log('Modal cerrado manualmente');
                    } else {
                        console.warn('Modal element not found');
                    }

                    // Trigger PDF download with all sale_ids
                    if (data.sale_ids && data.sale_ids.length > 0) {
                        const saleIdsParam = data.sale_ids.join(',');
                        const invoiceUrl = `/factura?ids=${saleIdsParam}`;
                        console.log('Generando descarga de factura con todos los IDs:', invoiceUrl);

                        const link = document.createElement('a');
                        link.href = invoiceUrl;
                        link.download = `factura_${data.sale_ids[0]}.pdf`; // Nombre basado en el primer ID
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