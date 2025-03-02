#qr controller

import io
import qrcode
from flask import send_file

class QrController:
    @staticmethod
    def generate_qr(product_id):
        """Genera un código QR en memoria sin guardarlo en archivo."""
        qr_data = f"http://localhost:5000/product/{product_id}"
        qr = qrcode.make(qr_data)
        
        img_io = io.BytesIO()
        qr.save(img_io, format="PNG")
        img_io.seek(0)
        
        return send_file(img_io, mimetype="image/png")
