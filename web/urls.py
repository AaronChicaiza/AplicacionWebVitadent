from django.urls import path
from django.contrib.auth.views import LogoutView

from . import views
from . import api

urlpatterns = [
    path("healthz/", views.healthz, name="healthz"),
    # Sitio público
    path("", views.inicio, name="inicio"),
    path("tratamientos/", views.tratamientos, name="tratamientos"),
    path("equipo/", views.especialistas, name="especialistas"),
    path("citas/", views.asistente_citas, name="asistente_citas"),
    path("api/interna/solicitudes/", views.api_interna_crear_solicitud, name="api_interna_crear_solicitud"),
    path("api/whatsapp/webhook/", views.webhook_whatsapp, name="webhook_whatsapp"),
    path("api/interna/citas/cancelar/", views.api_whatsapp_cancelar_cita, name="api_whatsapp_cancelar_cita"),
    path("api/interna/citas/consultar/", views.api_whatsapp_consultar_cita, name="api_whatsapp_consultar_cita"),
    path("api/interna/citas/reprogramar/", views.api_whatsapp_reprogramar_cita, name="api_whatsapp_reprogramar_cita"),
    path("api/v1/tratamientos/", api.TratamientosAPI.as_view(), name="api_tratamientos"),
    path("api/v1/especialistas/", api.EspecialistasAPI.as_view(), name="api_especialistas"),
    path("api/v1/sucursales/", api.SucursalesAPI.as_view(), name="api_sucursales"),
    path("api/v1/disponibilidad/", api.DisponibilidadAPI.as_view(), name="api_disponibilidad"),
    path("api/v1/citas/", api.CitasAPI.as_view(), name="api_citas"),
    path("api/v1/citas/<int:pk>/", api.CitaDetalleAPI.as_view(), name="api_cita_detalle"),
    path("api/v1/pacientes/", api.PacientesAPI.as_view(), name="api_pacientes"),
    path("api/v1/conversaciones/", api.ConversacionesAPI.as_view(), name="api_conversaciones"),
    path("api/v1/conversaciones/<int:pk>/", api.ConversacionDetalleAPI.as_view(), name="api_conversacion_detalle"),
    path("acceso/", views.acceso_personal, name="acceso_personal"),
    path("acceso/ingresar/", views.AccesoDjangoView.as_view(), name="ingresar_personal"),
    path("acceso/cambiar-clave/", views.cambiar_clave_inicial, name="cambiar_clave_inicial"),
    path("acceso/salir/", LogoutView.as_view(), name="salir_personal"),

    # Panel de administración
    path("gestion/", views.gestion_inicio, name="gestion_inicio"),
    path("gestion/citas/", views.gestion_citas, name="gestion_citas"),
    path("gestion/pacientes/", views.gestion_pacientes, name="gestion_pacientes"),
    path("gestion/agenda/", views.gestion_agenda, name="gestion_agenda"),
    path("gestion/especialistas/", views.gestion_especialistas, name="gestion_especialistas"),
    path("gestion/tratamientos/", views.gestion_tratamientos, name="gestion_tratamientos"),
    path("gestion/notificaciones/", views.gestion_notificaciones, name="gestion_notificaciones"),
    path("gestion/conversaciones/", views.gestion_conversaciones, name="gestion_conversaciones"),
    path("gestion/conversaciones/<int:pk>/", views.gestion_conversaciones, name="gestion_conversacion_detalle"),
    path("gestion/auditoria/", views.gestion_auditoria, name="gestion_auditoria"),

    # Espacio profesional
    path("doctor/", views.espacio_especialista, name="espacio_especialista"),
    path("doctor/pacientes/", views.espacio_especialista, name="especialista_pacientes"),
    path("doctor/agenda/", views.espacio_especialista, name="especialista_agenda"),
]
