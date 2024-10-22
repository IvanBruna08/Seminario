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
from django.db.models import Sum
from django.views.decorators.csrf import csrf_exempt
from .forms import ClienteForm,TransporteForm, PredioForm, DistribuidorForm, PalletForm,RecepcionForm,CustomLoginForm, DistribuidorPalletForm, CajaForm,TipoCajaForm
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from .models import Predio, Distribuidor, Transporte, Cliente, Pallet, EnvioPallet,Recepcion,Caja,Empaque,EnvioCaja,Pago, DistribuidorPallet, TipoCaja
import json
from django.contrib.admin.views.decorators import staff_member_required
import os
from datetime import datetime, timezone as dt_timezone
import requests
from django.contrib.auth import authenticate as django_authenticate
from django.conf import settings
from django.views.generic import ListView
from django.forms import formset_factory
from .utils import get_web3
from django.utils import timezone
from django.contrib import messages
from .decorators import login_required_for_model
from math import radians, sin, cos, sqrt, atan2
# Conectar con Ganache
ganache_url = "http://127.0.0.1:8545"
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
    """
    Genera un hash seguro basado en el nombre del modelo y su ID.
    El resultado es una cadena segura que puede usarse en la URL.
    """
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
def registrar_predio(request):
    if request.method == 'POST':
        form = PredioForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')
    else:
        form = PredioForm()
    return render(request, 'registrar_predio.html', {'form': form})

def registrar_transportista(request):
    if request.method == 'POST':
        form = TransporteForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')
    else:
        form = TransporteForm()
    return render(request, 'registrar_transportista.html', {'form': form})

def registrar_distribuidor(request):
    if request.method == 'POST':
        form = DistribuidorForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')
    else:
        form = DistribuidorForm()
    return render(request, 'registrar_distribuidor.html', {'form': form})

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
'''def login_view(request):
    if request.method == 'POST':
        billetera = request.POST.get('billetera')
        
        # Buscar al usuario por billetera en los diferentes modelos
        tipo_usuario = None
        
        if Cliente.objects.filter(billetera=billetera).exists():
            cliente = Cliente.objects.get(billetera=billetera)
            set_usuario_session(request, 'cliente', cliente)
            tipo_usuario = 'cliente'
        elif Predio.objects.filter(billetera=billetera).exists():
            predio = Predio.objects.get(billetera=billetera)
            set_usuario_session(request, 'predio', predio)
            tipo_usuario = 'predio'
        elif Distribuidor.objects.filter(billetera=billetera).exists():
            distribuidor = Distribuidor.objects.get(billetera=billetera)
            set_usuario_session(request, 'distribuidor', distribuidor)
            tipo_usuario = 'distribuidor'
        elif Transporte.objects.filter(billetera=billetera).exists():
            transporte = Transporte.objects.get(billetera=billetera)
            set_usuario_session(request, 'transporte', transporte)
            tipo_usuario = 'transporte'
        else:
            error_message = "Billetera no válida. Intenta nuevamente."
            return render(request, 'login.html', {'error_message': error_message})

        # Redirigir a la página correspondiente según el tipo de usuario
        return redirect(f'dashboard_{tipo_usuario}')
        
    return render(request, 'login.html')'''
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
            latitude = request.POST.get('ruta_inicio_latitude')
            longitude = request.POST.get('ruta_inicio_longitude')

            # Verificar que las coordenadas iniciales existan
            if latitude is None or longitude is None:
                return JsonResponse({'success': False, 'message': 'Faltan coordenadas iniciales'})

            # Obtener el objeto de transporte y pallet
            transporte = get_object_or_404(Transporte, id=request.session.get('user_id'))
            pallet = get_object_or_404(Pallet, id=pallet_id)
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
                coordenadas_transporte=[],  # Inicializa como lista vacía
            )

            # Actualizar el estado del pallet a 'En Proceso'
            pallet.estado_envio = 'en_ruta'
            pallet.save()

            return JsonResponse({'success': True, 'envio_id': envio.id, 'pallet_id': pallet.id})


        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})

    return JsonResponse({'success': False, 'message': 'Método no permitido'}, status=405)

@login_required_for_model(Transporte)
@csrf_exempt
def finalizar_entrega(request, secure_id):
    # Validar el hash y recuperar el pallet_id original
    pallet_id = validate_and_recover_id(secure_id, 'Pallet')
    if pallet_id is None:
        # Si el hash no es válido, muestra un mensaje de error o redirige
        return render(request, 'error.html', {'message': 'ID no válido'})
    if request.method == 'POST':
        try:
            # Verifica si el contenido es JSON o un formulario
            if request.content_type == 'application/json':
                data = json.loads(request.body)
            else:
                data = request.POST

            # Obtén y convierte los valores a float cuando sea necesario
            latitude = data.get('latitude')
            longitude = data.get('longitude')
            coordenadas_transporte = data.get('coordenadasTransporte')
            envio_id = data.get('envio_id')

            # Valida los datos necesarios
            if not latitude or not longitude:
                return JsonResponse({'success': False, 'message': 'Faltan la latitud o la longitud.'})
            if not envio_id:
                return JsonResponse({'success': False, 'message': 'Falta el ID del envío.'})
            if not coordenadas_transporte:
                return JsonResponse({'success': False, 'message': 'No se recibieron coordenadas de transporte.'})

            # Convierte latitud y longitud a float
            latitude = float(latitude)
            longitude = float(longitude)

            # Si `coordenadasTransporte` es una cadena JSON, debemos decodificarla
            if isinstance(coordenadas_transporte, str):
                coordenadas_transporte = json.loads(coordenadas_transporte)

            # Procesar la lista de coordenadas y asegurarse de que los tiempos estén en la zona horaria local de Chile
            for coord in coordenadas_transporte:
                # Convertir el tiempo de cada coordenada a la zona horaria local configurada en Django
                if 'tiempo' in coord:
                    tiempo_utc = coord['tiempo']
                    # Convertir la cadena de tiempo UTC a un objeto datetime
                    tiempo_local = datetime.strptime(tiempo_utc, '%Y-%m-%dT%H:%M:%S.%fZ')
                    # Hacer que sea consciente de la zona horaria UTC utilizando datetime.timezone.utc
                    tiempo_local = tiempo_local.replace(tzinfo=dt_timezone.utc)
                    # Convertir el tiempo a la zona horaria local configurada en Django (America/Santiago)
                    coord['tiempo'] = timezone.localtime(tiempo_local).strftime('%d-%m-%Y, %I:%M:%S %p')

            # Obtén el objeto de envío y el pallet
            envio = get_object_or_404(EnvioPallet, id=envio_id)
            pallet = get_object_or_404(Pallet, id=pallet_id)

            # Asignación de los valores
            envio.ruta_final_latitude = latitude
            envio.ruta_final_longitude = longitude
            envio.fecha_llegada = timezone.now()  # Mantiene la fecha en UTC, pero la convierte al mostrar
            envio.coordenadas_transporte = json.dumps(coordenadas_transporte)  # Guardar coordenadas con tiempos locales

            # Calcular distancia y guardar
            envio.distancia = calcular_distancia(
                envio.ruta_inicio_latitude,
                envio.ruta_inicio_longitude,
                envio.ruta_final_latitude,
                envio.ruta_final_longitude
            )
            envio.save()

            # Actualizar el estado del pallet
            pallet.estado_envio = 'completado'
            pallet.save()

            return JsonResponse({'success': True, 'message': 'Entrega finalizada con éxito.'})

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

def verificar_pallet(request):
    pallet_id = request.GET.get('id')  # Obtener el ID del pallet desde la solicitud
    # Obtener todos los DistribuidorPallet asociados a ese pallet
    distribuidor_pallets = DistribuidorPallet.objects.filter(pallet_id=pallet_id)
    
    # Verificar si todos los DistribuidorPallet tienen 'completado' en estado_pallet
    completados = all(dp.estado_pallet == 'completado' for dp in distribuidor_pallets)

    # Enviar una respuesta indicando si el pallet está completamente completado
    return JsonResponse({'completado': completados})

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

    # Obtener las distribuciones asociadas al pallet
    distribuciones = DistribuidorPallet.objects.filter(pallet=pallet)

    # Verificar si hay distribuidores asociados
    if not distribuciones.exists() or not any(d.distribuidor for d in distribuciones):
        messages.error(request, 'No hay distribuidores asociados a este pallet.')
        return redirect('pallet_list')  # Redirigir a una lista de pallets o a donde desees

    # Asegurarse de que se esté trabajando con un transporte
    if user_type != 'transporte':
        messages.error(request, 'Acceso no autorizado.')
        return redirect('login')  # O podrías mostrar un mensaje de error

    # Obtener el objeto Transporte relacionado con el ID de la sesión
    transporte = get_object_or_404(Transporte, id=transporte_id)

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
        'secure_id': secure_id
    })

# REGISTRAR LA RECEPCION DEL PALLET
@login_required_for_model(Distribuidor)
@csrf_exempt
def registrar_recepcion(request, secure_id):
    # Validar el hash y recuperar el pallet_id original
    pallet_id = validate_and_recover_id(secure_id, 'Pallet')
    if pallet_id is None:
        # Si el hash no es válido, muestra un mensaje de error
        return render(request, 'error.html', {'message': 'ID no válido'})

    # Verificar si hay un usuario distribuidor en la sesión
    distribuidor_id = request.session.get('user_id')  # Suponiendo que user_id es el ID del distribuidor
    if not distribuidor_id:
        return redirect('login')  # Redirigir al login si no hay usuario en sesión

    # Obtener el pallet correspondiente al pallet_id
    pallet = get_object_or_404(Pallet, id=pallet_id)

    # Obtener el envío asociado al pallet
    envio_pallet = get_object_or_404(EnvioPallet, pallet=pallet)

    # Obtener el distribuidor
    distribuidor = get_object_or_404(Distribuidor, id=distribuidor_id)

    # Obtener DistribuidorPallet relacionado con este pallet y distribuidor
    dp = get_object_or_404(DistribuidorPallet, distribuidor=distribuidor_id, pallet=pallet_id)

    # Si el método es POST, procesamos el formulario
    if request.method == 'POST':
        form = RecepcionForm(request.POST)
        if form.is_valid():
            # Guardar la recepción asociada al envío y distribuidor
            recepcion = form.save(commit=False)
            recepcion.envio_pallet = envio_pallet  # Asignar EnvioPallet
            recepcion.distribuidor = distribuidor  # Asignar distribuidor
            recepcion.peso_ingresado = recepcion.peso_recepcion  # Guardar el peso ingresado
            recepcion.save()  # Guardar la recepción en la base de datos

            # Actualizar estado del DistribuidorPallet a 'completado'
            DistribuidorPallet.objects.filter(
                pallet=pallet_id,
                distribuidor=distribuidor_id
            ).update(estado_pallet='completado')

            return redirect('registrar_recepcion', secure_id=secure_id)  # Redirigir a la misma página tras completar

    else:
        # Si el método no es POST, se crea un formulario vacío
        form = RecepcionForm()

    # Renderizar el template con los datos necesarios
    return render(request, 'registrar_recepcion.html', {
        'pallet': pallet,
        'envio_pallet': envio_pallet,
        'dp': dp,
        'form': form,
        'secure_id': secure_id
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
def crear_empaque(request):
    """Vista para crear un empaque a partir de una recepción seleccionada."""
    if request.method == 'POST':
        recepcion_id = request.POST.get('recepcion_id')
        # Obtener la recepción seleccionada
        recepcion = get_object_or_404(Recepcion, id=recepcion_id, estado_recepcion='completado')

        try:
            # Obtener el peso del pallet asociado a la recepción
            peso_pallet = recepcion.peso_final

            # Crear el nuevo empaque
            empaque = Empaque.objects.create(
                recepcion=recepcion,
                peso_pallet=peso_pallet,
                cantidad_cajas=0  # Inicialmente, cantidad de cajas es 0
            )

            messages.success(request, f"Empaque creado exitosamente con ID: {empaque.id}")
            return redirect('distribuir_caja')  # Redirigir a la vista de cajas
        except EnvioPallet.DoesNotExist:
            messages.error(request, "No se encontró el peso del pallet para esta recepción.")
    
    # Obtener todas las recepciones que están en estado 'completado' para la selección
    recepciones = Recepcion.objects.filter(estado_recepcion='completado')  
    return render(request, 'crear_empaque.html', {
        'recepciones': recepciones,
    })

@login_required_for_model(Distribuidor)
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
                    return redirect('confirmation_page')
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
def distribuir_pallet(request):
    # Obtener todos los pallets disponibles
    predio_id = request.session.get('user_id')  # Suponiendo que user_id es el ID del distribuidor
    pallets = Pallet.objects.filter(predio = predio_id)
    distribuidores = Distribuidor.objects.all()
    errores = []
    pallet = None

    if request.method == 'POST':
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
@login_required_for_model(Distribuidor)
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
def cajas_view(request):
    """Vista para gestionar las cajas asociadas a un distribuidor específico o mostrar las cajas filtradas por recepción."""
    
    # Obtener el ID del distribuidor que ha iniciado sesión
    distribuidor_id = request.session.get('user_id')  # Suponiendo que user_id es el ID del distribuidor
    if not distribuidor_id:
        # Si no hay un distribuidor autenticado, redirigir o mostrar un mensaje adecuado
        return render(request, 'error.html', {'message': 'No ha iniciado sesión como distribuidor.'})
    
    # Obtener las recepciones asociadas al distribuidor
    recepciones = Recepcion.objects.filter(distribuidor=distribuidor_id)
    
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
    if user_type == 'cliente':
        return redirect('recibir_caja', secure_id=secure_id)
    elif user_type == 'transporte':
        return redirect('transportar_caja', secure_id=secure_id)
    elif user_type == 'distribuidor':
        return redirect('informacion_caja', secure_id=secure_id)

    # Redirigir a una vista de error si el tipo no es válido
    return redirect('login')






@login_required_for_model(Distribuidor)
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
    envio_pallet = recepcion.envio_pallet
    pallet = envio_pallet.pallet
    predio= pallet.predio
    
    # Asegurarse de que se esté trabajando con un transporte
    if user_type != 'transporte':
        # Si no es un transporte, redirigir o mostrar un error
        return redirect('login')  # O podrías mostrar un mensaje de error

    # Obtener el objeto Transporte relacionado con el ID de la sesión
    transporte = get_object_or_404(Transporte, id=transporte_id)
    
    # Renderizar la plantilla y pasar los datos
    return render(request, 'transportar_caja.html', {
        'caja': caja,
        'transporte': transporte,
        'cliente': cliente,
        'recepcion': recepcion,
        'envio_pallet': envio_pallet,
        'pallet': pallet,
        'predio': predio
    })

@login_required_for_model(Transporte)
@csrf_exempt
def iniciar_entrega_caja(request, secure_id):
    # Validar el hash y recuperar el pallet_id original
    caja_id = validate_and_recover_id(secure_id, 'Caja')
    if secure_id is None:
        # Si el hash no es válido, muestra un mensaje de error o redirige
        return render(request, 'error.html', {'message': 'ID no válido'})
    if request.method == "POST":
        try:
            transporte_id = request.session.get('user_id')
            transporte = get_object_or_404(Transporte, id=transporte_id)

            # Obtener la caja y su envío relacionado
            caja = get_object_or_404(Caja, id=caja_id)

            # Capturar las coordenadas iniciales desde el formulario o frontend
            ruta_inicio_latitude = float(request.POST['ruta_inicio_latitude'])
            ruta_inicio_longitude = float(request.POST['ruta_inicio_longitude'])

            # Crear un nuevo registro de EnvioCaja
            envio_caja = EnvioCaja.objects.create(
                caja=caja,
                transporte=transporte,
                ruta_inicio_latitude=ruta_inicio_latitude,
                ruta_inicio_longitude=ruta_inicio_longitude,
                fecha_inicio=timezone.now(),
                estado_envio='enviado'
            )
            
            # Redirigir de nuevo o mostrar mensaje
            return redirect('transportar_caja', caja_id=caja_id)

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

@csrf_exempt
def finalizar_entrega_caja(request, secure_id):
    # Validar el hash y recuperar el pallet_id original
    caja_id = validate_and_recover_id(secure_id, 'Caja')
    if secure_id is None:
        # Si el hash no es válido, muestra un mensaje de error o redirige
        return render(request, 'error.html', {'message': 'ID no válido'})
    if request.method == "POST":
        try:
            transporte_id = request.session.get('user_id')
            transporte = get_object_or_404(Transporte, id=transporte_id)

            # Obtener la caja
            caja = get_object_or_404(Caja, id=caja_id)

            # Obtener el envío relacionado a la caja y transporte
            envio_caja = get_object_or_404(EnvioCaja, caja=caja, transporte=transporte)

            # Capturar las coordenadas finales desde el formulario o frontend
            ruta_final_latitude = float(request.POST['ruta_final_latitude'])
            ruta_final_longitude = float(request.POST['ruta_final_longitude'])

            # Calcular la distancia (utilizando la fórmula Haversine)
            distancia = calcular_distancia(
                envio_caja.ruta_inicio_latitude,
                envio_caja.ruta_inicio_longitude,
                ruta_final_latitude,
                ruta_final_longitude
            )

            # Actualizar el modelo EnvioCaja
            envio_caja.ruta_final_latitude = ruta_final_latitude
            envio_caja.ruta_final_longitude = ruta_final_longitude
            envio_caja.fecha_llegada = timezone.now()
            envio_caja.distancia = distancia
            envio_caja.estado_envio = 'entregado'
            envio_caja.save()

            # Redirigir de nuevo o mostrar mensaje
            return redirect('transportar_caja', caja_id=caja_id)

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)


def recibir_caja(request, secure_id):
    # Validar el hash y recuperar el pallet_id original
    caja_id = validate_and_recover_id(secure_id, 'Caja')
    if secure_id is None:
        # Si el hash no es válido, muestra un mensaje de error o redirige
        return render(request, 'error.html', {'message': 'ID no válido'})
    if request.method == "GET":
        try:
            # Obtener la caja por su ID
            caja = get_object_or_404(Caja, id=caja_id)
            cliente = caja.cliente
            empaque = caja.empaque
            recepcion = empaque.recepcion
            envio_pallet = recepcion.envio_pallet
            pallet = envio_pallet.pallet
            predio= pallet.predio
            transporte_pallet = envio_pallet.transporte


            # Obtener el envío relacionado a la caja
            envio_caja = get_object_or_404(EnvioCaja, caja=caja)
            transporte_caja = envio_caja.transporte

            # Aquí se debe obtener el precio de la caja (ajusta según tu modelo)
            precio = (pallet.precio_venta * caja.peso_caja)
            precio_formateado = f"${precio:,.1f}".replace(",", "X").replace(".", ",").replace("X", ".")

            return render(request, 'recibir_caja.html', {
                'caja': caja,
                'envio_caja': envio_caja,
                'precio': precio,
                'predio': predio,
                'transporte_pallet': transporte_pallet,
                'transporte_caja' : transporte_caja,
                'pallet': pallet,
                'precio_formateado': precio_formateado
            })

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    elif request.method == "POST":
        try:
            # Obtener datos del cliente
            cliente_id = request.session.get('user_id')  # Suponiendo que guardas el ID del cliente en la sesión
            caja = get_object_or_404(Caja, id=caja_id)

            # Crear el pago asociado a la caja y cliente
            pago = Pago(
                enviocaja=envio_caja,           # Relación con EnvioCaja
                cliente_id=cliente_id,          # Relación con Cliente
                monto=precio                    # Monto que debe pagar el cliente
            )
            pago.save()  # Guardar el registro en la base de datos

            # Redirigir a una página de éxito o confirmación
            return redirect('pagina_exito')  # Ajusta esto a la URL de tu elección

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

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
def asignar_cliente(request):
    distribuidor_id = request.session.get('user_id')
    # Filtrar las cajas del distribuidor sin cliente asignado
    cajas = Caja.objects.filter(recepcion__distribuidor=distribuidor_id, cliente__isnull=True)
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

def actualizar_pallet(request):
    pallets = Pallet.objects.all()  # Obtener todos los pallets para mostrarlos

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

def actualizar_datos_pallet(request, pallet_id):
    # Obtener el pallet correspondiente
    pallet = get_object_or_404(Pallet, id=pallet_id)
    # Obtener los distribuidores asociados al pallet
    distribuidores = DistribuidorPallet.objects.filter(pallet=pallet)

    if request.method == 'POST':
        form = PalletForm(request.POST, instance=pallet)
        
        if form.is_valid():
            # Guardar los datos del pallet
            form.save()
            
            # Inicializar nuevo_peso_pallet
            nuevo_peso_pallet = form.cleaned_data['peso']
            total_peso_distribuidores = 0
            
            # Actualizar pesos de los distribuidores
            for distribuidor in distribuidores:
                distribuidor_peso_field = f"peso_enviado_{distribuidor.id}"
                nuevo_peso_distribuidor = request.POST.get(distribuidor_peso_field)

                if nuevo_peso_distribuidor:
                    try:
                        distribuidor.peso_enviado = float(nuevo_peso_distribuidor)
                        distribuidor.save()  # Guardar cambios en el distribuidor
                        total_peso_distribuidores += float(nuevo_peso_distribuidor)
                    except ValueError:
                        messages.error(request, "El peso ingresado no es válido.")
                        return redirect('actualizar_datos_pallet', pallet_id=pallet_id)

            # Validar que el peso total de los distribuidores coincida con el peso del pallet
            if total_peso_distribuidores != nuevo_peso_pallet:
                messages.error(request, "El peso total de los distribuidores debe ser igual al peso del pallet.")
                return redirect('actualizar_datos_pallet', pallet_id=pallet_id)

            messages.success(request, 'Pallet y pesos de distribuidores actualizados correctamente.')
            return redirect('actualizar_pallet')

    else:
        form = PalletForm(instance=pallet)

    context = {
        'form': form,
        'distribuidores': distribuidores,
        'pallet': pallet,
    }
    return render(request, 'actualizar_datos_pallet.html', context)

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

def eliminar_distribuidor_pallet(request, distribuidor_pallet_id):
     
    if request.method == 'POST' and request.headers.get('x-requested-with') == 'XMLHttpRequest':
        try:
            # Obtener el distribuidor_pallet que se desea eliminar
            distribuidor_pallet = get_object_or_404(DistribuidorPallet, id=distribuidor_pallet_id)
            pallet = distribuidor_pallet.pallet
            peso_pallet = pallet.peso  # Guardar el peso original del pallet
            
            # Obtener todos los distribuidores asociados al pallet
            distribuidores = DistribuidorPallet.objects.filter(pallet=pallet)
            
            # Eliminar el distribuidor
            with transaction.atomic():
                distribuidor_pallet.delete()

                # Obtener los distribuidores restantes después de eliminar
                distribuidores_restantes = DistribuidorPallet.objects.filter(pallet=pallet)
                
                if distribuidores_restantes.exists():
                    # Suma de los pesos restantes
                    peso_restante = sum(d.peso_enviado for d in distribuidores_restantes)

                    # Verificar si la suma de los pesos es menor que el peso total del pallet
                    diferencia = peso_pallet - peso_restante

                    if diferencia != 0:
                        # Redistribuir la diferencia proporcionalmente entre los distribuidores restantes
                        for distribuidor in distribuidores_restantes:
                            proporcion = distribuidor.peso_enviado / peso_restante
                            distribuidor.peso_enviado += round(proporcion * diferencia, 2)
                            distribuidor.save()
                else:
                    # Si no quedan distribuidores, el pallet recupera su peso original
                    pallet.peso = peso_pallet
                    pallet.save()

            # Retornar respuesta JSON de éxito
            return JsonResponse({'success': True})
        
        except Exception as e:
            # Retornar respuesta de error en caso de excepción
            return JsonResponse({'success': False, 'error': str(e)})
    else:
        return JsonResponse({'success': False, 'error': 'Método no permitido o no es una solicitud AJAX.'})


def añadir_distribuidor(request, pallet_id):
    pallet = get_object_or_404(Pallet, id=pallet_id)
    distribuidores = Distribuidor.objects.all()
    distribuidor_pallets = DistribuidorPallet.objects.filter(pallet=pallet)
    errores = []

    if request.method == 'POST':
        # Recoger el peso del distribuidor existente y el nuevo distribuidor
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

        # Si no hay errores, guardar los cambios
        if not errores:
            # Limpiar los DistribuidorPallet existentes (esto puede no ser necesario si sólo actualizas)
            DistribuidorPallet.objects.filter(pallet=pallet).delete()
            # Actualizar o crear los DistribuidorPallet
            for distribuidor, peso in distribuidor_pallets_data:
                DistribuidorPallet.objects.create(pallet=pallet, distribuidor=distribuidor, peso_enviado=peso)

            return redirect('dashboard_predio')

    return render(request, 'añadir_distribuidor.html', {
        'pallet': pallet,
        'distribuidores': distribuidores,
        'distribuidor_pallets': distribuidor_pallets,
        'errores': errores,
    })
"""""
def ingreso_trabajador(request):
    if request.method == 'POST':
        direccion = request.POST.get('direccion')

        # Verificar si la dirección existe en la base de datos
        try:
            trabajador = Trabajador.objects.get(direccion=direccion)
            # Guardar la dirección y el nombre en la sesión para su uso posterior
            request.session['direccion_trabajador'] = direccion
            request.session['nombre_trabajador'] = trabajador.nombre  # Guardar el nombre del trabajador

            # Redirigir según el área del trabajador
            if trabajador.area == 'cosecha':
                return redirect('cosecha')  # Redirigir a la plantilla de cosecha
            elif trabajador.area == 'transporte':
                return redirect('transporte')  # Redirigir a la plantilla de transporte
        except Trabajador.DoesNotExist:
            error_message = "Acceso denegado. Dirección no encontrada."
            return render(request, 'ingreso_trabajador.html', {'error': error_message})

    return render(request, 'ingreso_trabajador.html')
def acceso_trabajador(request, area):
    # Aquí puedes manejar la lógica para el área
    # Por ejemplo, redirigir a la plantilla correspondiente
    if area == 'cosecha':
        return render(request, 'registrar-cosecha.html')
    elif area == 'transporte':
        return render(request, 'transporte.html')
    else:
        return render(request, 'error.html', {'message': 'Área no autorizada.'})


def cosecha(request):
    return render(request, 'cosecha.html')
def mostrar_mapa(request):
    return render(request, 'maps.html', {
        'mapbox_token': settings.MAPBOX_ACCESS_TOKEN,
    })
def transporte(request):
    return render(request, 'transporte.html')
def cliente(request):
    return render(request, 'cliente.html')

def contract_status(request):
    try:
        # Determina si estás trabajando con el contrato de Cosecha o Transporte
        contract = get_cosecha_contract()  # o get_transporte_contract()

        # Obtener detalles del contrato, como el número de registros
        # Cambia estas llamadas según las funciones disponibles en tu contrato
        total_records = contract.functions.cosechaCounter().call()  # Asegúrate de que `cosechaCounter` sea una función válida en tu contrato

        context = {
            'contract_address': contract.address,
            'total_records': total_records,
        }

        return render(request, 'contract-status.html', context)

    except FileNotFoundError as e:
        return render(request, 'error.html', {'message': str(e)})
    except ConnectionError as e:
        return render(request, 'error.html', {'message': str(e)})
    except Exception as e:
        return render(request, 'error.html', {'message': f'Error inesperado: {str(e)}'})

def registrar_cosecha(request):
    if request.method == 'POST':
        form = CosechaForm(request.POST)
        if form.is_valid():
            producto = form.cleaned_data['producto']
            fecha_cosecha = form.cleaned_data['fecha_cosecha']
            ubicacion = form.cleaned_data['ubicacion']
            cantidad_lote = form.cleaned_data['cantidad_lote']
            cantidad_agua = form.cleaned_data['cantidad_agua']
            pesticidas_fertilizantes = form.cleaned_data['pesticidas_fertilizantes']
            practicas_cultivo = form.cleaned_data['practicas_cultivo']

            try:
                web3 = get_web3()
                contract = get_cosecha_contract()

                tx = contract.functions.registrarCosecha(
                    producto,
                    fecha_cosecha.isoformat(),
                    ubicacion,
                    cantidad_lote,
                    cantidad_agua,
                    pesticidas_fertilizantes,
                    practicas_cultivo
                ).transact({'from': web3.eth.accounts[0]})

                tx_receipt = web3.eth.wait_for_transaction_receipt(tx)
                 # Obtener el total de registros después de la transacción
                block_number = tx_receipt.blockNumber
                # Crear el registro en la base de datos
                # Verificar si el registro ya existe
                if not Cosecha.objects.filter(id=block_number).exists():
                    cosecha = Cosecha(
                        id=block_number,
                        producto=producto,
                        fecha_cosecha=fecha_cosecha,
                        ubicacion=ubicacion,
                        cantidad_lote=cantidad_lote,
                        cantidad_agua=cantidad_agua,
                        pesticidas_fertilizantes=pesticidas_fertilizantes,
                        practicas_cultivo=practicas_cultivo
                    )
                    cosecha.save()  # Esto generará el QR y lo guardará
                else:
                    # Si ya existe, podrías optar por actualizar o simplemente ignorar
                    pass

                return redirect('registro_exitoso', block_number=block_number)

            except IntegrityError as e:
                return render(request, 'error.html', {'message': f'Error de integridad en la base de datos: {e}'})
            except Exception as e:
                return render(request, 'error.html', {'message': str(e)})
    else:
        form = CosechaForm()

    return render(request, 'registrar-cosecha.html', {'form': form})

def lista_cosechas(request):
    ganache_url = "HTTP://127.0.0.1:7545"  # URL de Ganache
    web3 = Web3(Web3.HTTPProvider(ganache_url))

    # Ruta a Cosecha.json dentro del directorio static
    json_file_path = os.path.join(settings.BASE_DIR, "SIA", "static", "contract", "Cosecha.json")

    with open(json_file_path) as file:
        contract_json = json.load(file)
        contract_abi = contract_json['abi']
        contract_address = contract_json['networks']['5777']['address']

        # Cargar contrato
        contract = web3.eth.contract(address=contract_address, abi=contract_abi)

        # Obtener el total de cosechas registradas
        cosecha_counter = contract.functions.cosechaCounter().call()

        # Crear una lista de ID de cosechas
        cosecha_ids = list(range(1, cosecha_counter + 1))

    return render(request, 'detalle-cosecha.html', {'cosecha_ids': cosecha_ids})

def obtener_detalle_cosecha(request, id):
    try:
        web3 = get_web3()
        contract = get_cosecha_contract()  # Asegúrate de que esta función devuelva el contrato correctamente

        # Obtener el detalle de la cosecha
        cosecha = contract.functions.obtenerCosecha(id).call()

        print(f"Detalles de la cosecha para ID {id}: {cosecha}")  # Verificar el objeto cosecha

        context = {
            'id_cosecha': id,
            'producto': cosecha[1],
            'fecha_cosecha': cosecha[2],
            'ubicacion': cosecha[3],
            'cantidad_lote': cosecha[4],
            'cantidad_agua': cosecha[5],
            'pesticidas_fertilizantes': cosecha[6],
            'practicas_cultivo': cosecha[7],
            'transportada': 'Sí' if cosecha[8] else 'No',
        }
        
        # Obtener la lista de IDs de cosechas
        cosecha_counter = contract.functions.cosechaCounter().call()
        cosecha_ids = list(range(1, cosecha_counter + 1))

        context['cosecha_ids'] = cosecha_ids

        return render(request, 'detalle-cosecha.html', context)
    except Exception as e:
        return render(request, 'error.html', {'message': 'Ocurrió un error al obtener los detalles de la cosecha. ' + str(e)})

class TransportadoListView(ListView):
    template_name = 'marcar-transportado.html'
    context_object_name = 'cosechas'

    def get_queryset(self):
     try:
        # Conexión a la blockchain
        web3 = get_web3()

        # Cargar el contrato de Cosecha
        cosecha_contract = get_cosecha_contract()  # Llama a la función y recibe directamente el objeto de contrato

        # Obtener el total de cosechas
        cosecha_counter = cosecha_contract.functions.cosechaCounter().call()

        # Filtrar las cosechas no transportadas
        cosechas = []
        for i in range(1, cosecha_counter + 1):  # Comenzar en 1 si los IDs de las cosechas empiezan en 1
            try:
                cosecha = cosecha_contract.functions.obtenerCosecha(i).call()
                if not cosecha[8]:  # 'transportado' está en el índice 8 del tuple
                    cosechas.append({
                        'id': i,
                        'nombre_producto': cosecha[1],  # 'producto' está en el índice 1 del tuple
                    })
            except Exception as e:
                print(f"Error al obtener la cosecha con ID {i}: {e}")

        return cosechas
     except Exception as e:
        print(f"Error en get_queryset: {e}")
        return []

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = MarcarTransportadoForm()  # Agrega el formulario al contexto
        return context

'''def verificar_cosecha(request, cosecha_id):
    cosecha = get_object_or_404(Cosecha, id=cosecha_id)

    # Obtener la dirección de la billetera del usuario
    direccion_billetera = request.session.get('direccion_billetera')

    if not direccion_billetera:
        # Redirigir al usuario a la página de ingreso de billetera
        return redirect('ingresar_direccion_billetera')

    try:
        trabajador = Trabajador.objects.get(direccion=direccion_billetera)
    except Trabajador.DoesNotExist:
        messages.error(request, 'No se encontró un trabajador con esa dirección de billetera.')
        return redirect('ingresar_direccion_billetera')

    if trabajador.area == 'transporte':
        # Mostrar formulario para transportista
        if request.method == 'POST':
            form = PlacaForm(request.POST)
            if form.is_valid():
                placa = form.cleaned_data['placa']
                cosecha.transportado = True
                cosecha.save()
                messages.success(request, 'El producto ha sido recibido por el transportista.')
                return redirect('home')  # Redirigir a una página principal o de éxito
        else:
            form = PlacaForm()

        return render(request, 'recepcion_transporte.html', {'form': form, 'cosecha': cosecha})
    else:
        # Si no es transporte, mostrar detalles de la cosecha
        return render(request, 'verificar_cosecha.html', {'cosecha': cosecha})'''

def ingresar_direccion_billetera(request):
    if request.method == 'POST':
        direccion_billetera = request.POST.get('direccion_billetera')
        request.session['direccion_billetera'] = direccion_billetera
        
        # Recuperar cosecha_id de la URL
        cosecha_id = request.GET.get('cosecha_id')
        if cosecha_id:
            return redirect('verificar_cosecha', cosecha_id=cosecha_id)
        else:
            messages.error(request, 'ID de cosecha no proporcionado.')
            return redirect('home')  # O redirigir a otra vista

    return render(request, 'ingresar_direccion_billetera.html')

class MarcarTransportadoView(View):
    def post(self, request, *args, **kwargs):
        form = MarcarTransportadoForm(request.POST)
        if form.is_valid():
            id_cosecha = form.cleaned_data['id_cosecha']
            
            try:
                web3 = get_web3()
                contract = get_cosecha_contract()  # Usa directamente el contrato

                account = web3.eth.accounts[0]  # Cambia esto por la cuenta correcta si es necesario

                # Estimar gas necesario
                estimated_gas = contract.functions.marcarTransportado(id_cosecha).estimate_gas({'from': account})

                # Construir y enviar la transacción
                tx = contract.functions.marcarTransportado(id_cosecha).transact({
                    'from': account,
                    'gas': estimated_gas + 10000,  # Agrega un margen adicional para el gas
                    'gasPrice': web3.to_wei('1', 'gwei'),
                })

                # Esperar a que se mine la transacción
                tx_receipt = web3.eth.wait_for_transaction_receipt(tx)
                print(f"Transacción confirmada en el bloque: {tx_receipt.blockNumber}")

                return redirect('marcar_transportado')  # Redirigir a la lista después de marcar como transportado

            except Exception as e:
                return render(request, 'error.html', {'message': str(e)})

        return render(request, 'marcar-transportado.html', {'form': form})
def obtener_productos_transportados():
    try:
        web3 = get_web3()  # Obtener la instancia de Web3
        cosecha_contract = get_cosecha_contract()  # Obtener el contrato de cosecha

        # Obtener el total de cosechas
        cosecha_counter = cosecha_contract.functions.cosechaCounter().call()

        # Procesar las cosechas que están listas para ser transportadas
        productos_listos = []
        for i in range(1, cosecha_counter + 1):  # Asumiendo que los IDs empiezan en 1
            cosecha_detalles = cosecha_contract.functions.obtenerCosecha(i).call()
            if len(cosecha_detalles) > 8 and cosecha_detalles[8]:  # Verificar si la cosecha ha sido transportada
                productos_listos.append({
                    'id': cosecha_detalles[0],
                    'nombre_producto': cosecha_detalles[1],
                    'fecha_cosecha': cosecha_detalles[2],
                    'ubicacion': cosecha_detalles[3],
                    'cantidad_lote': cosecha_detalles[4],
                    'cantidad_agua': cosecha_detalles[5],
                    'pesticidas_fertilizantes': cosecha_detalles[6],
                    'practicas_cultivo': cosecha_detalles[7],
                })

        return productos_listos

    except Exception as e:
        print(f"Error al obtener productos listos para transportar: {str(e)}")
        return []

def registrar_transporte(request):
    # Obtener la billetera del trabajador de transporte desde la sesión
    direccion_billetera_transporte = request.session.get('direccion_billetera')
    if not direccion_billetera_transporte:
        return render(request, 'registrar_transporte.html', {'message': 'Dirección de billetera no encontrada en la sesión.'})

    print(f"Billetera del trabajador de transporte: {direccion_billetera_transporte}")

    # Obtener productos transportados desde la blockchain
    productos_transportados = obtener_productos_transportados()

    if request.method == 'POST':
        print("Datos del formulario:", request.POST)  # Verificar los datos enviados
        form = RegistroTransporteForm(request.POST)
        if form.is_valid():
            print("Formulario válido")
            # Obtener los datos del formulario
            fecha = form.cleaned_data['fecha']
            destino = form.cleaned_data['destino']
            transportista = form.cleaned_data['transportista']
            id_cosecha = form.cleaned_data['id_cosecha']

            try:
                web3 = get_web3()
                transport_contract = get_transporte_contract()
                
                # Imprimir detalles del contrato de transporte
                contract_address = transport_contract.address
                print(f"Dirección del contrato de transporte: {contract_address}")

                # Llamar a la función registerTransport usando la billetera del trabajador
                tx = transport_contract.functions.registerTransport(
                    id_cosecha,
                    fecha.isoformat(),
                    destino,
                    transportista
                ).transact({'from': direccion_billetera_transporte})

                # Esperar a que se mine la transacción
                tx_receipt = web3.eth.wait_for_transaction_receipt(tx)
                print(f"Transporte registrado en el bloque: {tx_receipt.blockNumber}")

                # Opcional: Marcar la cosecha como transportada
                cosecha_contract = get_cosecha_contract()
                
                # Imprimir detalles del contrato de cosecha
                cosecha_contract_address = cosecha_contract.address
                print(f"Dirección del contrato de cosecha: {cosecha_contract_address}")
                
                cosecha_contract.functions.marcarTransportado(id_cosecha).transact({'from': direccion_billetera_transporte})

                # Filtrar la lista de productos transportados para eliminar el ID registrado
                productos_transportados = [producto for producto in productos_transportados if producto['id'] != id_cosecha]

                return redirect('contract_status')  # Redirigir a una página de éxito

            except Exception as e:
                print(f"Error al registrar transporte: {e}")
                return render(request, 'error.html', {'message': str(e)})

        else:
            print("Errores en el formulario:", form.errors)

    else:
        form = RegistroTransporteForm()

    return render(request, 'registrar_transporte.html', {
        'form': form,
        'productos_transportados': productos_transportados,
    })



    # Obtener productos transportados desde la blockchain
    productos_transportados = obtener_productos_transportados()

    if request.method == 'POST':
        form = RegistroTransporteForm(request.POST)
        if form.is_valid():
            # Obtener los datos del formulario
            fecha = form.cleaned_data['fecha']
            destino = form.cleaned_data['destino']
            transportista = form.cleaned_data['transportista']
            id_cosecha = form.cleaned_data['id_cosecha']  # ID de la cosecha seleccionada

            try:
                web3 = get_web3()
                transport_contract = get_transporte_contract()
                
                # Aquí obtén la billetera del trabajador (ejemplo simplificado)
                trabajador = Trabajador.objects.get(area='Transporte')
                direccion_billetera = trabajador.direccion

                # Imprimir detalles del contrato de transporte
                contract_address = transport_contract.address
                print(f"Dirección del contrato de transporte: {contract_address}")

                # Llamar a la función registerTransport
                tx = transport_contract.functions.registerTransport(
                    id_cosecha,
                    fecha.isoformat(),
                    destino,
                    transportista
                ).transact({'from': direccion_billetera})

                # Esperar a que se mine la transacción
                tx_receipt = web3.eth.wait_for_transaction_receipt(tx)
                print(f"Transporte registrado en el bloque: {tx_receipt.blockNumber}")

                # Opcional: Marcar la cosecha como transportada
                cosecha_contract = get_cosecha_contract()
                
                # Imprimir detalles del contrato de cosecha
                cosecha_contract_address = cosecha_contract.address
                print(f"Dirección del contrato de cosecha: {cosecha_contract_address}")
                
                cosecha_contract.functions.marcarTransportado(id_cosecha).transact({'from': direccion_billetera})

                # Filtrar la lista de productos transportados para eliminar el ID registrado
                productos_transportados = [producto for producto in productos_transportados if producto['id'] != id_cosecha]

                return redirect('contrat_status')  # Redirigir a una página de éxito

            except Exception as e:
                return render(request, 'error.html', {'message': str(e)})

    else:
        form = RegistroTransporteForm()

    return render(request, 'registrar_transporte.html', {
        'form': form,
        'productos_transportados': productos_transportados,
    })
def detalle_transporte(request, id):
    try:
        # Obtén el contrato de transporte
        transport_contract = get_transporte_contract()
        
        # Llama a la función para obtener detalles del transporte
        transport_details = transport_contract.functions.getTransportDetails(int(id)).call()

        # Descompón los datos de la tupla
        id_transporte = transport_details[0]
        fecha = transport_details[1]
        destino = transport_details[2]
        transportista = transport_details[3]
        estado = transport_details[4]  # Enum index
        
        # Descompón la tupla anidada para la cosecha
        cosecha_info = transport_details[5]
        id_cosecha = cosecha_info[0]
        producto = cosecha_info[1]
        fecha_cosecha = cosecha_info[2]
        ubicacion = cosecha_info[3]
        cantidad_lote = cosecha_info[4]
        cantidad_agua = cosecha_info[5]
        pesticidas_fertilizantes = cosecha_info[6]
        practicas_cultivo = cosecha_info[7]
        transportado = cosecha_info[8]

        # Mapeo de estados a descripciones legibles
        status_mapping = {
            0: 'En Camino',
            1: 'Entregado',
            2: 'Retrasado'
        }
        
        estado_descripcion = status_mapping.get(estado, 'Desconocido')

        # Renderiza la plantilla con los datos obtenidos
        return render(request, 'detalle-transporte.html', {
            'id_transporte': id_transporte,
            'fecha': fecha,
            'destino': destino,
            'transportista': transportista,
            'estado': estado_descripcion,  # Usa la descripción legible
            'cosecha': {
                'id': id_cosecha,
                'producto': producto,
                'fecha_cosecha': fecha_cosecha,
                'ubicacion': ubicacion,
                'cantidad_lote': cantidad_lote,
                'cantidad_agua': cantidad_agua,
                'pesticidas_fertilizantes': pesticidas_fertilizantes,
                'practicas_cultivo': practicas_cultivo,
                'transportado': 'Sí' if transportado else 'No'
            }
        })
    except Exception as e:
        return render(request, 'error.html', {'message': str(e)})
def actualizar_estado_transporte(request):
    if request.method == 'POST':
        form = ActualizarEstadoTransporteForm(request.POST)
        if form.is_valid():
            id_transporte = form.cleaned_data['id']
            nuevo_estado = form.cleaned_data['status']

            try:
                web3 = get_web3()
                transport_contract = get_transporte_contract()

                # Llamar a la función actualizarEstadoTransporte
                tx = transport_contract.functions.actualizarEstadoTransporte(
                    id_transporte,
                    nuevo_estado
                ).transact({'from': web3.eth.accounts[0]})

                # Esperar a que se mine la transacción
                tx_receipt = web3.eth.wait_for_transaction_receipt(tx)
                print(f"Estado del transporte actualizado en el bloque: {tx_receipt.blockNumber}")

                return redirect('home')  # Redirigir a una página de éxito

            except Exception as e:
                return render(request, 'error.html', {'message': str(e)})

    else:
        form = ActualizarEstadoTransporteForm()

    return render(request, 'actualizar_estado_transporte.html', {'form': form})
def lista_transportes(request):
    try:
        # Obtén el contrato de transporte
        transport_contract = get_transporte_contract()

        # Obtén el número total de transportes
        total_transportes = transport_contract.functions.nextTransportId().call()

        transportes = []

        # Mapear valores de estado a descripciones
        estado_mapping = {
            0: 'En Camino',
            1: 'Entregado',
            2: 'Retrasado'
        }

        # Obtén detalles de cada transporte
        for i in range(total_transportes):
            transporte = transport_contract.functions.getTransportDetails(i).call()
            transportes.append({
                'id': transporte[0],
                'date': transporte[1],
                'destination': transporte[2],
                'carrier': transporte[3],
                'status': estado_mapping.get(transporte[4], 'Desconocido'),
                'harvest_id': transporte[5][0]  # Ajusta según los datos de cosecha
            })

        if request.method == 'POST':
            # Manejo del formulario POST
            selected_id = request.POST.get('transport_id')
            return redirect('detalle_transporte', id=selected_id)

        # Renderiza la lista de transportes con el formulario para seleccionar el ID
        return render(request, 'lista-transporte.html', {
            'transportes': transportes,
        })
    except Exception as e:
        return render(request, 'error.html', {'message': str(e)})
    
def cosecha_exito(request, block_number):
    # Obtener la cosecha por ID
    cosecha = get_object_or_404(Cosecha, id=block_number)
    
    # Obtener la dirección y el nombre del trabajador desde la sesión
    direccion = request.session.get('direccion_trabajador')
    nombre = request.session.get('nombre_trabajador')

    if direccion is None:
        return HttpResponse("Dirección no encontrada en la sesión", status=400)
    
    # Obtener el trabajador por dirección
    trabajador = get_object_or_404(Trabajador, direccion=direccion)
    
    # Verificar si el nombre almacenado en la sesión coincide con el nombre del trabajador
    if nombre and trabajador.nombre != nombre:
        return HttpResponse("Nombre del trabajador no coincide", status=400)
    
    context = {
        'cosecha': cosecha,
        'trabajador': trabajador
    }

    return render(request, 'registro_exitoso.html', context)

# Usamos la API de Mapbox para convertir direcciones en coordenadas
MAPBOX_ACCESS_TOKEN = 'pk.eyJ1IjoiaXZhYjk4IiwiYSI6ImNtMHlwdGR4bTBxemYyc3EzeWlweTB4b3UifQ.SqDs4IzkxrtKlWqrbDfNXw'

def obtener_coordenadas(direccion):
    url = f"https://api.mapbox.com/geocoding/v5/mapbox.places/{direccion}.json"
    params = {
        'access_token': MAPBOX_ACCESS_TOKEN,
        'limit': 1
    }
    response = requests.get(url, params=params)
    data = response.json()

    if data['features']:
        longitude, latitude = data['features'][0]['center']
        return latitude, longitude
    return None, None

def registrar_cliente(request):
    if request.method == 'POST':
        form = ClienteForm(request.POST)
        if form.is_valid():
            cliente = form.save(commit=False)
            
            # Obtener la dirección ingresada
            direccion = form.cleaned_data['direccion']
            
            # Convertir la dirección a coordenadas
            latitude, longitude = obtener_coordenadas(direccion)
            
            if latitude and longitude:
                # Guardar las coordenadas en el cliente
                cliente.latitude = latitude
                cliente.longitude = longitude
                cliente.save()
                return redirect('cliente_exito')  # Redirigir a una página de éxito
            else:
                form.add_error('direccion', 'No se pudieron obtener las coordenadas para la dirección proporcionada.')
    else:
        form = ClienteForm()

    return render(request, 'registrar_cliente.html', {'form': form})

def cliente_exito(request):
    return render(request, 'cliente_exito.html')

def update_location(request, transporte_id):
    transporte = get_object_or_404(Transporte, id=transporte_id)
    latitude = request.POST.get('latitude')
    longitude = request.POST.get('longitude')
    status = request.POST.get('status')  # Para determinar si el seguimiento se detuvo

    if latitude and longitude:
        transporte.latitude = latitude
        transporte.longitude = longitude
        if status == 'stop':
            transporte.seguimiento_activo = False
            transporte.fecha_fin_seguimiento = timezone.now()
        else:
            transporte.seguimiento_activo = True
            if not transporte.fecha_inicio_seguimiento:
                transporte.fecha_inicio_seguimiento = timezone.now()
        transporte.save()
        return JsonResponse({'status': 'success'})
    return JsonResponse({'status': 'error'}, status=400)
def transporte_view(request, transporte_id):
    transporte = get_object_or_404(Transporte, id=transporte_id)
    return render(request, 'transporte_view.html', {'transporte': transporte})
def verificar_cosecha(request, cosecha_id):
    cosecha = get_object_or_404(Cosecha, id=cosecha_id)
    if request.method == 'POST':
        if 'start_shipping' in request.POST:
            # Activar el GPS y comenzar el seguimiento
            # Redirigir a la página de seguimiento
            return redirect('seguir_envio', cosecha_id=cosecha_id)
    
    return render(request, 'verificar_cosecha.html', {'cosecha': cosecha})

def seguir_envio(request, cosecha_id):
    cosecha = get_object_or_404(Cosecha, id=cosecha_id)
    return render(request, 'seguir_envio.html', {'cosecha': cosecha})

def prueba_ubicacion(request):
    return render(request, 'prueba_ubicacion.html')"""