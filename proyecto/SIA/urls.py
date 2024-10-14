from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('login', views.custom_login, name='login'),
    path('logout/', views.custom_logout, name='custom_logout'),
    #REGISTRO
    path('registro_actores', views.registro_actores, name='registro_actores'),
    path('registrar_predio', views.registrar_predio, name='registrar_predio'),
    path('registrar_transportista', views.registrar_transportista, name='registrar_transportista'),
    path('registrar_distribuidor', views.registrar_distribuidor, name='registrar_distribuidor'),
    path('registrar_cliente', views.registrar_cliente, name='registrar_cliente'),
    #VISTAS PRINCIPAL
    path('predio', views.predio, name='dashboard_predio'), 
    path('cliente', views.cliente, name='dashboard_cliente'),
    path('transporte', views.transporte, name='dashboard_transporte'),
    path('distribuidor', views.distribuidor, name='dashboard_distribuidor'),
    # FUNCIONES DE ACTORES
    path('registrar_pallet', views.crear_pallet, name='registrar_pallet'),
    path('distribuir_pallet', views.distribuir_pallet, name='distribuir_pallet'),
    path('Pallets/', views.pallet_view, name='pallet_view'),
    path('informacion_pallet/<int:pallet_id>/', views.informacion_pallet, name='informacion_pallet'),
    path('recepcion/<int:pallet_id>/', views.registrar_recepcion, name='registrar_recepcion'),
    # Ruta para transportar pallet y cajas
    path('transportar_pallet/<int:pallet_id>/', views.transportar_pallet, name='transportar_pallet'),
    path('iniciar-entrega-pallet/<int:pallet_id>/', views.iniciar_entrega, name='iniciar_entrega'),
    path('finalizar-entrega-pallet/<int:pallet_id>/', views.finalizar_entrega, name='finalizar_entrega'),
    path('verificar-pallet/', views.verificar_pallet, name='verificar_pallet'),
    path('transportar-caja/<int:caja_id>/', views.transportar_caja, name='transportar_caja'),
    path('iniciar-entrega-caja/<int:caja_id>/', views.iniciar_entrega_caja, name='iniciar_entrega_caja'),
    path('finalizar-entrega-caja/<int:caja_id>/', views.finalizar_entrega_caja,name='finalizar_entrega_caja'),
    path('seleccionar_opcion/<int:pallet_id>/', views.seleccionar_opcion, name='selecionar_opcion'),
    # Para las funciones de crear caja y empaque
    path('recepciones-completadas/', views.recepciones_completadas, name='recepciones_completadas'),
    path('crear-empaque/', views.crear_empaque, name='crear_empaque'),
    path('distribuir-caja/', views.distribuir_caja, name='distribuir_caja'),
    path('cajas/', views.cajas_view, name='cajas_view'),
    # Funciones para escanear qr de caja
    path('seleccionar_caja/<int:caja_id>/', views.seleccionar_caja, name='selecionar_caja'),
    path('informacion_caja/<int:caja_id>/', views.informacion_caja, name='informacion_caja'),
    # funcion para cliente
    path('recibir_caja/<int:caja_id>/', views.recibir_caja, name='recibir_caja'),
]
