"""Flujo guiado de solicitud; el servidor valida y persiste cada cita."""

import re
import unicodedata
from datetime import datetime, timedelta

from django.db import transaction
from django.core.exceptions import ValidationError
from django.utils import timezone

from .models import Cita, CitaEvento, Especialista, HorarioAtencion, Paciente, Tratamiento
from .validaciones import especialidad_admite_tratamiento, validar_identificacion_ecuador


def normalizar(texto):
    texto = unicodedata.normalize("NFKD", texto.casefold())
    return "".join(c for c in texto if not unicodedata.combining(c)).strip()


def responder_solicitud(request, texto):
    """Avanza un turno de reserva guardando el estado temporal en la sesión."""
    estado = request.session.get("flujo_cita", {"paso": "inicio"})
    mensaje = texto.strip()[:500]
    normalizado = normalizar(mensaje)

    if normalizado in {"reiniciar", "empezar de nuevo", "cancelar solicitud"}:
        request.session.pop("flujo_cita", None)
        return {"respuesta": "De acuerdo. Reinicié esta conversación. Si deseas una cita, escribe «reservar cita».", "reiniciar": True}

    if estado["paso"] == "inicio":
        if "cancelar" in normalizado and "reprogramar" in normalizado:
            request.session["flujo_cita"] = {"paso": "elegir_operacion"}
            return {"respuesta": "¿Quieres cancelar o reprogramar? Escribe una sola de esas opciones."}
        if "reprogramar" in normalizado or "cambiar la fecha" in normalizado or "mover el turno" in normalizado:
            request.session["flujo_cita"] = {"paso": "verificar_identificacion", "accion": "reprogramar"}
            return {"respuesta": "Para localizar la cita necesito verificarte. Ingresa la identificación usada al solicitarla."}
        if "cancelar" in normalizado or "anular" in normalizado:
            request.session["flujo_cita"] = {"paso": "verificar_identificacion", "accion": "cancelar"}
            return {"respuesta": "Para localizar la cita necesito verificarte. Ingresa la identificación usada al solicitarla."}
        if "confirmar mi cita" in normalizado or "confirmar asistencia" in normalizado:
            request.session["flujo_cita"] = {"paso": "verificar_identificacion", "accion": "confirmar"}
            return {"respuesta": "Ingresa la identificación asociada a la cita para consultar su estado."}
        if "disponibilidad" in normalizado or "horarios disponibles" in normalizado:
            request.session["flujo_cita"] = {"paso": "disponibilidad_tratamiento"}
            return {"respuesta": "¿Para qué tratamiento buscas disponibilidad? Escribe el nombre del catálogo."}
        if any(palabra in normalizado for palabra in ("reservar", "agendar", "cita")):
            estado = {"paso": "nombre", "datos": {}}
            request.session["flujo_cita"] = estado
            return {"respuesta": "Puedo registrar una solicitud de cita para que recepción confirme la disponibilidad. ¿Cuál es tu nombre y apellido?"}
        if "tratamiento" in normalizado or "servicio" in normalizado:
            opciones = list(Tratamiento.objects.filter(activo=True).values_list("nombre", flat=True)[:40])
            respuesta = "Tratamientos registrados: " + ", ".join(opciones) if opciones else "El catálogo de tratamientos aún no está cargado. Contacta a recepción para solicitar una cita."
            return {"respuesta": respuesta}
        if "especialista" in normalizado or "doctor" in normalizado or "doctora" in normalizado:
            opciones = list(Especialista.objects.filter(activo=True).values_list("nombre_completo", flat=True))
            return {"respuesta": "Especialistas: " + ", ".join(opciones) if opciones else "El equipo aún no está cargado en el sistema."}
        return {"respuesta": "Puedo ayudarte con una solicitud de cita, consultar tratamientos o mostrar especialistas. Escribe «reservar cita» para empezar. No doy diagnósticos."}

    if estado["paso"] == "elegir_operacion":
        if "reprogramar" in normalizado or "cambiar" in normalizado:
            estado["accion"] = "reprogramar"
        elif "cancelar" in normalizado or "anular" in normalizado:
            estado["accion"] = "cancelar"
        else:
            return {"respuesta": "Escribe «cancelar» o «reprogramar»."}
        estado["paso"] = "verificar_identificacion"
        request.session["flujo_cita"] = estado
        return {"respuesta": "Ingresa la identificación usada al solicitar la cita."}

    if estado["paso"] == "disponibilidad_tratamiento":
        tratamientos = list(Tratamiento.objects.filter(activo=True))
        tratamiento = next((t for t in tratamientos if normalizar(t.nombre) == normalizado), None)
        if not tratamiento:
            return {"respuesta": "No encontré ese tratamiento. Elige uno del catálogo: " + "; ".join(t.nombre for t in tratamientos[:30])}
        estado.update({"paso": "disponibilidad_fecha", "tratamiento_id": tratamiento.pk})
        request.session["flujo_cita"] = estado
        return {"respuesta": "Indica el día que deseas consultar con formato DD/MM/AAAA."}

    if estado["paso"] == "disponibilidad_fecha":
        try:
            dia = datetime.strptime(mensaje, "%d/%m/%Y").date()
        except ValueError:
            return {"respuesta": "Usa el formato DD/MM/AAAA para consultar el día."}
        hoy = timezone.localdate()
        if dia < hoy or dia > hoy + timedelta(days=90):
            return {"respuesta": "La consulta debe ser para hoy o dentro de los próximos 90 días."}
        tratamiento = Tratamiento.objects.get(pk=estado["tratamiento_id"], activo=True)
        duracion = tratamiento.duracion_minutos or 30
        candidatos = []
        for horario in HorarioAtencion.objects.filter(dia_semana=dia.weekday(), activo=True, especialista__activo=True).select_related("especialista"):
            if not especialidad_admite_tratamiento(tratamiento.area, horario.especialista.especialidad):
                continue
            inicio = timezone.make_aware(datetime.combine(dia, horario.hora_inicio), timezone.get_current_timezone())
            fin_bloque = timezone.make_aware(datetime.combine(dia, horario.hora_fin), timezone.get_current_timezone())
            paso = 30
            actual = inicio
            while actual + timedelta(minutes=duracion) <= fin_bloque:
                fin = actual + timedelta(minutes=duracion)
                if actual > timezone.now():
                    ocupadas = Cita.objects.filter(especialista=horario.especialista, estado__in=[Cita.Estado.CONFIRMADA, Cita.Estado.REPROGRAMADA], fecha_hora_solicitada__lt=fin).select_related("tratamiento")
                    cruce = any(c.fecha_hora_solicitada + timedelta(minutes=c.tratamiento.duracion_minutos or 30) > actual for c in ocupadas)
                    if not cruce:
                        candidatos.append((actual, horario.especialista.nombre_completo))
                actual += timedelta(minutes=paso)
        request.session.pop("flujo_cita", None)
        if not candidatos:
            return {"respuesta": "No hay bloques visibles para ese tratamiento y día, o la clínica aún no configuró horarios individuales. Recepción debe verificar la disponibilidad."}
        opciones = "; ".join(f"{nombre}: {hora:%H:%M}" for hora, nombre in candidatos[:10])
        return {"respuesta": f"Bloques disponibles registrados para {dia:%d/%m/%Y}: {opciones}. Son horarios libres en el sistema; puedes iniciar una solicitud para reservar uno."}

    if estado["paso"] == "verificar_identificacion":
        try:
            validar_identificacion_ecuador(mensaje)
        except ValidationError:
            return {"respuesta": "La identificación no es válida; revisa sus dígitos."}
        identificacion = re.sub(r"\D", "", mensaje)
        estado["identificacion"] = identificacion
        estado["paso"] = "codigo_reserva"
        request.session["flujo_cita"] = estado
        return {"respuesta": "Escribe el código de la cita. La identificación y el código deben coincidir."}

    if estado["paso"] == "codigo_reserva":
        codigo = mensaje.upper().strip()
        cita = Cita.objects.filter(codigo=codigo, paciente__identificacion=estado["identificacion"]).first()
        if not cita:
            return {"respuesta": "No encontré una cita con esa combinación. Revisa el código y la identificación."}
        accion = estado["accion"]
        if accion == "confirmar":
            request.session.pop("flujo_cita", None)
            if cita.estado == Cita.Estado.CONFIRMADA:
                return {"respuesta": f"La cita {cita.codigo} está confirmada para {timezone.localtime(cita.fecha_hora_solicitada):%d/%m/%Y %H:%M}."}
            return {"respuesta": f"La cita {cita.codigo} figura como {cita.get_estado_display()}. Solo recepción puede confirmar el horario."}
        if accion == "cancelar":
            estado.update({"paso": "confirmar_cancelacion", "cita_id": cita.pk})
            request.session["flujo_cita"] = estado
            return {"respuesta": f"La cita {cita.codigo} está en estado «{cita.get_estado_display()}». ¿Confirmas que deseas cancelarla? Responde sí o no."}
        estado.update({"paso": "fecha_reprogramacion", "cita_id": cita.pk})
        request.session["flujo_cita"] = estado
        return {"respuesta": f"Indica la nueva fecha y hora preferidas para la cita {cita.codigo}, como DD/MM/AAAA HH:MM. Recepción volverá a comprobar disponibilidad."}

    if estado["paso"] == "confirmar_cancelacion":
        cita = Cita.objects.get(pk=estado["cita_id"])
        request.session.pop("flujo_cita", None)
        if normalizado not in {"si", "sí", "confirmo", "cancelar"}:
            return {"respuesta": "No cancelé la cita."}
        if cita.estado in {Cita.Estado.CANCELADA, Cita.Estado.ATENDIDA}:
            return {"respuesta": f"No se puede cancelar una cita que figura como {cita.get_estado_display()}."}
        cita.estado = Cita.Estado.CANCELADA
        cita.save(update_fields=["estado"])
        CitaEvento.objects.create(cita=cita, accion=CitaEvento.Accion.CANCELADA)
        return {"respuesta": f"La cita {cita.codigo} quedó cancelada."}

    if estado["paso"] == "fecha_reprogramacion":
        try:
            fecha = timezone.make_aware(datetime.strptime(mensaje, "%d/%m/%Y %H:%M"), timezone.get_current_timezone())
        except ValueError:
            return {"respuesta": "Usa el formato DD/MM/AAAA HH:MM."}
        if fecha <= timezone.now() or fecha > timezone.now() + timedelta(days=365):
            return {"respuesta": "La nueva fecha debe ser futura y estar dentro de los próximos 12 meses."}
        cita = Cita.objects.get(pk=estado["cita_id"])
        if cita.estado in {Cita.Estado.CANCELADA, Cita.Estado.ATENDIDA}:
            request.session.pop("flujo_cita", None)
            return {"respuesta": f"No se puede reprogramar una cita que figura como {cita.get_estado_display()}."}
        anterior = cita.fecha_hora_solicitada
        cita.fecha_hora_solicitada = fecha
        cita.estado = Cita.Estado.REPROGRAMADA
        cita.save(update_fields=["fecha_hora_solicitada", "estado"])
        CitaEvento.objects.create(cita=cita, accion=CitaEvento.Accion.REPROGRAMADA, fecha_anterior=anterior, fecha_nueva=fecha)
        request.session.pop("flujo_cita", None)
        return {"respuesta": f"Registré la preferencia de cambio para {fecha:%d/%m/%Y %H:%M}. La cita {cita.codigo} queda pendiente de revisión y confirmación por recepción."}

    datos = estado["datos"]
    if estado["paso"] == "nombre":
        if len(mensaje) < 3 or len(mensaje) > 80 or not re.fullmatch(r"[A-Za-zÁÉÍÓÚÜÑáéíóúüñ][A-Za-zÁÉÍÓÚÜÑáéíóúüñ .'-]{1,78}", mensaje):
            return {"respuesta": "Escribe tu nombre y apellido usando letras, espacios o guiones (3 a 80 caracteres)."}
        datos["nombre"] = " ".join(mensaje.split())
        estado["paso"] = "identificacion"
        request.session["flujo_cita"] = estado
        return {"respuesta": "¿Cuál es tu número de cédula o identificación? Se usará para vincular esta solicitud con tus citas."}

    if estado["paso"] == "identificacion":
        try:
            validar_identificacion_ecuador(mensaje)
        except ValidationError:
            return {"respuesta": "La identificación no es válida. Revisa sus dígitos y vuelve a ingresarla."}
        identificacion = re.sub(r"\D", "", mensaje)
        datos["identificacion"] = identificacion
        estado["paso"] = "telefono"
        request.session["flujo_cita"] = estado
        return {"respuesta": "¿A qué número de teléfono puede contactarte la clínica? Incluye el código de país si corresponde."}

    if estado["paso"] == "telefono":
        if not re.fullmatch(r"[0-9+() -]{7,20}", mensaje):
            return {"respuesta": "El teléfono solo puede contener dígitos, espacios, paréntesis, + o guion."}
        telefono = re.sub(r"\D", "", mensaje)
        if not 7 <= len(telefono) <= 15:
            return {"respuesta": "Ingresa un teléfono válido de 7 a 15 dígitos."}
        datos["telefono"] = telefono
        estado["paso"] = "tratamiento"
        request.session["flujo_cita"] = estado
        tratamientos = list(Tratamiento.objects.filter(activo=True).values_list("nombre", flat=True)[:30])
        if not tratamientos:
            request.session.pop("flujo_cita", None)
            return {"respuesta": "Todavía no se ha cargado el catálogo oficial de tratamientos; no puedo registrar la cita. La solicitud no se guardó."}
        return {"respuesta": "¿Qué tratamiento necesitas? Opciones: " + "; ".join(tratamientos)}

    if estado["paso"] == "tratamiento":
        tratamientos = list(Tratamiento.objects.filter(activo=True))
        tratamiento = next((t for t in tratamientos if normalizar(t.nombre) == normalizado), None)
        if not tratamiento:
            return {"respuesta": "No encontré ese tratamiento en el catálogo activo. Escribe el nombre de una de estas opciones: " + "; ".join(t.nombre for t in tratamientos[:30])}
        datos["tratamiento_id"] = tratamiento.pk
        estado["paso"] = "especialista"
        request.session["flujo_cita"] = estado
        nombres = list(Especialista.objects.filter(activo=True).values_list("nombre_completo", flat=True))
        return {"respuesta": "¿Prefieres algún especialista? " + "; ".join(nombres) + ". También puedes escribir «cualquiera»." if nombres else "No hay especialistas cargados todavía. Escribe «cualquiera» para que recepción asigne uno."}

    if estado["paso"] == "especialista":
        especialista = None
        if normalizado not in {"cualquiera", "cualquiera de ellos", "no", "me da igual"}:
            especialistas = list(Especialista.objects.filter(activo=True))
            especialista = next((e for e in especialistas if normalizar(e.nombre_completo) == normalizado), None)
            if not especialista:
                nombres = list(Especialista.objects.filter(activo=True).values_list("nombre_completo", flat=True))
                return {"respuesta": "No identifiqué al especialista. Escribe un nombre del catálogo o «cualquiera»: " + "; ".join(nombres)}
        datos["especialista_id"] = especialista.pk if especialista else None
        estado["paso"] = "fecha_hora"
        request.session["flujo_cita"] = estado
        return {"respuesta": "Indica tu fecha y hora preferidas con formato DD/MM/AAAA HH:MM. Es una preferencia; recepción verificará el horario real."}

    if estado["paso"] == "fecha_hora":
        try:
            preferencia = timezone.make_aware(datetime.strptime(mensaje, "%d/%m/%Y %H:%M"), timezone.get_current_timezone())
        except ValueError:
            return {"respuesta": "No pude leer la fecha. Usa el formato DD/MM/AAAA HH:MM, por ejemplo 15/12/2026 10:30."}
        ahora = timezone.now()
        if preferencia <= ahora or preferencia > ahora + timedelta(days=365):
            return {"respuesta": "La fecha debe ser futura y estar dentro de los próximos 12 meses. Intenta con otra fecha y hora."}
        datos["fecha_hora"] = preferencia.isoformat()
        tratamiento = Tratamiento.objects.get(pk=datos["tratamiento_id"])
        especialista = Especialista.objects.filter(pk=datos.get("especialista_id")).first()
        estado["paso"] = "confirmacion"
        request.session["flujo_cita"] = estado
        profesional = especialista.nombre_completo if especialista else "por asignar por recepción"
        return {"respuesta": f"Revisa la solicitud: {datos['nombre']}, tratamiento {tratamiento.nombre}, profesional {profesional}, preferencia {timezone.localtime(preferencia):%d/%m/%Y %H:%M}. ¿La envío a recepción? Responde sí o no."}

    if estado["paso"] == "confirmacion":
        if normalizado not in {"si", "sí", "confirmo", "enviar", "correcto"}:
            request.session.pop("flujo_cita", None)
            return {"respuesta": "No envié la solicitud. Puedes empezar otra cuando quieras; escribe «reservar cita».", "reiniciar": True}
        tratamiento = Tratamiento.objects.get(pk=datos["tratamiento_id"], activo=True)
        especialista = Especialista.objects.filter(pk=datos.get("especialista_id"), activo=True).first()
        if especialista and not especialidad_admite_tratamiento(tratamiento.area, especialista.especialidad):
            return {"respuesta": "Ese profesional no figura en el catálogo para el área seleccionada. Inicia una nueva solicitud y elige «cualquiera» para que recepción asigne."}
        fecha_hora = datetime.fromisoformat(datos["fecha_hora"])
        with transaction.atomic():
            paciente, creado = Paciente.objects.get_or_create(
                identificacion=datos["identificacion"],
                defaults={"nombre_completo": datos["nombre"], "telefono": datos["telefono"]},
            )
            if not creado:
                paciente.nombre_completo = datos["nombre"]
                paciente.telefono = datos["telefono"]
                paciente.save(update_fields=["nombre_completo", "telefono"])
            cita = Cita.objects.create(
                paciente=paciente,
                especialista=especialista,
                tratamiento=tratamiento,
                fecha_hora_solicitada=fecha_hora,
            )
            CitaEvento.objects.create(cita=cita, accion=CitaEvento.Accion.SOLICITADA)
        request.session.pop("flujo_cita", None)
        return {"respuesta": f"Solicitud registrada con el código {cita.codigo}. Aún no está confirmada: recepción verificará disponibilidad y se comunicará al teléfono indicado.", "reiniciar": True, "codigo": cita.codigo}

    request.session.pop("flujo_cita", None)
    return {"respuesta": "La conversación se reinició porque su estado no era válido. Escribe «reservar cita» para empezar.", "reiniciar": True}
