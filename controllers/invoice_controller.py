from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm, cm
from reportlab.lib.colors import Color
from reportlab.platypus import Paragraph, Frame
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.enums import TA_RIGHT, TA_CENTER, TA_LEFT
import io
import os
from db import Config as db
from flask import make_response, request
from datetime import datetime

class InvoiceGenerator:
    def validate_input(self, sale_ids):
        """Validate that sale_ids is a non-empty list or tuple."""
        if not sale_ids or not isinstance(sale_ids, (list, tuple)):
            print(f"sale_ids inválido: {sale_ids}")
            return False
        return True

    def fetch_sales_data(self, sale_ids):
        """Fetch sales data from the database."""
        connection = db.get_db_connection()
        cursor = connection.cursor(dictionary=True)
        try:
            query = """
                SELECT s.sale_group_id, s.sale_date, s.payment_method, s.sale_price, s.quantity, s.profit,
                       p.name AS product_name,
                       u.username AS seller_name,
                       c.name AS company_name,
                       c.address AS company_address,
                       c.phone AS company_phone
                FROM sales s
                JOIN products p ON s.product_id = p.id
                JOIN users u ON s.user_id = u.id
                JOIN companies c ON s.company_id = c.id
                WHERE s.id IN ({})
            """.format(','.join(['%s'] * len(sale_ids)))

            cursor.execute(query, tuple(sale_ids))
            ventas = cursor.fetchall()

            if not ventas:
                print(f"No se encontraron ventas para los IDs: {sale_ids}")
                return None

            #print(f"Ventas recuperadas: {ventas}")
            return ventas

        except Exception as e:
            print(f"Error al consultar la base de datos: {str(e)}")
            return None
        finally:
            cursor.close()
            connection.close()

    def generate_pdf(self, ventas):
        """Generate the PDF invoice based on sales data and return it as bytes."""
        buffer = io.BytesIO()
        p = canvas.Canvas(buffer, pagesize=A4)
        width, height = A4
        
        # Colores
        naranja_claro = Color(0.95, 0.75, 0.55)
        naranja_acento = Color(0.9, 0.5, 0.3, alpha=0.8)
        negro = Color(0.1, 0.1, 0.1)
        gris_oscuro = Color(0.3, 0.3, 0.3)
        gris_medio = Color(0.6, 0.6, 0.6)
        gris_claro = Color(0.95, 0.95, 0.95)
        
        def draw_header_and_table_start(p, y_start):
            """Dibuja el encabezado de la factura y el inicio de la tabla en una nueva página."""
            p.setFillColor(Color(1, 1, 1))
            p.rect(0, 0, width, height, fill=True, stroke=False)
            
            p.setFillColor(naranja_acento)
            p.rect(0, height - 15, width, 15, fill=True, stroke=False)
            
            logo_path = ""
            if os.path.exists(logo_path):
                p.drawImage(logo_path, 40, height - 80, width=100, height=50, preserveAspectRatio=True)
            
            p.setFillColor(negro)
            p.setFont("Helvetica-Bold", 22)
            invoice_text_width = p.stringWidth("FACTURA", "Helvetica-Bold", 22)
            invoice_x = width - 40 - invoice_text_width
            p.drawString(invoice_x, height - 65, "FACTURA")
            
            p.setStrokeColor(naranja_acento)
            p.setLineWidth(1.5)
            p.line(invoice_x, height - 70, invoice_x + invoice_text_width, height - 70)
            
            p.setFillColor(gris_oscuro)
            p.setFont("Helvetica-Bold", 12)
            invoice_num = f"N° {ventas[0]['sale_group_id']:06d}"
            invoice_num_width = p.stringWidth(invoice_num, "Helvetica-Bold", 12)
            p.drawString(invoice_x + invoice_text_width - invoice_num_width, height - 90, invoice_num)
            
            y_info = height - 130
            label_font_size = 12
            value_font_size = 12
            
            first_sale = ventas[0]
            p.setFillColor(negro)
            p.setFont("Helvetica-Bold", label_font_size)
            p.drawString(40, y_info, "Empresa:")
            p.setFont("Helvetica", value_font_size)
            p.drawString(110, y_info, first_sale['company_name'] or "Empresa no especificada")
            
            p.setFillColor(negro)
            p.setFont("Helvetica-Bold", label_font_size)
            p.drawString(40, y_info - 25, "Ubicación:")
            p.setFont("Helvetica", value_font_size)
            p.drawString(110, y_info - 25, first_sale['company_address'] or "Ubicación no especificada")
            
            now = datetime.now()
            p.setFillColor(negro)
            p.setFont("Helvetica-Bold", label_font_size)
            right_column_x = width/2 + 30
            p.drawString(right_column_x, y_info, "Vendedor:")
            p.setFont("Helvetica", value_font_size)
            p.drawString(right_column_x + 70, y_info, f"{first_sale['seller_name'] or 'Desconocido'}")
            
            p.setFillColor(negro)
            p.setFont("Helvetica-Bold", label_font_size)
            p.drawString(right_column_x, y_info - 25, "Teléfono:")
            p.setFont("Helvetica", value_font_size)
            phone_x = right_column_x + p.stringWidth("Teléfono: ", "Helvetica-Bold", label_font_size) + 5
            phone_text = f"{first_sale['company_phone']}"
            max_width = width - phone_x - 40 
            phone_width = p.stringWidth(phone_text, "Helvetica", value_font_size)
            if phone_width > max_width:
                p.setFont("Helvetica", value_font_size - 2)  # Reducir fuente a 10
                phone_width = p.stringWidth(phone_text, "Helvetica", value_font_size - 2)
                if phone_width > max_width:
                    while phone_width > max_width and len(phone_text) > 0:
                        phone_text = phone_text[:-1]
                        phone_width = p.stringWidth(phone_text + "...", "Helvetica", value_font_size - 2)
                    phone_text += "..."
            p.drawString(phone_x, y_info - 25, phone_text)
           
            y_details = y_info - 65
            p.setFillColor(gris_claro)
            p.roundRect(40, y_details, width - 80, 30, 5, fill=True, stroke=False)
            
            payment_x = 55
            date_x = width - 245
            p.setFillColor(gris_oscuro)
            p.setFont("Helvetica-Bold", 10)
            p.drawString(payment_x, y_details + 10, "MÉTODO DE PAGO:")
            p.setFillColor(negro)
            p.setFont("Helvetica", 10)
            p.drawString(payment_x + 100, y_details + 10, {
                'cash': 'Efectivo',
                'transfer': 'Transferencia',
                'stripe': 'Tarjeta de crédito/débito'
            }.get(first_sale['payment_method'], first_sale['payment_method']))

            
            p.setFillColor(gris_oscuro)
            p.setFont("Helvetica-Bold", 10)
            p.drawString(date_x, y_details + 10, "FECHA DE VENTA: ")
            p.setFillColor(negro)
            p.setFont("Helvetica", 10)
            p.drawString(date_x + 90, y_details + 10, f"  {first_sale['sale_date'].strftime('%d/%m/%Y')}")
            
            y_table = y_details - 30
            p.setFillColor(naranja_claro)
            p.roundRect(40, y_table - 10, width - 80, 30, 3, fill=True, stroke=False)
            
            concept_x = 55
            quantity_x = width - 280
            price_x = width - 200
            total_x = width - 100
            
            p.setFillColor(gris_oscuro)
            p.setFont("Helvetica-Bold", 10)
            p.drawString(concept_x, y_table + 5, "CONCEPTO")
            p.drawString(quantity_x, y_table + 5, "CANTIDAD")
            p.drawString(price_x, y_table + 5, "PRECIO")
            p.drawString(total_x, y_table + 5, "TOTAL")
            
            return y_table - 30, concept_x, quantity_x, price_x, total_x

        y, concept_x, quantity_x, price_x, total_x = draw_header_and_table_start(p, height)
        p.setFont("Helvetica", 9)
        total = 0
        row_height = 25
        
        for i, venta in enumerate(ventas):
            if y < 150:
                p.showPage()
                y, concept_x, quantity_x, price_x, total_x = draw_header_and_table_start(p, height)
                p.setFont("Helvetica", 9)

            p.setFillColor(gris_claro)
            p.rect(40, y - 5, width - 80, row_height, fill=True, stroke=False)
            
            concepto = venta['product_name'] or "Producto no especificado"
            cantidad = venta['quantity'] or 0
            precio = float(venta['sale_price'] or 0)
            subtotal = cantidad * precio
            total += subtotal
            
            p.setFillColor(negro)
            p.drawString(concept_x, y + 5, concepto[:50])
            p.setFillColor(gris_oscuro)
            p.drawString(quantity_x, y + 5, str(cantidad))
            p.drawString(price_x, y + 5, f"${precio:.2f}")
            p.drawString(total_x, y + 5, f"${subtotal:.2f}")
            
            y -= row_height
        
        if y < 150:
            p.showPage()
            y = height - 50
        p.setStrokeColor(gris_medio)
        p.setLineWidth(0.5)
        p.line(40, y - 10, width - 40, y - 10)
        
        # Totales (ajustados más a la izquierda)
        y -= 40
        if y < 150:
            p.showPage()
            y = height - 50
        
        itbis = total * 0.18
        total_final = total + itbis
        
        # Nuevas posiciones más a la izquierda
        text_x = width - 245  # Movido 100 puntos más a la izquierda (antes era width - 200)
        value_x = width - 125  # Movido 100 puntos más a la izquierda (antes era width - 80)
        row_spacing = 25
        
        p.setFillColor(gris_oscuro)
        p.setFont("Helvetica", 10)
        p.drawString(text_x, y, "Subtotal:")
        p.drawString(value_x, y, f"${total:.2f}")
        y -= row_spacing
        
        if y < 150:
            p.showPage()
            y = height - 50
        p.drawString(text_x, y, "ITBIS (18%):")
        p.drawString(value_x, y, f"${itbis:.2f}")
        y -= row_spacing
        
        if y < 150:
            p.showPage()
            y = height - 50
        p.setFillColor(naranja_claro)
        p.roundRect(text_x - 15, y - 10, 215, 30, 5, fill=True, stroke=False)  # Mantengo el ancho del rectángulo
        p.setFillColor(negro)
        p.setFont("Helvetica-Bold", 12)
        p.drawString(text_x, y, "TOTAL:")
        p.drawString(value_x, y, f"${total_final:.2f}")
        
        # Pie de página
        footer_y = 70
        if y - 60 < footer_y:
            p.showPage()
            y = height - 50

        p.setStrokeColor(naranja_acento)
        p.setLineWidth(1)
        p.line(40, footer_y, width - 40, footer_y)

        p.setFillColor(negro)
        p.setFont("Helvetica-Bold", 9)
        p.drawString(40, footer_y - 20, "GRACIAS POR SU COMPRA")

        p.setFillColor(gris_oscuro)
        p.setFont("Helvetica", 8)
        p.drawString(40, footer_y - 35, f"MÉTODO DE PAGO: { {
            'cash': 'Efectivo',
            'transfer': 'Transferencia',
            'stripe': 'Tarjeta de crédito/débito'
        }.get(ventas[0]['payment_method'], ventas[0]['payment_method']) }")

        
        p.showPage()
        p.save()
        pdf_data = buffer.getvalue()
        buffer.close()
        return pdf_data

    def generate(self, sale_ids):
        """Main method to generate the invoice and return PDF bytes or None on failure."""
        if not self.validate_input(sale_ids):
            return None

        ventas = self.fetch_sales_data(sale_ids)
        if not ventas:
            return None

        print("Ventas recibidas para el PDF:")
        for v in ventas:
            print(f"- Producto: {v['product_name']} - Cantidad: {v['quantity']} - Precio: {v['sale_price']}")

        pdf_data = self.generate_pdf(ventas)
        print(f"Factura generada exitosamente para sale_ids: {sale_ids}")
        return pdf_data

    @staticmethod
    def get_factura():
        """Handle the /factura route to generate an invoice based on sale_ids from query params."""
        sale_ids = request.args.get('ids')
        if not sale_ids:
            return "No se proporcionaron IDs de venta", 400

        try:
            ids_to_use = [int(id.strip()) for id in sale_ids.split(',')]
        except ValueError:
            return "Formato inválido de IDs", 400

        generator = InvoiceGenerator()
        pdf_data = generator.generate(ids_to_use)
        if pdf_data:
            response = make_response(pdf_data)
            response.headers['Content-Type'] = 'application/pdf'
            response.headers['Content-Disposition'] = 'attachment; filename=factura.pdf'
            return response
        return "Error generating invoice", 500