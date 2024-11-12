from django.db import models, transaction
import qrcode
from io import BytesIO
from decimal import Decimal, InvalidOperation
from django.core.files.base import ContentFile
from .utils import get_coordinates
from django.core.validators import RegexValidator
from django.core.exceptions import ValidationError
import re
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
    rut = models.CharField(max_length=9, null=True, blank=True)
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
    rut = models.CharField(max_length=9, null=True, blank=True)
    password = models.CharField(max_length=10, null=True, blank=True)
    billetera = models.CharField(max_length=42, null=True, blank=True)
    def __str__(self):
        return self.nombre  # Mostrar el nombre del distribuidor

class Vehiculo(models.Model):
    MARCAS = [
        ('HYUNDAI', 'Hyundai'),
        ('MERCEDES_BENZ', 'Mercedes-Benz'),
        ('FOTON', 'Foton'),
        ('CHEVROLET', 'Chevrolet'),
        ('IVECO', 'Iveco'),
        ('HINO', 'Hino'),
    ]

    marca = models.CharField(max_length=20, choices=MARCAS,default='Hyundai')
    modelo = models.CharField(max_length=20 ,null=True,blank=False)
    patente = models.CharField(max_length=6, unique=True,null=True, validators=[RegexValidator(regex=r'^[A-Z]{4}\d{2}$', message='La patente debe tener el formato AAAA00.')])
    

    def clean(self):
        super().clean()
        if not re.match(r'^[A-Z]{4}\d{2}$', self.patente):
            raise ValidationError('La patente debe tener el formato AAAA00.')

# Modelo Distribuidor
class Distribuidor(models.Model):
    direccion = models.CharField(max_length=100, null=True, blank=True)
    nombre = models.CharField(max_length=100, null=True, blank=True)
    billetera = models.CharField(max_length=42, null=True, blank=True)
    rut = models.CharField(max_length=9, null=True, blank=True)
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
    rut = models.CharField(max_length=9, null=True, blank=True)
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
    producto = models.CharField(max_length=100, choices=[('tomate', 'Tomate'),('zanahoria','Zanahoria'),('lechuga','Lechuga'),('brócoli','Brócoli')])
    clasificacion = models.CharField(max_length=100,choices=[
        ('Hortaliza de Hoja', 'Hortaliza de Hoja'),
        ('Hortaliza de Fruto', 'Hortaliza de Fruto'),
        ('Hortaliza de Raíz', 'Hortaliza de Raíz'),
        ('Hortaliza de Flor', 'Hortaliza de Flor'),
    ])
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
        # Asignar automáticamente la clasificación basada en el producto
        if not self.clasificacion:
            if self.producto == 'lechuga':
                self.clasificacion = 'Hortaliza de Hoja'
            elif self.producto == 'tomate':
                self.clasificacion = 'Hortaliza de Fruto'
            elif self.producto == 'zanahoria':
                self.clasificacion = 'Hortaliza de Raíz'
            elif self.producto == 'brocoli':
                self.clasificacion = 'Hortaliza de Flor'
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
    vehiculo = models.ForeignKey(Vehiculo, on_delete=models.CASCADE , null=True)
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
        Actualiza el peso del pallet y la cantidad de cajas después de la creación de nuevas cajas
        basándose en la capacidad de las cajas según el tipo de caja.
        """
        # Calcular el peso total basado en la capacidad de las cajas (TipoCaja)
        peso_total_cajas = sum(caja.tipo_caja.capacidad for caja in nuevas_cajas if caja.tipo_caja is not None)
        
        # Verificar que el peso de las nuevas cajas no exceda el peso disponible del pallet
        if peso_total_cajas > self.peso_recepcion:
            raise ValueError("El peso de las nuevas cajas excede el peso restante del pallet.")
        
        # Actualizar el peso del pallet restando el peso de las nuevas cajas (basado en la capacidad)
        self.peso_recepcion -= peso_total_cajas

        # Acumular la cantidad de cajas creadas
        self.cantidad_cajas += len(nuevas_cajas)

        # Guardar la recepción con los valores actualizados
        self.save()

        return self.peso_recepcion

    def __str__(self):
        return f"Recepción {self.id} - Pallet {self.envio_pallet.pallet.id}"


class TipoCaja(models.Model):

    Material = models.CharField(max_length=20,choices=[
        ('carton', 'Cartón'),
        ('madera', 'Madera'),
    ],default='carton',blank=False)
    capacidad = models.DecimalField(max_digits=10, decimal_places=2,blank=False)
    recicable = models.BooleanField(default=False)
    def __str__(self):
        return self.Material  # Mostrar el nombre del distribuidor


class Caja(models.Model):
    recepcion = models.ForeignKey(Recepcion, on_delete=models.CASCADE, null=True, blank=True)  # Relación con Empaque
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, null=True, blank=True)  # Relación con cliente
    tipo_caja = models.ForeignKey(TipoCaja, on_delete=models.CASCADE, null=True,blank=True)
    qr_caja = models.ImageField(upload_to='qr_codes/', blank=True, null=True)
    fecha_caja = models.DateTimeField(auto_now_add=True, null=True)  # Fecha y hora actual al crear la caja, null=True para registros existentes
    estado_envio = models.CharField(max_length=100, choices=[('pendiente', 'Pendiente'), ('en_ruta', 'En Ruta'), ('entregado', 'Entregado')],default='pendiente')

    def save(self, *args, **kwargs):
        # Usamos una transacción para asegurar que ambos procesos se ejecuten correctamente
        with transaction.atomic():
            if self.recepcion and self.tipo_caja:
                # Obtener todas las cajas asociadas a la recepción
                cajas_existentes = Caja.objects.filter(recepcion=self.recepcion)
                
                # Calcular la capacidad total de las cajas actuales
                capacidad_total_existente = sum(caja.tipo_caja.capacidad for caja in cajas_existentes)
                
                # Capacidad de la caja actual que se está guardando
                capacidad_nueva_caja = self.tipo_caja.capacidad
                
                # Calcular la nueva capacidad total si se agrega esta nueva caja
                capacidad_total = capacidad_total_existente + capacidad_nueva_caja
                
                # Verificar si la nueva capacidad excede el peso del pallet
                if capacidad_total > self.recepcion.peso_recepcion:
                    raise ValueError("La capacidad total de las cajas excede el peso restante del pallet.")
                
                # Actualizar el peso y la cantidad en la recepción (si es necesario)
                self.recepcion.actualizar_peso_y_cantidad([self])  # Solo esta caja en la lista
            
            # Guardar el objeto inicialmente para obtener un pk (si aún no lo tiene)
            if self.pk is None:
                super().save(*args, **kwargs)

            # Generar QR si el cliente está asignado y aún no hay QR generado
            if  not self.qr_caja:
                qr_data = f'/seleccionar_caja/{self.pk}/'  # URL que redirige a la vista
                qr_code = generate_qr_code(qr_data)
                qr_image_name = f'caja_{self.pk}.png'
                self.qr_caja.save(qr_image_name, ContentFile(qr_code), save=False)

            # Guardar la caja nuevamente después de generar el QR
            super().save(*args, **kwargs)
            
class EnvioCaja(models.Model):
    caja = models.ForeignKey(Caja, on_delete=models.CASCADE)
    transporte = models.ForeignKey('Transporte', on_delete=models.CASCADE)
    vehiculo = models.ForeignKey(Vehiculo, on_delete=models.CASCADE, null= True)
    fecha_inicio = models.DateTimeField(auto_now_add=True)  # Captura la fecha y hora de inicio automáticamente
    fecha_llegada = models.DateTimeField(null=True, blank=True)  # Se llenará al finalizar la entrega
    ruta_inicio_latitude = models.FloatField(null=True, blank=True)  # Captura posición inicial GPS
    ruta_inicio_longitude = models.FloatField(null=True, blank=True)  # Captura posición inicial GPS
    ruta_final_latitude = models.FloatField(null=True, blank=True)  # Captura posición llegada GPS
    ruta_final_longitude = models.FloatField(null=True, blank=True)  # Captura posición llegada GPS
    distancia = models.FloatField(null=True, blank=True)  # Distancia entre la ruta inicial y final
    coordenadas_transporte = models.JSONField(null=True, blank=True)

    def __str__(self):
        return f"Envio de Caja {self.caja.id} por Transporte {self.transporte.id}"

class RecepcionCliente(models.Model):
    caja = models.ForeignKey('Caja',on_delete=models.CASCADE, null=True, blank=True)
    fecha = models.DateTimeField(auto_now_add=True)
    cliente_registrado = models.BooleanField(default=False)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)

    def __str__(self):
        return f"Recepcion {self.id} de Caja {self.caja} "
























