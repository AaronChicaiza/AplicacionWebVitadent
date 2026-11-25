import json
import hmac
import re
import math
import unicodedata
from datetime import date, datetime, timedelta
from decimal import Decimal, InvalidOperation
from urllib.parse import quote

from django.conf import settings
from django.core.exceptions import PermissionDenied, ValidationError
from django.contrib import messages
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.views import LoginView
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseForbidden, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.core.paginator import Paginator
from django.urls import reverse_lazy
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction
from django.db.models import Count, Max, OuterRef, Q, Subquery, Sum
from django.db.models.functions import TruncDate, TruncMonth, TruncWeek
from django.utils import timezone

from .datos_demo import ESPECIALISTAS, GRUPOS_TRATAMIENTOS, ordenar_catalogo_tratamientos
from .models import AccesoPersonal, Cita, CitaEvento, Conversacion, Especialista, EventoAuditoria, HorarioAtencion, MensajeConversacion, Paciente, Sucursal, Tratamiento
from .serializers import OperacionCitaWhatsAppSerializer, SolicitudWhatsAppSerializer
from .servicios_whatsapp import enviar_mensaje_whatsapp, firma_meta_valida, procesar_evento_whatsapp
from .validaciones import especialidad_admite_tratamiento
from .forms_gestion import (
    CitaGestionForm,
    EspecialistaGestionForm,
    HorarioGestionForm,
    PacienteGestionForm,
    SucursalGestionForm,
    TratamientoGestionForm,
)


def contexto_base(**adicionales):
    """Prepara la información compartida por las vistas del prototipo."""
    catalogo = list(Especialista.objects.filter(activo=True))
    if catalogo:
        tonos = ["a", "b", "c", "d"]
        especialistas_contexto = [{
            "nombre": item.nombre_completo,
            "especialidad": item.especialidad,
            "iniciales": "".join(parte[0] for parte in item.nombre_completo.replace("Dra.", "").replace("Dr.", "").strip().split()[:2]).upper(),
            "tono": tonos[indice % len(tonos)],
        } for indice, item in enumerate(catalogo)]
    else:
        especialistas_contexto = ESPECIALISTAS
    tratamientos_db = list(Tratamiento.objects.filter(activo=True))
    pares_activos = {(item.nombre, item.area) for item in tratamientos_db}
    if tratamientos_db:
        tratamientos_contexto = [
            {**grupo, "procedimientos": [nombre for nombre in grupo["procedimientos"] if (nombre, grupo["nombre"]) in pares_activos]}
            for grupo in GRUPOS_TRATAMIENTOS
            if any((nombre, grupo["nombre"]) in pares_activos for nombre in grupo["procedimientos"])
        ]
    else:
        tratamientos_contexto = GRUPOS_TRATAMIENTOS
    contexto = {
        "especialistas": especialistas_contexto,
        "grupos_tratamientos": tratamientos_contexto,
    }
    contexto.update(adicionales)
    return contexto


# ----------------- SITIO PÚBLICO -----------------
def inicio(request):
    return render(request, "web/inicio.html", contexto_base())


def healthz(request):
    return JsonResponse({"estado": "ok"})


def tratamientos(request):
    return render(request, "web/tratamientos.html", contexto_base())


def especialistas(request):
    return render(request, "web/especialistas.html", contexto_base())


def asistente_citas(request):
    numero = re.sub(r"\D", "", getattr(settings, "VITADENT_WHATSAPP_NUMBER", ""))
    whatsapp_url = ""
    if re.fullmatch(r"[0-9]{7,20}", numero):
        mensaje = quote("Hola, quiero agendar una cita en VitaDent.")
        whatsapp_url = f"https://wa.me/{numero}?text={mensaje}"
    return render(request, "web/asistente_citas.html", contexto_base(whatsapp_url=whatsapp_url))


@csrf_exempt
@require_POST
def api_interna_crear_solicitud(request):
    """Entrada servidor-a-servidor para acciones Rasa; token obligatorio."""
    token_configurado = getattr(settings, "VITADENT_RASA_TOKEN", "")
    bearer = request.headers.get("Authorization", "")
    if not token_configurado or not bearer.startswith("Bearer ") or not hmac.compare_digest(bearer[7:], token_configurado):
        return JsonResponse({"error": "No autorizado."}, status=401)
    if len(request.body) > 32_768:
        return JsonResponse({"error": "La solicitud supera el tamaño permitido."}, status=413)
    try:
        datos = json.loads(request.body or b"{}")
    except (json.JSONDecodeError, UnicodeDecodeError):
        return JsonResponse({"error": "JSON no válido."}, status=400)
    if not isinstance(datos, dict):
        return JsonResponse({"error": "El cuerpo debe ser un objeto JSON."}, status=400)
    formulario = SolicitudWhatsAppSerializer(data=datos)
    if not formulario.is_valid():
        return JsonResponse({"error": "Los datos no pasaron la validación.", "detalles": formulario.errors}, status=400)
    valores = formulario.validated_data
    with transaction.atomic():
        paciente, creado = Paciente.objects.get_or_create(
            identificacion=valores["identificacion"],
            defaults={"nombre_completo": valores["nombre"], "telefono": valores["telefono"], "correo": valores.get("correo", "")},
        )
        if not creado:
            paciente.nombre_completo = valores["nombre"]
            paciente.telefono = valores["telefono"]
            paciente.correo = valores.get("correo", "")
            paciente.save(update_fields=["nombre_completo", "telefono", "correo"])
        cita, creada = Cita.objects.get_or_create(
            idempotency_key=valores["idempotency_key"],
            defaults={
                "paciente": paciente,
                "especialista": valores.get("especialista_obj"),
                "tratamiento": valores["tratamiento_obj"],
                "sucursal": valores.get("sucursal_obj"),
                "fecha_hora_solicitada": valores["fecha_hora"],
            },
        )
        if creada:
            CitaEvento.objects.create(cita=cita, accion=CitaEvento.Accion.SOLICITADA, motivo="Solicitud recibida por WhatsApp")
            EventoAuditoria.objects.create(accion="solicitud_whatsapp_creada", tipo_objeto="Cita", identificador_objeto=str(cita.pk), detalles={"canal": "whatsapp"})
    return JsonResponse({"codigo": cita.codigo, "estado": cita.get_estado_display()}, status=201 if creada else 200)


@csrf_exempt
def webhook_whatsapp(request):
    """Webhook de Meta; valida suscripción GET y firma SHA-256 en cada POST."""
    if request.method == "GET":
        modo = request.GET.get("hub.mode", "")
        token = request.GET.get("hub.verify_token", "")
        desafio = request.GET.get("hub.challenge", "")
        esperado = getattr(settings, "WHATSAPP_VERIFY_TOKEN", "")
        if modo == "subscribe" and esperado and hmac.compare_digest(token, esperado) and len(desafio) <= 256:
            return HttpResponse(desafio, content_type="text/plain")
        return JsonResponse({"error": "Verificación no autorizada."}, status=403)
    if request.method != "POST":
        return JsonResponse({"error": "Método no permitido."}, status=405)
    if request.content_type != "application/json":
        return JsonResponse({"error": "Se requiere application/json."}, status=415)
    cuerpo = request.body
    if len(cuerpo) > 262_144:
        return JsonResponse({"error": "El webhook supera el tamaño permitido."}, status=413)
    if not firma_meta_valida(cuerpo, request.headers.get("X-Hub-Signature-256", "")):
        return JsonResponse({"error": "Firma de webhook no válida."}, status=401)
    try:
        payload = json.loads(cuerpo)
    except (json.JSONDecodeError, UnicodeDecodeError):
        return JsonResponse({"error": "JSON no válido."}, status=400)
    if not isinstance(payload, dict) or payload.get("object") != "whatsapp_business_account":
        return JsonResponse({"error": "Evento no reconocido."}, status=400)
    procesar_evento_whatsapp(payload)
    return JsonResponse({"estado": "recibido"})


def _token_rasa_valido(request):
    token = getattr(settings, "VITADENT_RASA_TOKEN", "")
    bearer = request.headers.get("Authorization", "")
    return bool(token and bearer.startswith("Bearer ") and hmac.compare_digest(bearer[7:], token))


def _obtener_cita_whatsapp(datos):
    return Cita.objects.select_for_update().select_related("paciente", "especialista", "tratamiento").filter(
        codigo__iexact=datos["codigo"],
        paciente__identificacion=datos["identificacion"],
        paciente__telefono=datos["telefono"],
    ).first()


@csrf_exempt
@require_POST
def api_whatsapp_cancelar_cita(request):
    if not _token_rasa_valido(request):
        return JsonResponse({"error": "No autorizado."}, status=401)
    if len(request.body) > 16_384:
        return JsonResponse({"error": "Solicitud demasiado grande."}, status=413)
    try:
        body = json.loads(request.body or b"{}")
    except (json.JSONDecodeError, UnicodeDecodeError):
        return JsonResponse({"error": "JSON no válido."}, status=400)
    formulario = OperacionCitaWhatsAppSerializer(data=body)
    if not formulario.is_valid():
        return JsonResponse({"error": "No se pudo validar la solicitud."}, status=400)
    datos = formulario.validated_data
    with transaction.atomic():
        cita = _obtener_cita_whatsapp(datos)
        if not cita or cita.fecha_hora_solicitada <= timezone.now():
            return JsonResponse({"error": "No encontramos una cita futura con esos datos."}, status=404)
        if cita.estado not in {Cita.Estado.SOLICITADA, Cita.Estado.CONFIRMADA, Cita.Estado.REPROGRAMADA}:
            return JsonResponse({"error": "Esta cita ya no se puede cancelar desde el asistente."}, status=409)
        horas_minimas = max(0, settings.VITADENT_MIN_CANCEL_HOURS)
        if cita.fecha_hora_solicitada - timezone.now() < timedelta(hours=horas_minimas):
            return JsonResponse({"error": "La política de la clínica requiere que contactes a recepción para cancelar esta cita."}, status=409)
        anterior = cita.estado
        cita.estado = Cita.Estado.CANCELADA
        cita.save(update_fields=["estado"])
        motivo = datos.get("motivo") or "Cancelada por el paciente mediante WhatsApp"
        CitaEvento.objects.create(cita=cita, accion=CitaEvento.Accion.CANCELADA, motivo=motivo)
        EventoAuditoria.objects.create(accion="cita_cancelada_whatsapp", tipo_objeto="Cita", identificador_objeto=str(cita.pk), detalles={"estado_anterior": anterior, "canal": "whatsapp"})
    return JsonResponse({"codigo": cita.codigo, "estado": cita.get_estado_display()})


@csrf_exempt
@require_POST
def api_whatsapp_consultar_cita(request):
    if not _token_rasa_valido(request):
        return JsonResponse({"error": "No autorizado."}, status=401)
    if len(request.body) > 16_384:
        return JsonResponse({"error": "Solicitud demasiado grande."}, status=413)
    try:
        body = json.loads(request.body or b"{}")
    except (json.JSONDecodeError, UnicodeDecodeError):
        return JsonResponse({"error": "JSON no válido."}, status=400)
    formulario = OperacionCitaWhatsAppSerializer(data=body)
    if not formulario.is_valid():
        return JsonResponse({"error": "No encontramos una cita con esos datos."}, status=404)
    datos = formulario.validated_data
    cita = Cita.objects.select_related("tratamiento", "especialista").filter(
        codigo__iexact=datos["codigo"],
        paciente__identificacion=datos["identificacion"],
        paciente__telefono=datos["telefono"],
    ).first()
    if not cita:
        return JsonResponse({"error": "No encontramos una cita con esos datos."}, status=404)
    return JsonResponse({
        "codigo": cita.codigo,
        "estado": cita.get_estado_display(),
        "fecha_hora": timezone.localtime(cita.fecha_hora_solicitada).isoformat(),
        "tratamiento": cita.tratamiento.nombre,
        "especialista": cita.especialista.nombre_completo if cita.especialista_id else "Por asignar",
    })


@csrf_exempt
@require_POST
def api_whatsapp_reprogramar_cita(request):
    if not _token_rasa_valido(request):
        return JsonResponse({"error": "No autorizado."}, status=401)
    if len(request.body) > 16_384:
        return JsonResponse({"error": "Solicitud demasiado grande."}, status=413)
    try:
        body = json.loads(request.body or b"{}")
    except (json.JSONDecodeError, UnicodeDecodeError):
        return JsonResponse({"error": "JSON no válido."}, status=400)
    formulario = OperacionCitaWhatsAppSerializer(data=body)
    if not formulario.is_valid() or not formulario.validated_data.get("nueva_fecha_hora"):
        return JsonResponse({"error": "Indica un código, identificación, teléfono y nueva fecha válidos."}, status=400)
    datos = formulario.validated_data
    nueva_fecha = datos["nueva_fecha_hora"]
    with transaction.atomic():
        cita = _obtener_cita_whatsapp(datos)
        if not cita or cita.fecha_hora_solicitada <= timezone.now():
            return JsonResponse({"error": "No encontramos una cita futura con esos datos."}, status=404)
        if cita.estado not in {Cita.Estado.SOLICITADA, Cita.Estado.CONFIRMADA, Cita.Estado.REPROGRAMADA}:
            return JsonResponse({"error": "Esta cita ya no se puede reprogramar desde el asistente."}, status=409)
        if not cita.especialista_id or not cita.especialista.activo:
            return JsonResponse({"error": "Recepción debe revisar esta solicitud de reprogramación."}, status=409)
        Especialista.objects.select_for_update().get(pk=cita.especialista_id)
        duracion = cita.tratamiento.duracion_minutos or 30
        local = timezone.localtime(nueva_fecha)
        horario = HorarioAtencion.objects.filter(especialista=cita.especialista, dia_semana=local.weekday(), activo=True, hora_inicio__lte=local.time(), hora_fin__gte=(local + timedelta(minutes=duracion)).time()).exists()
        if not horario:
            return JsonResponse({"error": "El horario propuesto no está dentro de la agenda del especialista."}, status=409)
        fin = nueva_fecha + timedelta(minutes=duracion)
        ocupadas = Cita.objects.filter(especialista=cita.especialista, estado__in=[Cita.Estado.CONFIRMADA, Cita.Estado.REPROGRAMADA], fecha_hora_solicitada__lt=fin).exclude(pk=cita.pk).select_related("tratamiento")
        if any(otra.fecha_hora_solicitada + timedelta(minutes=otra.tratamiento.duracion_minutos or 30) > nueva_fecha for otra in ocupadas):
            return JsonResponse({"error": "Ese bloque ya no está disponible. Propón otro horario."}, status=409)
        anterior = cita.fecha_hora_solicitada
        cita.fecha_hora_solicitada = nueva_fecha
        cita.estado = Cita.Estado.REPROGRAMADA
        cita.save(update_fields=["fecha_hora_solicitada", "estado"])
        motivo = datos.get("motivo") or "Reprogramación solicitada por WhatsApp"
        CitaEvento.objects.create(cita=cita, accion=CitaEvento.Accion.REPROGRAMADA, fecha_anterior=anterior, fecha_nueva=nueva_fecha, motivo=motivo)
        EventoAuditoria.objects.create(accion="cita_reprogramada_whatsapp", tipo_objeto="Cita", identificador_objeto=str(cita.pk), detalles={"canal": "whatsapp"})
    return JsonResponse({"codigo": cita.codigo, "estado": cita.get_estado_display(), "fecha_hora": timezone.localtime(cita.fecha_hora_solicitada).isoformat()})


def acceso_personal(request):
    if request.user.is_authenticated:
        acceso = getattr(request.user, "acceso_personal", None)
        if acceso and acceso.cambio_clave_obligatorio:
            return redirect("cambiar_clave_inicial")
        if request.user.is_staff or (hasattr(request.user, "perfil_especialista") and request.user.perfil_especialista.activo):
            return redirigir_segun_rol(request.user)
        return render(request, "web/acceso_login.html", contexto_base(error_acceso="Esta cuenta no tiene un rol activo en VitaDent."))
    return render(request, "web/acceso_login.html", contexto_base())


@login_required(login_url="acceso_personal")
def cambiar_clave_inicial(request):
    acceso = getattr(request.user, "acceso_personal", None)
    if not acceso or not acceso.cambio_clave_obligatorio:
        return redirigir_segun_rol(request.user)
    formulario = PasswordChangeForm(request.user, request.POST or None)
    if request.method == "POST" and formulario.is_valid():
        usuario = formulario.save()
        update_session_auth_hash(request, usuario)
        acceso.cambio_clave_obligatorio = False
        acceso.save(update_fields=["cambio_clave_obligatorio"])
        messages.success(request, "Tu contraseña quedó actualizada.")
        if usuario.is_staff:
            return redirect("gestion_inicio")
        return redirect("espacio_especialista")
    return render(request, "web/cambiar_clave.html", contexto_base(formulario_clave=formulario))


def redirigir_segun_rol(usuario):
    if usuario.is_staff:
        return redirect("gestion_inicio")
    if hasattr(usuario, "perfil_especialista") and usuario.perfil_especialista.activo:
        return redirect("espacio_especialista")
    return HttpResponseForbidden("La cuenta no tiene permisos para este espacio.")


class AccesoDjangoView(LoginView):
    template_name = "web/acceso_login.html"
    authentication_form = AuthenticationForm
    redirect_authenticated_user = True

    def get_success_url(self):
        usuario = self.request.user
        acceso = getattr(usuario, "acceso_personal", None)
        if acceso and acceso.cambio_clave_obligatorio:
            return reverse_lazy("cambiar_clave_inicial")
        if usuario.is_staff:
            return reverse_lazy("gestion_inicio")
        if hasattr(usuario, "perfil_especialista") and usuario.perfil_especialista.activo:
            return reverse_lazy("espacio_especialista")
        return reverse_lazy("acceso_personal")


# ----------------- PANEL DE ADMINISTRACIÓN -----------------
@staff_member_required(login_url="acceso_personal")
def gestion_inicio(request):
    return redirect("gestion_citas")


def _es_veronica_martinez(perfil):
    if not perfil or not perfil.activo:
        return False
    nombre = unicodedata.normalize("NFD", perfil.nombre_completo.casefold())
    nombre = "".join(caracter for caracter in nombre if unicodedata.category(caracter) != "Mn")
    palabras = re.findall(r"[a-z]+", nombre)
    if palabras and palabras[0] in {"dra", "doctora"}:
        palabras = palabras[1:]
    return palabras == ["veronica", "martinez"]


COLORES_AGENDA_ESPECIALISTAS = {
    "veronica": "#70A83B",
    "santiago": "#FFDE00",
    "daniela": "#303030",
    "odalis": "#D875A4",
    "karen": "#EA8C37",
    "mishel": "#8666A9",
    "adrian": "#D34A48",
    "wilson": "#77D1E9",
    "daysi": "#4475A9",
}
COLORES_TEXTO_AGENDA_ESPECIALISTAS = {
    "daniela": "#FFFFFF",
    "mishel": "#FFFFFF",
    "adrian": "#FFFFFF",
    "daysi": "#FFFFFF",
}


def _clave_color_especialista(nombre_completo):
    nombre = unicodedata.normalize("NFD", nombre_completo.casefold())
    nombre = "".join(caracter for caracter in nombre if unicodedata.category(caracter) != "Mn")
    palabras = re.findall(r"[a-z]+", nombre)
    return next((persona for persona in COLORES_AGENDA_ESPECIALISTAS if persona in palabras), None)


@login_required(login_url="acceso_personal")
def especialista_dashboard(request):
    perfil = getattr(request.user, "perfil_especialista", None)
    if not _es_veronica_martinez(perfil):
        raise PermissionDenied("Este dashboard está habilitado únicamente para Verónica Martínez.")
    return _renderizar_dashboard(request, perfil)


def _renderizar_dashboard(request, perfil):
    hoy = timezone.localdate()
    inicio_semana = hoy - timedelta(days=hoy.weekday())
    inicio_mes = hoy.replace(day=1)
    ingresos = Cita.objects.filter(
        estado=Cita.Estado.ATENDIDA,
        atendida_en__isnull=False,
        monto_ingreso__isnull=False,
    )

    def datos_por_periodo(truncador, desde, hasta):
        filas = ingresos.filter(atendida_en__date__gte=desde, atendida_en__date__lte=hasta).annotate(
            periodo=truncador("atendida_en", tzinfo=timezone.get_current_timezone())
        ).values("periodo").annotate(total=Sum("monto_ingreso"))
        datos = {}
        for fila in filas:
            periodo = fila["periodo"]
            if isinstance(periodo, datetime):
                periodo = timezone.localtime(periodo).date()
            datos[periodo] = fila["total"] or Decimal("0")
        return datos

    def barras(periodos, datos):
        valores = [datos.get(periodo, Decimal("0")) for periodo, _ in periodos]
        maximo = max(valores, default=Decimal("0"))
        resultado = []
        for (periodo, etiqueta), valor in zip(periodos, valores):
            altura = int(valor * 100 / maximo) if maximo else 0
            resultado.append({
                "etiqueta": etiqueta,
                "valor": f"${valor:,.2f}",
                "altura": max(3, altura) if valor > 0 else 0,
                "tiene_ingreso": valor > 0,
            })
        return resultado

    meses_es = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"]
    dias = [(hoy - timedelta(days=offset), f"{(hoy - timedelta(days=offset)).day:02d} {meses_es[(hoy - timedelta(days=offset)).month - 1]}") for offset in range(6, -1, -1)]
    ingresos_dia = datos_por_periodo(TruncDate, dias[0][0], hoy)

    semana_actual = hoy - timedelta(days=hoy.weekday())
    semanas = []
    for offset in range(7, -1, -1):
        inicio = semana_actual - timedelta(weeks=offset)
        semanas.append((inicio, f"{inicio.day:02d} {meses_es[inicio.month - 1]}"))
    ingresos_semana = datos_por_periodo(TruncWeek, semanas[0][0], hoy)

    meses = []
    for offset in range(5, -1, -1):
        indice = hoy.year * 12 + hoy.month - 1 - offset
        periodo = date(indice // 12, indice % 12 + 1, 1)
        meses.append((periodo, f"{meses_es[periodo.month - 1]} {str(periodo.year)[-2:]}"))
    ingresos_mes = datos_por_periodo(TruncMonth, meses[0][0], hoy)
    barras_diarias = barras(dias, ingresos_dia)
    barras_semanales = barras(semanas, ingresos_semana)
    barras_mensuales = barras(meses, ingresos_mes)

    atenciones = list(Cita.objects.filter(estado=Cita.Estado.ATENDIDA).values(
        "tratamiento__nombre"
    ).annotate(total=Count("pk")).order_by("-total", "tratamiento__nombre"))
    colores = ["#77D1E9", "#DCF73A", "#4475A9", "#303030"]
    if len(atenciones) > 4:
        atenciones = atenciones[:3] + [{
            "tratamiento__nombre": "Otros",
            "total": sum(item["total"] for item in atenciones[3:]),
        }]
    total_atenciones = sum(item["total"] for item in atenciones)
    porciones = []
    inicio_porcion = 0.0
    for indice, item in enumerate(atenciones):
        porcentaje = item["total"] * 100 / total_atenciones if total_atenciones else 0
        fin_porcion = 100.0 if indice == len(atenciones) - 1 else inicio_porcion + porcentaje
        angulo_inicio = math.radians(inicio_porcion * 3.6 - 90)
        angulo_fin = math.radians(fin_porcion * 3.6 - 90)
        x_inicio = 100 + 96 * math.cos(angulo_inicio)
        y_inicio = 100 + 96 * math.sin(angulo_inicio)
        x_fin = 100 + 96 * math.cos(angulo_fin)
        y_fin = 100 + 96 * math.sin(angulo_fin)
        barrido = fin_porcion - inicio_porcion
        if barrido >= 99.999:
            x_medio = 100 + 96 * math.cos(angulo_inicio + math.pi)
            y_medio = 100 + 96 * math.sin(angulo_inicio + math.pi)
            ruta_svg = f"M 100 100 L {x_inicio:.2f} {y_inicio:.2f} A 96 96 0 1 1 {x_medio:.2f} {y_medio:.2f} A 96 96 0 1 1 {x_inicio:.2f} {y_inicio:.2f} Z"
        else:
            arco_largo = 1 if barrido > 50 else 0
            ruta_svg = f"M 100 100 L {x_inicio:.2f} {y_inicio:.2f} A 96 96 0 {arco_largo} 1 {x_fin:.2f} {y_fin:.2f} Z"
        porciones.append({
            "nombre": item["tratamiento__nombre"],
            "cantidad": item["total"],
            "porcentaje": round(porcentaje, 1),
            "color": colores[indice % len(colores)],
            "inicio": round(inicio_porcion, 2),
            "fin": round(fin_porcion, 2),
            "ruta_svg": ruta_svg,
        })
        inicio_porcion = fin_porcion

    return render(
        request,
        "web/doctor/dashboard_especialista.html",
        contexto_base(
            seccion_especialista="dashboard",
            puede_ver_dashboard=True,
            perfil=perfil,
            total_citas=Cita.objects.count(),
            pendientes=Cita.objects.filter(estado=Cita.Estado.SOLICITADA).count(),
            total_especialistas=Especialista.objects.filter(activo=True).count(),
            total_tratamientos=Tratamiento.objects.filter(activo=True).count(),
            barras_diarias=barras_diarias,
            barras_semanales=barras_semanales,
            barras_mensuales=barras_mensuales,
            periodos_dashboard=[
                {"titulo": "Diario", "barras": barras_diarias, "periodo": "Últimos 7 días"},
                {"titulo": "Semanal", "barras": barras_semanales, "periodo": "Últimas 8 semanas"},
                {"titulo": "Mensual", "barras": barras_mensuales, "periodo": "Últimos 6 meses"},
            ],
            ingreso_hoy=ingresos.filter(atendida_en__date=hoy).aggregate(total=Sum("monto_ingreso"))["total"] or Decimal("0"),
            ingreso_semana=ingresos.filter(atendida_en__date__gte=inicio_semana, atendida_en__date__lte=hoy).aggregate(total=Sum("monto_ingreso"))["total"] or Decimal("0"),
            ingreso_mes=ingresos.filter(atendida_en__date__gte=inicio_mes, atendida_en__date__lte=hoy).aggregate(total=Sum("monto_ingreso"))["total"] or Decimal("0"),
            ingresos_registrados=ingresos.filter(monto_ingreso__gt=0).count(),
            atenciones_realizadas=total_atenciones,
            tratamientos_mas_realizados=porciones,
        ),
    )


def _auditar_gestion(request, accion, objeto):
    """Registra la operación del panel sin copiar datos personales al log."""
    EventoAuditoria.objects.create(
        actor=request.user,
        accion=accion,
        tipo_objeto=objeto.__class__.__name__,
        identificador_objeto=str(objeto.pk),
        detalles={"origen": "panel_gestion"},
    )


def _resumen_errores_formulario(form):
    errores = [str(error) for grupo in form.errors.values() for error in grupo]
    return "No se guardaron los cambios. " + " ".join(errores or ["Revisa los campos e inténtalo de nuevo."])


def _validar_bloque_cita(cita):
    """Comprueba agenda y solapamientos antes de mover una cita ya confirmada."""
    if not cita.especialista or not cita.especialista.activo:
        return "Asigna un especialista activo antes de reprogramar esta cita."
    if not especialidad_admite_tratamiento(cita.tratamiento.area, cita.especialista.especialidad):
        return "El especialista seleccionado no corresponde al tratamiento."
    if cita.fecha_hora_solicitada <= timezone.now():
        return "La nueva fecha debe ser futura."

    inicio_local = timezone.localtime(cita.fecha_hora_solicitada)
    duracion = cita.tratamiento.duracion_minutos or 30
    fin = cita.fecha_hora_solicitada + timedelta(minutes=duracion)
    fin_local = timezone.localtime(fin)
    horario = HorarioAtencion.objects.filter(
        especialista=cita.especialista,
        dia_semana=inicio_local.weekday(),
        activo=True,
        hora_inicio__lte=inicio_local.time(),
        hora_fin__gt=inicio_local.time(),
    ).first()
    if not horario or fin_local.date() != inicio_local.date() or fin_local.time() > horario.hora_fin:
        return "La nueva fecha no cabe dentro de un horario activo del especialista."

    otras = Cita.objects.filter(
        especialista=cita.especialista,
        estado__in=[Cita.Estado.CONFIRMADA, Cita.Estado.REPROGRAMADA],
        fecha_hora_solicitada__lt=fin,
    ).exclude(pk=cita.pk).select_related("tratamiento")
    for otra in otras:
        fin_otra = otra.fecha_hora_solicitada + timedelta(minutes=otra.tratamiento.duracion_minutos or 30)
        if fin_otra > cita.fecha_hora_solicitada:
            return "Ese bloque se cruza con otra cita confirmada. Selecciona otro horario."
    return ""


@staff_member_required(login_url="acceso_personal")
def gestion_citas(request):
    if request.method == "POST":
        accion = request.POST.get("accion", "")
        if accion in {"crear", "editar"}:
            pk = request.POST.get("cita_id") or request.POST.get("registro_id")
            cita_existente = get_object_or_404(Cita, pk=pk) if accion == "editar" else None
            if cita_existente and cita_existente.estado in {Cita.Estado.CANCELADA, Cita.Estado.ATENDIDA}:
                messages.error(request, "Las citas canceladas o atendidas no se pueden editar; el historial se conserva.")
                return redirect("gestion_citas")
            form = CitaGestionForm(request.POST, instance=cita_existente)
            if form.is_valid():
                fecha_previa = cita_existente.fecha_hora_solicitada if cita_existente else None
                cita = form.save(commit=False)
                cita_previa = cita_existente
                with transaction.atomic():
                    if cita_previa and cita_previa.estado in {Cita.Estado.CONFIRMADA, Cita.Estado.REPROGRAMADA}:
                        if not cita.especialista_id:
                            messages.error(request, "Asigna un especialista activo antes de reprogramar esta cita.")
                            return redirect("gestion_citas")
                        Especialista.objects.select_for_update().get(pk=cita.especialista_id)
                        error_agenda = _validar_bloque_cita(cita)
                        if error_agenda:
                            messages.error(request, error_agenda)
                            return redirect("gestion_citas")
                        cita.estado = Cita.Estado.REPROGRAMADA
                    cita.save()
                    if cita_previa is None:
                        CitaEvento.objects.create(cita=cita, accion=CitaEvento.Accion.SOLICITADA, actor=request.user)
                        mensaje = f"Se registró la solicitud {cita.codigo}. Aún debe confirmarse desde el panel."
                    else:
                        CitaEvento.objects.create(
                            cita=cita,
                            accion=CitaEvento.Accion.REPROGRAMADA,
                            fecha_anterior=fecha_previa,
                            fecha_nueva=cita.fecha_hora_solicitada,
                            motivo="Ajuste realizado desde el panel de administración.",
                            actor=request.user,
                        )
                        mensaje = f"Se actualizaron los datos de la cita {cita.codigo}."
                    _auditar_gestion(request, "crear_cita" if cita_previa is None else "editar_cita", cita)
                messages.success(request, mensaje)
            else:
                messages.error(request, _resumen_errores_formulario(form))
            return redirect("gestion_citas")

        cita = get_object_or_404(Cita.objects.select_related("especialista", "tratamiento"), pk=request.POST.get("cita_id"))
        if accion == "cancelar" and cita.estado in {Cita.Estado.SOLICITADA, Cita.Estado.CONFIRMADA, Cita.Estado.REPROGRAMADA}:
            cita.estado = Cita.Estado.CANCELADA
            cita.save(update_fields=["estado"])
            CitaEvento.objects.create(cita=cita, accion=CitaEvento.Accion.CANCELADA, actor=request.user)
            _auditar_gestion(request, "cancelar_cita", cita)
            messages.success(request, f"La cita {cita.codigo} quedó cancelada.")
        elif accion == "confirmar" and cita.estado in {Cita.Estado.SOLICITADA, Cita.Estado.REPROGRAMADA}:
            horario = None
            cita_local = timezone.localtime(cita.fecha_hora_solicitada)
            if cita.especialista_id:
                horario = HorarioAtencion.objects.filter(
                    especialista=cita.especialista,
                    dia_semana=cita_local.weekday(),
                    activo=True,
                    hora_inicio__lte=cita_local.time(),
                    hora_fin__gt=cita_local.time(),
                ).first()
            especialista_compatible = bool(cita.especialista and especialidad_admite_tratamiento(cita.tratamiento.area, cita.especialista.especialidad))
            duracion = cita.tratamiento.duracion_minutos or 30
            fin_solicitado = cita.fecha_hora_solicitada + timedelta(minutes=duracion)
            cabe_en_bloque = bool(horario and timezone.localtime(fin_solicitado).time() <= horario.hora_fin)
            conflicto = False
            if horario:
                existentes = Cita.objects.filter(
                    especialista=cita.especialista,
                    estado__in=[Cita.Estado.CONFIRMADA, Cita.Estado.REPROGRAMADA],
                    fecha_hora_solicitada__lt=fin_solicitado,
                ).exclude(pk=cita.pk).select_related("tratamiento")
                conflicto = any(
                    otra.fecha_hora_solicitada + timedelta(minutes=otra.tratamiento.duracion_minutos or 30) > cita.fecha_hora_solicitada
                    for otra in existentes
                )
            if not especialista_compatible:
                messages.error(request, "El tratamiento no corresponde a la especialidad del profesional asignado. Corrige la asignación antes de confirmar.")
            elif not horario or not cabe_en_bloque:
                messages.error(request, "No se puede confirmar: asigna un especialista y configura su horario individual para ese día y hora.")
            elif conflicto:
                messages.error(request, "Ese bloque se cruza con otra cita confirmada. Reprograma la solicitud antes de confirmarla.")
            elif cita.fecha_hora_solicitada <= timezone.now():
                messages.error(request, "La fecha solicitada ya pasó; actualízala antes de confirmar.")
            else:
                with transaction.atomic():
                    cita.estado = Cita.Estado.CONFIRMADA
                    cita.save(update_fields=["estado"])
                    CitaEvento.objects.create(cita=cita, accion=CitaEvento.Accion.CONFIRMADA, actor=request.user)
                    _auditar_gestion(request, "confirmar_cita", cita)
                messages.success(request, f"La cita {cita.codigo} quedó confirmada.")
        elif accion == "atender" and cita.estado in {Cita.Estado.CONFIRMADA, Cita.Estado.REPROGRAMADA}:
            try:
                monto = Decimal(request.POST.get("monto_ingreso", "").strip().replace(",", "."))
                if not monto.is_finite() or monto < 0 or monto > Decimal("99999999.99") or monto.as_tuple().exponent < -2:
                    raise InvalidOperation
            except (InvalidOperation, AttributeError):
                messages.error(request, "Ingresa el valor cobrado con hasta dos decimales; puede ser 0.00 si no hubo ingreso.")
            else:
                if cita.fecha_hora_solicitada > timezone.now():
                    messages.error(request, "No se puede registrar como atendida antes de la fecha de la cita.")
                else:
                    cita.estado = Cita.Estado.ATENDIDA
                    cita.monto_ingreso = monto
                    cita.atendida_en = timezone.now()
                    cita.save(update_fields=["estado", "monto_ingreso", "atendida_en"])
                    CitaEvento.objects.create(
                        cita=cita,
                        accion=CitaEvento.Accion.ATENDIDA,
                        motivo=f"Ingreso registrado: USD {monto:.2f}",
                        actor=request.user,
                    )
                    _auditar_gestion(request, "registrar_atencion", cita)
                    messages.success(request, f"Se registró la atención y el ingreso de la cita {cita.codigo}.")
        else:
            messages.warning(request, "La acción no corresponde al estado actual de la cita.")
        return redirect("gestion_citas")
    citas = Cita.objects.select_related("paciente", "tratamiento", "especialista", "sucursal")
    estado = request.GET.get("estado", "")
    busqueda = request.GET.get("q", "").strip()[:100]
    if estado in Cita.Estado.values:
        citas = citas.filter(estado=estado)
    if busqueda:
        citas = citas.filter(paciente__nombre_completo__icontains=busqueda) | citas.filter(codigo__icontains=busqueda)
    citas = list(citas)
    for cita in citas:
        if cita.especialista_id:
            clave = _clave_color_especialista(cita.especialista.nombre_completo)
            cita.especialista.color_agenda = COLORES_AGENDA_ESPECIALISTAS.get(clave, "#4475A9")
            cita.especialista.color_agenda_texto = COLORES_TEXTO_AGENDA_ESPECIALISTAS.get(clave, "#303030")
    return render(
        request,
        "web/admin/citas.html",
        contexto_base(
            seccion_activa="citas", citas=citas, estado_filtro=estado, busqueda=busqueda,
            estados_cita=Cita.Estado.choices, ahora=timezone.now(), cita_form=CitaGestionForm(),
            pacientes_catalogo=Paciente.objects.order_by("nombre_completo"),
            tratamientos_catalogo=ordenar_catalogo_tratamientos(Tratamiento.objects.filter(activo=True)),
            especialistas_catalogo=Especialista.objects.filter(activo=True).order_by("nombre_completo"),
            sucursales_catalogo=Sucursal.objects.filter(activa=True).order_by("nombre"),
        ),
    )


@staff_member_required(login_url="acceso_personal")
def gestion_pacientes(request):
    if request.method == "POST":
        accion = request.POST.get("accion", "")
        paciente = get_object_or_404(Paciente, pk=request.POST.get("registro_id")) if request.POST.get("registro_id") else None
        if accion == "eliminar" and paciente:
            if paciente.citas.exists():
                messages.error(request, "No se puede eliminar este paciente porque tiene citas en el historial. Puedes corregir sus datos desde Editar.")
            else:
                pk = paciente.pk
                paciente.delete()
                EventoAuditoria.objects.create(actor=request.user, accion="eliminar_paciente", tipo_objeto="Paciente", identificador_objeto=str(pk), detalles={"accion_panel": "eliminar"})
                messages.success(request, "Se eliminó el registro del paciente.")
            return redirect("gestion_pacientes")
        if accion in {"crear", "editar"}:
            form = PacienteGestionForm(request.POST, instance=paciente if accion == "editar" else None)
            if form.is_valid():
                paciente = form.save()
                _auditar_gestion(request, "crear_paciente" if accion == "crear" else "editar_paciente", paciente)
                messages.success(request, "Datos del paciente actualizados exitosamente." if accion == "editar" else "Paciente creado exitosamente.")
            else:
                messages.error(request, _resumen_errores_formulario(form))
            return redirect("gestion_pacientes")

    pacientes = Paciente.objects.annotate(total_citas=Count("citas")).order_by("nombre_completo")
    busqueda = request.GET.get("q", "").strip()[:100]
    if busqueda:
        pacientes = pacientes.filter(nombre_completo__icontains=busqueda) | pacientes.filter(telefono__icontains=busqueda) | pacientes.filter(identificacion__icontains=busqueda)
    return render(
        request,
        "web/admin/pacientes.html",
        contexto_base(seccion_activa="pacientes", pacientes=pacientes, busqueda=busqueda, paciente_form=PacienteGestionForm()),
    )


@staff_member_required(login_url="acceso_personal")
def gestion_agenda(request):
    if request.method == "POST":
        accion = request.POST.get("accion", "")
        horario = get_object_or_404(HorarioAtencion, pk=request.POST.get("registro_id")) if request.POST.get("registro_id") else None
        if accion == "eliminar" and horario:
            pk = horario.pk
            horario.delete()
            EventoAuditoria.objects.create(actor=request.user, accion="eliminar_horario", tipo_objeto="HorarioAtencion", identificador_objeto=str(pk), detalles={"accion_panel": "eliminar"})
            messages.success(request, "Se eliminó el horario.")
            return redirect("gestion_agenda")
        if accion in {"crear", "editar"}:
            form = HorarioGestionForm(request.POST, instance=horario if accion == "editar" else None)
            if form.is_valid():
                horario = form.save()
                _auditar_gestion(request, "crear_horario" if accion == "crear" else "editar_horario", horario)
                messages.success(request, "Horario de atención actualizado exitosamente." if accion == "editar" else "Horario de atención creado exitosamente.")
            else:
                messages.error(request, _resumen_errores_formulario(form))
            return redirect("gestion_agenda")
    prioridades = {nombre: indice for indice, nombre in enumerate(COLORES_AGENDA_ESPECIALISTAS)}
    columnas = []
    especialistas = list(Especialista.objects.filter(activo=True).prefetch_related("horarios"))
    for especialista in especialistas:
        clave = _clave_color_especialista(especialista.nombre_completo)
        especialista.color_agenda = COLORES_AGENDA_ESPECIALISTAS.get(clave, "#4475A9")
        especialista.horarios_agenda = list(especialista.horarios.all().order_by("dia_semana", "hora_inicio"))
        columnas.append((prioridades.get(clave, len(prioridades)), especialista.nombre_completo.casefold(), especialista))
    columnas.sort(key=lambda item: (item[0], item[1]))
    horarios = list(HorarioAtencion.objects.select_related("especialista").order_by("especialista__nombre_completo", "dia_semana", "hora_inicio"))
    for horario in horarios:
        clave = _clave_color_especialista(horario.especialista.nombre_completo)
        horario.especialista.color_agenda = COLORES_AGENDA_ESPECIALISTAS.get(clave, "#4475A9")
        horario.especialista.color_agenda_texto = COLORES_TEXTO_AGENDA_ESPECIALISTAS.get(clave, "#303030")
    return render(
        request,
        "web/admin/agenda.html",
        contexto_base(
            seccion_activa="agenda",
            horarios=horarios,
            agenda_especialistas=[item[2] for item in columnas],
            horario_form=HorarioGestionForm(),
        ),
    )


@staff_member_required(login_url="acceso_personal")
def gestion_especialistas(request):
    if request.method == "POST":
        accion = request.POST.get("accion", "")
        especialista = get_object_or_404(Especialista, pk=request.POST.get("registro_id")) if request.POST.get("registro_id") else None
        if accion == "eliminar" and especialista:
            if especialista.usuario_id or especialista.citas.exists() or especialista.horarios.exists():
                especialista.activo = False
                especialista.save(update_fields=["activo"])
                _auditar_gestion(request, "desactivar_especialista", especialista)
                messages.warning(request, "El especialista tiene relaciones o historial. Se desactivó para conservar los registros asociados.")
            else:
                pk = especialista.pk
                especialista.delete()
                EventoAuditoria.objects.create(actor=request.user, accion="eliminar_especialista", tipo_objeto="Especialista", identificador_objeto=str(pk), detalles={"accion_panel": "eliminar"})
                messages.success(request, "Se eliminó el especialista del catálogo.")
            return redirect("gestion_especialistas")
        if accion in {"crear", "editar"}:
            form = EspecialistaGestionForm(request.POST, instance=especialista if accion == "editar" else None)
            if form.is_valid():
                especialista = form.save()
                _auditar_gestion(request, "crear_especialista" if accion == "crear" else "editar_especialista", especialista)
                messages.success(request, "Datos del especialista actualizados exitosamente." if accion == "editar" else "Especialista creado exitosamente.")
            else:
                messages.error(request, _resumen_errores_formulario(form))
            return redirect("gestion_especialistas")
    return render(
        request,
        "web/admin/especialistas.html",
        contexto_base(
            seccion_activa="especialistas",
            catalogo_especialistas=Especialista.objects.annotate(total_citas=Count("citas", distinct=True), total_horarios=Count("horarios", distinct=True)).order_by("nombre_completo"),
            especialista_form=EspecialistaGestionForm(),
        ),
    )


@staff_member_required(login_url="acceso_personal")
def gestion_tratamientos(request):
    if request.method == "POST":
        accion = request.POST.get("accion", "")
        tratamiento = get_object_or_404(Tratamiento, pk=request.POST.get("registro_id")) if request.POST.get("registro_id") else None
        if accion == "eliminar" and tratamiento:
            if tratamiento.citas.exists():
                tratamiento.activo = False
                tratamiento.save(update_fields=["activo"])
                _auditar_gestion(request, "desactivar_tratamiento", tratamiento)
                messages.warning(request, "El tratamiento tiene citas asociadas. Se desactivó para conservar el historial.")
            else:
                pk = tratamiento.pk
                tratamiento.delete()
                EventoAuditoria.objects.create(actor=request.user, accion="eliminar_tratamiento", tipo_objeto="Tratamiento", identificador_objeto=str(pk), detalles={"accion_panel": "eliminar"})
                messages.success(request, "Se eliminó el tratamiento del catálogo.")
            return redirect("gestion_tratamientos")
        if accion in {"crear", "editar"}:
            form = TratamientoGestionForm(request.POST, instance=tratamiento if accion == "editar" else None)
            if form.is_valid():
                tratamiento = form.save()
                _auditar_gestion(request, "crear_tratamiento" if accion == "crear" else "editar_tratamiento", tratamiento)
                messages.success(request, "Datos del tratamiento actualizados exitosamente." if accion == "editar" else "Tratamiento creado exitosamente.")
            else:
                messages.error(request, _resumen_errores_formulario(form))
            return redirect("gestion_tratamientos")
    return render(
        request,
        "web/admin/tratamientos.html",
        contexto_base(
            seccion_activa="tratamientos",
            catalogo_tratamientos=ordenar_catalogo_tratamientos(Tratamiento.objects.filter(activo=True).annotate(total_citas=Count("citas"))),
            tratamiento_form=TratamientoGestionForm(),
        ),
    )


@staff_member_required(login_url="acceso_personal")
def gestion_sucursales(request):
    if request.method == "POST":
        accion = request.POST.get("accion", "")
        sucursal = get_object_or_404(Sucursal, pk=request.POST.get("registro_id")) if request.POST.get("registro_id") else None
        if accion == "eliminar" and sucursal:
            if sucursal.citas.exists():
                sucursal.activa = False
                sucursal.save(update_fields=["activa"])
                _auditar_gestion(request, "desactivar_sucursal", sucursal)
                messages.warning(request, "La sucursal tiene citas asociadas. Se desactivó para conservar el historial.")
            else:
                pk = sucursal.pk
                sucursal.delete()
                EventoAuditoria.objects.create(actor=request.user, accion="eliminar_sucursal", tipo_objeto="Sucursal", identificador_objeto=str(pk), detalles={"accion_panel": "eliminar"})
                messages.success(request, "Se eliminó la sucursal.")
            return redirect("gestion_sucursales")
        if accion in {"crear", "editar"}:
            form = SucursalGestionForm(request.POST, instance=sucursal if accion == "editar" else None)
            if form.is_valid():
                sucursal = form.save()
                _auditar_gestion(request, "crear_sucursal" if accion == "crear" else "editar_sucursal", sucursal)
                messages.success(request, "Datos de la sucursal actualizados exitosamente." if accion == "editar" else "Sucursal creada exitosamente.")
            else:
                messages.error(request, _resumen_errores_formulario(form))
            return redirect("gestion_sucursales")
    return render(
        request,
        "web/admin/sucursales.html",
        contexto_base(
            seccion_activa="sucursales",
            sucursales=Sucursal.objects.annotate(total_citas=Count("citas")).order_by("nombre"),
            sucursal_form=SucursalGestionForm(),
        ),
    )


@staff_member_required(login_url="acceso_personal")
def gestion_notificaciones(request):
    return render(
        request,
        "web/admin/notificaciones.html",
        contexto_base(seccion_activa="notificaciones"),
    )


@staff_member_required(login_url="acceso_personal")
def gestion_conversaciones(request, pk=None):
    """Bandeja protegida para revisar y responder conversaciones de WhatsApp."""
    if pk is not None:
        conversacion = get_object_or_404(Conversacion.objects.prefetch_related("mensajes"), pk=pk)
        if request.method == "POST":
            accion = request.POST.get("accion", "")
            if accion == "estado":
                estado = request.POST.get("estado", "")
                if estado not in Conversacion.Estado.values:
                    messages.error(request, "Selecciona un estado válido para la conversación.")
                else:
                    conversacion.estado = estado
                    conversacion.save(update_fields=["estado", "ultima_actividad"])
                    EventoAuditoria.objects.create(actor=request.user, accion="whatsapp_estado_cambiado", tipo_objeto="Conversacion", identificador_objeto=str(conversacion.pk), detalles={"estado": estado})
                    messages.success(request, "Se actualizó el estado de la conversación.")
                return redirect("gestion_conversacion_detalle", pk=conversacion.pk)
            if accion == "responder":
                texto = request.POST.get("mensaje", "").strip()
                if not texto or len(texto) > 1000:
                    messages.error(request, "Escribe un mensaje de 1 a 1000 caracteres.")
                elif enviar_mensaje_whatsapp(conversacion.whatsapp_id, texto, conversacion):
                    conversacion.estado = Conversacion.Estado.HUMANA
                    conversacion.save(update_fields=["estado", "ultima_actividad"])
                    EventoAuditoria.objects.create(actor=request.user, accion="whatsapp_respuesta_enviada", tipo_objeto="Conversacion", identificador_objeto=str(conversacion.pk), detalles={"canal": "whatsapp"})
                    messages.success(request, "El mensaje se envió por WhatsApp.")
                else:
                    messages.error(request, "No se envió. Verifica la conexión y las credenciales de WhatsApp Cloud API.")
                return redirect("gestion_conversacion_detalle", pk=conversacion.pk)
            messages.error(request, "La acción solicitada no es válida.")
            return redirect("gestion_conversacion_detalle", pk=conversacion.pk)
        historial = list(conversacion.mensajes.order_by("-creado_en")[:200])
        historial.reverse()
        return render(request, "web/admin/conversacion_detalle.html", contexto_base(
            seccion_activa="conversaciones", conversacion=conversacion,
            mensajes_conversacion=historial[:200], estados_conversacion=Conversacion.Estado.choices,
        ))

    estado = request.GET.get("estado", "")
    ultimo_mensaje = MensajeConversacion.objects.filter(conversacion_id=OuterRef("pk")).order_by("-creado_en").values("contenido")[:1]
    queryset = Conversacion.objects.annotate(ultimo_mensaje=Subquery(ultimo_mensaje))
    if estado in Conversacion.Estado.values:
        queryset = queryset.filter(estado=estado)
    pagina_actual = Paginator(queryset, 25).get_page(request.GET.get("pagina"))
    return render(request, "web/admin/conversaciones.html", contexto_base(
        seccion_activa="conversaciones", conversaciones=pagina_actual,
        estado_filtro=estado, estados_conversacion=Conversacion.Estado.choices,
        total_conversaciones=Conversacion.objects.count(),
        conversaciones_activas=Conversacion.objects.filter(estado=Conversacion.Estado.ACTIVA).count(),
        conversaciones_humanas=Conversacion.objects.filter(estado=Conversacion.Estado.HUMANA).count(),
        conversaciones_cerradas=Conversacion.objects.filter(estado=Conversacion.Estado.CERRADA).count(),
    ))


@staff_member_required(login_url="acceso_personal")
def gestion_auditoria(request):
    return render(
        request,
        "web/admin/auditoria.html",
        contexto_base(seccion_activa="auditoria", eventos=CitaEvento.objects.select_related("cita", "cita__paciente", "actor")[:200]),
    )


# ----------------- ESPACIO DEL ESPECIALISTA -----------------
@login_required(login_url="acceso_personal")
def espacio_especialista(request):
    perfil = getattr(request.user, "perfil_especialista", None)
    if not perfil or not perfil.activo:
        return redirigir_segun_rol(request.user)
    citas = Cita.objects.filter(especialista=perfil).select_related("paciente", "tratamiento").order_by("fecha_hora_solicitada")
    seccion = {
        "espacio_especialista": "resumen",
        "especialista_pacientes": "pacientes",
        "especialista_agenda": "agenda",
    }.get(request.resolver_match.url_name, "resumen")
    estados_activos = [Cita.Estado.SOLICITADA, Cita.Estado.CONFIRMADA, Cita.Estado.REPROGRAMADA, Cita.Estado.ATENDIDA]
    return render(request, "web/espacio_especialista.html", contexto_base(
        perfil=perfil,
        seccion_especialista=seccion,
        puede_ver_dashboard=_es_veronica_martinez(perfil),
        citas=citas,
        citas_proximas=citas.filter(estado__in=[Cita.Estado.CONFIRMADA, Cita.Estado.REPROGRAMADA], fecha_hora_solicitada__gte=timezone.now())[:5],
        pacientes=Paciente.objects.filter(citas__especialista=perfil, citas__estado__in=estados_activos).annotate(
            total_citas=Count("citas", filter=Q(citas__especialista=perfil, citas__estado__in=estados_activos)),
            ultima_cita=Max("citas__fecha_hora_solicitada", filter=Q(citas__especialista=perfil, citas__estado__in=estados_activos)),
        ).distinct().order_by("nombre_completo"),
        total_pacientes=citas.values("paciente_id").distinct().count(),
        citas_solicitadas=citas.filter(estado=Cita.Estado.SOLICITADA).count(),
        citas_atendidas=citas.filter(estado=Cita.Estado.ATENDIDA).count(),
        horarios=HorarioAtencion.objects.filter(especialista=perfil, activo=True),
    ))
