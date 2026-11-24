"""Adaptador del canal WhatsApp Cloud API hacia Rasa y Django."""

import hashlib
import hmac
import logging
import re

import requests
from django.conf import settings
from django.db import IntegrityError, transaction
from django.utils import timezone

from .models import Conversacion, EventoAuditoria, MensajeConversacion

logger = logging.getLogger("vitadent.whatsapp")


def firma_meta_valida(cuerpo: bytes, firma: str) -> bool:
    secreto = getattr(settings, "WHATSAPP_APP_SECRET", "")
    if not secreto or not firma.startswith("sha256="):
        return False
    esperada = "sha256=" + hmac.new(secreto.encode(), cuerpo, hashlib.sha256).hexdigest()
    return hmac.compare_digest(esperada, firma)


def _hash_remitente(wa_id: str) -> str:
    return hashlib.sha256(wa_id.encode("utf-8")).hexdigest()


def procesar_evento_whatsapp(cuerpo: dict) -> None:
    """Procesa mensajes entrantes; eventos de estado del proveedor se ignoran."""
    for entrada in cuerpo.get("entry", []):
        if not isinstance(entrada, dict):
            continue
        for cambio in entrada.get("changes", []):
            if not isinstance(cambio, dict):
                continue
            valor = cambio.get("value", {})
            if not isinstance(valor, dict):
                continue
            if cambio.get("field") != "messages" and "messages" not in valor:
                continue
            contactos = valor.get("contacts", [])
            nombre_contacto = ""
            if contactos and isinstance(contactos[0], dict):
                perfil = contactos[0].get("profile", {})
                if isinstance(perfil, dict):
                    nombre_contacto = str(perfil.get("name", ""))[:120]
            for mensaje in valor.get("messages", []):
                if isinstance(mensaje, dict):
                    _procesar_mensaje(mensaje, valor, nombre_contacto)


def _procesar_mensaje(mensaje: dict, valor: dict, nombre_contacto: str) -> None:
    wa_id = str(mensaje.get("from", ""))
    message_id = str(mensaje.get("id", ""))[:180]
    tipo = str(mensaje.get("type", "unknown"))[:24]
    texto = ""
    if tipo == "text":
        cuerpo_texto = mensaje.get("text", {})
        if isinstance(cuerpo_texto, dict):
            texto = str(cuerpo_texto.get("body", ""))
    if not re.fullmatch(r"[0-9]{7,20}", wa_id) or not message_id or len(texto) > 4000:
        logger.warning("whatsapp_message_rejected reason=shape")
        return

    try:
        with transaction.atomic():
            conversacion, _ = Conversacion.objects.get_or_create(
                identificador_hash=_hash_remitente(wa_id),
                defaults={"canal": "whatsapp", "whatsapp_id": wa_id},
            )
            _, creado = MensajeConversacion.objects.get_or_create(
                identificador_proveedor=message_id,
                defaults={
                    "conversacion": conversacion,
                    "direccion": MensajeConversacion.Direccion.ENTRANTE,
                    "tipo": tipo,
                    "contenido": texto,
                },
            )
    except IntegrityError:
        return
    if not creado:
        return
    if conversacion.estado == Conversacion.Estado.CERRADA:
        conversacion.estado = Conversacion.Estado.ACTIVA
    conversacion.save(update_fields=["estado", "ultima_actividad"])

    if tipo != "text" or not texto.strip():
        respuestas = ["Por ahora puedo atender mensajes de texto para gestionar citas. Escríbeme qué necesitas o pide hablar con recepción."]
    elif conversacion.estado == Conversacion.Estado.HUMANA:
        respuestas = ["Tu conversación está pendiente de atención por recepción. La clínica te responderá por este mismo WhatsApp."]
    else:
        respuestas = enviar_a_rasa(wa_id, texto, nombre_contacto)

    for respuesta in respuestas:
        enviar_mensaje_whatsapp(wa_id, respuesta, conversacion)


def enviar_a_rasa(wa_id: str, texto: str, nombre_contacto: str = "") -> list[str]:
    base = getattr(settings, "RASA_REST_URL", "").strip().rstrip("/")
    if not base:
        return ["El agendamiento automatizado aún no está habilitado. Puedes escribir a recepción para coordinar tu cita."]
    try:
        respuesta = requests.post(
            f"{base}/webhooks/rest/webhook",
            json={"sender": wa_id, "message": texto, "metadata": {"canal": "whatsapp", "nombre_contacto": nombre_contacto}},
            timeout=(3, 8),
            allow_redirects=False,
        )
        respuesta.raise_for_status()
        salidas = respuesta.json()
    except (requests.RequestException, ValueError):
        logger.warning("rasa_unavailable channel=whatsapp")
        return ["El asistente no está disponible en este momento. No se registró ninguna cita; vuelve a escribir más tarde o contacta a recepción."]

    textos = []
    for salida in salidas if isinstance(salidas, list) else []:
        if not isinstance(salida, dict):
            continue
        texto_salida = salida.get("text")
        if isinstance(texto_salida, str) and texto_salida.strip():
            textos.append(texto_salida.strip()[:4000])
        custom = salida.get("custom")
        if isinstance(custom, dict) and custom.get("handoff"):
            Conversacion.objects.filter(identificador_hash=_hash_remitente(wa_id)).update(estado=Conversacion.Estado.HUMANA)
            EventoAuditoria.objects.create(accion="whatsapp_handoff", tipo_objeto="Conversacion", detalles={"canal": "whatsapp"})
    return textos or ["No recibí una respuesta del asistente. Puedes intentarlo de nuevo más tarde."]


def enviar_mensaje_whatsapp(destinatario: str, texto: str, conversacion: Conversacion) -> bool:
    token = getattr(settings, "WHATSAPP_ACCESS_TOKEN", "")
    phone_id = getattr(settings, "WHATSAPP_PHONE_NUMBER_ID", "")
    version = getattr(settings, "WHATSAPP_GRAPH_API_VERSION", "")
    if not token or not re.fullmatch(r"[0-9]{5,30}", phone_id) or not re.fullmatch(r"v[0-9]{1,3}\.0", version):
        logger.warning("whatsapp_send_not_configured")
        return False
    url = f"https://graph.facebook.com/{version}/{phone_id}/messages"
    try:
        respuesta = requests.post(
            url,
            json={
                "messaging_product": "whatsapp",
                "recipient_type": "individual",
                "to": destinatario,
                "type": "text",
                "text": {"preview_url": False, "body": texto[:4000]},
            },
            headers={"Authorization": f"Bearer {token}"},
            timeout=(3, 8),
            allow_redirects=False,
        )
        respuesta.raise_for_status()
        resultado = respuesta.json()
        proveedor_id = None
        if isinstance(resultado.get("messages"), list) and resultado["messages"]:
            proveedor_id = str(resultado["messages"][0].get("id", ""))[:180] or None
        MensajeConversacion.objects.create(
            conversacion=conversacion,
            identificador_proveedor=proveedor_id,
            direccion=MensajeConversacion.Direccion.SALIENTE,
            tipo="text",
            contenido=texto[:4000],
        )
        conversacion.save(update_fields=["ultima_actividad"])
        return True
    except (requests.RequestException, ValueError, IntegrityError):
        logger.warning("whatsapp_send_failed channel=whatsapp")
        return False
