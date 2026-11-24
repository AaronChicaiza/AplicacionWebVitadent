from django.contrib import admin

from .models import (
    AccesoPersonal,
    Cita,
    CitaEvento,
    Conversacion,
    EventoAuditoria,
    HorarioAtencion,
    MensajeConversacion,
    Notificacion,
    Paciente,
    Sucursal,
    Especialista,
    Tratamiento,
)


@admin.register(Especialista)
class EspecialistaAdmin(admin.ModelAdmin):
    list_display = ("nombre_completo", "especialidad", "usuario", "activo")
    list_filter = ("activo", "especialidad")
    search_fields = ("nombre_completo", "usuario__username")


@admin.register(Tratamiento)
class TratamientoAdmin(admin.ModelAdmin):
    list_display = ("nombre", "area", "duracion_minutos", "activo")
    list_filter = ("activo", "area")
    search_fields = ("nombre", "area")


@admin.register(Paciente)
class PacienteAdmin(admin.ModelAdmin):
    list_display = ("nombre_completo", "identificacion", "telefono", "correo", "creado_en")
    search_fields = ("nombre_completo", "identificacion", "telefono", "correo")
    readonly_fields = ("creado_en",)


@admin.register(Cita)
class CitaAdmin(admin.ModelAdmin):
    list_display = ("codigo", "paciente", "tratamiento", "especialista", "fecha_hora_solicitada", "estado")
    list_filter = ("estado", "tratamiento", "especialista")
    search_fields = ("codigo", "paciente__nombre_completo", "paciente__telefono")
    readonly_fields = ("codigo", "creado_en", "estado")

    def save_model(self, request, obj, form, change):
        anterior = None
        if change:
            anterior = Cita.objects.get(pk=obj.pk)
        super().save_model(request, obj, form, change)
        if not anterior:
            CitaEvento.objects.create(cita=obj, accion=CitaEvento.Accion.SOLICITADA, actor=request.user)
            return
        if anterior.especialista_id != obj.especialista_id:
            CitaEvento.objects.create(cita=obj, accion=CitaEvento.Accion.ASIGNADA, actor=request.user)
        if anterior.fecha_hora_solicitada != obj.fecha_hora_solicitada:
            obj.estado = Cita.Estado.REPROGRAMADA
            obj.save(update_fields=["estado"])
            CitaEvento.objects.create(
                cita=obj,
                accion=CitaEvento.Accion.REPROGRAMADA,
                fecha_anterior=anterior.fecha_hora_solicitada,
                fecha_nueva=obj.fecha_hora_solicitada,
                actor=request.user,
            )


@admin.register(HorarioAtencion)
class HorarioAtencionAdmin(admin.ModelAdmin):
    list_display = ("especialista", "dia_semana", "hora_inicio", "hora_fin", "activo")
    list_filter = ("activo", "dia_semana", "especialista")


@admin.register(Sucursal)
class SucursalAdmin(admin.ModelAdmin):
    list_display = ("nombre", "direccion", "telefono", "activa")
    list_filter = ("activa",)
    search_fields = ("nombre", "direccion")


@admin.register(Conversacion)
class ConversacionAdmin(admin.ModelAdmin):
    list_display = ("id", "canal", "whatsapp_id", "estado", "ultima_actividad")
    list_filter = ("canal", "estado", "ultima_actividad")
    search_fields = ("whatsapp_id", "identificador_hash")
    readonly_fields = ("canal", "whatsapp_id", "identificador_hash", "iniciada_en", "ultima_actividad")


@admin.register(MensajeConversacion)
class MensajeConversacionAdmin(admin.ModelAdmin):
    list_display = ("conversacion", "direccion", "tipo", "creado_en")
    list_filter = ("direccion", "tipo", "creado_en")
    readonly_fields = ("conversacion", "identificador_proveedor", "direccion", "tipo", "contenido", "creado_en")

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(EventoAuditoria)
class EventoAuditoriaAdmin(admin.ModelAdmin):
    list_display = ("accion", "tipo_objeto", "identificador_objeto", "actor", "creado_en")
    list_filter = ("accion", "creado_en")
    search_fields = ("accion", "tipo_objeto", "identificador_objeto", "actor__username")
    readonly_fields = ("actor", "accion", "tipo_objeto", "identificador_objeto", "detalles", "creado_en")

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(Notificacion)
class NotificacionAdmin(admin.ModelAdmin):
    list_display = ("cita", "canal", "tipo", "estado", "programada_para", "enviada_en")
    list_filter = ("canal", "estado", "tipo")


@admin.register(CitaEvento)
class CitaEventoAdmin(admin.ModelAdmin):
    list_display = ("cita", "accion", "creado_en", "actor")
    list_filter = ("accion", "creado_en")
    search_fields = ("cita__codigo",)
    readonly_fields = ("cita", "accion", "fecha_anterior", "fecha_nueva", "actor", "creado_en")

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(AccesoPersonal)
class AccesoPersonalAdmin(admin.ModelAdmin):
    list_display = ("usuario", "cambio_clave_obligatorio", "creado_en")
    list_filter = ("cambio_clave_obligatorio",)
    search_fields = ("usuario__username", "usuario__first_name", "usuario__last_name")
    readonly_fields = ("usuario", "creado_en")
