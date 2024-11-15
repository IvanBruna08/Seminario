from web3 import Web3
from django.conf import settings 
import os
import json
import requests
import urllib.parse
from django.core.files.base import ContentFile
from io import BytesIO
import qrcode

def get_web3():
    web3 = Web3(Web3.HTTPProvider("HTTP://127.0.0.1:7545"))
    if not web3.is_connected():
        raise ConnectionError("No se pudo conectar a la red de Ethereum.")
    return web3

def get_pallet_contract():
    web3 = get_web3()
    json_file_path = os.path.join(settings.BASE_DIR, "SIA", "static", "contract", "PalletRegistry.json")

    try:
        with open(json_file_path) as file:
            contract_json = json.load(file)
            contract_abi = contract_json['abi']
            contract_address = contract_json['networks']['5777']['address']
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
    json_file_path = os.path.join(settings.BASE_DIR, "SIA", "static", "contract", "Transporte.json")

    try:
        with open(json_file_path) as file:
            contract_json = json.load(file)
            contract_abi = contract_json['abi']
            contract_address = contract_json['networks']['5777']['address']
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


def get_distribuidor_contract():
    web3 = get_web3()
    json_file_path = os.path.join(settings.BASE_DIR, "SIA", "static", "contract", "Distribuidor.json")

    try:
        with open(json_file_path) as file:
            contract_json = json.load(file)
            contract_abi = contract_json['abi']
            contract_address = contract_json['networks']['5777']['address']
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

import requests

def get_coordinates(address):
    url = "https://us1.locationiq.com/v1/search.php"
    params = {
        'key': 'pk.9354bd3dfb21f2189825cae5914748b0',  # Reemplaza con tu token de LocationIQ
        'q': address,
        'format': 'json',
        'limit': 1
    }

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()

        if data:
            best_match = data[0]
            # Asegúrate de usar '.' como separador decimal
            latitude = float(best_match['lat'].replace(',', '.'))
            longitude = float(best_match['lon'].replace(',', '.'))
            return latitude, longitude
        
        return None, None

    except requests.RequestException as e:
        print(f"Error al obtener las coordenadas: {e}")
        return None, None