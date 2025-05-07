
document.addEventListener('DOMContentLoaded', function () {
    const dropdownButton = document.getElementById('dropdownButton');
    const dropdownMenu = document.getElementById('timePeriodDropdown');
    const selectedPeriod = document.getElementById('selectedPeriod');
    const topProductsContainer = document.getElementById('topProductsContainer');

    // Mostrar/ocultar dropdown al hacer clic
    dropdownButton.addEventListener('click', function () {
        dropdownMenu.classList.toggle('hidden');
    });

    // Manejar clics en las opciones del dropdown
    dropdownMenu.querySelectorAll('a').forEach(option => {
        option.addEventListener('click', function (e) {
            e.preventDefault();
            const period = this.getAttribute('data-period');
            selectedPeriod.textContent = this.textContent;

            // Ocultar el dropdown después de seleccionar
            dropdownMenu.classList.add('hidden');

            // Llamar al backend para obtener datos filtrados
            fetchFilteredData(period);
        });
    });

    // Función para obtener y actualizar datos
    function fetchFilteredData(period) {
        fetch(`/filter-sales?period=${period}`, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json'
            }
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Error en la respuesta del servidor');
            }
            return response.json();
        })
        .then(data => {
            // Actualizar el contenedor de productos más vendidos
            updateTopProducts(data.products);
        })
        .catch(error => {
            console.error('Error al obtener datos:', error);
            topProductsContainer.innerHTML = `
                <div class="flex flex-col items-center justify-center h-40 bg-gray-50 rounded-lg">
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-10 w-10 text-red-500 mb-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                    </svg>
                    <p class="text-red-500 text-center">Error al cargar los datos.</p>
                </div>
            `;
        });
    }

    // Función para actualizar los productos en la interfaz
    function updateTopProducts(products) {
        if (products && products.length > 0) {
            let html = '<div class="grid grid-cols-1 sm:grid-cols-3 gap-4">';
            products.forEach(product => {
                html += `
                    <div class="flex flex-col items-center bg-gray-50 p-4 rounded-lg hover:shadow-md transition-all duration-200">
                        <div class="border border-gray-200 rounded-lg w-24 h-24 flex items-center justify-center mb-3 overflow-hidden bg-white">
                            ${product.image ? 
                                `<img src="/static/uploads/${product.image}" alt="${product.name}" class="max-h-full max-w-full object-contain">` : 
                                `<img src="/static/uploads/default.png" alt="Sin imagen" class="w-full h-full object-cover grayscale hover:grayscale-0 transition-all duration-500">`}
                        </div>
                        <p class="text-gray-600 text-sm font-medium text-center">${product.name}</p>
                        <p class="text-2xl font-bold text-black text-center mt-1">${product.sales_count}</p>
                        <p class="text-xs text-gray-500 text-center">unidades</p>
                    </div>
                `;
            });
            html += '</div>';
            topProductsContainer.innerHTML = html;
        } else {
            topProductsContainer.innerHTML = `
                <div class="flex flex-col items-center justify-center h-40 bg-gray-50 rounded-lg">
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-10 w-10 text-gray-400 mb-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                    </svg>
                    <p class="text-gray-500 text-center">No hay productos más vendidos para mostrar.</p>
                </div>
            `;
        }
    }

    // Cerrar dropdown si se hace clic fuera
    document.addEventListener('click', function (e) {
        if (!dropdownButton.contains(e.target) && !dropdownMenu.contains(e.target)) {
            dropdownMenu.classList.add('hidden');
        }
    });

    // Cargar los datos iniciales con "Último Mes"
    fetchFilteredData('month');
});
