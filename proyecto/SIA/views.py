from django.db.models.query import QuerySet
from django.db import IntegrityError
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from web3 import Web3
from django.views import View
import json
import os
from .forms import CosechaForm , MarcarTransportadoForm, RegistroTransporteForm, ActualizarEstadoTransporteForm, PlacaForm
from .models import Trabajador , Cosecha
from django.conf import settings
from django.views.generic import ListView
from .utils import get_web3,get_transporte_contract,get_cosecha_contract
from django.utils.dateparse import parse_date
from django.contrib.auth.decorators import login_required
from django.contrib import messages
# Reemplaza con tu URL de Infura
infura_url = "https://sepolia.infura.io/v3/5cf427c2915a449ca23fbaa62461efba"
web3 = Web3(Web3.HTTPProvider(infura_url))

if web3.is_connected():
    print("Conexión exitosa a Infura.")
else:
    print("No se pudo conectar a Infura.")

def acceso_trabajador(request, area):
    if request.method == 'POST':
        direccion = request.POST.get('direccion')
        trabajador = Trabajador.objects.filter(direccion=direccion).first()
        
        if trabajador:
            if trabajador.area == area:
                # Almacenar la dirección del trabajador en la sesión
                request.session['direccion'] = trabajador.direccion  # Guarda la dirección del trabajador
                print(f"Dirección del trabajador: {trabajador.direccion}")  # Imprimir en la terminal

                if area == 'cosecha':
                    return redirect('registrar_cosecha')
                elif area == 'transporte':
                    return redirect('registrar_transporte')  # Asegúrate de redirigir a la función correcta
            else:
                return render(request, 'error.html', {'message': f'Usted pertenece al área de {trabajador.area}. No tiene acceso a {area}.'})
        else:
            return render(request, 'error.html', {'message': 'Trabajador no encontrado.'})

    return render(request, 'acceso-trabajador.html', {'area': area})


def home(request):
    return render(request, 'home.html')
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

@login_required
def verificar_cosecha(request, cosecha_id):
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
        return render(request, 'verificar_cosecha.html', {'cosecha': cosecha})

def ingresar_direccion_billetera(request):
    if request.method == 'POST':
        direccion_billetera = request.POST.get('direccion_billetera')
        request.session['direccion_billetera'] = direccion_billetera
        return redirect('verificar_cosecha', cosecha_id=request.GET.get('cosecha_id'))
    
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
    cosecha = get_object_or_404(Cosecha, id=block_number)
    
    direccion = request.session.get('direccion')
    trabajador = get_object_or_404(Trabajador, direccion=direccion)
    
    context = {
        'cosecha': cosecha,
        'trabajador': trabajador
    }

    return render(request, 'registro_exitoso.html', context)

