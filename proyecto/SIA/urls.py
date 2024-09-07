from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('registrar-cosecha/', views.registrar_cosecha, name='registrar_cosecha'),
    path('contract-status/', views.contract_status, name='contract_status'),
    path('detalle-cosecha/', views.lista_cosechas, name='detalle_cosecha'),
    path('detalle-cosecha/<int:id>/', views.obtener_detalle_cosecha, name='detalle_cosecha'),
    path('transporte',views.transporte, name='transporte'),
    path('cliente',views.cliente, name='cliente'),
    path('acceso/<str:area>/', views.acceso_trabajador, name='acceso_trabajador'),
    path('marcar-transportado/',views.TransportadoListView.as_view(), name='marcar_transportado'),
    path('marcar-transportado/accion',views.MarcarTransportadoView.as_view(), name='marcar_transportado_accion'),
    path('lista-transporte/', views.lista_transportes, name='lista_transporte'),
    path('registrar-transporte/', views.registrar_transporte, name='registrar_transporte'),
    path('detalle-transporte/<int:id>/', views.detalle_transporte, name='detalle_transporte'),
    path('registro_exitoso/<int:block_number>/', views.cosecha_exito, name='registro_exitoso'),
    path('cosecha/<int:cosecha_id>/verificar/', views.verificar_cosecha, name='verificar_cosecha'),
    path('ingresar_direccion_billetera/', views.ingresar_direccion_billetera, name='ingresar_direccion_billetera'),
]
