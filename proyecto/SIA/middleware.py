"""from django.shortcuts import redirect
from .models import Trabajador  # Asegúrate de que esta ruta sea correcta

class AreaTrabajadorMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Verificar que el trabajador ha ingresado y tiene una dirección de billetera en la sesión
        direccion_billetera = request.session.get('direccion_billetera')

        if direccion_billetera:
            try:
                # Consultar el área del trabajador en la base de datos
                trabajador = Trabajador.objects.get(direccion=direccion_billetera)
                request.session['area'] = trabajador.area
            except Trabajador.DoesNotExist:
                # Trabajador no encontrado, redirigir al acceso
                return redirect('acceso_trabajador')
        else:
            # No hay dirección de billetera en la sesión, redirigir al acceso
            return redirect('acceso_trabajador')

        # Continuar con la solicitud si todo está bien
        response = self.get_response(request)
        return response
"""