from django.contrib import admin
from django.utils.html import format_html
from .models import Trabajador, Cosecha
from .utils import sync_cosechas, generar_codigo_qr

@admin.register(Trabajador)
class TrabajadorAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'direccion', 'area')

@admin.register(Cosecha)
class CosechaAdmin(admin.ModelAdmin):
    list_display = ('id', 'producto', 'fecha_cosecha', 'ubicacion', 'cantidad_lote', 'transportado', 'mostrar_qr_code')
    actions = ['sync_cosechas_action', 'generar_qr_faltantes']

    def mostrar_qr_code(self, obj):
        if obj.qr_code:
            return format_html('<img src="{}" width="100" height="100" />', obj.qr_code.url)
        return "No hay QR generado"
    mostrar_qr_code.short_description = 'Código QR'

    @admin.action(description='Generar códigos QR faltantes')
    def generar_qr_faltantes(self, request, queryset):
    # Filtrar cosechas sin un código QR
      cosechas_sin_qr = queryset.filter(qr_code__isnull=True) | queryset.filter(qr_code__exact='')

      if cosechas_sin_qr.exists():
            for cosecha in cosechas_sin_qr:
                # Generar el contenido del QR
                qr_content = generar_codigo_qr(cosecha)
                qr_filename = f'qr_cosecha_{cosecha.id}.png'
                
                # Guardar el archivo QR
                cosecha.qr_code.save(qr_filename, qr_content, save=False)
                cosecha.save()

            # Mostrar un mensaje de éxito con el conteo de QR generados
            self.message_user(request, f"Se han generado los códigos QR para {cosechas_sin_qr.count()} cosechas.")
      else:
        # Si no hay cosechas sin QR, mostrar una advertencia
        self.message_user(request, "No se encontraron cosechas sin código QR.", level='warning')