# webgis/context_processors.py

from django.conf import settings

def mapbox_data(request):
    mapbox_user = settings.MAPBOX_USER
    mapbox_access_token = settings.MAPBOX_ACCESS_TOKEN
    context = {
        'mapbox_user': mapbox_user,
        'mapbox_access_token': mapbox_access_token,
    }
    return context
