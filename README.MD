# 📦 StockBeam

StockBeam es una solución integral para la gestión de inventarios, diseñada especialmente para negocios que buscan eficiencia, control y automatización mediante el uso de **códigos QR**, reportes detallados y control de ventas.

## 🚀 Características Principales

- 📲 **Escaneo rápido con QR**: Identificación y registro ágil de productos.
- 📈 **Reportes inteligentes**: Ventas diarias, semanales, mensuales, semestrales y anuales.
- 🧾 **Facturación automatizada**: Emisión clara de comprobantes por cliente.
- 🏪 **Gestión de inventario**: Entradas, salidas, devoluciones, balance y más.
- 👥 **Manejo de roles**: Interfaces diferenciadas para Vendedores, Personal de Almacén y Gerentes.
- 🔄 **Devoluciones controladas**: Historial detallado y motivos específicos.
- 🧮 **Análisis de proveedores**: Rendimiento, entregas y actividad.
- 🔒 **Autenticación segura**: Acceso mediante credenciales personales.

## 🧑‍💻 Tecnologías Utilizadas

- **Backend**: Python con `mysql.connector`
- **Frontend**: HTML, CSS, JavaScript
- **Base de Datos**: MySQL
- **QR**: Generador y lector integrado

## 🛠️ Instalación

1. Clona este repositorio:
   ```bash
   git clone https://github.com/tu_usuario/stockbeam.git
   cd stockbeam
   ```

2. Configura el entorno e instala dependencias:
   ```bash
   pip install -r requirements.txt
   ```

3. Crea tu base de datos `stockbeam` e importa las tablas necesarias (`users`, `products`, `sales`, `roles`, etc.).

4. Configura tu archivo de conexión en `db/config.py`:
   ```python
   db = mysql.connector.connect(
       host="localhost",
       user="tu_usuario",
       password="tu_contraseña",
       database="stockbeam"
   )
   ```

5. Ejecuta el servidor:
   ```bash
   python app.py
   ```

## 🔑 Acceso al sistema

- Asegúrate de tener tus credenciales.
- Ingresa la URL en tu navegador.
- Introduce tu usuario y contraseña.

## 🧭 Estructura del Proyecto

```
stockbeam/
├── app.py
├── auth/
├── controllers/
├── db/
│   └── config.py
├── routes/
├── templates/
│   ├── admin/
│   ├── includes/
│   └── user/
└── static/
```

## 📚 Manual de Usuario

Puedes encontrar una guía completa sobre el uso del sistema en el documento `manual.docx`, donde se explica cómo:
- Registrar ventas
- Manejar devoluciones
- Visualizar reportes
- Agregar proveedores
- Supervisar el rendimiento de ventas

## 📩 Soporte

¿Tienes dudas o necesitas ayuda? Contacta al equipo técnico o abre un issue en este repositorio.

---

**StockBeam** — Optimiza, controla y crece con precisión. 📊
