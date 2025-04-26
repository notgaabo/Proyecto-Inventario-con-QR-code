 
    const saleIdInput = document.getElementById('sale_id');
    const saleDetails = document.getElementById('sale-details');
    const productList = document.getElementById('product-list');
    const form = document.getElementById('return-form');

    function loadSaleData(saleId) {
        if (!saleId || isNaN(saleId) || saleId <= 0) {
            saleDetails.classList.add('hidden');
            productList.innerHTML = '';
            alert('Por favor, ingrese un ID de venta válido.');
            return;
        }

        fetch(`/api/sale/${saleId}`)
            .then(response => {
                if (!response.ok) {
                    throw new Error(response.status === 404 ? 'El grupo de venta no existe' : 'Error al cargar los datos');
                }
                return response.json();
            })
            .then(data => {
                productList.innerHTML = '';

                if (data.products.length === 0) {
                    saleDetails.classList.add('hidden');
                    alert('No se encontraron productos para este grupo de venta.');
                    return;
                }

                data.products.forEach(product => {
                    const div = document.createElement('div');
                    div.classList.add('mb-2', 'p-2', 'border', 'rounded-lg');
                    div.textContent = `${product.name} (Cantidad vendida: ${product.quantity})`;
                    productList.appendChild(div);
                });

                saleDetails.classList.remove('hidden');
            })
            .catch(error => {
                saleDetails.classList.add('hidden');
                productList.innerHTML = '';
                alert(`Error: ${error.message}`);
            });
    }

    saleIdInput.addEventListener('blur', function() {
        const saleId = this.value.trim();
        loadSaleData(saleId);
    });

    saleIdInput.addEventListener('keypress', function(event) {
        if (event.key === 'Enter') {
            event.preventDefault();
            const saleId = this.value.trim();
            loadSaleData(saleId);
        }
    });

    form.addEventListener('submit', function(event) {
        const saleId = saleIdInput.value.trim();
        const reason = document.getElementById('reason').value.trim();

        if (!saleId || isNaN(saleId) || saleId <= 0) {
            event.preventDefault();
            alert('Por favor, ingrese un ID de venta válido.');
            return;
        }

        if (!reason) {
            event.preventDefault();
            alert('Por favor, proporcione un motivo para la devolución.');
            return;
        }
    });