"""Elimina mensajes y conversaciones vencidos según la retención configurada."""

from datetime import timedelta

from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import timezone

from web.models import Conversacion, MensajeConversacion


class Command(BaseCommand):
    help = "Elimina mensajes y conversaciones de WhatsApp vencidos."

    def handle(self, *args, **options):
        dias = max(1, int(settings.VITADENT_CONVERSATION_RETENTION_DAYS))
        limite = timezone.now() - timedelta(days=dias)
        mensajes, _ = MensajeConversacion.objects.filter(creado_en__lt=limite).delete()
        conversaciones, _ = Conversacion.objects.filter(ultima_actividad__lt=limite).delete()
        self.stdout.write(self.style.SUCCESS(f"Mensajes eliminados: {mensajes}; conversaciones eliminadas: {conversaciones}; retención: {dias} días."))
