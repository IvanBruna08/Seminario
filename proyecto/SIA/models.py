from django.db import models, transaction
import qrcode
from io import BytesIO
from decimal import Decimal, InvalidOperation
from django.core.files.base import ContentFile
from .utils import get_coordinates
import json

def generate_qr_code(data):
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill='black', back_color='white')

    # Usar BytesIO para obtener los bytes de la imagen
    buffer = BytesIO()
    img.save(buffer, format='PNG')
    return buffer.getvalue()


# Modelo Predio
class Predio(models.Model):
    nombre = models.CharField(max_length=100, null=True, blank=True)
    direccion = models.CharField(max_length=100, null=True, blank=True)
    billetera = models.CharField(max_length=42, null=True, blank=True)
    rut = models.CharField(max_length=11, null=True, blank=True)
    password = models.CharField(max_length=10, null=True, blank=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.latitude or not self.longitude:
            self.latitude, self.longitude = get_coordinates(self.direccion)
        super().save(*args, **kwargs)


# Modelo Transporte
class Transporte(models.Model):
    nombre = models.CharField(max_length=100, null=True, blank=True)
    auto = models.CharField(max_length=100, null=True, blank=True)
    patente = models.CharField(max_length=7, null=True, blank=True)
    rut = models.CharField(max_length=11, null=True, blank=True)
    password = models.CharField(max_length=10, null=True, blank=True)
    billetera = models.CharField(max_length=42, null=True, blank=True)
    def __str__(self):
        return self.nombre  # Mostrar el nombre del distribuidor

# Modelo Distribuidor
class Distribuidor(models.Model):
    direccion = models.CharField(max_length=100, null=True, blank=True)
    nombre = models.CharField(max_length=100, null=True, blank=True)
    billetera = models.CharField(max_length=42, null=True, blank=True)
    rut = models.CharField(max_length=11, null=True, blank=True)
    password = models.CharField(max_length=10, null=True, blank=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.latitude or not self.longitude:
            self.latitude, self.longitude = get_coordinates(self.direccion)
        super().save(*args, **kwargs)
    def __str__(self):
        return self.nombre if self.nombre else "Distribuidor sin nombre"

# Modelo Cliente
class Cliente(models.Model):
    nombre = models.CharField(max_length=100, null=True, blank=True)
    tipo_cliente = models.CharField(max_length=100, choices=[('supermercado', 'Supermercado'), ('restaurante', 'Restaurante'), ('hotel', 'Hotel')],blank=True)
    direccion = models.CharField(max_length=255, null=True, blank=True)
    rut = models.CharField(max_length=11, null=True, blank=True)
    password = models.CharField(max_length=10, null=True, blank=True)
    billetera = models.CharField(max_length=42, null=True, blank=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.latitude or not self.longitude:
            self.latitude, self.longitude = get_coordinates(self.direccion)
        super().save(*args, **kwargs)
    def __str__(self):
        return self.nombre 

class Pallet(models.Model):
    predio = models.ForeignKey('Predio', on_delete=models.CASCADE)  # Asegúrate de que el nombre sea consistente
    qr_pallet = models.ImageField(upload_to='qr_codes/', blank=True, null=True)
    lugar = models.CharField(max_length=100)
    producto = models.CharField(max_length=100)
    clasificacion = models.CharField(max_length=100)
    fecha_cosecha = models.DateField()
    cantidad = models.DecimalField(max_digits=10, decimal_places=2)
    peso = models.DecimalField(max_digits=10, decimal_places=2)
    precio_venta = models.DecimalField(max_digits=10, decimal_places=2)
    # Estado de recepción
    estado_envio = models.CharField(
        max_length=50,
        choices=[
            ('pendiente', 'Pendiente'),
            ('completado', 'Completado'),
            ('en_ruta', 'En Ruta')
        ],
        default='pendiente'
    )


    def save(self, *args, **kwargs):
        # Solo generar el código QR si no existe
        if not self.qr_pallet:
            # Asegúrate de que el objeto se haya guardado para obtener el ID
            super().save(*args, **kwargs)  # Guarda primero para obtener el ID
            qr_data = f'/seleccionar_opcion/{self.pk}/'  # URL que redirige a la vista
            qr_code = generate_qr_code(qr_data)
            # Crear un archivo temporal con el contenido del QR
            self.qr_pallet.save(f'pallet_{self.pk}.png', ContentFile(qr_code), save=False)
        super().save(*args, **kwargs)  # Guarda de nuevo para guardar el QR

class DistribuidorPallet(models.Model):
    pallet = models.ForeignKey(Pallet, on_delete=models.CASCADE)
    distribuidor = models.ForeignKey(Distribuidor,on_delete=models.CASCADE,null=True,blank=True)
    peso_enviado =  models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    estado_pallet = models.CharField(
        max_length=50,
        choices=[
            ('pendiente', 'Pendiente'),
            ('completado', 'Completado'),
            ('en_proceso', 'En Proceso')
        ],
        default='pendiente'
    )
    def __str__(self):
        return f'{self.distribuidor} - {self.pallet} - {self.peso_enviado} kg'

class EnvioPallet(models.Model):
    pallet = models.ForeignKey(Pallet, on_delete=models.CASCADE)
    transporte = models.ForeignKey(Transporte, on_delete=models.CASCADE)
    fecha_inicio = models.DateTimeField(auto_now_add=True)
    fecha_llegada = models.DateTimeField(null=True, blank=True)
    ruta_inicio_latitude = models.FloatField(null=True, blank=True)
    ruta_inicio_longitude = models.FloatField(null=True, blank=True)
    ruta_final_latitude = models.FloatField(null=True, blank=True)
    ruta_final_longitude = models.FloatField(null=True, blank=True)
    distancia = models.FloatField(null=True, blank=True)
    coordenadas_transporte = models.JSONField(null=True, blank=True)

    def __str__(self):
        return f"Envio de Pallet {self.pallet.id} por Transporte {self.transporte.id}"

class Recepcion(models.Model):

    envio_pallet = models.ForeignKey('EnvioPallet', on_delete=models.CASCADE)

    distribuidor = models.ForeignKey('Distribuidor', on_delete=models.CASCADE)

    # Fecha y hora de recepción
    fecha_recepcion = models.DateTimeField(auto_now_add=True)  # Se establece automáticamente al crear el registro
    peso_ingresado = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    peso_recepcion = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    cantidad_cajas = models.PositiveIntegerField(default=0)  # Cantidad total de cajas acumuladas en este
    # Estado de recepción
    estado_recepcion = models.CharField(
        max_length=50,
        choices=[
            ('pendiente', 'Pendiente'),
            ('completado', 'Completado'),
            ('en_proceso', 'En Proceso'),
            ('rechazado', 'Rechazado')
        ],
        default='pendiente'
    )
    def actualizar_peso_y_cantidad(self, nuevas_cajas):
        """
        Actualiza el peso del pallet y la cantidad de cajas después de la creación de nuevas cajas.
        """
        # Calcular el peso total de las nuevas cajas, ignorando las que no tienen peso asignado
        peso_nuevas_cajas = sum(caja.peso_caja for caja in nuevas_cajas if caja.peso_caja is not None)
        
        # Verificar que el peso de las nuevas cajas no exceda el peso disponible del pallet
        if peso_nuevas_cajas > self.peso_recepcion:
            raise ValueError("El peso de las nuevas cajas excede el peso restante del pallet.")
        
        # Actualizar el peso del pallet restando el peso de las nuevas cajas
        self.peso_recepcion -= peso_nuevas_cajas

        # Acumular la cantidad de cajas creadas (solo contando las que tienen peso)
        self.cantidad_cajas += len([caja for caja in nuevas_cajas if caja.peso_caja is not None])

        # Guardar el empaque con los valores actualizados
        self.save()
        return self.peso_recepcion

    def __str__(self):
        return f"Recepción {self.id} - Pallet {self.envio_pallet.pallet.id}"

class Empaque(models.Model):
    recepcion = models.ForeignKey(Recepcion, on_delete=models.CASCADE)  # Relación con Recepcion
    fecha_empaque = models.DateTimeField(auto_now_add=True)  # Fecha y hora de empaque
    peso_pallet = models.DecimalField(max_digits=10, decimal_places=2)  # Peso actual del pallet
    cantidad_cajas = models.PositiveIntegerField(default=0)  # Cantidad total de cajas acumuladas en este empaque

    def actualizar_peso_y_cantidad(self, nuevas_cajas):
        """
        Actualiza el peso del pallet y la cantidad de cajas después de la creación de nuevas cajas.
        """
        # Calcular el peso total de las nuevas cajas, ignorando las que no tienen peso asignado
        peso_nuevas_cajas = sum(caja.peso_caja for caja in nuevas_cajas if caja.peso_caja is not None)
        
        # Verificar que el peso de las nuevas cajas no exceda el peso disponible del pallet
        if peso_nuevas_cajas > self.peso_pallet:
            raise ValueError("El peso de las nuevas cajas excede el peso restante del pallet.")
        
        # Actualizar el peso del pallet restando el peso de las nuevas cajas
        self.peso_pallet -= peso_nuevas_cajas

        # Acumular la cantidad de cajas creadas (solo contando las que tienen peso)
        self.cantidad_cajas += len([caja for caja in nuevas_cajas if caja.peso_caja is not None])

        # Guardar el empaque con los valores actualizados
        self.save()
        return self.peso_pallet

    

class Caja(models.Model):
    recepcion = models.ForeignKey(Recepcion, on_delete=models.CASCADE, null=True, blank=True)  # Relación con Empaque
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, null=True, blank=True)  # Relación con Cliente
    qr_caja = models.ImageField(upload_to='qr_codes/', blank=True, null=True)
    peso_caja = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    tipo_caja = models.CharField(max_length=100, blank=True, null=True)  # Tipo de caja
    fecha_caja = models.DateTimeField(auto_now_add=True, null=True)  # Fecha y hora actual al crear la caja, null=True para registros existentes
    estado_envio = models.CharField(max_length=100, choices=[('pendiente', 'Pendiente'), ('enviado', 'Enviado'), ('entregado', 'Entregado')],default='pendiente')

    def save(self, *args, **kwargs):
        # Usamos una transacción para asegurar que ambos procesos se ejecuten correctamente
        with transaction.atomic():
            # Asegurar que peso_caja sea un Decimal válido
            if self.peso_caja is not None:
                try:
                    self.peso_caja = Decimal(self.peso_caja)  # Convertir a Decimal
                except (ValueError, InvalidOperation):
                    raise ValueError("El peso de la caja debe ser un número válido.")

            # Verificar que el peso de la caja no exceda el peso restante del pallet
            if self.peso_caja and self.recepcion and self.peso_caja > self.recepcion.peso_recepcion:
                raise ValueError("El peso de la caja excede el peso restante del pallet.")
            
            # Restar el peso de la caja del peso del pallet en el empaque
            self.recepcion.actualizar_peso_y_cantidad([self])  # Solo esta caja en la lista

            # Guardar el objeto inicialmente para obtener un pk (si aún no lo tiene)
            if self.pk is None:
                super().save(*args, **kwargs)

            # Generar QR si el peso y cliente están asignados y aún no hay QR generado
            if self.peso_caja and self.cliente and not self.qr_caja:
                qr_data = f'/seleccionar_caja/{self.pk}/'  # URL que redirige a la vista
                qr_code = generate_qr_code(qr_data)
                qr_image_name = f'caja_{self.pk}.png'
                self.qr_caja.save(qr_image_name, ContentFile(qr_code), save=False)

            # Guardar la caja nuevamente después de generar el QR
            super().save(*args, **kwargs)
            
class EnvioCaja(models.Model):
    caja = models.ForeignKey(Caja, on_delete=models.CASCADE)
    transporte = models.ForeignKey('Transporte', on_delete=models.CASCADE)
    fecha_inicio = models.DateTimeField(auto_now_add=True)  # Captura la fecha y hora de inicio automáticamente
    fecha_llegada = models.DateTimeField(null=True, blank=True)  # Se llenará al finalizar la entrega
    ruta_inicio_latitude = models.FloatField(null=True, blank=True)  # Captura posición inicial GPS
    ruta_inicio_longitude = models.FloatField(null=True, blank=True)  # Captura posición inicial GPS
    ruta_final_latitude = models.FloatField(null=True, blank=True)  # Captura posición llegada GPS
    ruta_final_longitude = models.FloatField(null=True, blank=True)  # Captura posición llegada GPS
    distancia = models.FloatField(null=True, blank=True)  # Distancia entre la ruta inicial y final

    def __str__(self):
        return f"Envio de Caja {self.caja.id} por Transporte {self.transporte.id}"

class Pago(models.Model):
    enviocaja = models.ForeignKey('EnvioCaja',on_delete=models.CASCADE, null=True, blank=True)
    cliente = models.ForeignKey('Cliente', on_delete=models.CASCADE)
    monto = models.DecimalField(max_digits=10, decimal_places=2)
    fecha_pago = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Pago {self.id} de Cliente {self.cliente.id} por ${self.monto}"
























