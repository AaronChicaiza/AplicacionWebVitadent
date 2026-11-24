"""Auditoría de acceso sin guardar usuarios escritos ni direcciones IP."""

import hashlib

from django.contrib.auth.signals import user_logged_in, user_login_failed
from django.dispatch import receiver

from .models import EventoAuditoria


def _hash(valor: str) -> str:
    return hashlib.sha256(valor.encode("utf-8", errors="ignore")).hexdigest()[:24]


@receiver(user_logged_in)
def registrar_acceso_correcto(sender, request, user, **kwargs):
    ip = request.META.get("REMOTE_ADDR", "") if request else ""
    EventoAuditoria.objects.create(
        actor=user,
        accion="acceso_correcto",
        tipo_objeto="Usuario",
        identificador_objeto=str(user.pk),
        detalles={"ip_hash": _hash(ip) if ip else ""},
    )


@receiver(user_login_failed)
def registrar_acceso_fallido(sender, credentials, request, **kwargs):
    usuario = str(credentials.get("username", "")).strip().casefold()[:150]
    ip = request.META.get("REMOTE_ADDR", "") if request else ""
    EventoAuditoria.objects.create(
        accion="acceso_fallido",
        tipo_objeto="Usuario",
        detalles={"usuario_hash": _hash(usuario) if usuario else "", "ip_hash": _hash(ip) if ip else ""},
    )
