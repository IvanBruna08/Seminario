from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('login', views.custom_login, name='login'),
    path('logout/', views.custom_logout, name='custom_logout'),
    #REGISTRO
    path('registro_actores', views.registro_actores, name='registro_actores'),
    path('registro_vehiculo', views.registrar_vehiculo, name='registrar_vehiculo'),
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
    path('informacion_pallet/<str:secure_id>/', views.informacion_pallet, name='informacion_pallet'),
    path('recepcion/<str:secure_id>/', views.registrar_recepcion, name='registrar_recepcion'),
    # Ruta para transportar pallet y cajas
    path('transportar_pallet/<str:secure_id>/', views.transportar_pallet, name='transportar_pallet'),
    path('actualizar_pallet/', views.actualizar_pallet, name='actualizar_pallet'),
    path('actualizar_datos_pallet/<int:pallet_id>/', views.actualizar_datos_pallet, name='actualizar_datos_pallet'),
    path('eliminar_distribuidor/<int:pallet_id>', views.eliminar_distribuidores, name='eliminar_distribuidor'),
    path('eliminar-distribuidorpallet/<int:distribuidor_pallet_id>/', views.eliminar_distribuidor_pallet, name='eliminar_distribuidor_pallet'),
    path('añadir_distribuidor/<int:pallet_id>/', views.añadir_distribuidor, name='añadir_distribuidor'),


    
    path('iniciar-entrega-pallet/<str:secure_id>/', views.iniciar_entrega, name='iniciar_entrega'),
    path('finalizar-entrega-pallet/<str:secure_id>/', views.finalizar_entrega, name='finalizar_entrega'),
    path('actualizar-coordenadas/', views.actualizar_coordenadas, name='actualizar_coordenadas'),
    path('actualizar-coordenadas-caja/',views.actualizar_coordenadas_caja,name='actualizar_coordenadas_caja'),

    path('verificar-pallet/', views.verificar_pallet, name='verificar_pallet'),
    path('verificar-caja/', views.verificar_caja, name='verificar_caja'),
    path('transportar-caja/<str:secure_id>/', views.transportar_caja, name='transportar_caja'),
    path('iniciar-entrega-caja/<str:secure_id>/', views.iniciar_entrega_caja, name='iniciar_entrega_caja'),
    path('finalizar-entrega-caja/<str:secure_id>/', views.finalizar_entrega_caja,name='finalizar_entrega_caja'),
    path('seleccionar_opcion/<int:pallet_id>/', views.seleccionar_opcion, name='selecionar_opcion'),
    # Para las funciones de crear caja y empaque
    path('recepciones-completadas/', views.recepciones_completadas, name='recepciones_completadas'),
    path('distribuir-caja/', views.distribuir_caja, name='distribuir_caja'),
    path('cajas/', views.cajas_view, name='cajas_view'),
    # Funciones para escanear qr de caja
    path('seleccionar_caja/<int:caja_id>/', views.seleccionar_caja, name='selecionar_caja'),
    path('informacion_caja/<str:secure_id>/', views.informacion_caja, name='informacion_caja'),
    # funcion para cliente
    path('recibir_caja/<str:secure_id>/', views.recibir_caja, name='recibir_caja'),
    path('asignar_cliente/', views.asignar_cliente, name='asignar_cliente'),
    path('crear_caja/', views.tipocaja, name='crear_caja'),
     path('detalles-caja/<str:secure_id>/', views.detalles_caja, name='detalles_caja'),
]
