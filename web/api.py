"""API REST versionada para consulta pública y gestión autenticada."""

from datetime import date, datetime, time, timedelta

from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework.pagination import PageNumberPagination
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Cita, CitaEvento, Conversacion, Especialista, EventoAuditoria, Paciente, Sucursal, Tratamiento
from .agenda import bloque_disponible, bloques_disponibles
from .serializers import (
    CambioEstadoCitaSerializer,
    CitaLecturaSerializer,
    ConversacionResumenSerializer,
    EstadoConversacionSerializer,
    EspecialistaPublicoSerializer,
    DisponibilidadRespuestaSerializer,
    MensajeConversacionSerializer,
    PacienteLecturaSerializer,
    SucursalSerializer,
    TratamientoSerializer,
)


def pagina(queryset, request, serializer):
    paginador = PageNumberPagination()
    paginador.page_size = 50
    items = paginador.paginate_queryset(queryset, request)
    return paginador.get_paginated_response(serializer(items, many=True).data)


class TratamientosAPI(APIView):
    permission_classes = [AllowAny]

    @extend_schema(responses=TratamientoSerializer(many=True), summary="Listar tratamientos activos")
    def get(self, request):
        return pagina(Tratamiento.objects.filter(activo=True), request, TratamientoSerializer)


class EspecialistasAPI(APIView):
    permission_classes = [AllowAny]

    @extend_schema(responses=EspecialistaPublicoSerializer(many=True), summary="Listar especialistas activos")
    def get(self, request):
        return pagina(Especialista.objects.filter(activo=True), request, EspecialistaPublicoSerializer)


class SucursalesAPI(APIView):
    permission_classes = [AllowAny]

    @extend_schema(responses=SucursalSerializer(many=True), summary="Listar sucursales activas")
    def get(self, request):
        return pagina(Sucursal.objects.filter(activa=True), request, SucursalSerializer)


class DisponibilidadAPI(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        summary="Consultar bloques disponibles de un especialista",
        responses=DisponibilidadRespuestaSerializer,
        parameters=[
            OpenApiParameter("fecha", str, description="Fecha local YYYY-MM-DD", required=True),
            OpenApiParameter("especialista", int, description="ID del especialista activo", required=True),
            OpenApiParameter("tratamiento", int, description="ID de tratamiento activo", required=False),
        ],
    )
    def get(self, request):
        fecha_texto = request.query_params.get("fecha", "")
        especialista_id = request.query_params.get("especialista", "")
        tratamiento_id = request.query_params.get("tratamiento", "")
        try:
            fecha = date.fromisoformat(fecha_texto)
            if fecha_texto != fecha.isoformat() or fecha < timezone.localdate() or fecha > timezone.localdate() + timedelta(days=365):
                raise ValueError
            especialista_id = int(especialista_id)
        except (ValueError, TypeError):
            raise ValidationError({"fecha": "Indica una fecha futura o de hoy en formato YYYY-MM-DD y un especialista válido."})
        especialista = get_object_or_404(Especialista, pk=especialista_id, activo=True)
        tratamiento = None
        if tratamiento_id:
            try:
                tratamiento = get_object_or_404(Tratamiento, pk=int(tratamiento_id), activo=True)
            except (ValueError, TypeError):
                raise ValidationError({"tratamiento": "El tratamiento debe ser un identificador del catálogo."})

        duracion = tratamiento.duracion_minutos if tratamiento and tratamiento.duracion_minutos else 30
        bloques = bloques_disponibles(especialista, fecha, duracion)
        return Response({"fecha": fecha.isoformat(), "especialista": especialista.pk, "duracion_minutos": duracion, "bloques": bloques})


def citas_visibles(usuario):
    queryset = Cita.objects.select_related("paciente", "tratamiento", "especialista", "sucursal")
    if usuario.is_staff:
        return queryset
    perfil = getattr(usuario, "perfil_especialista", None)
    if not perfil or not perfil.activo:
        raise PermissionDenied("La cuenta no tiene un rol profesional activo.")
    return queryset.filter(especialista=perfil)


class CitasAPI(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(summary="Listar citas permitidas para el rol autenticado", responses=CitaLecturaSerializer(many=True))
    def get(self, request):
        queryset = citas_visibles(request.user)
        estado = request.query_params.get("estado", "")
        if estado:
            if estado not in Cita.Estado.values:
                raise ValidationError({"estado": "Estado no permitido."})
            queryset = queryset.filter(estado=estado)
        fecha_desde = request.query_params.get("desde")
        fecha_hasta = request.query_params.get("hasta")
        try:
            if fecha_desde:
                queryset = queryset.filter(fecha_hora_solicitada__date__gte=date.fromisoformat(fecha_desde))
            if fecha_hasta:
                queryset = queryset.filter(fecha_hora_solicitada__date__lte=date.fromisoformat(fecha_hasta))
        except ValueError:
            raise ValidationError({"fecha": "Las fechas deben usar el formato YYYY-MM-DD."})
        return pagina(queryset.order_by("fecha_hora_solicitada"), request, CitaLecturaSerializer)


class CitaDetalleAPI(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(summary="Consultar una cita dentro del alcance del rol", responses=CitaLecturaSerializer)
    def get(self, request, pk):
        cita = get_object_or_404(citas_visibles(request.user), pk=pk)
        return Response(CitaLecturaSerializer(cita).data)

    @extend_schema(request=CambioEstadoCitaSerializer, summary="Cambiar el estado de una cita (administración)", responses=CitaLecturaSerializer)
    def patch(self, request, pk):
        if not request.user.is_staff:
            raise PermissionDenied("Solo administración puede cambiar el estado de citas.")
        datos = CambioEstadoCitaSerializer(data=request.data)
        datos.is_valid(raise_exception=True)
        nuevo_estado = datos.validated_data["estado"]
        motivo = datos.validated_data.get("motivo", "")
        with transaction.atomic():
            cita = get_object_or_404(Cita.objects.select_for_update().select_related("especialista", "tratamiento"), pk=pk)
            estado_anterior = cita.estado
            permitidas = {
                Cita.Estado.SOLICITADA: {Cita.Estado.CONFIRMADA, Cita.Estado.CANCELADA},
                Cita.Estado.REPROGRAMADA: {Cita.Estado.CONFIRMADA, Cita.Estado.CANCELADA},
                Cita.Estado.CONFIRMADA: {Cita.Estado.CANCELADA, Cita.Estado.ATENDIDA},
            }
            if nuevo_estado not in permitidas.get(estado_anterior, set()):
                raise ValidationError({"estado": "Transición no permitida para el estado actual."})
            if nuevo_estado == Cita.Estado.CONFIRMADA:
                if not cita.especialista_id or cita.fecha_hora_solicitada <= timezone.now():
                    raise ValidationError({"estado": "Asigna un especialista y una fecha futura antes de confirmar."})
                if not cita.especialista.activo:
                    raise ValidationError({"estado": "El especialista ya no está activo."})
                Especialista.objects.select_for_update().get(pk=cita.especialista_id)
                duracion = cita.tratamiento.duracion_minutos or 30
                if not bloque_disponible(cita.especialista, cita.fecha_hora_solicitada, duracion, excluir_cita=cita.pk):
                    raise ValidationError({"estado": "El horario no coincide con la agenda o se cruza con otra cita o solicitud."})
            cita.estado = nuevo_estado
            cita.save(update_fields=["estado"])
            accion = {
                Cita.Estado.CONFIRMADA: CitaEvento.Accion.CONFIRMADA,
                Cita.Estado.CANCELADA: CitaEvento.Accion.CANCELADA,
                Cita.Estado.ATENDIDA: CitaEvento.Accion.ATENDIDA,
            }[nuevo_estado]
            CitaEvento.objects.create(cita=cita, accion=accion, actor=request.user, motivo=motivo)
            EventoAuditoria.objects.create(actor=request.user, accion="cita_estado_cambiado", tipo_objeto="Cita", identificador_objeto=str(cita.pk), detalles={"estado_anterior": estado_anterior, "estado_nuevo": nuevo_estado})
        return Response(CitaLecturaSerializer(cita).data)


class PacientesAPI(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(summary="Listar pacientes (solo administración)", responses=PacienteLecturaSerializer(many=True))
    def get(self, request):
        if not request.user.is_staff:
            raise PermissionDenied("Solo administración puede consultar el padrón de pacientes.")
        texto = request.query_params.get("q", "").strip()
        if len(texto) > 100:
            raise ValidationError({"q": "La búsqueda no puede superar 100 caracteres."})
        pacientes = Paciente.objects.all()
        if texto:
            pacientes = pacientes.filter(Q(nombre_completo__icontains=texto) | Q(identificacion__icontains=texto))
        return pagina(pacientes.order_by("nombre_completo"), request, PacienteLecturaSerializer)


class ConversacionesAPI(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(operation_id="conversaciones_listar", summary="Listar conversaciones de WhatsApp para administración", responses=ConversacionResumenSerializer(many=True))
    def get(self, request):
        if not request.user.is_staff:
            raise PermissionDenied("Solo administración puede revisar las conversaciones.")
        estado = request.query_params.get("estado", "")
        conversaciones = Conversacion.objects.all()
        if estado:
            if estado not in Conversacion.Estado.values:
                raise ValidationError({"estado": "Estado no permitido."})
            conversaciones = conversaciones.filter(estado=estado)
        return pagina(conversaciones.order_by("-ultima_actividad"), request, ConversacionResumenSerializer)


class ConversacionDetalleAPI(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(operation_id="conversacion_mensajes", summary="Consultar mensajes de una conversación de WhatsApp", responses=MensajeConversacionSerializer(many=True))
    def get(self, request, pk):
        if not request.user.is_staff:
            raise PermissionDenied("Solo administración puede revisar las conversaciones.")
        conversacion = get_object_or_404(Conversacion, pk=pk)
        return Response(MensajeConversacionSerializer(conversacion.mensajes.all()[:100], many=True).data)

    @extend_schema(operation_id="conversacion_cambiar_estado", request=EstadoConversacionSerializer, summary="Poner o quitar una conversación en atención humana", responses=ConversacionResumenSerializer)
    def patch(self, request, pk):
        if not request.user.is_staff:
            raise PermissionDenied("Solo administración puede cambiar el estado de una conversación.")
        formulario = EstadoConversacionSerializer(data=request.data)
        formulario.is_valid(raise_exception=True)
        estado = formulario.validated_data["estado"]
        conversacion = get_object_or_404(Conversacion, pk=pk)
        conversacion.estado = estado
        conversacion.save(update_fields=["estado", "ultima_actividad"])
        EventoAuditoria.objects.create(actor=request.user, accion="whatsapp_estado_cambiado", tipo_objeto="Conversacion", identificador_objeto=str(conversacion.pk), detalles={"estado": estado})
        return Response(ConversacionResumenSerializer(conversacion).data)
