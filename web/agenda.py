"""Cálculos de agenda compartidos por disponibilidad y solicitudes WhatsApp."""

from datetime import datetime, time, timedelta

from django.utils import timezone

from .models import Cita, HorarioAtencion


ESTADOS_QUE_OCUPAN_BLOQUE = (
    Cita.Estado.SOLICITADA,
    Cita.Estado.CONFIRMADA,
    Cita.Estado.REPROGRAMADA,
)


def bloques_disponibles(especialista, fecha, duracion_minutos=30, excluir_cita=None):
    """Devuelve inicios cada 15 minutos dentro del horario y sin cruces."""
    tz = timezone.get_current_timezone()
    horarios = HorarioAtencion.objects.filter(
        especialista=especialista, dia_semana=fecha.weekday(), activo=True
    ).order_by("hora_inicio")
    inicio_dia = timezone.make_aware(datetime.combine(fecha, time.min), tz)
    fin_dia = inicio_dia + timedelta(days=1)
    ocupadas = list(Cita.objects.filter(
        especialista=especialista,
        estado__in=ESTADOS_QUE_OCUPAN_BLOQUE,
        fecha_hora_solicitada__gte=inicio_dia,
        fecha_hora_solicitada__lt=fin_dia,
    ).exclude(pk=excluir_cita).select_related("tratamiento"))
    libres = []
    for horario in horarios:
        cursor = timezone.make_aware(datetime.combine(fecha, horario.hora_inicio), tz)
        cierre = timezone.make_aware(datetime.combine(fecha, horario.hora_fin), tz)
        while cursor + timedelta(minutes=duracion_minutos) <= cierre:
            fin = cursor + timedelta(minutes=duracion_minutos)
            if not any(
                cita.fecha_hora_solicitada < fin
                and cita.fecha_hora_solicitada + timedelta(minutes=cita.tratamiento.duracion_minutos or 30) > cursor
                for cita in ocupadas
            ):
                libres.append({"inicio": cursor, "fin": fin})
            cursor += timedelta(minutes=15)
    return libres


def bloque_disponible(especialista, fecha_hora, duracion_minutos=30):
    local = timezone.localtime(fecha_hora)
    if local.second or local.microsecond:
        return False
    return any(
        bloque["inicio"] == local
        for bloque in bloques_disponibles(especialista, local.date(), duracion_minutos)
    )
