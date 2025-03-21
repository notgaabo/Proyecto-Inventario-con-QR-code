
document.addEventListener('DOMContentLoaded', () => {
    const checkoutBtn = document.getElementById('checkout_btn');
    const confirmCheckoutBtn = document.getElementById('confirm_checkout');
    const checkoutModal = document.getElementById('checkout-modal');
    const cartContainer = document.getElementById('cart_items');
    const cartTotalElement = document.getElementById('cart_total');

    // Verificar si Flowbite está cargado
    if (typeof Modal === 'undefined') {
        console.error('Flowbite no está cargado.');
        return;
    }

    // Crear instancia del modal
    const modal = new Modal(checkoutModal);
    console.log("Instancia del modal:", modal);

    const calculateItemTotal = (price, quantity) => (Number(price) || 0) * (Number(quantity) || 0);

    const updateCartTotal = () => {
        const items = cartContainer.querySelectorAll('div[data-product-id]');
        let total = 0;
        items.forEach(item => {
            const price = parseFloat(item.querySelector('.text-gray-600')?.textContent.replace(/[^0-9.]/g, '') || '0');
            const quantity = parseInt(item.querySelector('input')?.value || '0');
            total += calculateItemTotal(price, quantity);
        });
        cartTotalElement.textContent = `Total Registrado: $${total.toFixed(2)}`;
    };

    const clearCart = () => {
        cartContainer.innerHTML = '<p class="text-gray-500">Registro vacío</p>';
        cartTotalElement.textContent = 'Total Registrado: $0.00';
        modal.hide();
    };

    const loadCartData = () => {
        const modalProducts = document.getElementById('modal_products');
        if (!modalProducts) return;

        modalProducts.innerHTML = '';
        let subtotal = 0;
        const cartItems = cartContainer.querySelectorAll('div[data-product-id]');

        if (!cartItems.length) {
            modalProducts.innerHTML = '<p class="text-gray-500">No hay productos en el carrito.</p>';
        } else {
            cartItems.forEach(item => {
                const price = parseFloat(item.querySelector('.text-gray-600')?.textContent.replace(/[^0-9.]/g, '') || '0');
                const quantity = parseInt(item.querySelector('input')?.value || '0');
                const itemSubtotal = calculateItemTotal(price, quantity);
                subtotal += itemSubtotal;

                const productName = item.querySelector('.font-semibold')?.textContent || 'Producto desconocido';
                modalProducts.innerHTML += `
                    <div class="flex justify-between items-center">
                        <span class="text-gray-800">${productName} (x${quantity})</span>
                        <span class="font-medium">$${itemSubtotal.toFixed(2)}</span>
                    </div>
                `;
            });
        }

        const tax = subtotal * 0.18;
        const total = subtotal + tax;

        document.getElementById('modal_subtotal').textContent = `$${subtotal.toFixed(2)}`;
        document.getElementById('modal_tax').textContent = `$${tax.toFixed(2)}`;
        document.getElementById('modal_total').textContent = `$${total.toFixed(2)}`;
    };

    if (checkoutBtn) {
        checkoutBtn.addEventListener('click', () => {
            loadCartData();
            modal.show();
        });
    }

    if (confirmCheckoutBtn) {
        confirmCheckoutBtn.addEventListener('click', async () => {
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
                modal.hide();
                return;
            }

            try {
                const response = await fetch('/register_sale', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Accept': 'application/json'
                    },
                    body: JSON.stringify({ items: itemsToSend }),
                    credentials: 'same-origin'
                });

                if (!response.ok) {
                    const errorData = await response.json().catch(() => ({}));
                    throw new Error(errorData.error || `Error del servidor: ${response.status}`);
                }

                const data = await response.json();

                if (data.success) {
                    clearCart();
                    alert('Venta registrada con éxito');
                } else {
                    throw new Error(data.error || 'Error desconocido del servidor');
                }
            } catch (error) {
                console.error('Error:', error);
                alert(`Error al registrar la venta: ${error.message}`);
                modal.hide();
            }
        });
    }

    // Cerrar modal al hacer clic fuera de él
    if (checkoutModal) {
        checkoutModal.addEventListener('click', (event) => {
            if (event.target === checkoutModal) {
                modal.hide();
            }
        });

        // Agregar evento al botón de cierre del modal
        const closeModalBtn = checkoutModal.querySelector('[data-modal-hide]');
        if (closeModalBtn) {
            closeModalBtn.addEventListener('click', () => {
                modal.hide();
            });
        }
    }

    document.addEventListener('cartUpdated', updateCartTotal);
    updateCartTotal();
});
