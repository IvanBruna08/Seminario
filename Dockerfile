# Usar una imagen base de Python
FROM python:3.11

# Establecer el directorio de trabajo en el subdirectorio donde está manage.py
WORKDIR /app/proyecto

# Copiar el archivo de requerimientos desde el directorio raíz
COPY requirements.txt /app/

# Instalar las dependencias del archivo requirements.txt
RUN pip install -r /app/requirements.txt

# Copiar el resto de los archivos de la aplicación desde el directorio raíz
COPY proyecto /app/proyecto

# Comando para ejecutar la aplicación
CMD ["python", "manage.py", "runserver", "0.0.0.0:8080"]
