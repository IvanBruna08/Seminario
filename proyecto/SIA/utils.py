from web3 import Web3
from django.conf import settings
import os
import json
from .models import Cosecha
from django.core.files.base import ContentFile
from io import BytesIO
import qrcode

def get_web3():
    infura_url = "https://sepolia.infura.io/v3/5cf427c2915a449ca23fbaa62461efba"
    web3 = Web3(Web3.HTTPProvider(infura_url))
    if not web3.is_connected():
        raise ConnectionError("No se pudo conectar a la red de Ethereum.")
    return web3

def get_cosecha_contract():
    web3 = get_web3()
    json_file_path = os.path.join(settings.BASE_DIR, "SIA", "static", "contract", "Cosecha.json")

    try:
        with open(json_file_path) as file:
            contract_json = json.load(file)
            contract_abi = contract_json['abi']
            contract_address = contract_json['networks']['11155111']['address']
            return web3.eth.contract(address=contract_address, abi=contract_abi)
    except FileNotFoundError:
        print(f"Error: No se encontró el archivo {json_file_path}.")
        raise
    except json.JSONDecodeError:
        print("Error: No se pudo decodificar el archivo JSON.")
        raise
    except Exception as e:
        print(f"Error al cargar el contrato: {e}")
        raise

def get_transporte_contract():
    web3 = get_web3()
    json_file_path = os.path.join(settings.BASE_DIR, "SIA", "static", "contract", "TransportContract.json")

    try:
        with open(json_file_path) as file:
            contract_json = json.load(file)
            contract_abi = contract_json['abi']
            contract_address = contract_json['networks']['11155111']['address']
            print(f"Dirección del contrato de transporte cargada: {contract_address}")
            return web3.eth.contract(address=contract_address, abi=contract_abi)
    except FileNotFoundError:
        print(f"Error: No se encontró el archivo {json_file_path}.")
        raise
    except json.JSONDecodeError:
        print("Error: No se pudo decodificar el archivo JSON.")
        raise
    except Exception as e:
        print(f"Error al cargar el contrato: {e}")
        raise

def load_cosecha_contract():
    with open(os.path.join(settings.BASE_DIR, 'SIA', 'static', 'contract', 'Cosecha.json')) as f:
        contract_data = json.load(f)
    return contract_data['abi'], contract_data['networks']['11155111']['address']

def load_transporte_contract():
    with open(os.path.join(settings.BASE_DIR, 'SIA', 'static', 'contract', 'TransportContract.json')) as f:
        contract_data = json.load(f)
    return contract_data['abi'], contract_data['networks']['11155111']['address']
def sync_cosechas():
    contract = get_cosecha_contract()
    cosecha_counter = contract.functions.cosechaCounter().call()

    for i in range(1, cosecha_counter + 1):
        cosecha_data = contract.functions.obtenerCosecha(i).call()

        # Aquí actualizamos o creamos el objeto Cosecha en la base de datos
        obj, created = Cosecha.objects.update_or_create(
            id=cosecha_data[0],
            defaults={
                'producto': cosecha_data[1],
                'fecha_cosecha': cosecha_data[2],
                'ubicacion': cosecha_data[3],
                'cantidad_lote': cosecha_data[4],
                'cantidad_agua': cosecha_data[5],
                'pesticidas_fertilizantes': cosecha_data[6],
                'practicas_cultivo': cosecha_data[7],
                'transportado': cosecha_data[8],
            }
        )
        if created:
            print(f"Cosecha creada: {obj.id}")
        else:
            print(f"Cosecha actualizada: {obj.id}")

def generar_codigo_qr(cosecha):
    # Generar la URL dinámica para verificar la cosecha
    qr_url = f"{settings.SITE_URL}/cosecha/{cosecha.id}/verificar"
    
    # Crear los datos del QR con la URL
    data = (
        f"URL para verificar cosecha: {qr_url}\n"
        f"Cosecha ID: {cosecha.id}\n"
        f"Producto: {cosecha.producto}\n"
        f"Fecha: {cosecha.fecha_cosecha}\n"
        f"Ubicación: {cosecha.ubicacion}\n"
        f"Cantidad Lote: {cosecha.cantidad_lote}\n"
        f"Cantidad Agua: {cosecha.cantidad_agua}\n"
        f"Pesticidas/Fertilizantes: {cosecha.pesticidas_fertilizantes}\n"
        f"Prácticas de Cultivo: {cosecha.practicas_cultivo}\n"
        f"Transportado: {'Sí' if cosecha.transportado else 'No'}"
    )
    
    # Generar el código QR
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
    qr_content = ContentFile(qr_io.getvalue(), name=f'qr_cosecha_{cosecha.id}.png')
    
    return qr_content