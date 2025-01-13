 // Función para cargar los datos desde la API
 async function cargarDatos() {
    const response = await fetch('/api/ventas');
    const data = await response.json();

    const ventasMensuales = data.ventas_mensuales.map(item => item.total);
    const ventasAnuales = data.ventas_anuales.map(item => item.total);
    const meses = data.meses;
    const anios = data.anios;

    // Crear el gráfico de ventas mensuales
    var ctx1 = document.getElementById('chart1').getContext('2d');
    new Chart(ctx1, {
      type: 'line',
      data: {
        labels: meses,
        datasets: [{
          label: 'Ventas Mensuales',
          data: ventasMensuales,
          borderColor: 'rgba(54, 162, 235, 1)',
          borderWidth: 2
        }]
      }
    });

    // Crear el gráfico de ventas anuales
    var ctx2 = document.getElementById('chart2').getContext('2d');
    new Chart(ctx2, {
      type: 'line',
      data: {
        labels: anios,
        datasets: [{
          label: 'Ventas Anuales',
          data: ventasAnuales,
          borderColor: 'rgba(75, 192, 192, 1)',
          borderWidth: 2
        }]
      }
    });
  }

  // Llamar a la función para cargar los datos al cargar la página
  cargarDatos();