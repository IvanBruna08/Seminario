from django.contrib import admin
from django.utils.html import format_html
from .models import Transporte, Predio,Cliente,Distribuidor,Pallet, EnvioPallet, Recepcion, Empaque, Caja, EnvioCaja,Pago,DistribuidorPallet

class ClienteAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'tipo_cliente','direccion','billetera', 'latitude', 'longitude', 'map_view')
    def map_view(self, obj):
        if obj.latitude and obj.longitude:
            return format_html(
                '<div id="map-{}" style="height: 300px; width: 100%;"></div>',
                obj.id
            )
        else:
            return "No location data available"
    map_view.short_description = "Map"

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context['show_map'] = False
        return super().changelist_view(request, extra_context=extra_context)

    def change_view(self, request, object_id, form_url='', extra_context=None):
        extra_context = extra_context or {}
        extra_context['show_map'] = True
        return super().change_view(request, object_id, form_url, extra_context=extra_context)

admin.site.register(Cliente, ClienteAdmin)

class PredioAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'direccion','billetera', 'latitude', 'longitude', 'map_view')

    def map_view(self, obj):
        if obj.latitude and obj.longitude:
            return format_html(
                '<div id="map-{}" style="height: 300px; width: 100%;"></div>',
                obj.id
            )
        else:
            return "No location data available"
    map_view.short_description = "Map"

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context['show_map'] = False
        return super().changelist_view(request, extra_context=extra_context)

    def change_view(self, request, object_id, form_url='', extra_context=None):
        extra_context = extra_context or {}
        extra_context['show_map'] = True
        return super().change_view(request, object_id, form_url, extra_context=extra_context)

admin.site.register(Predio, PredioAdmin)

class DistribuidorAdmin(admin.ModelAdmin):
    list_display = ('nombre','direccion','billetera', 'latitude', 'longitude', 'map_view')

    def map_view(self, obj):
        if obj.latitude and obj.longitude:
            return format_html(
                '<div id="map-{}" style="height: 300px; width: 100%;"></div>',
                obj.id
            )
        else:
            return "No location data available"
    map_view.short_description = "Map"

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context['show_map'] = False
        return super().changelist_view(request, extra_context=extra_context)

    def change_view(self, request, object_id, form_url='', extra_context=None):
        extra_context = extra_context or {}
        extra_context['show_map'] = True
        return super().change_view(request, object_id, form_url, extra_context=extra_context)

admin.site.register(Distribuidor, DistribuidorAdmin)

class TransporteAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'rut','auto','patente', 'billetera')

admin.site.register(Transporte, TransporteAdmin)

class PalletAdmin(admin.ModelAdmin):
    list_display = ['id', 'predio', 'producto', 'clasificacion', 'fecha_cosecha', 'cantidad', 'peso', 'precio_venta','estado_envio']
    search_fields = ['producto', 'clasificacion']
    list_filter = ['fecha_cosecha', 'clasificacion']
    readonly_fields = ['qr_pallet']  # Campo de solo lectura porque se genera automáticamente

    def save_model(self, request, obj, form, change):
        # Guardar el modelo y generar el QR en caso de que no exista
        obj.save()

admin.site.register(Pallet, PalletAdmin)

class DistribuidorPalletAdmin(admin.ModelAdmin):
    list_display = ['id', 'pallet', 'distribuidor', 'peso_enviado', 'estado_pallet']
    search_fields = ['pallet']
    list_filter = ['distribuidor']

    def save_model(self, request, obj, form, change):
        # Guardar el modelo y generar el QR en caso de que no exista
        obj.save()

admin.site.register(DistribuidorPallet, DistribuidorPalletAdmin)

class EnvioPalletAdmin(admin.ModelAdmin):
    list_display = ('pallet', 'transporte', 'fecha_inicio', 'fecha_llegada')
    list_filter = ('transporte', 'fecha_inicio')
    search_fields = ('pallet__id', 'transporte__id')  # Suponiendo que Transporte tiene un campo 'nombre'

admin.site.register(EnvioPallet, EnvioPalletAdmin)

class RecepcionAdmin(admin.ModelAdmin):
    # Lista de campos que se mostrarán en la vista de lista del panel de administración
    list_display = ('id', 'envio_pallet', 'distribuidor', 'fecha_recepcion', 'estado_recepcion','cantidad_cajas','peso_recepcion')
    # Hacer que algunos campos sean enlaces que llevan a la vista de detalle del registro
    list_display_links = ('id', 'envio_pallet')
    # Agregar filtros laterales
    list_filter = ('estado_recepcion', 'fecha_recepcion')
    # Habilitar la búsqueda por campos específicos
    search_fields = ('envio_pallet__pallet__id', 'distribuidor__nombre', 'estado_recepcion')
# Registrar el modelo Recepcion en el admin junto con su configuración
admin.site.register(Recepcion, RecepcionAdmin)

class EmpaqueAdmin(admin.ModelAdmin):
    list_display = ('id', 'recepcion', 'fecha_empaque', 'peso_pallet', 'cantidad_cajas')  # Eliminamos 'tipo_caja'
    search_fields = ('recepcion__id',)  # Eliminamos 'tipo_caja'
    list_filter = ('fecha_empaque',)

class CajaAdmin(admin.ModelAdmin):
    list_display = ('id', 'recepcion', 'cliente', 'tipo_caja','fecha_caja','qr_caja', 'estado_envio')  # Añadimos 'tipo_caja'
    search_fields = ['cliente__nombre', 'recepcion__id']  # Añadimos 'tipo_caja' en búsqueda
    list_filter = ('recepcion', 'tipo_caja')  # Añadimos 'tipo_caja' en filtros

class EnvioCajaAdmin(admin.ModelAdmin):
    list_display = ('id', 'caja', 'transporte', 'fecha_inicio')
    search_fields = ('caja__id', 'transporte__nombre')  # Asumiendo que Transporte tiene un campo 'nombre'
    list_filter = ('caja_id',)

class PagoAdmin(admin.ModelAdmin):
    list_display = ('id', 'cliente', 'monto', 'fecha_pago')
    search_fields = ('cliente__nombre',)  # Asumiendo que Cliente tiene un campo 'nombre'
    list_filter = ('fecha_pago',)

# Registro de los modelos en el admin
admin.site.register(Empaque, EmpaqueAdmin)
admin.site.register(Caja, CajaAdmin)
admin.site.register(EnvioCaja, EnvioCajaAdmin)
admin.site.register(Pago, PagoAdmin)