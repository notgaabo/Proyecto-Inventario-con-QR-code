let itemCount = 1;
        
function addItem() {
    const itemsDiv = document.getElementById('items');
    const newItem = document.createElement('div');
    newItem.className = 'item-row';
    newItem.style.marginBottom = '10px';
    newItem.style.paddingBottom = '10px';
    newItem.style.borderBottom = '1px dashed #eee';
    newItem.style.display = 'flex';
    newItem.style.alignItems = 'center';
    
    newItem.innerHTML = `
        <select name="items[${itemCount}][product_id]" required style="width: 60%; padding: 10px; border: 1px solid #ddd; border-radius: 4px; margin-right: 10px; background-color: #fff; color: #333; font-size: 16px;">
            <option value="">Selecciona un producto</option>
            {% for product in products %}
                <option value="{{ product.id }}">{{ product.name }}</option>
            {% endfor %}
        </select>
        <input type="number" name="items[${itemCount}][quantity]" min="1" required placeholder="Cantidad" style="width: 25%; padding: 10px; border: 1px solid #ddd; border-radius: 4px; background-color: #fff; color: #333; font-size: 16px; margin-right: 10px;">
        <button type="button" class="delete-btn" onclick="deleteItem(this)" style="background-color: transparent; border: none; cursor: pointer; color: #f44336; padding: 5px; border-radius: 4px;" title="Eliminar producto">
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <polyline points="3 6 5 6 21 6"></polyline>
                <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
                <line x1="10" y1="11" x2="10" y2="17"></line>
                <line x1="14" y1="11" x2="14" y2="17"></line>
            </svg>
        </button>
    `;
    
    itemsDiv.appendChild(newItem);
    itemCount++;
    
    // Mostrar el botón de eliminar en la primera fila una vez que hay más de una fila
    if (itemsDiv.querySelectorAll('.item-row').length > 1) {
        document.querySelector('.delete-btn').style.visibility = 'visible';
    }
}

function deleteItem(button) {
    const itemsDiv = document.getElementById('items');
    const itemRow = button.parentNode;
    
    // No permitir eliminar si solo queda una fila
    if (itemsDiv.querySelectorAll('.item-row').length > 1) {
        itemRow.remove();
        
        // Ocultar el botón de eliminar en la primera fila si solo queda una
        if (itemsDiv.querySelectorAll('.item-row').length === 1) {
            document.querySelector('.delete-btn').style.visibility = 'hidden';
        }
        
        // Reordenar los índices
        reindexItems();
    }
}

function reindexItems() {
    const itemRows = document.querySelectorAll('.item-row');
    itemRows.forEach((row, index) => {
        const select = row.querySelector('select');
        const input = row.querySelector('input');
        
        select.name = `items[${index}][product_id]`;
        input.name = `items[${index}][quantity]`;
    });
    
    // Actualizar el contador
    itemCount = itemRows.length;
}