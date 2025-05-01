from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image, Flowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm, mm
from reportlab.lib.colors import HexColor
import datetime
from reportlab.pdfgen import canvas
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.graphics.shapes import Drawing, Rect, String, Line, Circle, Wedge
from reportlab.graphics.charts.piecharts import Pie
from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.graphics import renderPDF
from reportlab.platypus.frames import Frame
import math

# Clase personalizada para crear formas redondeadas
class RoundedRect(Flowable):
    def __init__(self, width, height, radius=10, fillColor=None, strokeColor=None, strokeWidth=1):
        Flowable.__init__(self)
        self.width = width
        self.height = height
        self.radius = radius
        self.fillColor = fillColor
        self.strokeColor = strokeColor
        self.strokeWidth = strokeWidth

    def draw(self):
        c = self.canv
        c.saveState()
        if self.fillColor:
            c.setFillColor(self.fillColor)
        if self.strokeColor:
            c.setStrokeColor(self.strokeColor)
            c.setLineWidth(self.strokeWidth)
        c.roundRect(0, 0, self.width, self.height, self.radius, fill=bool(self.fillColor), stroke=bool(self.strokeColor))
        c.restoreState()

# Clase personalizada para círculo con valor en el centro
class CircleValue(Flowable):
    def __init__(self, radius=20, fillColor=None, strokeColor=None, value="", textColor=None):
        Flowable.__init__(self)
        self.radius = radius
        self.fillColor = fillColor
        self.strokeColor = strokeColor
        self.value = value
        self.textColor = textColor or HexColor('#FFFFFF')
        self.width = 2 * radius
        self.height = 2 * radius

    def draw(self):
        c = self.canv
        c.saveState()
        if self.fillColor:
            c.setFillColor(self.fillColor)
        if self.strokeColor:
            c.setStrokeColor(self.strokeColor)
        c.circle(self.radius, self.radius, self.radius, fill=1)
        c.setFillColor(self.textColor)
        c.setFont("Helvetica-Bold", 11)
        text_width = c.stringWidth(self.value, "Helvetica-Bold", 11)
        c.drawCentredString(self.radius, self.radius - 4, self.value)
        c.restoreState()

# Mini gráfico de barras estilizado
class MiniBarChart(Flowable):
    def __init__(self, data, width=100, height=40, bars_color=HexColor('#FF6600'), bg_color=HexColor('#F8F8F8')):
        Flowable.__init__(self)
        self.data = data
        self.width = width
        self.height = height
        self.bars_color = bars_color
        self.bg_color = bg_color

    def draw(self):
        c = self.canv
        c.saveState()
        
        # Fondo
        c.setFillColor(self.bg_color)
        c.rect(0, 0, self.width, self.height, fill=1, stroke=0)
        
        # Calcular valores para las barras
        max_val = max(self.data)
        bar_width = self.width / len(self.data) * 0.7
        space_width = self.width / len(self.data) * 0.3
        
        # Dibujar barras
        c.setFillColor(self.bars_color)
        for i, val in enumerate(self.data):
            bar_height = (val / max_val) * self.height * 0.8
            x = i * (bar_width + space_width) + space_width/2
            y = self.height * 0.1
            c.roundRect(x, y, bar_width, bar_height, 2, fill=1, stroke=0)
        
        c.restoreState()

class WaveSeparator(Flowable):
    def __init__(self, width, height=15, color=HexColor('#FF6600')):
        Flowable.__init__(self)
        self.width = width
        self.height = height
        self.color = color
        
    def draw(self):
        canvas = self.canv
        canvas.saveState()
        canvas.setFillColor(self.color)
        
        # Dibujar una onda
        path = canvas.beginPath()
        path.moveTo(0, 0)
        
        # Crear onda
        amplitude = self.height * 0.6
        period = self.width / 6
        
        for x in range(0, int(self.width) + 1, 2):
            y = amplitude * math.sin((x/period) * 2 * math.pi)
            path.lineTo(x, y + self.height/2)
            
        path.lineTo(self.width, 0)
        path.close()
        canvas.drawPath(path, fill=1, stroke=0)
        canvas.restoreState()

class ModernTab(Flowable):
    def __init__(self, width, height=30, text="", active=False, orange=HexColor('#FF6600'), bg_color=HexColor('#F5F5F5')):
        Flowable.__init__(self)
        self.width = width
        self.height = height
        self.text = text
        self.active = active
        self.orange = orange
        self.bg_color = bg_color
        
    def draw(self):
        canvas = self.canv
        canvas.saveState()
        
        # Fondo del tab
        canvas.setFillColor(self.orange if self.active else self.bg_color)
        canvas.roundRect(0, 0, self.width, self.height, 10, fill=1, stroke=0)
        
        # Texto del tab
        canvas.setFillColor(HexColor('#FFFFFF') if self.active else HexColor('#222222'))
        canvas.setFont("Helvetica-Bold", 11)
        text_width = canvas.stringWidth(self.text, "Helvetica-Bold", 11)
        canvas.drawCentredString(self.width/2, self.height/2 - 4, self.text)
        
        canvas.restoreState()

def generate_inventory_sales_report(filename="reporte_inventario_ventas.pdf",
                                   company_name="TECNO SOLUTIONS S.A.",
                                   report_date="27/04/2025"):
    """
    Genera un reporte moderno de ventas e inventario con estilo contemporáneo
    usando formas redondeadas y elementos visuales mejorados.
    """
    # Colores del tema
    ORANGE = HexColor('#FF6600')  # Naranja principal
    ORANGE_LIGHT = HexColor('#FF9966')  # Naranja claro para acentos
    ORANGE_VERY_LIGHT = HexColor('#FFE0CC')  # Naranja muy claro para fondos sutiles
    BLACK = HexColor('#222222')  # Negro suave para texto
    GRAY_DARK = HexColor('#444444')  # Gris oscuro para títulos secundarios
    GRAY_MEDIUM = HexColor('#777777')  # Gris medio para texto secundario
    GRAY_LIGHT = HexColor('#F5F5F5')  # Gris claro para fondos alternativos
    WHITE = HexColor('#FFFFFF')  # Blanco

    # Datos estáticos
    stats = {
        "total_sales": 187450.00,
        "total_transactions": 153,
        "total_profit": 78350.00,
        "low_stock_items": 5,
        "all_categories": 12,
        "all_items": 524,
        "period_stats": {
            "semana": {"sales": 50000, "transactions": 50, "profit": 20000},
            "mes": {"sales": 187450, "transactions": 153, "profit": 78350},
            "trimestre": {"sales": 450000, "transactions": 400, "profit": 180000}
        }
    }
    
    top_products = [
        {"name": "Laptop Dell XPS 15", "sales_count": 38},
        {"name": "Monitor Ultrawide LG", "sales_count": 42},
        {"name": "iPhone 15 Pro", "sales_count": 27}
    ]
    
    suppliers = [
        {"name": "TechSolutions Inc.", "products_bought": 35, "total_value": 28500.00, "delivery_time": "7 días"},
        {"name": "GlobalGadgets S.A.", "products_bought": 42, "total_value": 31250.00, "delivery_time": "5 días"},
        {"name": "ElectroComp Ltd.", "products_bought": 18, "total_value": 15640.00, "delivery_time": "12 días"}
    ]
    
    # Configuración del documento
    doc = SimpleDocTemplate(
        filename,
        pagesize=A4,
        rightMargin=30,
        leftMargin=30,
        topMargin=60,
        bottomMargin=40
    )
    
    # Contenedor para los elementos del PDF
    elements = []
    
    # Estilos para el texto
    styles = getSampleStyleSheet()
    
    # Estilo de título principal - moderno y elegante
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        alignment=TA_CENTER,
        fontSize=24,
        spaceAfter=20,
        textColor=BLACK,
        fontName='Helvetica-Bold',
        leading=28
    )
    
    # Estilo para subtítulos con borde inferior redondeado
    subtitle_style = ParagraphStyle(
        'CustomSubtitle',
        parent=styles['Heading2'],
        fontSize=16,
        spaceBefore=15,
        spaceAfter=10,
        textColor=ORANGE,
        fontName='Helvetica-Bold',
    )
    
    # Estilo para títulos de tarjetas
    card_title_style = ParagraphStyle(
        'CardTitle',
        parent=styles['Normal'],
        fontSize=11,
        textColor=GRAY_MEDIUM,
        fontName='Helvetica-Bold',
        spaceAfter=6
    )
    
    # Estilo para valores principales
    card_value_style = ParagraphStyle(
        'CardValue',
        parent=styles['Normal'],
        fontSize=22,
        textColor=BLACK,
        fontName='Helvetica-Bold'
    )
    
    # Estilo para texto normal
    normal_style = ParagraphStyle(
        'CustomNormal',
        parent=styles['Normal'],
        fontSize=10,
        textColor=BLACK,
        leading=14
    )
    
    # Estilo para pie de página
    footer_style = ParagraphStyle(
        'Footer',
        parent=styles['Normal'],
        fontSize=8,
        textColor=GRAY_MEDIUM,
        alignment=TA_CENTER
    )
    
    # Encabezado moderno con línea curva
    header_data = [
        [Paragraph(f'<font color="#222222" size="14"><b>{company_name}</b></font>', styles["Normal"]), 
         Paragraph(f'<font color="#222222" size="12">Fecha: <b>{report_date}</b></font>', styles["Normal"])]
    ]
    
    header_table = Table(header_data, colWidths=[doc.width/2.0]*2)
    header_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (0, 0), 'LEFT'),
        ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 15),
        ('TOPPADDING', (0, 0), (-1, -1), 15),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
        ('RIGHTPADDING', (0, 0), (-1, -1), 5),
    ]))
    
    elements.append(header_table)
    elements.append(WaveSeparator(width=doc.width))
    elements.append(Spacer(1, 20))
    
    # Título del reporte
    elements.append(Paragraph("Reporte de Ventas e Inventario", title_style))
    elements.append(Spacer(1, 10))
    
    # Tarjetas de resumen financiero modernas con esquinas redondeadas
    elements.append(Paragraph("Resumen Financiero", subtitle_style))
    elements.append(Spacer(1, 15))
    
    # Crear contenedor redondeado para las tarjetas financieras
    elements.append(RoundedRect(doc.width, 90, radius=15, fillColor=ORANGE_VERY_LIGHT))
    elements.append(Spacer(1, -80))  # Ajustar posición para superponer contenido
    
    # Tarjetas con valores financieros
    financial_data = [
        [Paragraph("Total Ventas", card_title_style), 
         Paragraph("Total Transacciones", card_title_style), 
         Paragraph("Total Ganancias", card_title_style)],
        [Paragraph(f"<font color='#FF6600'><b>${stats['total_sales']:,.2f}</b></font>", card_value_style), 
         Paragraph(f"<font color='#222222'><b>{stats['total_transactions']}</b></font>", card_value_style), 
         Paragraph(f"<font color='#FF6600'><b>${stats['total_profit']:,.2f}</b></font>", card_value_style)]
    ]
    
    financial_table = Table(financial_data, colWidths=[doc.width/3.0]*3)
    financial_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('TOPPADDING', (0, 1), (-1, 1), 4),
        ('BOTTOMPADDING', (0, 1), (-1, 1), 18),
    ]))
    
    elements.append(financial_table)
    elements.append(Spacer(1, 25))
    
    # Detalles del Inventario y Productos Más Vendidos con tarjetas modernas
    elements.append(Paragraph("Detalles y Productos Destacados", subtitle_style))
    elements.append(Spacer(1, 15))
    
    # Diseño de dos columnas para inventario y productos
    left_column = []
    right_column = []
    
    # === COLUMNA IZQUIERDA: DETALLES DE INVENTARIO ===
    inventory_tab = ModernTab(width=doc.width/2.0 - 15, text="DETALLES DEL INVENTARIO", active=True)
    left_column.append(inventory_tab)
    left_column.append(Spacer(1, 15))
    
    # Contenedor redondeado para inventario
    left_column.append(RoundedRect(doc.width/2.0 - 15, 190, radius=15, fillColor=GRAY_LIGHT, strokeColor=ORANGE_LIGHT, strokeWidth=1))
    
    # Círculos con valores importantes
    inventory_circles = [
        [CircleValue(radius=25, fillColor=ORANGE, value=str(stats['low_stock_items'])),
         Paragraph("<b>Productos en Bajo Stock</b><br/>Necesitan reposición", normal_style)],
        [CircleValue(radius=25, fillColor=ORANGE, value=str(stats['all_categories'])),
         Paragraph("<b>Categorías Disponibles</b><br/>Clasificación de productos", normal_style)],
        [CircleValue(radius=25, fillColor=ORANGE, value=str(stats['all_items'])),
         Paragraph("<b>Total Productos</b><br/>En inventario actual", normal_style)]
    ]
    
    inventory_circles_table = Table(inventory_circles, colWidths=[60, doc.width/2.0 - 85])
    inventory_circles_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
        ('RIGHTPADDING', (0, 0), (-1, -1), 5),
    ]))
    
    left_column.append(Spacer(1, -180))  # Ajustar posición
    left_column.append(inventory_circles_table)
    
    # === COLUMNA DERECHA: PRODUCTOS MÁS VENDIDOS ===
    products_tab = ModernTab(width=doc.width/2.0 - 15, text="PRODUCTOS MÁS VENDIDOS", active=True)
    right_column.append(products_tab)
    right_column.append(Spacer(1, 15))
    
    # Contenedor redondeado para productos
    right_column.append(RoundedRect(doc.width/2.0 - 15, 190, radius=15, fillColor=GRAY_LIGHT, strokeColor=ORANGE_LIGHT, strokeWidth=1))
    
    # Lista de productos con mini gráficos
    product_rows = []
    for product in top_products:
        # Crear barras muy simples que representan ventas
        bar_data = [15, 30, product['sales_count'], 20, 10]  # Datos ficticios para contexto visual
        
        product_rows.append([
            Paragraph(f"<b>{product['name']}</b>", normal_style),
            MiniBarChart(bar_data, width=80, height=25),
            Paragraph(f"<font color='#FF6600'><b>{product['sales_count']}</b></font> <font color='#777777'>unidades</font>", normal_style)
        ])
    
    product_table = Table(product_rows, colWidths=[doc.width/4.0 - 20, 90, doc.width/4.0 - 90])
    product_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN', (2, 0), (2, -1), 'RIGHT'),
        ('TOPPADDING', (0, 0), (-1, -1), 15),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 15),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
    ]))
    
    right_column.append(Spacer(1, -180))  # Ajustar posición
    right_column.append(product_table)
    
    # Combinar ambas columnas en una tabla
    combined_data = [[left_column, right_column]]
    combined_table = Table(combined_data, colWidths=[doc.width/2.0, doc.width/2.0])
    combined_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (0, 0), 0),
        ('RIGHTPADDING', (0, 0), (0, 0), 5),
        ('LEFTPADDING', (1, 0), (1, 0), 5),
        ('RIGHTPADDING', (1, 0), (1, 0), 0),
    ]))
    
    # Convertir columnas a tabla para añadirlas al documento
    for item in left_column + right_column:
        elements.append(item)
    
    elements.append(Spacer(1, 35))  # Espacio adicional después de las secciones
    
    # Proveedores principales con diseño de tarjetas
    elements.append(Paragraph("Proveedores Principales", subtitle_style))
    elements.append(Spacer(1, 15))

    # Crear las tarjetas de proveedores lado a lado
    supplier_cards = []
    for supplier in suppliers:
        # Contenedor para cada tarjeta de proveedor
        card = []
        
        # Cabecera de la tarjeta
        card.append(Paragraph(f"<font color='#FFFFFF' size='12'><b>{supplier['name']}</b></font>", normal_style))
        
        # Contenido de la tarjeta - tabla de datos
        supplier_details = [
            [Paragraph("Productos:", normal_style), 
             Paragraph(f"<b>{supplier['products_bought']}</b>", normal_style)],
            [Paragraph("Valor Total:", normal_style), 
             Paragraph(f"<font color='#FF6600'><b>${supplier['total_value']:,.2f}</b></font>", normal_style)],
            [Paragraph("Plazo Entrega:", normal_style), 
             Paragraph(f"<b>{supplier['delivery_time']}</b>", normal_style)]
        ]
        
        # Crear tabla para los detalles
        details_table = Table(supplier_details, colWidths=[doc.width/6.0 - 20, doc.width/6.0 - 20])
        details_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('LEFTPADDING', (0, 0), (0, -1), 10),
            ('RIGHTPADDING', (1, 0), (1, -1), 10),
        ]))
        
        # Crear tabla para toda la tarjeta completa
        supplier_data = [
            [Paragraph(f"<font color='#FFFFFF' size='12'><b>{supplier['name']}</b></font>", normal_style)],
            [details_table]
        ]
        supplier_table = Table(supplier_data, colWidths=[doc.width/3.0 - 20])
        supplier_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, 0), ORANGE),
            ('ALIGN', (0, 0), (0, 0), 'CENTER'),
            ('VALIGN', (0, 0), (0, 0), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (0, 0), 10),
            ('BOTTOMPADDING', (0, 0), (0, 0), 10),
            ('LEFTPADDING', (0, 0), (0, 0), 5),
            ('RIGHTPADDING', (0, 0), (0, 0), 5),
            ('BACKGROUND', (0, 1), (0, 1), WHITE),
            ('TOPPADDING', (0, 1), (0, 1), 0),
            ('BOTTOMPADDING', (0, 1), (0, 1), 0),
            ('LEFTPADDING', (0, 1), (0, 1), 0),
            ('RIGHTPADDING', (0, 1), (0, 1), 0),
            ('BOX', (0, 0), (0, 1), 1, GRAY_DARK),
        ]))
        
        supplier_cards.append(supplier_table)
    
    # Colocar las tarjetas en una fila
    suppliers_row = [supplier_cards]
    suppliers_table = Table(suppliers_row, colWidths=[doc.width/3.0] * 3)
    suppliers_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
        ('RIGHTPADDING', (0, 0), (-1, -1), 5),
    ]))
    
    elements.append(suppliers_table)
    elements.append(Spacer(1, 25))
    
    # Resumen de Ventas por Periodo con visualización más moderna
    elements.append(Paragraph("Resumen de Ventas por Periodo", subtitle_style))
    elements.append(Spacer(1, 15))
    
    # Crear un contenedor redondeado para el resumen
    elements.append(RoundedRect(doc.width, 150, radius=15, fillColor=GRAY_LIGHT))
    elements.append(Spacer(1, -140))  # Ajustar posición
    
    # Encabezados modernos para la tabla de resumen
    period_header = [
        [Paragraph("<font color='#FFFFFF'><b>PERIODO</b></font>", normal_style),
         Paragraph("<font color='#FFFFFF'><b>VENTAS</b></font>", normal_style),
         Paragraph("<font color='#FFFFFF'><b>TRANS.</b></font>", normal_style),
         Paragraph("<font color='#FFFFFF'><b>GANANCIAS</b></font>", normal_style)]
    ]
    
    period_header_table = Table(period_header, colWidths=[doc.width*0.25, doc.width*0.25, doc.width*0.20, doc.width*0.30])
    period_header_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), ORANGE),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('VALIGN', (0, 0), (-1, 0), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
    ]))
    
    elements.append(period_header_table)
    
    # Datos de periodos
    periods = {"semana": "Esta Semana", "mes": "Este Mes", "trimestre": "Este Trimestre"}
    
    period_rows = []
    for i, (period_key, period_name) in enumerate(periods.items()):
        data = stats["period_stats"][period_key]
        period_rows.append([
            Paragraph(f"<b>{period_name}</b>", normal_style),
            Paragraph(f"<font color='#FF6600'><b>${data['sales']:,.2f}</b></font>", normal_style),
            Paragraph(f"{data['transactions']}", normal_style),
            Paragraph(f"<font color='#FF6600'><b>${data['profit']:,.2f}</b></font>", normal_style)
        ])
    
    periods_data = Table(period_rows, colWidths=[doc.width*0.25, doc.width*0.25, doc.width*0.20, doc.width*0.30])
    periods_data.setStyle(TableStyle([
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('ALIGN', (2, 0), (2, -1), 'CENTER'),
        ('ALIGN', (3, 0), (3, -1), 'RIGHT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 12),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ('LEFTPADDING', (0, 0), (-1, -1), 15),
        ('RIGHTPADDING', (0, 0), (-1, -1), 15),
        ('BACKGROUND', (0, 0), (-1, 0), WHITE),
        ('BACKGROUND', (0, 1), (-1, 1), GRAY_LIGHT),
        ('BACKGROUND', (0, 2), (-1, 2), WHITE),
    ]))
    
    elements.append(periods_data)
    elements.append(Spacer(1, 25))
    
    # Separador final estilizado
    elements.append(WaveSeparator(width=doc.width))
    elements.append(Spacer(1, 15))
    
    # Pie de página con estilo
    footer_text = f"Reporte generado el {report_date} | {company_name} | CONFIDENCIAL"
    elements.append(Paragraph(footer_text, footer_style))
    
    # Función para añadir elementos de página
    def add_page_elements(canvas, doc):
        # Añadir una línea de color naranja en la parte superior
        canvas.setStrokeColor(ORANGE)
        canvas.setFillColor(ORANGE)
        canvas.rect(30, doc.height + 45, doc.width, 8, fill=1)
        
        # Añadir una línea de color naranja en la parte inferior
        canvas.rect(30, 20, doc.width, 3, fill=1)
        
        # Numeración de página
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(BLACK)
        text = f"Página {doc.page}"
        canvas.drawRightString(doc.width + 30, 12, text)
    
    # Construir el PDF con elementos de página personalizados
    doc.build(elements, onFirstPage=add_page_elements, onLaterPages=add_page_elements)
    
    print(f"Reporte generado exitosamente: {filename}")

if __name__ == "__main__":
    generate_inventory_sales_report()