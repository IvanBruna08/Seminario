from django.db.models.query import QuerySet
from django.db import IntegrityError
from decimal import Decimal, InvalidOperation
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from web3 import Web3
from django.urls import reverse
from django.views import View
from django.db import transaction
from django.http import JsonResponse
import hashlib
import base64
from django.db.models import Sum, Count
from django.views.decorators.csrf import csrf_exempt
from .forms import ClienteForm,TransporteForm, PredioForm, DistribuidorForm, PalletForm,RecepcionForm,CustomLoginForm, DistribuidorPalletForm, CajaForm,TipoCajaForm,VehiculoForm
from django.contrib.auth.decorators import login_required
from django.core.files.base import ContentFile
from django.shortcuts import render, redirect
from .models import Predio, Distribuidor, Transporte, Cliente, Pallet, EnvioPallet,Recepcion,Caja,EnvioCaja,RecepcionCliente, DistribuidorPallet, TipoCaja, generate_qr_code, Vehiculo
import json
from django.contrib.admin.views.decorators import staff_member_required
import os
from datetime import datetime, timezone as dt_timezone
import requests
from django.contrib.auth import authenticate as django_authenticate
from django.conf import settings
from django.views.generic import ListView
from django.forms import formset_factory
from .utils import get_web3 , get_pallet_contract, get_transporte_contract, get_distribuidor_contract
from django.utils import timezone
from django.contrib import messages
from .decorators import login_required_for_model
from math import radians, sin, cos, sqrt, atan2
# Conectar con Ganache
ganache_url = "http://127.0.0.1:7545"
web3 = Web3(Web3.HTTPProvider(ganache_url))
if web3.is_connected():
    print("Conexión exitosa a Ganache.")
else:
    print("No se pudo conectar a Ganache.")
# VISTAS PRINCIPALES
def home(request):
    return render(request, 'home.html')

# proteger urls
# Función genérica para generar un hash seguro basado en cualquier ID
def generate_secure_url_id(model_name, record_id):
    unique_string = f"{model_name}-{record_id}"
    hash_object = hashlib.sha256(unique_string.encode())
    return base64.urlsafe_b64encode(hash_object.digest()).decode('utf-8')[:22]

# Función para validar el hash y obtener el ID original
def validate_and_recover_id(secure_id, model_name):
    # Esta función simula la validación del hash
    # Recorre todos los objetos del modelo correspondiente y compara el hash
    if model_name == "Pallet":
        for pallet in Pallet.objects.all():
            expected_secure_id = generate_secure_url_id("Pallet", pallet.id)
            if secure_id == expected_secure_id:
                return pallet.id
    elif model_name == "Caja":
        for caja in Caja.objects.all():
            expected_secure_id = generate_secure_url_id("Caja", caja.id)
            if secure_id == expected_secure_id:
                return caja.id
    return None
@login_required_for_model(Cliente)
@csrf_exempt
def cliente(request):
    # Acceder a los datos del usuario directamente desde la sesión
    user_id = request.session.get('user_id')
    user_type = request.session.get('user_type')

    # Obtener el cliente usando el user_id
    cliente_obj = get_object_or_404(Cliente, id=user_id)

    # Renderizar la plantilla del dashboard de cliente y pasar el nombre del cliente
    return render(request, 'dashboard_cliente.html', {
        'user_id': user_id,
        'user_type': user_type,
        'nombre_usuario': cliente_obj.nombre,  # Pasamos el nombre del cliente al contexto
    })

@login_required_for_model(Transporte)
@csrf_exempt
def transporte(request):
    # Obtener el estado de la entrega desde la sesión
    entrega_iniciada = request.session.get('entrega_iniciada', False)
    
    # Obtener el ID del pallet desde la sesión
    pallet_id = request.session.get('pallet_id')
    
    # Acceder a los datos del usuario directamente desde la sesión
    user_id = request.session.get('user_id')
    user_type = request.session.get('user_type')
    transporte_obj = get_object_or_404(Transporte, id=user_id)
    # Renderizar la plantilla del dashboard del transporte
    return render(request, 'dashboard_transporte.html', {
        'entrega_iniciada': entrega_iniciada,
        'pallet_id': pallet_id,
        'user_id': user_id,
        'user_type': user_type,
        'nombre_usuario': transporte_obj.nombre
    })

@login_required_for_model(Distribuidor)
@csrf_exempt
def distribuidor(request):
    # Acceder a los datos del usuario directamente desde la sesión
    user_id = request.session.get('user_id')
    user_type = request.session.get('user_type')

    # Renderizar la plantilla del dashboard de distribuidor
    return render(request, 'dashboard_distribuidor.html', {
        'user_id': user_id,
        'user_type': user_type,
    })

@login_required_for_model(Predio)
@csrf_exempt
def predio(request):
    # Acceder a los datos del usuario directamente desde la sesión
    user_id = request.session.get('user_id')
    user_type = request.session.get('user_type')

    # Renderizar la plantilla del dashboard de predio
    return render(request, 'dashboard_predio.html', {
        'user_id': user_id,
        'user_type': user_type,
    })

# REGISTRO DE LOS ACTORES
@csrf_exempt 
def registrar_predio(request):
    if request.method == 'POST':
        form = PredioForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')
    else:
        form = PredioForm()
    return render(request, 'registrar_predio.html', {'form': form})
@csrf_exempt
def registrar_transportista(request):
    if request.method == 'POST':
        form = TransporteForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')
    else:
        form = TransporteForm()
    return render(request, 'registrar_transportista.html', {'form': form})
@csrf_exempt
def registrar_distribuidor(request):
    if request.method == 'POST':
        form = DistribuidorForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')
    else:
        form = DistribuidorForm()
    return render(request, 'registrar_distribuidor.html', {'form': form})
@csrf_exempt
def registrar_cliente(request):
    if request.method == 'POST':
        form = ClienteForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')
    else:
        form = ClienteForm()
    return render(request, 'registrar_cliente.html', {'form': form})
# LOGIN DE LOS ACTORES
@staff_member_required
@csrf_exempt
def registro_actores(request):
    if request.method == 'POST':
        tipo_actor = request.POST.get('tipo_actor')  # Obtener el tipo de actor seleccionado
        
        # Redirigir a la URL de registro correspondiente según el tipo de actor
        if tipo_actor == 'cliente':
            return redirect('registrar_cliente')  # URL para el registro de cliente
        elif tipo_actor == 'predio':
            return redirect('registrar_predio')  # URL para el registro de predio
        elif tipo_actor == 'distribuidor':
            return redirect('registrar_distribuidor')  # URL para el registro de distribuidor
        elif tipo_actor == 'transporte':
            return redirect('registrar_transportista')  # URL para el registro de transporte
    return render(request, 'registro_actores.html')


@staff_member_required
@csrf_exempt
def registrar_vehiculo(request):
    if request.method == 'POST':
        form = VehiculoForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')
    else:
        form = VehiculoForm()
    return render(request, 'registrar_vehiculo.html', {'form': form})

@csrf_exempt
def custom_login(request):
    error_message = None
    next_url = request.GET.get('next')  # Captura la URL de redirección

    if request.method == 'POST':
        form = CustomLoginForm(request.POST)
        if form.is_valid():
            user = form.user
            user_type = form.user_type

            # Establecer la sesión del usuario
            request.session['user_id'] = user.id
            request.session['user_type'] = user_type

            # Redirigir a la vista específica según el tipo de usuario
            if next_url:  # Si hay una URL de redirección, usarla
                return redirect(next_url)

            # Redirigir a la vista específica según el tipo de usuario
            if user_type == 'cliente':
                return redirect('dashboard_cliente')
            elif user_type == 'distribuidor':
                return redirect('dashboard_distribuidor')
            elif user_type == 'transporte':
                return redirect('dashboard_transporte')
            elif user_type == 'predio':
                return redirect('dashboard_predio')
        else:
            error_message = form.errors.as_text()  # Captura los errores del formulario

    else:
        form = CustomLoginForm()

    return render(request, 'login.html', {'form': form, 'error_message': error_message})
def custom_logout(request):
    # Limpiar solo las claves del usuario
    request.session.pop('user_id', None)
    request.session.pop('user_type', None)
    
    # Redirigir o mostrar una página de confirmación de logout
    return redirect('login')

# ACCESO AL QR PARA CADA ACTOR DE PALLET
def seleccionar_opcion(request, pallet_id):
    # Asegúrate de que el usuario esté autenticado
    user_id = request.session.get('user_id')
    user_type = request.session.get('user_type')

    # Obtener el pallet
    pallet = get_object_or_404(Pallet, pk=pallet_id)

    # Generar un secure_id basado en el pallet_id
    secure_id = generate_secure_url_id('Pallet', pallet_id)

    # Redirigir según el tipo de actor, pero usando secure_id en la URL
    if user_type == 'cliente':
        return redirect('informacion_pallet', secure_id=secure_id)
    elif user_type == 'distribuidor':
        return redirect('registrar_recepcion', secure_id=secure_id)
    elif user_type == 'transporte':
        return redirect('transportar_pallet', secure_id=secure_id)
    elif user_type == 'predio':
        return redirect('informacion_pallet', secure_id=secure_id)

    # Redirigir a una vista de error si el tipo no es válido
    return redirect('login')

# CREAR PALLET
@login_required_for_model(Predio)
@csrf_exempt
def crear_pallet(request):
    user_id = request.session.get('user_id')
    if user_id:
        try:
            predio = Predio.objects.get(id=user_id)
        except Predio.DoesNotExist:
            return redirect('login')
        
        if request.method == 'POST':
            form = PalletForm(request.POST)
            if form.is_valid():
                pallet = form.save(commit=False)
                pallet.predio = predio
                pallet.save()
                # Llamada al contrato inteligente para registrar el pallet
                pallet_contract = get_pallet_contract()
                
                                # Obtener los datos necesarios del pallet
                id_pallet = pallet.id  # ID del pallet
                id_predio = predio.id  # ID del predio
                producto = pallet.producto  # Nombre del producto

                # Convertir la fecha de cosecha a timestamp
                fecha_cosecha_datetime = datetime(pallet.fecha_cosecha.year, pallet.fecha_cosecha.month, pallet.fecha_cosecha.day)
                fecha_cosecha_timestamp = int(fecha_cosecha_datetime.timestamp())

                # Convertir peso a entero escalado (por ejemplo, multiplicando por 10)
                factor_escala = 10
                peso_pallet = int(Decimal(pallet.peso) * factor_escala)

                # Transacción para registrar el pallet
                try:
                    tx_hash = pallet_contract.functions.registerPallet(
                        id_pallet,
                        id_predio,
                        producto,
                        fecha_cosecha_timestamp,
                        peso_pallet
                    ).transact({'from': web3.eth.accounts[0]})

                    tx_receipt = web3.eth.wait_for_transaction_receipt(tx_hash)
                    
                    print("Transacción exitosa:", tx_hash.hex())
                except ValueError as e:
                    print("Error al registrar el pallet en la blockchain:", e)
                    # Aquí podrías manejar el error como consideres necesario

                return redirect('dashboard_predio')
        else:
            form = PalletForm()
        
        return render(request, 'registrar_pallet.html', {'form': form})
    else:
        return redirect('login')
#TRANPORTAR CAJA Y PALLET
@login_required_for_model(Transporte)
@csrf_exempt
def iniciar_entrega(request, secure_id):
    # Validar el hash y recuperar el pallet_id original
    pallet_id = validate_and_recover_id(secure_id, 'Pallet')
    if pallet_id is None:
        # Si el hash no es válido, muestra un mensaje de error o redirige
        return render(request, 'error.html', {'message': 'ID no válido'})
    if request.method == 'POST':
        try:
            # Obtener las coordenadas iniciales del formulario
            vehiculo_id = request.POST.get('vehiculo_id')  # Obtener el ID del vehículo
            latitude = request.POST.get('ruta_inicio_latitude')
            longitude = request.POST.get('ruta_inicio_longitude')

            # Verificar que las coordenadas iniciales existan
            if latitude is None or longitude is None:
                return JsonResponse({'success': False, 'message': 'Faltan coordenadas iniciales'})

            # Obtener el objeto de transporte y pallet
            transporte = get_object_or_404(Transporte, id=request.session.get('user_id'))
            pallet = get_object_or_404(Pallet, id=pallet_id)
            # Obtener la instancia de Vehiculo utilizando el vehiculo_id
            vehiculo = get_object_or_404(Vehiculo, id=vehiculo_id)
            # Obtener todos los registros de DistribuidorPallet asociados al pallet
            distribuidores_pallet = DistribuidorPallet.objects.filter(pallet_id=pallet_id)

            if not distribuidores_pallet.exists():
                return JsonResponse({'success': False, 'message': 'No hay distribuidores asociados a este pallet'})

            # Actualizar el estado de cada distribuidor a 'en_proceso'
            distribuidores_pallet.update(estado_pallet='en_proceso')

            # Crear un nuevo registro de EnvioPallet
            envio = EnvioPallet.objects.create(
                pallet=pallet,
                transporte=transporte,
                fecha_inicio=timezone.now(),
                ruta_inicio_latitude=latitude,
                ruta_inicio_longitude=longitude,
                vehiculo = vehiculo,
                coordenadas_transporte=[],  # Inicializa como lista vacía
            )
            latitude_conversion = int(float(envio.ruta_inicio_latitude) * 10**10)
            longitude_conversion = int(float(envio.ruta_inicio_longitude) * 10**10)

            transporte_contracto = get_transporte_contract()
            try:
                tx_hash = transporte_contracto.functions.iniciarEnvioPallet(
                    envio.pallet.id,
                    envio.transporte.id,
                    envio.vehiculo.id,
                    latitude_conversion,
                    longitude_conversion
                ).transact({'from': web3.eth.accounts[1]})
                tx_receipt = web3.eth.wait_for_transaction_receipt(tx_hash)
                print("Transacción exitosa:", tx_hash.hex())
            except Exception as e:
                print("Error al registrar en la blockchain:", e)

            # Actualizar el estado del pallet a 'En Proceso'
            pallet.estado_envio = 'en_ruta'
            pallet.save()
            return JsonResponse({'success': True, 'envio_id': envio.id, 'pallet_id': pallet.id})
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})

    return JsonResponse({'success': False, 'message': 'Método no permitido'}, status=405)


@csrf_exempt
def finalizar_entrega(request, secure_id):
    print("Se ha recibido una solicitud en finalizar_entrega")
    # Validar el hash y recuperar el pallet_id original
    pallet_id = validate_and_recover_id(secure_id, 'Pallet')
    if pallet_id is None:
        # Si el hash no es válido, muestra un mensaje de error o redirige
        return render(request, 'error.html', {'message': 'ID no válido'})
    if request.method == 'POST':
        try:
            print("Se ha recibido una solicitud en finalizar_entrega 2")
            # Verifica si el contenido es JSON o un formulario
            if request.content_type == 'application/json':
                data = json.loads(request.body)
            else:
                data = request.POST

            # Obtén y convierte los valores a float cuando sea necesario
            latitude = data.get('ruta_final_latitude')
            longitude = data.get('ruta_final_longitude')
            envio_id = data.get('envio_id')

            # Valida los datos necesarios
            if not latitude or not longitude:
                return JsonResponse({'success': False, 'message': 'Faltan la latitud o la longitud.'})
            if not envio_id:
                return JsonResponse({'success': False, 'message': 'Falta el ID del envío.'})

            # Convierte latitud y longitud a float
            latitude = float(latitude)
            longitude = float(longitude)
            
            # Obtén el objeto de envío y el pallet
            envio = get_object_or_404(EnvioPallet, id=envio_id)
            pallet = get_object_or_404(Pallet, id=pallet_id)

            # Asignación de los valores
            envio.ruta_final_latitude = latitude
            envio.ruta_final_longitude = longitude
            envio.fecha_llegada = timezone.now()  # Mantiene la fecha en UTC, pero la convierte al mostrartiempos locales

            # Calcular distancia y guardar
            envio.distancia = calcular_distancia(
                envio.ruta_inicio_latitude,
                envio.ruta_inicio_longitude,
                envio.ruta_final_latitude,
                envio.ruta_final_longitude
            )
            envio.save()
            latitude_conversion = int(float(envio.ruta_final_latitude) * 10**10)
            longitude_conversion = int(float(envio.ruta_final_longitude) * 10**10)

            transporte_contracto = get_transporte_contract()
            try:
                tx_hash = transporte_contracto.functions.finalizarEnvioPallet(
                    envio.pallet.id,
                    latitude_conversion,
                    longitude_conversion
                ).transact({'from': web3.eth.accounts[1]})
                tx_receipt = web3.eth.wait_for_transaction_receipt(tx_hash)
                print("Transacción exitosa:", tx_hash.hex())
            except Exception as e:
                print("Error al registrar en la blockchain:", e)            

            # Actualizar el estado del pallet
            pallet.estado_envio = 'completado'
            pallet.save()

            return JsonResponse({'success': True, 'message': 'Entrega finalizada exitosamente.'})

        except ValueError as e:
            # Captura errores de conversión a float
            return JsonResponse({'success': False, 'message': f'Error en la conversión a número: {str(e)}'})

        except json.JSONDecodeError as e:
            # Captura errores de JSON
            print(f"Error decodificando JSON: {str(e)}")
            return JsonResponse({'success': False, 'message': 'Error en el formato JSON.'})

        except Exception as e:
            # Cualquier otro error
            return JsonResponse({'success': False, 'message': str(e)})

    return JsonResponse({'success': False, 'message': 'Método no permitido.'})
# Actualizar coordenadas para Pallet
@csrf_exempt
def actualizar_coordenadas(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            envio_id = data.get('envio_id')
            latitud = data.get('latitud')
            longitud = data.get('longitud')
            tiempo = data.get('tiempo')

            # Validar datos
            if not (envio_id and latitud and longitud and tiempo):
                return JsonResponse({'success': False, 'message': 'Datos incompletos.'})

            envio = get_object_or_404(EnvioPallet, id=envio_id)

            # Decodifica, actualiza y vuelve a codificar las coordenadas
            coordenadas = json.loads(envio.coordenadas_transporte or "[]")
            coordenadas.append({'latitud': latitud, 'longitud': longitud, 'tiempo': tiempo})
            envio.coordenadas_transporte = json.dumps(coordenadas)
            envio.save()

            return JsonResponse({'success': True, 'message': 'Coordenada actualizada exitosamente.'})

        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})

    return JsonResponse({'success': False, 'message': 'Método no permitido.'})
# Para Caja
@csrf_exempt
def actualizar_coordenadas_caja(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            enviocaja_id = data.get('enviocaja_id')
            latitud = data.get('latitud')
            longitud = data.get('longitud')
            tiempo = data.get('tiempo')

            # Validar datos
            if not (enviocaja_id and latitud and longitud and tiempo):
                return JsonResponse({'success': False, 'message': 'Datos incompletos.'})

            enviocaja = get_object_or_404(EnvioCaja, id=enviocaja_id)

            # Decodifica, actualiza y vuelve a codificar las coordenadas
            coordenadas = json.loads(enviocaja.coordenadas_transporte or "[]")
            coordenadas.append({'latitud': latitud, 'longitud': longitud, 'tiempo': tiempo})
            enviocaja.coordenadas_transporte = json.dumps(coordenadas)
            enviocaja.save()

            return JsonResponse({'success': True, 'message': 'Coordenada actualizada exitosamente.'})

        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})

    return JsonResponse({'success': False, 'message': 'Método no permitido.'})


def verificar_pallet(request):
    pallet_id = request.GET.get('id')  # Obtener el ID del pallet desde la solicitud
    # Obtener todos los DistribuidorPallet asociados a ese pallet
    distribuidor_pallets = DistribuidorPallet.objects.filter(pallet_id=pallet_id)
    
    # Verificar si todos los DistribuidorPallet tienen 'completado' en estado_pallet
    completados = all(dp.estado_pallet == 'completado' for dp in distribuidor_pallets)

    # Enviar una respuesta indicando si el pallet está completamente completado
    return JsonResponse({'completado': completados})

# PARA CAJA
def verificar_caja(request):
    caja_id = request.GET.get('id')  # Obtener el ID de la caja desde la solicitud

    # Obtener la instancia de la caja con el ID proporcionado
    try:
        caja = Caja.objects.get(id=caja_id)
    except Caja.DoesNotExist:
        return JsonResponse({'error': 'Caja no encontrada'}, status=404)

    # Verificar si el estado de la caja es 'entregado'
    entregado = caja.estado_envio == 'entregado'

    # Enviar una respuesta indicando si la caja está en estado 'entregado'
    return JsonResponse({'entregado': entregado})

@login_required_for_model(Transporte)
@csrf_exempt
def transportar_pallet(request, secure_id):
    # Validar el hash y recuperar el pallet_id original
    pallet_id = validate_and_recover_id(secure_id, 'Pallet')
    if pallet_id is None:
        # Si el hash no es válido, muestra un mensaje de error o redirige
        return render(request, 'error.html', {'message': 'ID no válido'})

    # Acceder al user_id y user_type desde la sesión
    transporte_id = request.session.get('user_id')
    user_type = request.session.get('user_type')

    # Obtener el pallet por su ID
    pallet = get_object_or_404(Pallet, id=pallet_id)

    if pallet.estado_envio in ['completado', 'en_ruta']:
        return render(request, 'error.html', {'message': 'El Pallet ya está en ruta o ha sido entregada, no se puede iniciar el transporte.'})
    
    # Obtener las distribuciones asociadas al pallet
    distribuciones = DistribuidorPallet.objects.filter(pallet=pallet)

    # Verificar si hay distribuidores asociados
    if not distribuciones.exists() or not any(d.distribuidor for d in distribuciones):
        messages.error(request, 'No hay distribuidores asociados a este pallet.')
        return redirect('dashboard_transporte')  # Redirigir a una lista de pallets o a donde desees

    # Asegurarse de que se esté trabajando con un transporte
    if user_type != 'transporte':
        messages.error(request, 'Acceso no autorizado.')
        return redirect('login')  # O podrías mostrar un mensaje de error

    # Obtener el objeto Transporte relacionado con el ID de la sesión
    transporte = get_object_or_404(Transporte, id=transporte_id)
    vehiculos = Vehiculo.objects.all()

    # Verificar si la lista de vehículos está vacía
    if not vehiculos.exists():
        messages.error(request, 'No hay vehículos registrados. No puedes iniciar la entrega sin seleccionar un vehículo.')
        return redirect('dashboard_transporte')  # Redirige al transporte a un panel de control o vista informativa
    # Crear una lista de distribuidores con sus coordenadas
    distribuidores_info = []
    for distribucion in distribuciones:
        distribuidor = distribucion.distribuidor  # Acceder al distribuidor asociado
        distribuidores_info.append({
            'distribuidor': distribuidor.nombre,  # Suponiendo que tiene un campo nombre
            'latitud': distribuidor.latitude,
            'longitud': distribuidor.longitude,
            'peso_enviado': distribucion.peso_enviado  # Agregar el peso enviado
        })

    # Renderizar la plantilla y pasar los datos
    return render(request, 'transportar_pallet.html', {
        'pallet': pallet,
        'transporte': transporte,
        'distribuidores_info': distribuidores_info,  # Lista con información de distribuidores
        'predio': pallet.predio,
        'vehiculos': vehiculos,
        'secure_id': secure_id
    })

# REGISTRAR LA RECEPCION DEL PALLET
@login_required_for_model(Distribuidor)
@csrf_exempt
def registrar_recepcion(request, secure_id):
    # Validar el hash y recuperar el pallet_id original
    pallet_id = validate_and_recover_id(secure_id, 'Pallet')
    if pallet_id is None:
        return render(request, 'error.html', {'message': 'ID no válido'})

    distribuidor_id = request.session.get('user_id')
    if not distribuidor_id:
        return redirect('login')
    
    pesaje_confirmado = request.session.get('pesaje_confirmado', False)
    if pesaje_confirmado:
        del request.session['pesaje_confirmado']

    pallet = get_object_or_404(Pallet, id=pallet_id)
    envio_pallet = get_object_or_404(EnvioPallet, pallet=pallet)
    distribuidor = get_object_or_404(Distribuidor, id=distribuidor_id)
    dp = DistribuidorPallet.objects.filter(distribuidor=distribuidor, pallet=pallet_id).first()
    if dp is None:
        return render(request, 'error.html', {'message': 'Este pallet no está asignado a su distribuidor.'})
        # Verificar si ya existe una recepción registrada para este pallet
    if Pallet.objects.filter(id=pallet_id, estado_envio='completado').exists():
        return render(request, 'error.html', {'message': 'El pallet ya ha sido recepcionado.'})

    if request.method == 'POST':
        form = RecepcionForm(request.POST, dp=dp)  # Aquí se pasa el pallet al formulario
        if form.is_valid():
            recepcion = form.save(commit=False)
            recepcion.envio_pallet = envio_pallet
            recepcion.distribuidor = distribuidor
            recepcion.peso_ingresado = recepcion.peso_recepcion
            recepcion.estado_recepcion='completado'
            recepcion.save()
            distribuidor_contract = get_distribuidor_contract()
            _pesoenvio = int(float(recepcion.peso_ingresado )* 10)
            try: 
                tx_hash = distribuidor_contract.functions.registerRecepcion(
                    recepcion.id,
                    envio_pallet.id,
                    _pesoenvio                
                ).transact({'from': web3.eth.accounts[2]})
                tx_receipt = web3.eth.wait_for_transaction_receipt(tx_hash)
                print("Transaccion exitosa:",tx_hash.hex())
            except ValueError as e:
                print("Error al registrar recepción:",e)

            DistribuidorPallet.objects.filter(
                pallet=pallet_id,
                distribuidor=distribuidor_id
            ).update(estado_pallet='completado')

        request.session['pesaje_confirmado'] = True  # Almacena el estado en la sesión

        return redirect('registrar_recepcion', secure_id=secure_id)

    else:
        form = RecepcionForm(dp=dp)  # Pasar el pallet al crear el formulario vacío

    return render(request, 'registrar_recepcion.html', {
        'pallet': pallet,
        'envio_pallet': envio_pallet,
        'dp': dp,
        'form': form,
        'secure_id': secure_id,
        'pesaje_confirmado': pesaje_confirmado
    })


# MOSTRAR INFORMACION DEL PALLET PARA PREDIO
@login_required_for_model(Predio)
def informacion_pallet(request, secure_id):
    # Validar el hash y recuperar el pallet_id original
    pallet_id = validate_and_recover_id(secure_id, 'Pallet')
    if pallet_id is None:
        # Si el hash no es válido, muestra un mensaje de error o redirige
        return render(request, 'error.html', {'message': 'ID no válido'})
    
    # Recuperar el pallet usando el ID original
    pallet = get_object_or_404(Pallet, id=pallet_id)
    predio = pallet.predio  # Acceder al predio relacionado con el pallet
    distribuciones = DistribuidorPallet.objects.filter(pallet=pallet)
    
    return render(request, 'informacion_pallet.html', {
        'pallet': pallet,
        'predio': predio,  # Pasar el predio al template
        'distribuciones': distribuciones,
    })
# Función para calcular la distancia entre dos coordenadas

def calcular_distancia(lat1, lon1, lat2, lon2):
    R = 6371  # Radio de la Tierra en kilómetros
    # Convertir de grados a radianes
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])

    # Diferencias entre latitudes y longitudes
    dlat = lat2 - lat1
    dlon = lon2 - lon1

    # Fórmula de Haversine
    a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    # Retornar distancia en kilómetros
    return R * c

# VIEWS PARA EMPAQUE
@login_required_for_model(Distribuidor)
def recepciones_completadas(request):
    distribuidor_id = request.session.get('user_id')  # Suponiendo que user_id es el ID del distribuidor
    """Vista para mostrar todas las recepciones completadas."""
    recepciones = Recepcion.objects.filter(estado_recepcion='completado',distribuidor = distribuidor_id)  # Obtener recepciones confirmadas
    return render(request, 'recepciones_completadas.html', {'recepciones': recepciones})


@login_required_for_model(Distribuidor)
@csrf_exempt
def distribuir_caja(request):
    distribuidor_id = request.session.get('user_id')
    recepciones = Recepcion.objects.filter(distribuidor=distribuidor_id)
    recepcion = None
    tipocaja = TipoCaja.objects.all()
    errores = []

    if request.method == 'POST':
        recepcion_id = request.POST.get('recepcion_id')
        if recepcion_id:
            recepcion = get_object_or_404(Recepcion, id=recepcion_id)
            cantidad_cajas = int(request.POST.get('cantidad_cajas', 0))
            nuevas_cajas = []
            peso_total_cajas = 0  # Sumar pesos de los tipos de caja seleccionados

            for i in range(1, cantidad_cajas + 1):
                # Procesar el formulario para cada caja
                caja_form = CajaForm(request.POST, prefix=f'caja_{i}', recepcion=recepcion)

                if caja_form.is_valid():
                    caja = caja_form.save(commit=False)
                    caja.recepcion = recepcion
                    
                    # Obtener el tipo de caja seleccionado
                    tipo_caja = caja_form.cleaned_data['tipo_caja']
                    
                    # Obtener el peso del tipo de caja
                    peso_caja = tipo_caja.capacidad
                    
                    # Sumar el peso del tipo de caja al total
                    peso_total_cajas += peso_caja
                    
                    # Agregar la caja a la lista de cajas a guardar
                    nuevas_cajas.append(caja)
                else:
                    # Capturar errores del formulario
                    for field, field_errors in caja_form.errors.items():
                        for error in field_errors:
                            errores.append(f'Error en la caja {i}: {error}')

            # Validar que la suma de los pesos de los tipos de caja no exceda el peso del pallet (recepción)
            if peso_total_cajas > recepcion.peso_recepcion:
                errores.append(f'La suma de las capacidades de las cajas ({peso_total_cajas} kg) no puede ser mayor al peso total de la recepción ({recepcion.peso_recepcion} kg).')

            if not errores:
                try:
                    with transaction.atomic():
                        # Guardar cada caja
                        for caja in nuevas_cajas:
                            caja.save()
                            distribuidor_contract = get_distribuidor_contract()
                            try: 
                                tx_hash = distribuidor_contract.functions.registerCaja(
                                    caja.id,
                                    recepcion.id,
                                    caja.tipo_caja.id            
                                ).transact({'from': web3.eth.accounts[2]})
                                tx_receipt = web3.eth.wait_for_transaction_receipt(tx_hash.hex())
                                print("Transaccion exitosa:",tx_hash.hex())
                            except ValueError as e:
                                print("Error al registrar recepción:",e)
                    return redirect('dashboard_distribuidor')
                except ValueError as e:
                    errores.append(str(e))

    recepciones = Recepcion.objects.filter(estado_recepcion='completado', distribuidor=distribuidor_id)
    return render(request, 'distribuir_caja.html', {
        'recepciones': recepciones,
        'recepcion': recepcion,
        'errores': errores,
        'tipocaja': tipocaja,
    })

# lo mismo para pallet 
@login_required_for_model(Predio)
@csrf_exempt
def distribuir_pallet(request):
    # Obtener todos los pallets disponibles
    predio_id = request.session.get('user_id')  # Suponiendo que user_id es el ID del distribuidor
    pallets = Pallet.objects.filter(predio=predio_id).annotate(num_distribuciones=Count('distribuidorpallet')).filter(num_distribuciones=0)
    distribuidores = Distribuidor.objects.all()
    errores = []
    pallet = None

    if request.method == 'POST':
        pallet_contract = get_pallet_contract()
        factor_escala = 10
        # Obtener el ID del pallet seleccionado
        pallet_id = request.POST.get('pallet_id')
        if pallet_id:
            pallet = get_object_or_404(Pallet, id=pallet_id)

            # Obtener el número de distribuidores
            cantidad_distribuidores = int(request.POST.get('cantidad_distribuidores', 0))
            nuevas_distribuciones = []

            # Inicializar la suma de pesos enviados ya existentes
            suma_pesos_distribuidores = DistribuidorPallet.objects.filter(pallet=pallet).aggregate(Sum('peso_enviado'))['peso_enviado__sum'] or 0

            for i in range(1, cantidad_distribuidores + 1):
                # Crear el formulario para cada distribuidor
                distribuidor_form = DistribuidorPalletForm(request.POST, prefix=f'distribuidor_{i}')

                if distribuidor_form.is_valid():
                    distribucion = distribuidor_form.save(commit=False)
                    distribucion.pallet = pallet  # Relacionar el pallet
                    peso_total_con_nuevo = suma_pesos_distribuidores + (distribucion.peso_enviado or 0)

                    # Validar que la suma de los pesos no sea mayor al peso total del pallet
                    if peso_total_con_nuevo > pallet.peso:
                        errores.append(f'La suma del peso asignado ({peso_total_con_nuevo} kg) supera el peso total del pallet ({pallet.peso} kg) para el distribuidor {distribucion.distribuidor}.')
                        continue

                    # Si la validación es exitosa, agregar a la lista de nuevas distribuciones
                    nuevas_distribuciones.append(distribucion)
                    suma_pesos_distribuidores = peso_total_con_nuevo  # Actualizar la suma de pesos enviados

                else:
                    errores.append(f"Error en la distribución del distribuidor {i}: {distribuidor_form.errors}")

            # Verificar si la suma final de los pesos es exactamente igual al peso del pallet
            if suma_pesos_distribuidores != pallet.peso:
                errores.append(f'La suma total del peso distribuido ({suma_pesos_distribuidores} kg) no coincide con el peso total del pallet ({pallet.peso} kg). Debe distribuirse todo el peso.')

            # Si no hay errores, guardar las nuevas distribuciones
            if not errores:
                try:
                    with transaction.atomic():
                        for distribucion in nuevas_distribuciones:
                            distribucion.save()  # Guardar cada distribución

                            id_distribuidor_pallet = distribucion.id
                            id_pallet = distribucion.pallet.id  # Asegúrate de tener esta relación en el modelo
                            id_distribuidor = distribucion.distribuidor.id  # Asegúrate de tener esta relación en el modelo
                            peso_envio = int(Decimal(distribucion.peso_enviado) * factor_escala) 
                            try:
                                tx_hash = pallet_contract.functions.registerDistribuidorPallet(
                                    id_distribuidor_pallet,
                                    id_pallet,
                                    id_distribuidor,
                                    peso_envio
                                ).transact({'from': web3.eth.accounts[0]})

                                # Esperar el recibo de la transacción
                                tx_receipt = web3.eth.wait_for_transaction_receipt(tx_hash)
                                print(f"DistribuidorPallet registrado exitosamente en la blockchain: {tx_hash.hex()}")
                            except Exception as e:

                                print(f"Error en la transacción de DistribuidorPallet con id {id_distribuidor_pallet}: {e}")
                                raise e

                    return redirect('dashboard_predio')

                except ValueError as e:
                    errores.append(str(e))

    return render(request, 'distribuir_pallet.html', {
        'pallets': pallets,
        'pallet': pallet,
        'distribuidores': distribuidores,
        'errores': errores,
    })

# lo mismo para pallet 
@login_required_for_model(Predio)
@csrf_exempt
def pallet_view(request):
    """Vista para gestionar las cajas de un empaque específico o mostrar todas las cajas y empaques."""
    
    # Obtener el ID del empaque desde los parámetros GET
    predio_id = request.session.get('user_id')  # Suponiendo que user_id es el ID del distribuidor
    pallet_id = request.GET.get('pallet_id')  # Obtener el ID del empaque desde los parámetros GET
    pallets = Pallet.objects.filter(predio = predio_id)  # Obtener todos los empaques
    
    if pallet_id:
        # Si se selecciona un ID de empaque, filtrar las cajas asociadas a ese empaque
        pallet = get_object_or_404(Pallet, id=pallet_id)
        distribuidores = DistribuidorPallet.objects.filter(pallet=pallet)  # Obtener cajas asociadas al empaque
    else:
        pallet = None  # No se ha seleccionado ningún empaque
        distribuidores = DistribuidorPallet.objects.all()  # Obtener todas las cajas si no se selecciona un empaque

    return render(request, 'pallet_view.html', {
        'pallets': pallets,  # Lista de empaques para seleccionar
        'pallet': pallet,  # Empaque seleccionado (si hay alguno)
        'distribuidores': distribuidores,  # Lista de cajas (todas o filtradas por empaque)
    })

@login_required_for_model(Distribuidor)
@csrf_exempt
def cajas_view(request):
    """Vista para gestionar las cajas asociadas a un distribuidor específico o mostrar las cajas filtradas por recepción."""
    
    # Obtener el ID del distribuidor que ha iniciado sesión
    distribuidor_id = request.session.get('user_id')  # Suponiendo que user_id es el ID del distribuidor
    if not distribuidor_id:
        # Si no hay un distribuidor autenticado, redirigir o mostrar un mensaje adecuado
        return render(request, 'error.html', {'message': 'No ha iniciado sesión como distribuidor.'})
    
    # Obtener las recepciones asociadas al distribuidor
    recepciones = Recepcion.objects.filter(distribuidor=distribuidor_id,cantidad_cajas__gt=0)
    
    # Obtener el ID de la recepción seleccionada desde los parámetros GET
    recepcion_id = request.GET.get('recepcion_id')
    
    if recepcion_id:
        # Si se selecciona una recepción, filtrar las cajas asociadas a esa recepción y distribuidor
        recepcion = get_object_or_404(Recepcion, id=recepcion_id, distribuidor=distribuidor_id)
        cajas = Caja.objects.filter(recepcion=recepcion)
    else:
        # Si no se selecciona ninguna recepción, mostrar un mensaje
        recepcion = None
        cajas = []
    
    return render(request, 'cajas_view.html', {
        'recepciones': recepciones,  # Lista de recepciones asociadas al distribuidor
        'recepcion': recepcion,  # Recepción seleccionada (si se ha seleccionado alguna)
        'cajas': cajas,  # Cajas filtradas por la recepción seleccionada
        'mensaje': "Por favor seleccione una recepción para ver las cajas." if not recepcion_id else "",
    })


# ACCESO AL QR PARA CADA ACTOR DE PALLET

def seleccionar_caja(request, caja_id):
    # Asegúrate de que el usuario esté autenticado
    user_id = request.session.get('user_id')
    user_type = request.session.get('user_type')

    # Obtener la caja
    caja = get_object_or_404(Caja, pk=caja_id)

    # Generar un secure_id basado en el caja_id
    secure_id = generate_secure_url_id('Caja', caja_id)

    # Redirigir según el tipo de actor, pero usando secure_id en la URL
    if user_type == 'cliente' or user_type is None:
        return redirect('recibir_caja', secure_id=secure_id)
    elif user_type == 'transporte':
        return redirect('transportar_caja', secure_id=secure_id)
    elif user_type == 'distribuidor':
        return redirect('informacion_caja', secure_id=secure_id)
    # Redirigir a una vista de error si el tipo no es válido
    return redirect('login')


@login_required_for_model(Distribuidor)
@csrf_exempt
def informacion_caja(request, secure_id):
    # Validar el hash y recuperar el pallet_id original
    caja_id = validate_and_recover_id(secure_id, 'Caja')
    if secure_id is None:
        # Si el hash no es válido, muestra un mensaje de error o redirige
        return render(request, 'error.html', {'message': 'ID no válido'})
    caja = get_object_or_404(Caja, id=caja_id)
    cliente = caja.cliente
    recepcion = caja.recepcion
    envio_pallet = recepcion.envio_pallet
    pallet = envio_pallet.pallet
    predio = pallet.predio  # Asumiendo que hay una relación en el modelo Pallet
    return render(request, 'informacion_caja.html', {
        'caja': caja,
        'recepcion': recepcion,
        'envio_pallet': envio_pallet,
        'pallet': pallet,
        'predio': predio,
        'cliente': cliente
        })

@login_required_for_model(Transporte)
@csrf_exempt
def transportar_caja(request, secure_id):
    # Validar el hash y recuperar el pallet_id original
    caja_id = validate_and_recover_id(secure_id, 'Caja')
    if secure_id is None:
        # Si el hash no es válido, muestra un mensaje de error o redirige
        return render(request, 'error.html', {'message': 'ID no válido'})
    # Acceder al user_id y user_type desde la sesión
    transporte_id = request.session.get('user_id')
    user_type = request.session.get('user_type')
    
    # Obtener el pallet por su ID
    caja = get_object_or_404(Caja, id=caja_id)
    cliente = caja.cliente
    recepcion = caja.recepcion
    distribuidor=recepcion.distribuidor
    envio_pallet = recepcion.envio_pallet
    pallet = envio_pallet.pallet
    predio= pallet.predio
    # Validar el estado de la caja
    if caja.estado_envio in ['entregado', 'en_ruta']:
        return render(request, 'error.html', {'message': 'La caja ya está en ruta o ha sido entregada, no se puede iniciar el transporte.'})
    
    # Asegurarse de que se esté trabajando con un transporte
    if user_type != 'transporte':
        # Si no es un transporte, redirigir o mostrar un error
        return redirect('login')  # O podrías mostrar un mensaje de error

    # Obtener el objeto Transporte relacionado con el ID de la sesión
    transporte = get_object_or_404(Transporte, id=transporte_id)
    vehiculos = Vehiculo.objects.all()

    # Verificar si la lista de vehículos está vacía
    if not vehiculos.exists():
        messages.error(request, 'No hay vehículos registrados. No puedes iniciar la entrega sin seleccionar un vehículo.')
        return redirect('dashboard_transporte')  # Redirige al transporte a un panel de control o vista informativa
    
    # Renderizar la plantilla y pasar los datos
    return render(request, 'transportar_caja.html', {
        'caja': caja,
        'transporte': transporte,
        'cliente': cliente,
        'recepcion': recepcion,
        'envio_pallet': envio_pallet,
        'pallet': pallet,
        'vehiculos':vehiculos,
        'predio': predio,
        'distribuidor':distribuidor,
        'secure_id': secure_id
    })

@csrf_exempt
def iniciar_entrega_caja(request, secure_id):
    # Validar el hash y recuperar el caja_id original
    caja_id = validate_and_recover_id(secure_id, 'Caja')
    if caja_id is None:
        return JsonResponse({"error": "ID no válido"}, status=400)

    if request.method == "POST":
        try:
            # Obtener el ID del transporte desde la sesión
            transporte_id = request.session.get('user_id')
            transporte = get_object_or_404(Transporte, id=transporte_id)
            vehiculo_id = request.POST.get('vehiculo_id')

            # Obtener la caja y su envío relacionado
            caja = get_object_or_404(Caja, id=caja_id)
            # Validar que el vehículo existe
            vehiculo = get_object_or_404(Vehiculo, id=vehiculo_id)

            # Verifica si las coordenadas se están enviando por primera vez
            if 'ruta_inicio_latitude' in request.POST and 'ruta_inicio_longitude' in request.POST:
                # Obtener coordenadas iniciales
                latitude = request.POST.get('ruta_inicio_latitude')
                longitude = request.POST.get('ruta_inicio_longitude')

                if latitude is None or longitude is None:
                    return JsonResponse({'success': False, 'message': 'Faltan coordenadas iniciales'})

                # Crear un nuevo registro de EnvioCaja
                envio_caja = EnvioCaja.objects.create(
                    caja=caja,
                    transporte=transporte,
                    ruta_inicio_latitude=latitude,
                    ruta_inicio_longitude=longitude,
                    fecha_inicio=timezone.now(),
                    vehiculo=vehiculo
                    # Asignar el vehículo (asegúrate de que el modelo tiene este campo)
                )
                caja.estado_envio = 'en_ruta'
                caja.save()
                latitude_conversion = int(float(envio_caja.ruta_inicio_latitude) * 10**10)
                longitude_conversion = int(float(envio_caja.ruta_inicio_longitude) * 10**10)

                transporte_contracto = get_transporte_contract()
                try:
                    tx_hash = transporte_contracto.functions.iniciarEnvioCaja(
                        envio_caja.caja.id,
                        envio_caja.transporte.id,
                        envio_caja.vehiculo.id,
                        latitude_conversion,
                        longitude_conversion,
                    ).transact({'from': web3.eth.accounts[1]})
                    tx_receipt = web3.eth.wait_for_transaction_receipt(tx_hash)
                    print("Transacción exitosa:", tx_hash.hex())
                except Exception as e:
                    print("Error al registrar en la blockchain:", e)   
                # Devolver una respuesta JSON con el ID de la caja y el envío creado
            return JsonResponse({'success': True, 'envio_caja_id': envio_caja.id, 'caja_id': caja.id})

        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})

    return JsonResponse({'success': False, 'message': 'Método no permitido'}, status=405)

                

@csrf_exempt
def finalizar_entrega_caja(request, secure_id):
    # Validar el hash y recuperar el caja_id original
    caja_id = validate_and_recover_id(secure_id, 'Caja')
    
    if secure_id is None:
        # Si el hash no es válido, muestra un mensaje de error o redirige
        return render(request, 'error.html', {'message': 'ID no válido'})
    
    if request.method == "POST":
        try:
            # Verifica si el contenido es JSON o un formulario
            if request.content_type == 'application/json':
                data = json.loads(request.body)
            else:
                data = request.POST

            # Obtén y convierte los valores a float cuando sea necesario
            latitude = data.get('ruta_final_latitude')  # Cambiado de 'latitude' a 'ruta_final_latitude'
            longitude = data.get('ruta_final_longitude')  # Cambiado de 'longitude' a 'ruta_final_longitude'
            enviocaja_id = data.get('enviocaja_id')
            print(latitude)
            print(longitude)
            # Valida los datos necesarios
            if not latitude or not longitude:
                return JsonResponse({'success': False, 'message': 'Faltan la latitud o la longitud.'})
            if not enviocaja_id:
                return JsonResponse({'success': False, 'message': 'Falta el ID del envío.'})

            # Convierte latitud y longitud a float
            latitude = float(latitude)
            longitude = float(longitude)
            # Obtén el objeto de envío
            enviocaja = get_object_or_404(EnvioCaja, id=enviocaja_id)
            print(enviocaja_id)
            # Asignación de los valores
            enviocaja.ruta_final_latitude = latitude
            enviocaja.ruta_final_longitude = longitude
            enviocaja.fecha_llegada = timezone.now()  # Mantiene la fecha en UTC

            # Calcular distancia y guardar
            enviocaja.distancia = calcular_distancia(
                enviocaja.ruta_inicio_latitude,
                enviocaja.ruta_inicio_longitude,
                enviocaja.ruta_final_latitude,
                enviocaja.ruta_final_longitude
            )
            enviocaja.save()
            latitude_conversion = int(float(enviocaja.ruta_final_latitude) * 10**10)
            longitude_conversion = int(float(enviocaja.ruta_final_longitude) * 10**10)

            transporte_contracto = get_transporte_contract()
            try:
                tx_hash = transporte_contracto.functions.finalizarEnvioCaja(
                    enviocaja.caja.id,
                    latitude_conversion,
                    longitude_conversion
                ).transact({'from': web3.eth.accounts[1]})
                tx_receipt = web3.eth.wait_for_transaction_receipt(tx_hash)
                print("Transacción exitosa:", tx_hash.hex())
            except Exception as e:
                print("Error al registrar en la blockchain:", e) 
            # Respuesta para AJAX
            return JsonResponse({'success': True, 'message': 'Entrega finalizada con éxito.'})

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    # En caso de un método no soportado o el retorno de una respuesta GET, se podría mostrar un error o alguna información básica
    return JsonResponse({'success': False, 'message': 'Método no soportado'}, status=405)

@csrf_exempt
def recibir_caja(request, secure_id):
    # Validar el hash y recuperar el ID original de la caja-------------
    caja_id = validate_and_recover_id(secure_id, 'Caja')
    if caja_id is None:
        return render(request, 'error.html', {'message': 'ID no válido'})
    
    if RecepcionCliente.objects.filter(caja_id=caja_id).exists():
        return render(request, 'error.html', {'message': 'Esta caja ya fue registrada.'})

    # Obtener la caja por su ID antes de manejar el método POST o GET
    try:
        caja = get_object_or_404(Caja, id=caja_id)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
    hay_envio = EnvioCaja.objects.filter(caja=caja).exists()
    envio_caja = EnvioCaja.objects.filter(caja=caja).first()  # Usar first() para evitar errores 404
    if request.method == "GET":
        return render(request, 'recibir_caja.html', {'caja': caja, 'secure_id': secure_id,'hay_envio':hay_envio,'envio_caja':envio_caja})


    elif request.method == "POST":
        try:
            # Determinar si la caja tiene un cliente asignado
            cliente_registrado = caja.cliente is not None

            # Capturar la posición del cliente
            latitude = request.POST.get('latitude')
            longitude = request.POST.get('longitude')

            # Guardar el registro de la recepción
            recepcion = RecepcionCliente(
                caja=caja,
                cliente_registrado=cliente_registrado,
                latitude=latitude,
                longitude=longitude
            )
            recepcion.save()
            distribuidor_contracto = get_distribuidor_contract()
            latitude_conversion = int(float(recepcion.latitude) * 10**10)
            longitude_conversion = int(float(recepcion.longitude) * 10**10)
            fecha_recepcion = int(recepcion.fecha.timestamp())
            try:
                tx_hash = distribuidor_contracto.functions.registerRecepcionCliente(
                    recepcion.id,
                    recepcion.caja.id,
                    fecha_recepcion,
                    latitude_conversion,
                    longitude_conversion
                ).transact({'from': web3.eth.accounts[1]})
                tx_receipt = web3.eth.wait_for_transaction_receipt(tx_hash)
                print("Transacción exitosa:", tx_hash.hex())
            except Exception as e:
                print("Error al registrar en la blockchain:", e) 

            Caja.objects.filter(id=caja_id).update(estado_envio='entregado')

            # Generar la URL para la vista de detalles de la caja
            informacion_qr = request.build_absolute_uri(reverse('detalles_caja', args=[secure_id]))
            qr_code_data = informacion_qr  # Almacena la URL completa en el QR
            qr_code = generate_qr_code(qr_code_data)

            # Crear un archivo temporal para el QR
            qr_image_name = f'informacion_caja_{secure_id}.png'
            qr_content = ContentFile(qr_code)

            # Preparar el archivo para su descarga
            response = HttpResponse(qr_content, content_type='image/png')
            response['Content-Disposition'] = f'attachment; filename="{qr_image_name}"'
            response['X-Redirect'] = request.build_absolute_uri('/login')
            return response

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    # This can be reached in a case of an unexpected method (if needed)
    return render(request, 'recibir_caja.html', {'caja': caja, 'secure_id': secure_id,'hay_envio': hay_envio,'envio_caja':envio_caja})  # Agregar user_id al contexto})



@login_required_for_model(Distribuidor)
def tipocaja(request):
    if request.method == 'POST':
        form = TipoCajaForm(request.POST)
        if form.is_valid():
            form.save()  # Guarda el nuevo TipoCaja en la base de datos
            return redirect('dashboard_distribuidor')  # Redirige a la lista de tipos de caja
    else:
        form = TipoCajaForm()
    
    return render(request, 'crear_caja.html', {'form': form})

@login_required_for_model(Distribuidor)
@csrf_exempt
def asignar_cliente(request):
    distribuidor_id = request.session.get('user_id')
    # Filtrar las cajas del distribuidor sin cliente asignado
    cajas = Caja.objects.filter(recepcion__distribuidor=distribuidor_id, cliente__isnull=True,estado_envio='pendiente')
    clientes = Cliente.objects.all()  # Todos los clientes disponibles
    errores = []

    if request.method == 'POST':
        # Obtén las cajas seleccionadas desde el formulario
        cajas_seleccionadas = request.POST.getlist('cajas')  # Lista de IDs de cajas seleccionadas
        cliente_id = request.POST.get('cliente_id')  # Cliente seleccionado

        if cajas_seleccionadas:
            # Si se seleccionó un cliente
            cliente = None
            if cliente_id:
                cliente = get_object_or_404(Cliente, id=cliente_id)

            try:
                with transaction.atomic():
                    # Actualizar las cajas seleccionadas
                    for caja_id in cajas_seleccionadas:
                        caja = Caja.objects.get(id=caja_id)
                        caja.cliente = cliente  # Asigna el cliente o deja None
                        caja.save()  # Guarda la caja actualizada
                        distribuidor_contract = get_distribuidor_contract()
                        try: 
                                tx_hash = distribuidor_contract.functions.asignarClienteACaja(
                                    caja.id,
                                    caja.cliente.id            
                                ).transact({'from': web3.eth.accounts[2]})
                                tx_receipt = web3.eth.wait_for_transaction_receipt(tx_hash.hex())
                                print("Transaccion exitosa:",tx_hash.hex())
                        except ValueError as e:
                                print("Error al registrar recepción:",e)
                return redirect('dashboard_distribuidor')  # Redirige al confirmar
            except Exception as e:
                errores.append(f"Error al asignar cliente a las cajas: {str(e)}")
        else:
            errores.append("Debe seleccionar al menos una caja.")

    return render(request, 'asignar_cliente.html', {
        'cajas': cajas,
        'clientes': clientes,
        'errores': errores,
    })
@csrf_exempt
def actualizar_pallet(request):
    predio_id = request.session.get('user_id')
    pallets = Pallet.objects.filter(predio=predio_id,estado_envio='pendiente')

    if request.method == 'POST':
        # Aquí podrías manejar la lógica para actualizar según la opción seleccionada
        pallet_id = request.POST.get('pallet_id')
        action = request.POST.get('action')

        if action == 'actualizar_datos':
            return redirect('actualizar_datos_pallet', pallet_id=pallet_id)  # Redirigir a la vista específica para actualizar datos del pallet

        elif action == 'eliminar_distribuidor':
            return redirect('eliminar_distribuidor', pallet_id=pallet_id)  # Redirigir a la vista específica para eliminar un distribuidor

        elif action == 'añadir_distribuidor':
            return redirect('añadir_distribuidor', pallet_id=pallet_id)  # Redirigir a la vista específica para añadir un distribuidor

    context = {
        'pallets': pallets,
    }
    return render(request, 'actualizar_pallet.html', context)
@csrf_exempt
def actualizar_datos_pallet(request, pallet_id):
    # Obtener el pallet correspondiente
    pallet = get_object_or_404(Pallet, id=pallet_id)
    # Obtener los distribuidores asociados al pallet
    distribuidores = DistribuidorPallet.objects.filter(pallet=pallet)

    if request.method == 'POST':
        form = PalletForm(request.POST, instance=pallet)

        if form.is_valid():
            # Guardar los datos del pallet
            pallet_actualizado = form.save()
            pallet_contract = get_pallet_contract()

            # Obtener los datos necesarios para actualizar el pallet en la blockchain
            id_pallet = pallet_actualizado.id
            id_predio = pallet_actualizado.predio.id  # Asumiendo que hay una relación con Predio
            producto = pallet_actualizado.producto
            fecha_cosecha_datetime = datetime(pallet_actualizado.fecha_cosecha.year, pallet_actualizado.fecha_cosecha.month, pallet_actualizado.fecha_cosecha.day)
            fecha_cosecha_timestamp = int(fecha_cosecha_datetime.timestamp())
            factor_escala = 10
            peso_pallet = int(Decimal(pallet_actualizado.peso) * factor_escala)  # Escalado del peso

            # Transacción para actualizar el pallet en la blockchain
            try:
                tx_hash = pallet_contract.functions.updatePallet(
                    id_pallet,
                    id_predio,
                    producto,
                    fecha_cosecha_timestamp,
                    peso_pallet
                ).transact({'from': web3.eth.accounts[0]})

                tx_receipt = web3.eth.wait_for_transaction_receipt(tx_hash)
                print("Transacción exitosa:", tx_hash.hex())
            except ValueError as e:
                print("Error al registrar el pallet en la blockchain:", e)

            # Si no hay distribuidores, redirigir después de guardar
            if not distribuidores.exists():
                messages.success(request, 'Pallet actualizado correctamente. No hay distribuidores asociados.')
                return redirect('actualizar_pallet')

            # Si hay distribuidores, proceder a actualizar pesos
            nuevo_peso_pallet = form.cleaned_data['peso']
            total_peso_distribuidores = 0

            # Actualizar pesos de los distribuidores
            for distribuidor in distribuidores:
                distribuidor_peso_field = f"peso_enviado_{distribuidor.id}"
                nuevo_peso_distribuidor = request.POST.get(distribuidor_peso_field)

                if nuevo_peso_distribuidor:
                    try:
                        distribuidor.peso_enviado = float(nuevo_peso_distribuidor)
                        distribuidor.save()  # Guardar cambios en el DistribuidorPallet
                        total_peso_distribuidores += float(nuevo_peso_distribuidor)

                        # Convertir el peso a entero aplicando factor_escala para enviarlo a la blockchain
                        peso_distribuidor_escalado = int(float(nuevo_peso_distribuidor) * factor_escala)

                        # Actualizar el distribuidor en la blockchain
                        try:
                            # Acceder al ID del distribuidor desde la clave foránea
                            distribuidor_id = distribuidor.distribuidor.id  # Obtener el ID del distribuidor
                            print(f"ID Distribuidor: {distribuidor_id}")

                            tx_hash = pallet_contract.functions.updateDistribuidorPallet(
                                distribuidor.id,  # ID del DistribuidorPallet
                                pallet.id,  # ID del pallet
                                distribuidor_id,  # ID del distribuidor (usando distribuidor.id)
                                peso_distribuidor_escalado  # Nuevo peso de envío escalado
                            ).transact({'from': web3.eth.accounts[0]})

                            # Esperar la transacción
                            tx_receipt = web3.eth.wait_for_transaction_receipt(tx_hash)
                            print(f"Transacción exitosa para distribuidor {distribuidor.id}: {tx_hash.hex()}")
                        except Exception as e:
                            print(f"Error al actualizar DistribuidorPallet {distribuidor.id} en la blockchain:", e)

                    except ValueError:
                        messages.error(request, "El peso ingresado no es válido.")
                        return redirect('actualizar_datos_pallet', pallet_id=pallet_id)

            # Validar que el peso total de los distribuidores coincida con el peso del pallet
            if total_peso_distribuidores != nuevo_peso_pallet:
                messages.error(request, f"El peso total de los distribuidores ({total_peso_distribuidores}) debe ser igual al peso del pallet ({nuevo_peso_pallet}).")
                return redirect('actualizar_datos_pallet', pallet_id=pallet_id)

            messages.success(request, 'Pallet y pesos de distribuidores actualizados correctamente.')
            return redirect('actualizar_pallet')

    else:
        form = PalletForm(instance=pallet)
        # Convertir la fecha y el peso a los formatos correctos para el formulario
        pallet.fecha_cosecha = pallet.fecha_cosecha.strftime('%Y-%m-%d')

    context = {
        'form': form,
        'distribuidores': distribuidores,
        'pallet': pallet,
    }
    return render(request, 'actualizar_datos_pallet.html', context)



@csrf_exempt
def eliminar_distribuidores(request, pallet_id):
    """Vista para eliminar distribuidores de un pallet específico."""
    
    # Obtener el pallet que se está gestionando
    pallet = get_object_or_404(Pallet, id=pallet_id)
    
    # Obtener los distribuidores asociados a este pallet
    distribuidores_pallet = DistribuidorPallet.objects.filter(pallet=pallet)

    return render(request, 'eliminar_distribuidor.html', {
        'pallet': pallet,
        'distribuidores_pallet': distribuidores_pallet,
    })
@csrf_exempt
def eliminar_distribuidor_pallet(request, distribuidor_pallet_id):
    if request.method == 'POST' and request.headers.get('x-requested-with') == 'XMLHttpRequest':
        try:
            # Obtener el distribuidor_pallet que se desea eliminar y el pallet asociado
            distribuidor_pallet = get_object_or_404(DistribuidorPallet, id=distribuidor_pallet_id)
            pallet = distribuidor_pallet.pallet
            peso_pallet_original = pallet.peso  # Guardar el peso original del pallet

            # Obtener el contrato de la blockchain
            pallet_contract = get_pallet_contract()

            # Eliminar el distribuidor dentro de una transacción atómica
            with transaction.atomic():
                distribuidor_pallet.delete()

                # Obtener los distribuidores restantes
                distribuidores_restantes = DistribuidorPallet.objects.filter(pallet=pallet)

                if distribuidores_restantes.exists():
                    # Sumar los pesos restantes y calcular la diferencia
                    peso_restante = sum(d.peso_enviado for d in distribuidores_restantes)
                    diferencia = peso_pallet_original - peso_restante

                    # Redistribuir la diferencia proporcionalmente entre los distribuidores restantes
                    if diferencia != 0:
                        for distribuidor in distribuidores_restantes:
                            proporcion = distribuidor.peso_enviado / peso_restante
                            redistribuido = round(proporcion * diferencia, 2)
                            distribuidor.peso_enviado += redistribuido
                            distribuidor.save()

                            # Convertir peso a entero aplicando factor de escala
                            factor_escala = 10
                            peso_distribuidor_escalado = int(float(distribuidor.peso_enviado) * factor_escala)

                            # Actualizar el distribuidor en la blockchain
                            try:
                                distribuidor_id = distribuidor.distribuidor.id
                                tx_hash = pallet_contract.functions.updateDistribuidorPallet(
                                    distribuidor.id,
                                    pallet.id,
                                    distribuidor_id,
                                    peso_distribuidor_escalado
                                ).transact({'from': web3.eth.accounts[0]})

                                # Esperar la transacción--
                                web3.eth.wait_for_transaction_receipt(tx_hash)
                                print(f"Transacción exitosa para redistribuir el peso de distribuidor {distribuidor.id}: {tx_hash.hex()}")
                            except Exception as e:
                                print(f"Error al actualizar DistribuidorPallet {distribuidor.id} en la blockchain:", e)
                else:
                    # Si no quedan distribuidores, restaurar el peso original del pallet
                    pallet.peso = peso_pallet_original
                    pallet.save()

                # Emitir evento de eliminación en la blockchain
                try:
                    tx_hash = pallet_contract.functions.eliminarDistribuidorPallet(
                        pallet.id,
                        distribuidor_pallet_id
                    ).transact({'from': web3.eth.accounts[0]})
                    web3.eth.wait_for_transaction_receipt(tx_hash)
                    print("Transacción de eliminación exitosa:", tx_hash.hex())
                except Exception as blockchain_error:
                    print("Error en la transacción de blockchain:", blockchain_error)
                    return JsonResponse({'success': False, 'error': 'Error en la blockchain: ' + str(blockchain_error)})

            # Responder con éxito si todo el proceso se completó sin errores
            return JsonResponse({'success': True, 'mensaje': 'DistribuidorPallet eliminado correctamente.'})

        except Exception as e:
            # Retornar respuesta de error en caso de excepción
            return JsonResponse({'success': False, 'error': str(e)})
    else:
        return JsonResponse({'success': False, 'error': 'Método no permitido o no es una solicitud AJAX.'})
@csrf_exempt
def añadir_distribuidor(request, pallet_id):
    pallet = get_object_or_404(Pallet, id=pallet_id)
    distribuidores = Distribuidor.objects.all()
    distribuidor_pallets = DistribuidorPallet.objects.filter(pallet=pallet)
    errores = []
    pallet_contract = get_pallet_contract()
    factor_escala = 1000  # Factor de escala para convertir pesos

    if request.method == 'POST':
        # Recoger el peso de distribuidores existentes y el nuevo distribuidor
        total_peso = 0
        distribuidor_pallets_data = []

        # Sumar pesos de distribuidores existentes y recoger nuevos datos
        for distribuidor_pallet in distribuidor_pallets:
            distribuidor_id = distribuidor_pallet.distribuidor.id
            peso_enviado = request.POST.get(f'distribuidor_{distribuidor_id}-peso_enviado', distribuidor_pallet.peso_enviado)

            try:
                peso_enviado_float = float(peso_enviado)
                total_peso += peso_enviado_float  # Sumar peso del distribuidor existente
                distribuidor_pallets_data.append((distribuidor_pallet.distribuidor, peso_enviado_float))
            except ValueError:
                errores.append(f"El peso enviado para el distribuidor {distribuidor_id} debe ser un número válido.")
                continue

        # Recoger los datos del nuevo distribuidor
        nuevo_distribuidor_id = request.POST.get('nuevo_distribuidor')
        nuevo_peso = request.POST.get('nuevo_peso')

        if nuevo_distribuidor_id and nuevo_peso:
            try:
                nuevo_peso_float = float(nuevo_peso)
                total_peso += nuevo_peso_float  # Sumar el peso del nuevo distribuidor
                nuevo_distribuidor = Distribuidor.objects.get(id=nuevo_distribuidor_id)
                distribuidor_pallets_data.append((nuevo_distribuidor, nuevo_peso_float))
            except ValueError:
                errores.append("El peso del nuevo distribuidor debe ser un número válido.")

        # Validar que la suma total sea igual al peso del pallet
        if total_peso != pallet.peso:
            errores.append("La suma de los pesos de los distribuidores debe ser igual al peso del pallet.")

        # Si no hay errores, procesar transacciones en la blockchain y guardar los cambios
        if not errores:
            # Limpiar los DistribuidorPallet existentes
            DistribuidorPallet.objects.filter(pallet=pallet).delete()
            for distribuidor_pallet in distribuidor_pallets:
                distribuidor_pallet_id = distribuidor_pallet.id
                try:
                    # Emitir evento de eliminación en la blockchain
                    tx_hash = pallet_contract.functions.eliminarDistribuidorPallet(
                        pallet.id,
                        distribuidor_pallet_id
                    ).transact({'from': web3.eth.accounts[0]})
                    web3.eth.wait_for_transaction_receipt(tx_hash)
                    print("Transacción de eliminación exitosa:", tx_hash.hex())
                except Exception as blockchain_error:
                    errores.append(f"Error en la transacción de blockchain al eliminar: {blockchain_error}")
                    return JsonResponse({'success': False, 'error': 'Error en la blockchain: ' + str(blockchain_error)})

            # Crear los nuevos DistribuidorPallet y registrar en la blockchain
            for distribuidor, peso in distribuidor_pallets_data:
                distribucion = DistribuidorPallet.objects.create(
                    pallet=pallet,
                    distribuidor=distribuidor,
                    peso_enviado=peso
                )
                id_distribuidor_pallet = distribucion.id
                id_pallet = distribucion.pallet.id
                id_distribuidor = distribucion.distribuidor.id
                peso_envio = int(Decimal(peso) * factor_escala)

                try:
                    # Emitir evento de registro en la blockchain
                    tx_hash = pallet_contract.functions.registerDistribuidorPallet(
                        id_distribuidor_pallet,
                        id_pallet,
                        id_distribuidor,
                        peso_envio
                    ).transact({'from': web3.eth.accounts[0]})
                    web3.eth.wait_for_transaction_receipt(tx_hash)
                    print(f"DistribuidorPallet registrado exitosamente en la blockchain: {tx_hash.hex()}")
                except Exception as blockchain_error:
                    errores.append(f"Error en la transacción de blockchain al añadir: {blockchain_error}")
                    return JsonResponse({'success': False, 'error': 'Error en la blockchain: ' + str(blockchain_error)})

            # Redirigir si todo el proceso se completó sin errores
            return redirect('dashboard_predio')

    return render(request, 'añadir_distribuidor.html', {
        'pallet': pallet,
        'distribuidores': distribuidores,
        'distribuidor_pallets': distribuidor_pallets,
        'errores': errores,
    })



def detalles_caja(request, secure_id):
    # Valida y recupera el ID de la caja usando secure_id
    caja_id = validate_and_recover_id(secure_id, 'Caja')
    if caja_id is None:
        return render(request, 'error.html', {'message': 'ID no válido'})

    # Inicializar contratos
    distribuidor_contract = get_distribuidor_contract()
    transporte_contract = get_transporte_contract()
    predio_contract = get_pallet_contract()

    # Obtener los datos de la caja desde el contrato Distribuidor
    caja_data = distribuidor_contract.functions.cajas(caja_id).call()
    id_recepcion = caja_data[1]  # `idRecepcion`
    id_cliente = caja_data[2]     # `idCliente`
    tipocaja = caja_data[3]       # `tipocaja`

    # Obtener los datos de la recepción desde el contrato Distribuidor
    recepcion_data = distribuidor_contract.functions.recepciones(id_recepcion).call()
    id_envio_pallet = recepcion_data[1]  # `idEnvioPallet`
    peso_envio = recepcion_data[2]       # `pesoEnvio`

    pallet_id = Caja.objects.get(id=caja_id).recepcion.envio_pallet.pallet.id
    pallet = Pallet.objects.get(id=pallet_id)
    predio = get_object_or_404(Predio, id=pallet.predio.id)
    recepcion = Recepcion.objects.get(id=id_recepcion)
    distribuidor = get_object_or_404(Distribuidor, id=recepcion.distribuidor.id)

    pallet_data = predio_contract.functions.getPallet(pallet_id).call()
    producto_blockchain = pallet_data[2]
    pallet = Pallet.objects.get(id=pallet_id)
    caja_nor = Caja.objects.get(id=caja_id)
    enviocajanor= EnvioCaja.objects.get(caja=caja_id)
  


    # Obtener los datos de EnvioPallet desde el contrato Transporte
    envio_pallet_data = transporte_contract.functions.enviosPallet(pallet_id).call()
    transporte_id = envio_pallet_data[1]  # `transporteId`
    vehiculo_id = envio_pallet_data[2]    # `vehiculoId`
    fecha_inicio_pallet = envio_pallet_data[3]
    fecha_llegada_pallet = envio_pallet_data[4]
    ruta_inicio_lat = envio_pallet_data[5] / 10**10
    ruta_inicio_lon = envio_pallet_data[6] / 10**10
    ruta_final_lat = envio_pallet_data[7] / 10**10
    ruta_final_lon = envio_pallet_data[8] / 10**10

    envio_caja_data = transporte_contract.functions.enviosCaja(caja_id).call()
    if envio_caja_data[0] != 0:  # Solo incluir si los datos son válidos
     envio_caja= None
     envio_caja = {
        'transporte_id': envio_caja_data[1],
        'vehiculo_id': envio_caja_data[2],
        'fecha_inicio': envio_caja_data[3],
        'fecha_llegada': envio_caja_data[4],
        'ruta_inicio_lat': envio_caja_data[5] / 10**10, 
        'ruta_inicio_lon': envio_caja_data[6] / 10**10,
        'ruta_final_lat': envio_caja_data[7] / 10**10,
        'ruta_final_lon': envio_caja_data[8] / 10**10,
    }
    transporte_caja = Transporte.objects.get(id = envio_caja_data[1])
    vehiculo_caja = Vehiculo.objects.get(id = envio_caja_data[2])
    # Obtener los datos de RecepcionCliente (si existen) desde el contrato Distribuidor
    recepcion_cliente = RecepcionCliente.objects.filter(caja=caja_id).first()
    recepcion_cliente_data = distribuidor_contract.functions.recepcionClientes(recepcion_cliente.id).call()
    transporte_pallet = Transporte.objects.get(id= envio_pallet_data[1])
    vehiculo_pallet = Vehiculo.objects.get(id=envio_pallet_data[2])

    # 2. Dividir la latitud y longitud por 10**6
    latitude = recepcion_cliente_data[3] / 10**10
    longitude = recepcion_cliente_data[4] / 10**10
    fecha = recepcion_cliente.fecha

    # Crear el diccionario con los valores formateados
    recepcion_cliente = {
        'fecha': fecha,
        'latitude': latitude,
        'longitude': longitude
    }

    # Pasar toda la información a la plantilla
    context = {
        'caja': {
            'id': caja_id,
            'id_recepcion': id_recepcion,
            'id_cliente': id_cliente,
            'tipocaja': tipocaja,
        },
        'caja_nor': caja_nor,
        'predio':predio,
        'distribuidor':distribuidor,
        'recepcion': {
            'id_envio_pallet': id_envio_pallet,
            'peso_envio': peso_envio,
        },
        'recepcion':recepcion,
        'envio_pallet': {
            'transporte_id': transporte_id,
            'vehiculo_id': vehiculo_id,
            'fecha_inicio': fecha_inicio_pallet,
            'fecha_llegada': fecha_llegada_pallet,
            'ruta_inicio_lat': ruta_inicio_lat,
            'ruta_inicio_lon': ruta_inicio_lon,
            'ruta_final_lat': ruta_final_lat,
            'ruta_final_lon': ruta_final_lon,
        },
        'envio_caja': envio_caja,
        'recepcion_cliente': recepcion_cliente,
        'pallet_block':{
        'producto_blockchain':producto_blockchain,
        },
        'pallet':pallet,
        'transporte_pallet':transporte_pallet,
        'vehiculo_pallet':vehiculo_pallet,
        'transporte_caja':transporte_caja,
        'vehiculo_caja':vehiculo_caja,
        'enviocajanor':enviocajanor
    }

    return render(request, 'detalles_caja.html', context)


@login_required_for_model(Cliente)
@csrf_exempt
def historial_pago(request):
    cliente_id = request.session.get('user_id')  # Suponiendo que user_id es el ID del cliente autenticado
    if not cliente_id:
        # Si no hay un cliente autenticado, redirigir o mostrar un mensaje adecuado
        return render(request, 'error.html', {'message': 'No ha iniciado sesión como Cliente.'})
    
    # Obtener todas las recepciones asociadas a las cajas del cliente
    recepciones_cliente = RecepcionCliente.objects.filter(caja__cliente_id=cliente_id)
    
    if not recepciones_cliente:
        # Si no se encuentran recepciones asociadas a las cajas del cliente, mostrar un mensaje adecuado
        mensaje = "No se encontraron recepciones asociadas a su cuenta."
    else:
        mensaje = ""
    
    # Pasar las recepciones y el mensaje a la plantilla
    return render(request, 'historial_cliente.html', {
        'recepciones_cliente': recepciones_cliente,  # Recepciones asociadas a las cajas del cliente
        'mensaje': mensaje,
    })
