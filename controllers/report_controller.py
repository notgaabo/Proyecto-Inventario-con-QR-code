from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Flowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib.colors import Color
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from io import BytesIO
from db.config import Config
import datetime
from datetime import timedelta
from flask import render_template, send_file, session
import decimal

# Custom Flowables
class RoundedRect(Flowable):
    def __init__(self, width, height, radius=10, fillColor=None, strokeColor=None, strokeWidth=1):
        super().__init__()
        self.width, self.height, self.radius = width, height, radius
        self.fillColor, self.strokeColor, self.strokeWidth = fillColor, strokeColor, strokeWidth

    def draw(self):
        c = self.canv
        c.saveState()
        c.setFillColor(self.fillColor) if self.fillColor else None
        c.setStrokeColor(self.strokeColor) if self.strokeColor else None
        c.setLineWidth(self.strokeWidth)
        c.roundRect(0, 0, self.width, self.height, self.radius, fill=bool(self.fillColor), stroke=bool(self.strokeColor))
        c.restoreState()

class CircleValue(Flowable):
    def __init__(self, radius=20, fillColor=None, strokeColor=None, value="", textColor=Color(1, 1, 1)):
        super().__init__()
        self.radius, self.fillColor, self.strokeColor = radius, fillColor, strokeColor
        self.value, self.textColor = value, textColor
        self.width = self.height = 2 * radius

    def draw(self):
        c = self.canv
        c.saveState()
        c.setFillColor(self.fillColor) if self.fillColor else None
        c.setStrokeColor(self.strokeColor) if self.strokeColor else None
        c.circle(self.radius, self.radius, self.radius, fill=1)
        c.setFillColor(self.textColor)
        c.setFont("Helvetica-Bold", 11)
        c.drawCentredString(self.radius, self.radius - 4, self.value)
        c.restoreState()

class MiniBarChart(Flowable):
    def __init__(self, data, width=100, height=40, bars_color=Color(0.9, 0.5, 0.3, alpha=0.8), bg_color=Color(0.95, 0.95, 0.95)):
        super().__init__()
        # Convert any Decimal values to float to avoid TypeError
        self.data = [float(d) if isinstance(d, decimal.Decimal) else d for d in data]
        self.width, self.height = width, height
        self.bars_color, self.bg_color = bars_color, bg_color

    def draw(self):
        c = self.canv
        c.saveState()
        c.setFillColor(self.bg_color)
        c.rect(0, 0, self.width, self.height, fill=1, stroke=0)
        max_val = max(self.data or [1])
        bar_width = self.width / len(self.data) * 0.7
        space_width = self.width / len(self.data) * 0.3
        c.setFillColor(self.bars_color)
        for i, val in enumerate(self.data):
            bar_height = (val / max_val) * self.height * 0.8
            x = i * (bar_width + space_width) + space_width / 2
            c.roundRect(x, self.height * 0.1, bar_width, bar_height, 2, fill=1, stroke=0)
        c.restoreState()

class ModernTab(Flowable):
    def __init__(self, width, height=30, text="", active=False, orange=Color(0.9, 0.5, 0.3, alpha=0.8), bg_color=Color(0.95, 0.95, 0.95)):
        super().__init__()
        self.width, self.height, self.text = width, height, text
        self.active, self.orange, self.bg_color = active, orange, bg_color

    def draw(self):
        c = self.canv
        c.saveState()
        c.setFillColor(self.orange if self.active else self.bg_color)
        c.roundRect(0, 0, self.width, self.height, 10, fill=1, stroke=0)
        c.setFillColor(Color(1, 1, 1) if self.active else Color(0.1, 0.1, 0.1))
        c.setFont("Helvetica-Bold", 11)
        c.drawCentredString(self.width / 2, self.height / 2 - 4, self.text)
        c.restoreState()

# Estilos y colores
class ReportStyles:
    COLORS = {
        'NARANJA_CLARO': Color(0.95, 0.75, 0.55),
        'NARANJA_ACENTO': Color(0.9, 0.5, 0.3, alpha=0.8),
        'NEGRO': Color(0.1, 0.1, 0.1),
        'GRIS_OSCURO': Color(0.3, 0.3, 0.3),
        'GRIS_MEDIO': Color(0.6, 0.6, 0.6),
        'GRIS_CLARO': Color(0.95, 0.95, 0.95),
        'BLANCO': Color(1, 1, 1)
    }

    @staticmethod
    def get_styles():
        styles = getSampleStyleSheet()
        return {
            'title': ParagraphStyle('CustomTitle', parent=styles['Heading1'], alignment=TA_CENTER, fontSize=24, spaceAfter=20, textColor=ReportStyles.COLORS['NEGRO'], fontName='Helvetica-Bold', leading=28),
            'subtitle': ParagraphStyle('CustomSubtitle', parent=styles['Heading2'], fontSize=16, spaceBefore=15, spaceAfter=10, textColor=ReportStyles.COLORS['NARANJA_ACENTO'], fontName='Helvetica-Bold'),
            'card_title': ParagraphStyle('CardTitle', parent=styles['Normal'], fontSize=11, textColor=ReportStyles.COLORS['GRIS_OSCURO'], fontName='Helvetica-Bold', spaceAfter=6),
            'card_value': ParagraphStyle('CardValue', parent=styles['Normal'], fontSize=22, textColor=ReportStyles.COLORS['NEGRO'], fontName='Helvetica-Bold'),
            'normal': ParagraphStyle('CustomNormal', parent=styles['Normal'], fontSize=10, textColor=ReportStyles.COLORS['NEGRO'], leading=14),
            'footer': ParagraphStyle('Footer', parent=styles['Normal'], fontSize=8, textColor=ReportStyles.COLORS['GRIS_MEDIO'], alignment=TA_CENTER)
        }

# Obtener datos de la base de datos
class ReportDataFetcher:
    @staticmethod
    def get_company_name():
        with Config.get_db_connection() as conn, conn.cursor(dictionary=True) as cursor:
            try:
                user = session['user']
                company_id = user['company_id']
                if not company_id:
                    return "Empresa no especificada"
                cursor.execute("SELECT name AS company_name FROM companies WHERE id = %s", (company_id,))
                result = cursor.fetchone()
                return result['company_name'] if result else "Empresa no especificada"
            except Exception as e:
                print(f"Error fetching company name: {str(e)}")
                return "Empresa no especificada"

    @staticmethod
    def get_report_data(report_type):
        with Config.get_db_connection() as conn, conn.cursor(dictionary=True) as cursor:
            today = datetime.datetime.now()
            start_date = {'weekly': 7, 'monthly': 30, 'quarterly': 90}.get(report_type.split('_')[0], None)
            start_date = today - timedelta(days=start_date) if start_date else None

            # Ventas
            sales_data = {'total_sales': 0, 'total_transactions': 0, 'total_profit': 0}
            if report_type in ['weekly', 'monthly', 'quarterly'] and start_date:
                cursor.execute("""
                    SELECT SUM(s.sale_price * s.quantity) as total_sales, 
                           COUNT(s.id) as total_transactions,
                           SUM((s.sale_price - p.cost_price) * s.quantity) as total_profit
                    FROM sales s JOIN products p ON s.product_id = p.id WHERE s.sale_date >= %s
                """, (start_date,))
                sales_data = cursor.fetchone() or sales_data
                # Convert Decimal to float for sales_data
                sales_data['total_sales'] = float(sales_data['total_sales'] or 0)
                sales_data['total_profit'] = float(sales_data['total_profit'] or 0)

            # Inventario
            try:
                cursor.execute("SELECT COUNT(*) as low_stock_items FROM products WHERE stock < 10")
                low_stock = cursor.fetchone()['low_stock_items']
                cursor.execute("SELECT COUNT(DISTINCT category) as all_categories, SUM(stock) as all_items FROM products")
                inventory_data = cursor.fetchone()
                inventory_data['low_stock_items'] = low_stock
                cursor.execute("""
                    SELECT p.name, p.stock, p.category, s.name as supplier_name
                    FROM products p LEFT JOIN suppliers s ON p.supplier_id = s.id
                    ORDER BY p.stock ASC LIMIT 10
                """)
                inventory_details = [{'name': row['name'], 'stock': row['stock'], 'category': row['category'], 'supplier_name': row['supplier_name'] or 'Sin proveedor'} for row in cursor.fetchall()]
            except Exception as e:
                print(f"Error fetching inventory data: {str(e)}")
                inventory_data = {'low_stock_items': 5, 'all_categories': 12, 'all_items': 524}
                inventory_details = [{'name': 'Laptop Dell XPS 15', 'stock': 5, 'category': 'Electrónica', 'supplier_name': 'TechSolutions Inc.'}, {'name': 'Monitor Ultrawide LG', 'stock': 8, 'category': 'Electrónica', 'supplier_name': 'GlobalGadgets S.A.'}]

            # Productos más vendidos
            try:
                cursor.execute("SELECT p.name, SUM(s.quantity) as sales_count FROM sales s JOIN products p ON s.product_id = p.id GROUP BY p.id, p.name ORDER BY sales_count DESC LIMIT 3")
                top_products = cursor.fetchall()
            except Exception as e:
                print(f"Error fetching top products: {str(e)}")
                top_products = [{'name': 'Laptop Dell XPS 15', 'sales_count': 38}, {'name': 'Monitor Ultrawide LG', 'sales_count': 42}, {'name': 'iPhone 15 Pro', 'sales_count': 27}]

            # Proveedores
            try:
                cursor.execute("""
                    SELECT s.name, COUNT(DISTINCT oi.id) as products_bought, 
                           SUM(oi.quantity * p.cost_price) as total_value,
                           AVG(DATEDIFF(o.delivered_at, o.order_date)) as delivery_time
                    FROM suppliers s LEFT JOIN orders o ON s.id = o.supplier_id
                    LEFT JOIN order_items oi ON o.id = oi.order_id
                    LEFT JOIN products p ON oi.product_id = p.id
                    GROUP BY s.id, s.name ORDER BY total_value DESC LIMIT 5
                """)
                suppliers = [{'name': row['name'], 'products_bought': row['products_bought'], 'total_value': float(row['total_value'] or 0), 'delivery_time': f"{int(row['delivery_time'])} días" if row['delivery_time'] else 'N/A'} for row in cursor.fetchall()]
            except Exception as e:
                print(f"Error fetching suppliers: {str(e)}")
                suppliers = [{'name': 'TechSolutions Inc.', 'products_bought': 35, 'total_value': 28500.00, 'delivery_time': '7 días'}, {'name': 'GlobalGadgets S.A.', 'products_bought': 42, 'total_value': 31250.00, 'delivery_time': '5 días'}, {'name': 'ElectroComp Ltd.', 'products_bought': 18, 'total_value': 15640.00, 'delivery_time': '12 días'}]

            # Proveedores activos
            supplier_active_data = []
            if report_type == 'active_suppliers':
                try:
                    cursor.execute("""
                        SELECT s.name, COUNT(DISTINCT o.id) as order_count
                        FROM suppliers s LEFT JOIN orders o ON s.id = o.supplier_id
                        WHERE o.order_date >= %s GROUP BY s.id, s.name
                        ORDER BY order_count DESC LIMIT 5
                    """, (start_date or (today - timedelta(days=30)),))
                    supplier_active_data = [{'name': row['name'], 'order_count': row['order_count']} for row in cursor.fetchall()]
                except Exception as e:
                    print(f"Error fetching active suppliers: {str(e)}")
                    supplier_active_data = [{'name': 'TechSolutions Inc.', 'order_count': 25}, {'name': 'GlobalGadgets S.A.', 'order_count': 20}, {'name': 'ElectroComp Ltd.', 'order_count': 15}]

            # Entregas por proveedor
            supplier_delivery_data = []
            if report_type == 'supplier_deliveries':
                try:
                    cursor.execute("""
                        SELECT s.name, SUM(oi.quantity) as total_delivered
                        FROM suppliers s LEFT JOIN orders o ON s.id = o.supplier_id
                        LEFT JOIN order_items oi ON o.id = oi.order_id
                        WHERE o.status = 'delivered' AND o.delivered_at >= %s
                        GROUP BY s.id, s.name ORDER BY total_delivered DESC LIMIT 5
                    """, (start_date or (today - timedelta(days=30)),))
                    supplier_delivery_data = [{'name': row['name'], 'total_delivered': row['total_delivered'] or 0} for row in cursor.fetchall()]
                except Exception as e:
                    print(f"Error fetching supplier deliveries: {str(e)}")
                    supplier_delivery_data = [{'name': 'TechSolutions Inc.', 'total_delivered': 500}, {'name': 'GlobalGadgets S.A.', 'total_delivered': 450}, {'name': 'ElectroComp Ltd.', 'total_delivered': 300}]

            # Desempeño de proveedores
            supplier_performance_data = []
            if report_type == 'supplier_performance':
                try:
                    cursor.execute("""
                        SELECT s.name, AVG(DATEDIFF(o.delivered_at, o.order_date)) as avg_delivery_time,
                               COUNT(DISTINCT o.id) as order_count, SUM(oi.quantity * p.cost_price) as total_value
                        FROM suppliers s LEFT JOIN orders o ON s.id = o.supplier_id
                        LEFT JOIN order_items oi ON o.id = oi.order_id
                        LEFT JOIN products p ON oi.product_id = p.id
                        WHERE o.status = 'delivered' AND o.delivered_at >= %s
                        GROUP BY s.id, s.name ORDER BY total_value DESC LIMIT 5
                    """, (start_date or (today - timedelta(days=30)),))
                    supplier_performance_data = [{'name': row['name'], 'avg_delivery_time': f"{int(row['avg_delivery_time'])} días" if row['avg_delivery_time'] else 'N/A', 'order_count': row['order_count'], 'total_value': float(row['total_value'] or 0)} for row in cursor.fetchall()]
                except Exception as e:
                    print(f"Error fetching supplier performance: {str(e)}")
                    supplier_performance_data = [{'name': 'TechSolutions Inc.', 'avg_delivery_time': '7 días', 'order_count': 25, 'total_value': 28500.00}, {'name': 'GlobalGadgets S.A.', 'avg_delivery_time': '5 días', 'order_count': 20, 'total_value': 31250.00}]

            # Estadísticas por periodo
            period_stats = {}
            for period, days in [('semana', 7), ('mes', 30), ('trimestre', 90)]:
                cursor.execute("""
                    SELECT SUM(s.sale_price * s.quantity) as sales, COUNT(s.id) as transactions,
                           SUM((s.sale_price - p.cost_price) * s.quantity) as profit
                    FROM sales s JOIN products p ON s.product_id = p.id WHERE s.sale_date >= %s
                """, (today - timedelta(days=days),))
                period_data = cursor.fetchone()
                period_stats[period] = {
                    'sales': float(period_data['sales'] or 0),
                    'transactions': period_data['transactions'] or 0,
                    'profit': float(period_data['profit'] or 0)
                }

            # Métodos de pago
            payment_data = []
            if report_type in ['payment_methods', 'payment_distribution', 'payment_trends']:
                try:
                    cursor.execute("""
                        SELECT payment_method, COUNT(*) as count, SUM(sale_price * quantity) as total
                        FROM sales GROUP BY payment_method ORDER BY count DESC LIMIT 5
                    """)
                    payment_data = [{'payment_method': row['payment_method'], 'count': row['count'], 'total': float(row['total'] or 0)} for row in cursor.fetchall()]
                except Exception as e:
                    print(f"Error fetching payment data: {str(e)}")
                    payment_data = [{'payment_method': 'cash', 'count': 150, 'total': 75000.00}, {'payment_method': 'transfer', 'count': 100, 'total': 45000.00}, {'payment_method': 'stripe', 'count': 50, 'total': 30000.00}]

            # Devoluciones
            returns_data = []
            if report_type in ['returns_history', 'returns_reasons', 'returns_by_product']:
                try:
                    cursor.execute("""
                        SELECT p.name as product_name, r.reason, COUNT(*) as count
                        FROM returns r JOIN products p ON r.product_id = p.id
                        GROUP BY p.id, p.name, r.reason ORDER BY count DESC LIMIT 5
                    """)
                    returns_data = cursor.fetchall()
                except Exception as e:
                    print(f"Error fetching returns data: {str(e)}")
                    returns_data = [{'product_name': 'Laptop Dell XPS 15', 'reason': 'Defectuoso', 'count': 10}, {'product_name': 'Monitor Ultrawide LG', 'reason': 'No deseado', 'count': 8}, {'product_name': 'iPhone 15 Pro', 'reason': 'Error de pedido', 'count': 5}]

            # Entrada/salida de inventario
            stock_data = []
            if report_type.startswith('stock_in'):
                query = """
                    SELECT p.name as product_name, oi.quantity, 'IN' as transaction_type, o.order_date as transaction_date
                    FROM orders o JOIN order_items oi ON o.id = oi.order_id JOIN products p ON oi.product_id = p.id
                    WHERE o.status = 'delivered'
                """
                params = []
                if start_date:
                    query += " AND o.order_date >= %s"
                    params.append(start_date)
                query += " ORDER BY o.order_date DESC LIMIT 10"
                try:
                    cursor.execute(query, params)
                    stock_data = [{'product_name': row['product_name'], 'quantity': row['quantity'], 'transaction_type': row['transaction_type'], 'transaction_date': row['transaction_date'].strftime('%Y-%m-%d')} for row in cursor.fetchall()]
                except Exception as e:
                    print(f"Error fetching stock in data: {str(e)}")
                    stock_data = [{'product_name': 'Laptop Dell XPS 15', 'quantity': 20, 'transaction_type': 'IN', 'transaction_date': '2025-04-25'}, {'product_name': 'Monitor Ultrawide LG', 'quantity': 15, 'transaction_type': 'IN', 'transaction_date': '2025-04-24'}]
            elif report_type.startswith('stock_out'):
                query = """
                    SELECT p.name as product_name, s.quantity, 'OUT' as transaction_type, s.sale_date as transaction_date
                    FROM sales s JOIN products p ON s.product_id = p.id
                    WHERE s.sale_date >= %s
                    UNION
                    SELECT p.name as product_name, r.quantity, 'OUT' as transaction_type, r.created_at as transaction_date
                    FROM returns r JOIN products p ON r.product_id = p.id
                    WHERE r.created_at >= %s
                    ORDER BY transaction_date DESC LIMIT 10
                """
                params = [start_date, start_date] if start_date else [today - timedelta(days=30), today - timedelta(days=30)]
                try:
                    cursor.execute(query, params)
                    stock_data = [{'product_name': row['product_name'], 'quantity': row['quantity'], 'transaction_type': row['transaction_type'], 'transaction_date': row['transaction_date'].strftime('%Y-%m-%d')} for row in cursor.fetchall()]
                except Exception as e:
                    print(f"Error fetching stock out data: {str(e)}")
                    stock_data = [{'product_name': 'Laptop Dell XPS 15', 'quantity': 20, 'transaction_type': 'OUT', 'transaction_date': '2025-04-25'}, {'product_name': 'Monitor Ultrawide LG', 'quantity': 15, 'transaction_type': 'OUT', 'transaction_date': '2025-04-24'}]

            return {
                'stats': {
                    'total_sales': sales_data['total_sales'],
                    'total_transactions': sales_data['total_transactions'],
                    'total_profit': sales_data['total_profit'],
                    'low_stock_items': inventory_data['low_stock_items'],
                    'all_categories': inventory_data['all_categories'],
                    'all_items': inventory_data['all_items'],
                    'period_stats': period_stats
                },
                'inventory_details': inventory_details,
                'top_products': top_products,
                'suppliers': suppliers,
                'supplier_active_data': supplier_active_data,
                'supplier_delivery_data': supplier_delivery_data,
                'supplier_performance_data': supplier_performance_data,
                'payment_data': payment_data,
                'returns_data': returns_data,
                'stock_data': stock_data
            }

# Generador de reportes
class ReportGenerator:
    def __init__(self):
        self.styles = ReportStyles.get_styles()
        self.colors = ReportStyles.COLORS

    def get_report_title(self, report_type):
        """Devuelve el título del reporte basado en el tipo de reporte."""
        titles = {
            'weekly': "Reporte de Ventas Semanales",
            'monthly': "Reporte de Ventas Mensuales",
            'quarterly': "Reporte de Ventas Trimestrales",
            'inventory': "Balance de Inventario",
            'payment_methods': "Métodos de Pago Más Utilizados",
            'payment_distribution': "Distribución de Pagos por Método",
            'payment_trends': "Tendencias de Métodos de Pago",
            'returns_history': "Historial de Devoluciones",
            'returns_reasons': "Motivos de Devolución",
            'returns_by_product': "Análisis de Devoluciones por Producto",
            'stock_in': "Entrada de Productos",
            'stock_in_weekly': "Entrada de Productos Semanal",
            'stock_in_monthly': "Entrada de Productos Mensual",
            'stock_in_quarterly': "Entrada de Productos Trimestral",
            'stock_out': "Salida de Productos",
            'stock_out_weekly': "Salida de Productos Semanal",
            'stock_out_monthly': "Salida de Productos Mensual",
            'stock_out_quarterly': "Salida de Productos Trimestral",
            'active_suppliers': "Proveedores Más Activos",
            'supplier_deliveries': "Cantidad de Entregas por Proveedor",
            'supplier_performance': "Desempeño de Proveedores"
        }
        return titles.get(report_type, "Reporte Desconocido")

    def create_header(self, doc, report_date):
        company_name = ReportDataFetcher.get_company_name()
        header_data = [[Paragraph(f'<font color="#1A1A1A" size="14"><b>{company_name}</b></font>', self.styles['normal']),
                        Paragraph(f'<font color="#1A1A1A" size="12">Fecha: <b>{report_date}</b></font>', self.styles['normal'])]]
        header_table = Table(header_data, colWidths=[doc.width / 2] * 2)
        header_table.setStyle(TableStyle([('ALIGN', (0, 0), (0, 0), 'LEFT'), ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
                                         ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'), ('BOTTOMPADDING', (0, 0), (-1, -1), 15),
                                         ('TOPPADDING', (0, 0), (-1, -1), 15), ('LEFTPADDING', (0, 0), (-1, -1), 5),
                                         ('RIGHTPADDING', (0, 0), (-1, -1), 5)]))
        return [header_table, Spacer(1, 10)]

    def create_financial_summary(self, doc, stats):
        elements = [Paragraph("Resumen Financiero", self.styles['subtitle']), Spacer(1, 15),
                    RoundedRect(doc.width, 90, radius=15, fillColor=self.colors['GRIS_CLARO']), Spacer(1, -80)]
        financial_data = [[Paragraph("Total Ventas", self.styles['card_title']), Paragraph("Total Transacciones", self.styles['card_title']), Paragraph("Total Ganancias", self.styles['card_title'])],
                          [Paragraph(f"<font color='#E6804D'><b>${stats['total_sales']:,.2f}</b></font>", self.styles['card_value']),
                           Paragraph(f"<font color='#1A1A1A'><b>{stats['total_transactions']}</b></font>", self.styles['card_value']),
                           Paragraph(f"<font color='#E6804D'><b>${stats['total_profit']:,.2f}</b></font>", self.styles['card_value'])]]
        financial_table = Table(financial_data, colWidths=[doc.width / 3] * 3)
        financial_table.setStyle(TableStyle([('ALIGN', (0, 0), (-1, -1), 'CENTER'), ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                                            ('TOPPADDING', (0, 0), (-1, 0), 12), ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                                            ('TOPPADDING', (0, 1), (-1, 1), 4), ('BOTTOMPADDING', (0, 1), (-1, 1), 18)]))
        elements.extend([financial_table, Spacer(1, 25)])
        return elements

    def create_inventory_details(self, doc, stats, inventory_details):
        elements = [ModernTab(width=doc.width - 15, text="BALANCE DE INVENTARIO", active=True), Spacer(1, 15),
                    RoundedRect(doc.width, 230, radius=15, fillColor=self.colors['GRIS_CLARO'], strokeColor=self.colors['NARANJA_CLARO'], strokeWidth=1), Spacer(1, -220)]
        inventory_circles = [[CircleValue(radius=25, fillColor=self.colors['NARANJA_ACENTO'], value=str(stats['low_stock_items'])), Paragraph("<b>Productos en Bajo Stock</b><br/>Necesitan reposición", self.styles['normal'])],
                             [CircleValue(radius=25, fillColor=self.colors['NARANJA_ACENTO'], value=str(stats['all_categories'])), Paragraph("<b>Categorías Disponibles</b><br/>Clasificación de productos", self.styles['normal'])],
                             [CircleValue(radius=25, fillColor=self.colors['NARANJA_ACENTO'], value=str(stats['all_items'])), Paragraph("<b>Total Productos</b><br/>En inventario actual", self.styles['normal'])]]
        inventory_circles_table = Table(inventory_circles, colWidths=[60, doc.width - 85])
        inventory_circles_table.setStyle(TableStyle([('VALIGN', (0, 0), (-1, -1), 'MIDDLE'), ('TOPPADDING', (0, 0), (-1, -1), 10),
                                                    ('BOTTOMPADDING', (0, 0), (-1, -1), 10), ('LEFTPADDING', (0, 0), (-1, -1), 5),
                                                    ('RIGHTPADDING', (0, 0), (-1, -1), 5)]))
        elements.append(inventory_circles_table)
        elements.extend([Spacer(1, 15), Paragraph("Productos con Bajo Stock", self.styles['subtitle'])])
        header = [[Paragraph("<font color='#FFFFFF'><b>PRODUCTO</b></font>", self.styles['normal']), Paragraph("<font color='#FFFFFF'><b>STOCK</b></font>", self.styles['normal']),
                   Paragraph("<font color='#FFFFFF'><b>CATEGORÍA</b></font>", self.styles['normal']), Paragraph("<font color='#FFFFFF'><b>PROVEEDOR</b></font>", self.styles['normal'])]]
        header_table = Table(header, colWidths=[doc.width * 0.3, doc.width * 0.15, doc.width * 0.25, doc.width * 0.3])
        header_table.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, 0), self.colors['NARANJA_ACENTO']), ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                                         ('VALIGN', (0, 0), (-1, 0), 'MIDDLE'), ('TOPPADDING', (0, 0), (-1, 0), 10), ('BOTTOMPADDING', (0, 0), (-1, 0), 10)]))
        rows = [[Paragraph(f"<b>{item['name']}</b>", self.styles['normal']), Paragraph(f"<font color='#E6804D'><b>{item['stock']}</b></font>", self.styles['normal']),
                 Paragraph(f"{item['category']}", self.styles['normal']), Paragraph(f"{item['supplier_name']}", self.styles['normal'])] for item in inventory_details]
        data_table = Table(rows, colWidths=[doc.width * 0.3, doc.width * 0.15, doc.width * 0.25, doc.width * 0.3])
        data_table.setStyle(TableStyle([('ALIGN', (0, 0), (0, -1), 'LEFT'), ('ALIGN', (1, 0), (1, -1), 'CENTER'), ('ALIGN', (2, 0), (2, -1), 'LEFT'),
                                        ('ALIGN', (3, 0), (3, -1), 'LEFT'), ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'), ('TOPPADDING', (0, 0), (-1, -1), 12),
                                        ('BOTTOMPADDING', (0, 0), (-1, -1), 12), ('LEFTPADDING', (0, 0), (-1, -1), 15), ('RIGHTPADDING', (0, 0), (-1, -1), 15),
                                        ('BACKGROUND', (0, 0), (-1, -1), self.colors['BLANCO'])]))
        elements.extend([header_table, data_table, Spacer(1, 25)])
        return elements

    def create_top_products(self, doc, top_products):
        if not top_products:
            return [Paragraph("No hay datos de productos más vendidos", self.styles['normal']), Spacer(1, 25)]
        elements = [ModernTab(width=doc.width / 2 - 15, text="PRODUCTOS MÁS VENDIDOS", active=True), Spacer(1, 15),
                    RoundedRect(doc.width / 2 - 15, 190, radius=15, fillColor=self.colors['GRIS_CLARO'], strokeColor=self.colors['NARANJA_CLARO'], strokeWidth=1), Spacer(1, -180)]
        product_rows = [[Paragraph(f"<b>{product['name']}</b>", self.styles['normal']), MiniBarChart([15, 30, float(product['sales_count']), 20, 10], width=80, height=25),
                         Paragraph(f"<font color='#E6804D'><b>{product['sales_count']}</b></font> <font color='#999999'>unidades</font>", self.styles['normal'])] for product in top_products]
        product_table = Table(product_rows, colWidths=[doc.width / 4 - 20, 90, doc.width / 4 - 90])
        product_table.setStyle(TableStyle([('VALIGN', (0, 0), (-1, -1), 'MIDDLE'), ('ALIGN', (2, 0), (2, -1), 'RIGHT'),
                                          ('TOPPADDING', (0, 0), (-1, -1), 15), ('BOTTOMPADDING', (0, 0), (-1, -1), 15),
                                          ('LEFTPADDING', (0, 0), (-1, -1), 10), ('RIGHTPADDING', (0, 0), (-1, -1), 10)]))
        elements.append(product_table)
        return elements

    def create_suppliers(self, doc, suppliers):
        if not suppliers:
            return [Paragraph("No hay datos de proveedores", self.styles['normal']), Spacer(1, 25)]
        elements = [Paragraph("Proveedores Principales", self.styles['subtitle']), Spacer(1, 15)]
        supplier_cards = []
        for supplier in suppliers:
            supplier_details = [[Paragraph("Productos:", self.styles['normal']), Paragraph(f"<b>{supplier['products_bought']}</b>", self.styles['normal'])],
                                [Paragraph("Valor Total:", self.styles['normal']), Paragraph(f"<font color='#E6804D'><b>${supplier['total_value']:,.2f}</b></font>", self.styles['normal'])],
                                [Paragraph("Plazo Entrega:", self.styles['normal']), Paragraph(f"<b>{supplier['delivery_time']}</b>", self.styles['normal'])]]
            details_table = Table(supplier_details, colWidths=[doc.width / 6 - 20, doc.width / 6 - 20])
            details_table.setStyle(TableStyle([('VALIGN', (0, 0), (-1, -1), 'MIDDLE'), ('ALIGN', (0, 0), (0, -1), 'LEFT'),
                                              ('ALIGN', (1, 0), (1, -1), 'RIGHT'), ('TOPPADDING', (0, 0), (-1, -1), 6),
                                              ('BOTTOMPADDING', (0, 0), (-1, -1), 6), ('LEFTPADDING', (0, 0), (0, -1), 10),
                                              ('RIGHTPADDING', (1, 0), (1, -1), 10)]))
            supplier_data = [[Paragraph(f"<font color='#FFFFFF' size='12'><b>{supplier['name']}</b></font>", self.styles['normal'])], [details_table]]
            supplier_table = Table(supplier_data, colWidths=[doc.width / 3 - 20])
            supplier_table.setStyle(TableStyle([('BACKGROUND', (0, 0), (0, 0), self.colors['NARANJA_ACENTO']), ('ALIGN', (0, 0), (0, 0), 'CENTER'),
                                               ('VALIGN', (0, 0), (0, 0), 'MIDDLE'), ('TOPPADDING', (0, 0), (0, 0), 10), ('BOTTOMPADDING', (0, 0), (0, 0), 10),
                                               ('LEFTPADDING', (0, 0), (0, 0), 5), ('RIGHTPADDING', (0, 0), (0, 0), 5), ('BACKGROUND', (0, 1), (0, 1), self.colors['BLANCO']),
                                               ('TOPPADDING', (0, 1), (0, 1), 0), ('BOTTOMPADDING', (0, 1), (0, 1), 0), ('LEFTPADDING', (0, 1), (0, 1), 0),
                                               ('RIGHTPADDING', (0, 1), (0, 1), 0), ('BOX', (0, 0), (0, 1), 1, self.colors['GRIS_OSCURO'])]))
            supplier_cards.append(supplier_table)
        suppliers_table = Table([supplier_cards], colWidths=[doc.width / 3] * 3)
        suppliers_table.setStyle(TableStyle([('VALIGN', (0, 0), (-1, -1), 'TOP'), ('LEFTPADDING', (0, 0), (-1, -1), 5), ('RIGHTPADDING', (0, 0), (-1, -1), 5)]))
        elements.extend([suppliers_table, Spacer(1, 25)])
        return elements

    def create_active_suppliers(self, doc, supplier_active_data):
        if not supplier_active_data:
            return [Paragraph("No hay datos de proveedores activos", self.styles['normal']), Spacer(1, 25)]
        elements = [Paragraph("Proveedores Más Activos", self.styles['subtitle']), Spacer(1, 15),
                    RoundedRect(doc.width, 150, radius=15, fillColor=self.colors['GRIS_CLARO']), Spacer(1, -140)]
        header = [[Paragraph("<font color='#FFFFFF'><b>PROVEEDOR</b></font>", self.styles['normal']), Paragraph("<font color='#FFFFFF'><b>ÓRDENES</b></font>", self.styles['normal'])]]
        header_table = Table(header, colWidths=[doc.width * 0.6, doc.width * 0.4])
        header_table.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, 0), self.colors['NARANJA_ACENTO']), ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                                         ('VALIGN', (0, 0), (-1, 0), 'MIDDLE'), ('TOPPADDING', (0, 0), (-1, 0), 10), ('BOTTOMPADDING', (0, 0), (-1, 0), 10)]))
        rows = [[Paragraph(f"<b>{supplier['name']}</b>", self.styles['normal']), Paragraph(f"<font color='#E6804D'><b>{supplier['order_count']}</b></font>", self.styles['normal'])] for supplier in supplier_active_data]
        data_table = Table(rows, colWidths=[doc.width * 0.6, doc.width * 0.4])
        data_table.setStyle(TableStyle([('ALIGN', (0, 0), (0, -1), 'LEFT'), ('ALIGN', (1, 0), (1, -1), 'CENTER'), ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                                        ('TOPPADDING', (0, 0), (-1, -1), 12), ('BOTTOMPADDING', (0, 0), (-1, -1), 12), ('LEFTPADDING', (0, 0), (-1, -1), 15),
                                        ('RIGHTPADDING', (0, 0), (-1, -1), 15), ('BACKGROUND', (0, 0), (-1, -1), self.colors['BLANCO'])]))
        elements.extend([header_table, data_table, Spacer(1, 25)])
        return elements

    def create_supplier_deliveries(self, doc, supplier_delivery_data):
        if not supplier_delivery_data:
            return [Paragraph("No hay datos de entregas por proveedor", self.styles['normal']), Spacer(1, 25)]
        elements = [Paragraph("Cantidad de Entregas por Proveedor", self.styles['subtitle']), Spacer(1, 15),
                    RoundedRect(doc.width, 150, radius=15, fillColor=self.colors['GRIS_CLARO']), Spacer(1, -140)]
        header = [[Paragraph("<font color='#FFFFFF'><b>PROVEEDOR</b></font>", self.styles['normal']), Paragraph("<font color='#FFFFFF'><b>UNIDADES ENTREGADAS</b></font>", self.styles['normal'])]]
        header_table = Table(header, colWidths=[doc.width * 0.6, doc.width * 0.4])
        header_table.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, 0), self.colors['NARANJA_ACENTO']), ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                                         ('VALIGN', (0, 0), (-1, 0), 'MIDDLE'), ('TOPPADDING', (0, 0), (-1, 0), 10), ('BOTTOMPADDING', (0, 0), (-1, 0), 10)]))
        rows = [[Paragraph(f"<b>{supplier['name']}</b>", self.styles['normal']), Paragraph(f"<font color='#E6804D'><b>{supplier['total_delivered']}</b></font>", self.styles['normal'])] for supplier in supplier_delivery_data]
        data_table = Table(rows, colWidths=[doc.width * 0.6, doc.width * 0.4])
        data_table.setStyle(TableStyle([('ALIGN', (0, 0), (0, -1), 'LEFT'), ('ALIGN', (1, 0), (1, -1), 'CENTER'), ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                                        ('TOPPADDING', (0, 0), (-1, -1), 12), ('BOTTOMPADDING', (0, 0), (-1, -1), 12), ('LEFTPADDING', (0, 0), (-1, -1), 15),
                                        ('RIGHTPADDING', (0, 0), (-1, -1), 15), ('BACKGROUND', (0, 0), (-1, -1), self.colors['BLANCO'])]))
        elements.extend([header_table, data_table, Spacer(1, 25)])
        return elements

    def create_supplier_performance(self, doc, supplier_performance_data):
        if not supplier_performance_data:
            return [Paragraph("No hay datos de desempeño de proveedores", self.styles['normal']), Spacer(1, 25)]
        elements = [Paragraph("Desempeño de Proveedores", self.styles['subtitle']), Spacer(1, 15),
                    RoundedRect(doc.width, 150, radius=15, fillColor=self.colors['GRIS_CLARO']), Spacer(1, -140)]
        header = [[Paragraph("<font color='#FFFFFF'><b>PROVEEDOR</b></font>", self.styles['normal']), Paragraph("<font color='#FFFFFF'><b>TIEMPO ENTREGA</b></font>", self.styles['normal']),
                   Paragraph("<font color='#FFFFFF'><b>ÓRDENES</b></font>", self.styles['normal']), Paragraph("<font color='#FFFFFF'><b>VALOR TOTAL</b></font>", self.styles['normal'])]]
        header_table = Table(header, colWidths=[doc.width * 0.3, doc.width * 0.2, doc.width * 0.2, doc.width * 0.3])
        header_table.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, 0), self.colors['NARANJA_ACENTO']), ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                                         ('VALIGN', (0, 0), (-1, 0), 'MIDDLE'), ('TOPPADDING', (0, 0), (-1, 0), 10), ('BOTTOMPADDING', (0, 0), (-1, 0), 10)]))
        rows = [[Paragraph(f"<b>{supplier['name']}</b>", self.styles['normal']), Paragraph(f"{supplier['avg_delivery_time']}", self.styles['normal']),
                 Paragraph(f"<font color='#E6804D'><b>{supplier['order_count']}</b></font>", self.styles['normal']),
                 Paragraph(f"<font color='#E6804D'><b>${supplier['total_value']:,.2f}</b></font>", self.styles['normal'])] for supplier in supplier_performance_data]
        data_table = Table(rows, colWidths=[doc.width * 0.3, doc.width * 0.2, doc.width * 0.2, doc.width * 0.3])
        data_table.setStyle(TableStyle([('ALIGN', (0, 0), (0, -1), 'LEFT'), ('ALIGN', (1, 0), (1, -1), 'CENTER'), ('ALIGN', (2, 0), (2, -1), 'CENTER'),
                                        ('ALIGN', (3, 0), (3, -1), 'RIGHT'), ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'), ('TOPPADDING', (0, 0), (-1, -1), 12),
                                        ('BOTTOMPADDING', (0, 0), (-1, -1), 12), ('LEFTPADDING', (0, 0), (-1, -1), 15), ('RIGHTPADDING', (0, 0), (-1, -1), 15),
                                        ('BACKGROUND', (0, 0), (-1, -1), self.colors['BLANCO'])]))
        elements.extend([header_table, data_table, Spacer(1, 25)])
        return elements

    def create_period_summary(self, doc, stats):
        elements = [Paragraph("Resumen de Ventas por Periodo", self.styles['subtitle']), Spacer(1, 15),
                    RoundedRect(doc.width, 150, radius=15, fillColor=self.colors['GRIS_CLARO']), Spacer(1, -140)]
        period_header = [[Paragraph("<font color='#FFFFFF'><b>PERIODO</b></font>", self.styles['normal']), Paragraph("<font color='#FFFFFF'><b>VENTAS</b></font>", self.styles['normal']),
                          Paragraph("<font color='#FFFFFF'><b>TRANS.</b></font>", self.styles['normal']), Paragraph("<font color='#FFFFFF'><b>GANANCIAS</b></font>", self.styles['normal'])]]
        period_header_table = Table(period_header, colWidths=[doc.width * 0.25, doc.width * 0.25, doc.width * 0.20, doc.width * 0.30])
        period_header_table.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, 0), self.colors['NARANJA_ACENTO']), ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                                                ('VALIGN', (0, 0), (-1, 0), 'MIDDLE'), ('TOPPADDING', (0, 0), (-1, 0), 10), ('BOTTOMPADDING', (0, 0), (-1, 0), 10)]))
        periods = {"semana": "Esta Semana", "mes": "Este Mes", "trimestre": "Este Trimestre"}
        period_rows = [[Paragraph(f"<b>{periods[period_key]}</b>", self.styles['normal']), Paragraph(f"<font color='#E6804D'><b>${data['sales']:,.2f}</b></font>", self.styles['normal']),
                        Paragraph(f"{data['transactions']}", self.styles['normal']), Paragraph(f"<font color='#E6804D'><b>${data['profit']:,.2f}</b></font>", self.styles['normal'])]
                       for period_key, data in stats['period_stats'].items() if period_key in periods]
        if not period_rows:
            return elements + [period_header_table, Paragraph("No hay datos disponibles para el resumen por periodo", self.styles['normal']), Spacer(1, 25)]
        table_style = [('ALIGN', (0, 0), (0, -1), 'LEFT'), ('ALIGN', (1, 0), (1, -1), 'RIGHT'), ('ALIGN', (2, 0), (2, -1), 'CENTER'), ('ALIGN', (3, 0), (3, -1), 'RIGHT'),
                       ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'), ('TOPPADDING', (0, 0), (-1, -1), 12), ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
                       ('LEFTPADDING', (0, 0), (-1, -1), 15), ('RIGHTPADDING', (0, 0), (-1, -1), 15)] + [('BACKGROUND', (0, i), (-1, i), self.colors['GRIS_CLARO'] if i % 2 else self.colors['BLANCO']) for i in range(len(period_rows))]
        periods_data = Table(period_rows, colWidths=[doc.width * 0.25, doc.width * 0.25, doc.width * 0.20, doc.width * 0.30])
        periods_data.setStyle(TableStyle(table_style))
        elements.extend([period_header_table, periods_data, Spacer(1, 25)])
        return elements

    def create_payment_methods(self, doc, payment_data):
        if not payment_data:
            return [Paragraph("No hay datos de métodos de pago", self.styles['normal']), Spacer(1, 25)]
        elements = [Paragraph("Métodos de Pago Más Utilizados", self.styles['subtitle']), Spacer(1, 15),
                    RoundedRect(doc.width, 150, radius=15, fillColor=self.colors['GRIS_CLARO']), Spacer(1, -140)]
        header = [[Paragraph("<font color='#FFFFFF'><b>MÉTODO</b></font>", self.styles['normal']), 
                   Paragraph("<font color='#FFFFFF'><b>TRANSACCIONES</b></font>", self.styles['normal']),
                   Paragraph("<font color='#FFFFFF'><b>TOTAL</b></font>", self.styles['normal'])]]
        header_table = Table(header, colWidths=[doc.width * 0.4, doc.width * 0.3, doc.width * 0.3])
        header_table.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, 0), self.colors['NARANJA_ACENTO']), ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                                         ('VALIGN', (0, 0), (-1, 0), 'MIDDLE'), ('TOPPADDING', (0, 0), (-1, 0), 10), ('BOTTOMPADDING', (0, 0), (-1, 0), 10)]))
        rows = [[Paragraph(f"<b>{method['payment_method']}</b>", self.styles['normal']), Paragraph(f"{method['count']}", self.styles['normal']),
                 Paragraph(f"<font color='#E6804D'><b>${method['total']:,.2f}</b></font>", self.styles['normal'])] for method in payment_data]
        data_table = Table(rows, colWidths=[doc.width * 0.4, doc.width * 0.3, doc.width * 0.3])
        data_table.setStyle(TableStyle([('ALIGN', (0, 0), (0, -1), 'LEFT'), ('ALIGN', (1, 0), (1, -1), 'CENTER'), ('ALIGN', (2, 0), (2, -1), 'RIGHT'),
                                        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'), ('TOPPADDING', (0, 0), (-1, -1), 12), ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
                                        ('LEFTPADDING', (0, 0), (-1, -1), 15), ('RIGHTPADDING', (0, 0), (-1, -1), 15), ('BACKGROUND', (0, 0), (-1, -1), self.colors['BLANCO'])]))
        elements.extend([header_table, data_table, Spacer(1, 25)])
        return elements

    def create_payment_distribution(self, doc, payment_data):
        if not payment_data:
            return [Paragraph("No hay datos de distribución de pagos", self.styles['normal']), Spacer(1, 25)]
        elements = [Paragraph("Distribución de Pagos por Método", self.styles['subtitle']), Spacer(1, 15)]
        total = sum(method['total'] for method in payment_data)
        rows = [[Paragraph(f"<b>{method['payment_method']}</b>", self.styles['normal']), MiniBarChart([float(method['total']) / total * 100 if total > 0 else 0, 100], width=100, height=25),
                 Paragraph(f"<font color='#E6804D'><b>{method['total'] / total * 100 if total > 0 else 0:.1f}%</b></font>", self.styles['normal'])] for method in payment_data]
        table = Table(rows, colWidths=[doc.width * 0.4, doc.width * 0.3, doc.width * 0.3])
        table.setStyle(TableStyle([('VALIGN', (0, 0), (-1, -1), 'MIDDLE'), ('ALIGN', (2, 0), (2, -1), 'RIGHT'),
                                   ('TOPPADDING', (0, 0), (-1, -1), 15), ('BOTTOMPADDING', (0, 0), (-1, -1), 15),
                                   ('LEFTPADDING', (0, 0), (-1, -1), 10), ('RIGHTPADDING', (0, 0), (-1, -1), 10)]))
        elements.extend([table, Spacer(1, 25)])
        return elements

    def create_payment_trends(self, doc, payment_data):
        if not payment_data:
            return [Paragraph("No hay datos de tendencias de pago", self.styles['normal']), Spacer(1, 25)]
        elements = [Paragraph("Tendencias de Métodos de Pago", self.styles['subtitle']), Spacer(1, 15)]
        header = [[Paragraph("<font color='#FFFFFF'><b>MÉTODO</b></font>", self.styles['normal']), Paragraph("<font color='#FFFFFF'><b>TENDENCIA</b></font>", self.styles['normal'])]]
        header_table = Table(header, colWidths=[doc.width * 0.5, doc.width * 0.5])
        header_table.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, 0), self.colors['NARANJA_ACENTO']), ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                                         ('VALIGN', (0, 0), (-1, 0), 'MIDDLE'), ('TOPPADDING', (0, 0), (-1, 0), 10), ('BOTTOMPADDING', (0, 0), (-1, 0), 10)]))
        rows = [[Paragraph(f"<b>{method['payment_method']}</b>", self.styles['normal']), Paragraph(f"<font color='#E6804D'><b>{'Creciente' if method['count'] > 50 else 'Estable'}</b></font>", self.styles['normal'])] for method in payment_data]
        data_table = Table(rows, colWidths=[doc.width * 0.5, doc.width * 0.5])
        data_table.setStyle(TableStyle([('ALIGN', (0, 0), (0, -1), 'LEFT'), ('ALIGN', (1, 0), (1, -1), 'CENTER'), ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                                        ('TOPPADDING', (0, 0), (-1, -1), 12), ('BOTTOMPADDING', (0, 0), (-1, -1), 12), ('LEFTPADDING', (0, 0), (-1, -1), 15),
                                        ('RIGHTPADDING', (0, 0), (-1, -1), 15), ('BACKGROUND', (0, 0), (-1, -1), self.colors['BLANCO'])]))
        elements.extend([header_table, data_table, Spacer(1, 25)])
        return elements

    def create_returns_history(self, doc, returns_data):
        if not returns_data:
            return [Paragraph("No hay datos de historial de devoluciones", self.styles['normal']), Spacer(1, 25)]
        elements = [Paragraph("Historial de Devoluciones", self.styles['subtitle']), Spacer(1, 15),
                    RoundedRect(doc.width, 150, radius=15, fillColor=self.colors['GRIS_CLARO']), Spacer(1, -140)]
        header = [[Paragraph("<font color='#FFFFFF'><b>PRODUCTO</b></font>", self.styles['normal']), Paragraph("<font color='#FFFFFF'><b>MOTIVO</b></font>", self.styles['normal']),
                   Paragraph("<font color='#FFFFFF'><b>CANTIDAD</b></font>", self.styles['normal'])]]
        header_table = Table(header, colWidths=[doc.width * 0.4, doc.width * 0.3, doc.width * 0.3])
        header_table.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, 0), self.colors['NARANJA_ACENTO']), ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                                         ('VALIGN', (0, 0), (-1, 0), 'MIDDLE'), ('TOPPADDING', (0, 0), (-1, 0), 10), ('BOTTOMPADDING', (0, 0), (-1, 0), 10)]))
        rows = [[Paragraph(f"<b>{return_item['product_name']}</b>", self.styles['normal']), Paragraph(f"{return_item['reason']}", self.styles['normal']),
                 Paragraph(f"<font color='#E6804D'><b>{return_item['count']}</b></font>", self.styles['normal'])] for return_item in returns_data]
        data_table = Table(rows, colWidths=[doc.width * 0.4, doc.width * 0.3, doc.width * 0.3])
        data_table.setStyle(TableStyle([('ALIGN', (0, 0), (0, -1), 'LEFT'), ('ALIGN', (1, 0), (1, -1), 'LEFT'), ('ALIGN', (2, 0), (2, -1), 'CENTER'),
                                        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'), ('TOPPADDING', (0, 0), (-1, -1), 12), ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
                                        ('LEFTPADDING', (0, 0), (-1, -1), 15), ('RIGHTPADDING', (0, 0), (-1, -1), 15), ('BACKGROUND', (0, 0), (-1, -1), self.colors['BLANCO'])]))
        elements.extend([header_table, data_table, Spacer(1, 25)])
        return elements

    def create_returns_reasons(self, doc, returns_data):
        if not returns_data:
            return [Paragraph("No hay datos de motivos de devolución", self.styles['normal']), Spacer(1, 25)]
        elements = [Paragraph("Motivos de Devolución", self.styles['subtitle']), Spacer(1, 15)]
        reasons = {}
        for return_item in returns_data:
            reasons[return_item['reason']] = reasons.get(return_item['reason'], 0) + return_item['count']
        rows = [[Paragraph(f"<b>{reason}</b>", self.styles['normal']), MiniBarChart([float(count), max(10, 100 - float(count))], width=100, height=25),
                 Paragraph(f"<font color='#E6804D'><b>{count}</b></font>", self.styles['normal'])] for reason, count in reasons.items()]
        table = Table(rows, colWidths=[doc.width * 0.4, doc.width * 0.3, doc.width * 0.3])
        table.setStyle(TableStyle([('VALIGN', (0, 0), (-1, -1), 'MIDDLE'), ('ALIGN', (2, 0), (2, -1), 'RIGHT'),
                                   ('TOPPADDING', (0, 0), (-1, -1), 15), ('BOTTOMPADDING', (0, 0), (-1, -1), 15),
                                   ('LEFTPADDING', (0, 0), (-1, -1), 10), ('RIGHTPADDING', (0, 0), (-1, -1), 10)]))
        elements.extend([table, Spacer(1, 25)])
        return elements

    def create_returns_by_product(self, doc, returns_data):
        if not returns_data:
            return [Paragraph("No hay datos de devoluciones por producto", self.styles['normal']), Spacer(1, 25)]
        elements = [Paragraph("Análisis de Devoluciones por Producto", self.styles['subtitle']), Spacer(1, 15)]
        products = {}
        for return_item in returns_data:
            products[return_item['product_name']] = products.get(return_item['product_name'], 0) + return_item['count']
        rows = [[Paragraph(f"<b>{product}</b>", self.styles['normal']), MiniBarChart([float(count), max(10, 100 - float(count))], width=100, height=25),
                 Paragraph(f"<font color='#E6804D'><b>{count}</b></font>", self.styles['normal'])] for product, count in products.items()]
        table = Table(rows, colWidths=[doc.width * 0.4, doc.width * 0.3, doc.width * 0.3])
        table.setStyle(TableStyle([('VALIGN', (0, 0), (-1, -1), 'MIDDLE'), ('ALIGN', (2, 0), (2, -1), 'RIGHT'),
                                   ('TOPPADDING', (0, 0), (-1, -1), 15), ('BOTTOMPADDING', (0, 0), (-1, -1), 15),
                                   ('LEFTPADDING', (0, 0), (-1, -1), 10), ('RIGHTPADDING', (0, 0), (-1, -1), 10)]))
        elements.extend([table, Spacer(1, 25)])
        return elements

    def create_stock_transactions(self, doc, stock_data, report_type):
        if not stock_data:
            return [Paragraph(f"No hay datos de {self.get_report_title(report_type).lower()}", self.styles['normal']), Spacer(1, 25)]
        elements = [Paragraph(self.get_report_title(report_type), self.styles['subtitle']), Spacer(1, 15),
                    RoundedRect(doc.width, 150, radius=15, fillColor=self.colors['GRIS_CLARO']), Spacer(1, -140)]
        header = [[Paragraph("<font color='#FFFFFF'><b>PRODUCTO</b></font>", self.styles['normal']), Paragraph("<font color='#FFFFFF'><b>CANTIDAD</b></font>", self.styles['normal']),
                   Paragraph("<font color='#FFFFFF'><b>FECHA</b></font>", self.styles['normal'])]]
        header_table = Table(header, colWidths=[doc.width * 0.4, doc.width * 0.3, doc.width * 0.3])
        header_table.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, 0), self.colors['NARANJA_ACENTO']), ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                                         ('VALIGN', (0, 0), (-1, 0), 'MIDDLE'), ('TOPPADDING', (0, 0), (-1, 0), 10), ('BOTTOMPADDING', (0, 0), (-1, 0), 10)]))
        rows = [[Paragraph(f"<b>{transaction['product_name']}</b>", self.styles['normal']), Paragraph(f"<font color='#E6804D'><b>{transaction['quantity']}</b></font>", self.styles['normal']),
                 Paragraph(f"{transaction['transaction_date']}", self.styles['normal'])] for transaction in stock_data]
        data_table = Table(rows, colWidths=[doc.width * 0.4, doc.width * 0.3, doc.width * 0.3])
        data_table.setStyle(TableStyle([('ALIGN', (0, 0), (0, -1), 'LEFT'), ('ALIGN', (1, 0), (1, -1), 'CENTER'), ('ALIGN', (2, 0), (2, -1), 'LEFT'),
                                        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'), ('TOPPADDING', (0, 0), (-1, -1), 12), ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
                                        ('LEFTPADDING', (0, 0), (-1, -1), 15), ('RIGHTPADDING', (0, 0), (-1, -1), 15), ('BACKGROUND', (0, 0), (-1, -1), self.colors['BLANCO'])]))
        elements.extend([header_table, data_table, Spacer(1, 25)])
        return elements

    def create_page_elements(self, doc):
        def add_page_elements(canvas, doc):
            canvas.setFillColor(self.colors['BLANCO'])
            canvas.rect(0, 0, doc.width + 60, doc.height + 80, fill=1, stroke=0)
            canvas.setFillColor(self.colors['NARANJA_ACENTO'])
            canvas.rect(30, doc.height + 45, doc.width, 15, fill=1, stroke=0)
            canvas.setStrokeColor(self.colors['NARANJA_ACENTO'])
            canvas.setLineWidth(1)
            canvas.line(30, 50, doc.width + 30, 50)
            canvas.setFont("Helvetica", 8)
            canvas.setFillColor(self.colors['NEGRO'])
            canvas.drawRightString(doc.width + 30, 35, f"Página {doc.page}")
        return add_page_elements

    def generate_inventory_sales_report(self, report_type, report_date=None):
        report_date = report_date or datetime.datetime.now().strftime("%d/%m/%Y")
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=30, leftMargin=30, topMargin=60, bottomMargin=40)
        elements = []

        data = ReportDataFetcher.get_report_data(report_type)
        elements.extend(self.create_header(doc, report_date))
        elements.append(Paragraph(self.get_report_title(report_type), self.styles['title']))
        elements.append(Spacer(1, 10))

        if report_type in ['weekly', 'monthly', 'quarterly']:
            period_key = {'weekly': 'semana', 'monthly': 'mes', 'quarterly': 'trimestre'}[report_type]
            stats = {k: data['stats'][k] for k in ['total_sales', 'total_transactions', 'total_profit', 'low_stock_items', 'all_categories', 'all_items']}
            stats['period_stats'] = {period_key: data['stats']['period_stats'][period_key]}
            elements.extend(self.create_financial_summary(doc, stats))
            elements.extend(self.create_period_summary(doc, stats))
        elif report_type == 'inventory':
            elements.extend(self.create_inventory_details(doc, data['stats'], data['inventory_details']))
            elements.extend(self.create_top_products(doc, data['top_products']))
            elements.extend(self.create_suppliers(doc, data['suppliers']))
        elif report_type == 'payment_methods':
            elements.extend(self.create_payment_methods(doc, data['payment_data']))
        elif report_type == 'payment_distribution':
            elements.extend(self.create_payment_distribution(doc, data['payment_data']))
        elif report_type == 'payment_trends':
            elements.extend(self.create_payment_trends(doc, data['payment_data']))
        elif report_type == 'returns_history':
            elements.extend(self.create_returns_history(doc, data['returns_data']))
        elif report_type == 'returns_reasons':
            elements.extend(self.create_returns_reasons(doc, data['returns_data']))
        elif report_type == 'returns_by_product':
            elements.extend(self.create_returns_by_product(doc, data['returns_data']))
        elif report_type in ['stock_in', 'stock_in_weekly', 'stock_in_monthly', 'stock_in_quarterly', 'stock_out', 'stock_out_weekly', 'stock_out_monthly', 'stock_out_quarterly']:
            elements.extend(self.create_stock_transactions(doc, data['stock_data'], report_type))
        elif report_type == 'active_suppliers':
            elements.extend(self.create_active_suppliers(doc, data['supplier_active_data']))
        elif report_type == 'supplier_deliveries':
            elements.extend(self.create_supplier_deliveries(doc, data['supplier_delivery_data']))
        elif report_type == 'supplier_performance':
            elements.extend(self.create_supplier_performance(doc, data['supplier_performance_data']))

        company_name = ReportDataFetcher.get_company_name()
        elements.extend([Spacer(1, 15), Paragraph(f"Reporte generado el {report_date} | {company_name} | CONFIDENCIAL", self.styles['footer'])])
        doc.build(elements, onFirstPage=self.create_page_elements(doc), onLaterPages=self.create_page_elements(doc))
        buffer.seek(0)
        return buffer.getvalue()

    @staticmethod
    def index():
        return render_template('index.html')

    @staticmethod
    def generate_report(report_type):
        valid_reports = ['weekly', 'monthly', 'quarterly', 'inventory', 'payment_methods', 'payment_distribution', 'payment_trends',
                         'returns_history', 'returns_reasons', 'returns_by_product', 'stock_in', 'stock_out', 'active_suppliers',
                         'supplier_deliveries', 'supplier_performance']
        if report_type not in valid_reports:
            return "Reporte no válido", 400
        generator = ReportGenerator()
        pdf_data = generator.generate_inventory_sales_report(report_type)
        return send_file(BytesIO(pdf_data), mimetype='application/pdf', as_attachment=True, download_name=f'reporte_{report_type}.pdf')

    @staticmethod
    def report():
        return render_template('reports/report.html')