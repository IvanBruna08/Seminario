# decorators.py
from django.http import HttpResponseForbidden
from django.shortcuts import redirect
from .models import Cliente, Distribuidor, Transporte, Predio

def login_required_for_model(model_class):
    def decorator(view_func):
        def _wrapped_view(request, *args, **kwargs):
            user_id = request.session.get('user_id')
            if user_id:
                try:
                    user = model_class.objects.get(id=user_id)
                    return view_func(request, *args, **kwargs)
                except model_class.DoesNotExist:
                    return redirect('login')  # Redirigir si no tiene permiso
            return redirect('login')  # Redirigir si no hay un ID de usuario en la sesión
        return _wrapped_view
    return decorator
