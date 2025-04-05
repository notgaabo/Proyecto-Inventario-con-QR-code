import pandas as pd
from db.config import Config as get_connection
import matplotlib.pyplot as plt
from sklearn.preprocessing import PolynomialFeatures
from sklearn.linear_model import LinearRegression
import numpy as np

# 1. Conexión a la base de datos
conn = get_connection()
query = "SELECT sale_date, quantity FROM sales"
df = pd.read_sql(query, conn)
conn.close()

# 2. Preprocesamiento de fechas
df['sale_date'] = pd.to_datetime(df['sale_date'])
df['month'] = df['sale_date'].dt.to_period('M')

# Agrupación mensual
ventas_mensuales = df.groupby('month')['quantity'].sum().reset_index()

# 🔥 Rellenar meses faltantes con 0 ventas
rango_meses = pd.period_range(start=ventas_mensuales['month'].min(),
                              end=ventas_mensuales['month'].max(), freq='M')
ventas_mensuales = ventas_mensuales.set_index('month').reindex(rango_meses, fill_value=0).reset_index()
ventas_mensuales.rename(columns={'index': 'month'}, inplace=True)
ventas_mensuales['month_num'] = range(len(ventas_mensuales))

# 3. Variables
X = ventas_mensuales[['month_num']]
y = ventas_mensuales['quantity']

# 4. Modelo polinomial (parabólico)
poly = PolynomialFeatures(degree=2, include_bias=False)
X_poly = poly.fit_transform(X)
model = LinearRegression()
model.fit(X_poly, y)

# 5. Predicción
next_month = poly.transform([[len(ventas_mensuales)]])
predicted = model.predict(next_month)[0]
predicted = max(0, predicted)

# 6. Visualización mejorada
plt.figure(figsize=(12, 7))
ax = plt.gca()
ax.set_facecolor('#f8f9fa')
plt.grid(True, linestyle='--', alpha=0.7)

# Curva parabólica
X_plot = np.linspace(0, X['month_num'].iloc[-1], 100).reshape(-1, 1)
X_plot_poly = poly.transform(X_plot)
y_plot = model.predict(X_plot_poly)
plt.plot(X_plot, y_plot, color='#2c3e50', linewidth=2.5, label='Tendencia de ventas')

# Puntos reales
plt.scatter(X, y, color='#e74c3c', marker='o', s=100,
            edgecolors='white', linewidth=1.5, label='Ventas reales')

# Predicción
plt.scatter(len(ventas_mensuales), predicted, color='#27ae60', marker='*',
            s=300, edgecolors='white', linewidth=1.5, label='Predicción')

# Líneas punteadas
x_values = np.linspace(X['month_num'].iloc[-1], len(ventas_mensuales), 15)
y_values = np.linspace(y.iloc[-1], predicted, 15)
for i in range(len(x_values)-1):
    if i % 2 == 0:
        plt.plot([x_values[i], x_values[i+1]],
                 [y_values[i], y_values[i+1]],
                 color='#27ae60',
                 linestyle='-',
                 linewidth=1.2,
                 alpha=0.5)

# Estética
plt.title('Análisis de Ventas y Predicción',
          fontsize=16, pad=20, fontweight='bold')
plt.xlabel('Meses', fontsize=12)
plt.ylabel('Cantidad de Ventas', fontsize=12)
plt.legend(loc='upper left', frameon=True,
           facecolor='white', edgecolor='none',
           fontsize=10, bbox_to_anchor=(0.01, 0.99))
plt.tight_layout()
plt.grid(True, alpha=0.3)
plt.show()

# Consola
print(f"Predicción de ventas para el próximo mes: {predicted:.2f}")
