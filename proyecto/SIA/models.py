from django.db import models
import qrcode
from io import BytesIO
from django.conf import settings
from django.core.files.base import ContentFile

# Create your models here.
class Trabajador(models.Model):
    nombre = models.CharField(max_length=100)
    direccion = models.CharField(max_length=42, unique=True)
    AREA_CHOICES = [
        ('cosecha', 'Cosecha'),
        ('transporte', 'Transporte'),
    ]
    area = models.CharField(max_length=20, choices=AREA_CHOICES)

    def __str__(self):
        return self.nombre
    
class Cosecha(models.Model):
    id = models.AutoField(primary_key=True)  # Django generará automáticamente el ID
    producto = models.CharField(max_length=100)
    fecha_cosecha = models.DateField()
    ubicacion = models.CharField(max_length=255)
    cantidad_lote = models.IntegerField()
    cantidad_agua = models.IntegerField()
    pesticidas_fertilizantes = models.TextField()
    practicas_cultivo = models.TextField()
    qr_code = models.ImageField(upload_to='codigo_qr/', blank=True, null=True)
    transportado = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        # Llamar al método de save de la clase base antes de agregar lógica personalizada
        super().save(*args, **kwargs)

        # Verificar si el QR code ya ha sido generado
        if not self.qr_code:
            # Generar la URL dinámica que apunta a una vista en Django con el ID de la cosecha
            qr_url = f"{settings.SITE_URL}/cosecha/{self.id}/verificar"

            # Crear los datos del QR con la URL
            data = (
                f"URL para verificar cosecha: {qr_url}\n"
                f"Cosecha ID: {self.id}\n"
                f"Producto: {self.producto}\n"
                f"Fecha: {self.fecha_cosecha}\n"
                f"Ubicación: {self.ubicacion}\n"
                f"Cantidad Lote: {self.cantidad_lote}\n"
                f"Cantidad Agua: {self.cantidad_agua}\n"
                f"Pesticidas/Fertilizantes: {self.pesticidas_fertilizantes}\n"
                f"Prácticas de Cultivo: {self.practicas_cultivo}\n"
                f"Transportado: {'Sí' if self.transportado else 'No'}"
            )

            # Generar el QR code
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(data)
            qr.make(fit=True)

            qr_img = qr.make_image(fill='black', back_color='white')

            # Guardar el QR en un BytesIO
            qr_io = BytesIO()
            qr_img.save(qr_io, format="PNG")

            # Crear un ContentFile con el contenido del QR
            qr_content = ContentFile(qr_io.getvalue(), name=f'qr_cosecha_{self.id}.png')

            # Guardar la imagen QR en el campo qr_code
            self.qr_code.save(qr_content.name, qr_content, save=False)
            super().save(*args, **kwargs)