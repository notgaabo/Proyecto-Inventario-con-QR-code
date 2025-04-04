# app.py

import pandas as pd
from db.config import Config as get_connection
import matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error

# 1. Conexión a la base de datos
conn = get_connection()
query = "SELECT sale_date, quantity FROM sales"
df = pd.read_sql(query, conn)
conn.close()

# 2. Preprocesamiento de fechas
df['sale_date'] = pd.to_datetime(df['sale_date'])
df['month'] = df['sale_date'].dt.to_period('M')
ventas_mensuales = df.groupby('month')['quantity'].sum().reset_index()
ventas_mensuales['month_num'] = range(len(ventas_mensuales))

# 3. Variables
X = ventas_mensuales[['month_num']]
y = ventas_mensuales['quantity']

# 4. Modelo lineal
model = LinearRegression()
model.fit(X, y)
next_month = [[len(ventas_mensuales)]]
predicted = model.predict(next_month)[0]
predicted = max(0, predicted)

# 5. Visualización
plt.figure(figsize=(10, 6))

# Línea exacta que conecta los puntos reales
plt.plot(X, y, color='blue', linestyle='-', marker='o', label='Datos reales')

# Línea naranja hacia la predicción
plt.plot(
    [X['month_num'].iloc[-1], X['month_num'].iloc[-1] + 1],
    [y.iloc[-1], predicted],
    color='orange',
    linestyle='--',
    marker='o',
    label='Predicción próxima'
)

# Punto de predicción
plt.scatter(X['month_num'].iloc[-1] + 1, predicted, color='orange')

# Estética
plt.title('Predicción de ventas - Línea conectada y predicción')
plt.xlabel('Mes')
plt.ylabel('Cantidad vendida')
plt.legend()
plt.grid(True)
plt.tight_layout()

# Mostrar gráfica
plt.show()

# Mostrar en consola
print(f"Predicción de ventas para el próximo mes: {predicted:.2f}")
