// Script para manejar los círculos de selección
document.addEventListener('DOMContentLoaded', function() {
    const productCircle = document.getElementById('product-circle');
    const startDateCircle = document.getElementById('start-date-circle');
    const endDateCircle = document.getElementById('end-date-circle');
    
    // Función para cambiar el color del círculo
    function toggleCircle(circle) {
        if (circle.classList.contains('bg-orange-500')) {
            circle.classList.remove('bg-orange-500');
            circle.classList.add('bg-black');
        } else {
            circle.classList.remove('bg-black');
            circle.classList.add('bg-orange-500');
        }
    }
    
    // Eventos de clic para cada círculo
    productCircle.addEventListener('click', function() {
        toggleCircle(this);
        document.getElementById('product-filter').focus();
    });
    
    startDateCircle.addEventListener('click', function() {
        toggleCircle(this);
        document.getElementById('date-start').focus();
    });
    
    endDateCircle.addEventListener('click', function() {
        toggleCircle(this);
        document.getElementById('date-end').focus();
    });
    
    // Cambiar círculos automáticamente cuando se enfocan los inputs
    document.getElementById('product-filter').addEventListener('focus', function() {
        if (!productCircle.classList.contains('bg-black')) {
            toggleCircle(productCircle);
        }
    });
    
    document.getElementById('date-start').addEventListener('focus', function() {
        if (!startDateCircle.classList.contains('bg-black')) {
            toggleCircle(startDateCircle);
        }
    });
    
    document.getElementById('date-end').addEventListener('focus', function() {
        if (!endDateCircle.classList.contains('bg-black')) {
            toggleCircle(endDateCircle);
        }
    });
    
    // Establecer círculo como negro si el campo ya tiene un valor
    if (document.getElementById('product-filter').value !== 'all') {
        productCircle.classList.remove('bg-orange-500');
        productCircle.classList.add('bg-black');
    }
    
    if (document.getElementById('date-start').value) {
        startDateCircle.classList.remove('bg-orange-500');
        startDateCircle.classList.add('bg-black');
    }
    
    if (document.getElementById('date-end').value) {
        endDateCircle.classList.remove('bg-orange-500');
        endDateCircle.classList.add('bg-black');
    }
});