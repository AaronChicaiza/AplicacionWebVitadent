import hashlib
import hmac
import json
from datetime import timedelta
from unittest.mock import patch

import pytest
from django.contrib.auth import get_user_model
from django.test import Client, override_settings
from django.urls import reverse
from django.utils import timezone

from web.models import Cita, Conversacion, Especialista, MensajeConversacion, Paciente, Tratamiento
from web.servicios_whatsapp import procesar_evento_whatsapp


User = get_user_model()


@pytest.mark.django_db
def test_internal_booking_rejects_missing_token():
    response = Client().post(
        reverse("api_interna_crear_solicitud"),
        data=json.dumps({}),
        content_type="application/json",
    )
    assert response.status_code == 401


@pytest.mark.django_db
@override_settings(WHATSAPP_APP_SECRET="test-meta-secret")
def test_whatsapp_webhook_accepts_valid_signature_and_rejects_invalid_one():
    payload = json.dumps({"object": "whatsapp_business_account", "entry": []}).encode()
    signature = "sha256=" + hmac.new(b"test-meta-secret", payload, hashlib.sha256).hexdigest()
    client = Client()

    with patch("web.views.procesar_evento_whatsapp") as process:
        accepted = client.post(
            reverse("webhook_whatsapp"),
            data=payload,
            content_type="application/json",
            HTTP_X_HUB_SIGNATURE_256=signature,
        )
    rejected = client.post(
        reverse("webhook_whatsapp"),
        data=payload,
        content_type="application/json",
        HTTP_X_HUB_SIGNATURE_256="sha256=" + ("0" * 64),
    )

    assert accepted.status_code == 200
    process.assert_called_once()
    assert rejected.status_code == 401


@pytest.mark.django_db
def test_specialist_only_sees_assigned_appointments():
    doctor_user = User.objects.create_user(username="doctor", password="Secure-password-2026")
    other_user = User.objects.create_user(username="other", password="Secure-password-2026")
    doctor = Especialista.objects.create(usuario=doctor_user, nombre_completo="Dra. Ejemplo", especialidad="Odontología")
    other_doctor = Especialista.objects.create(usuario=other_user, nombre_completo="Dr. Segundo", especialidad="Odontología")
    treatment = Tratamiento.objects.create(nombre="Consulta general", area="Odontología", duracion_minutos=30)
    patient = Paciente.objects.create(nombre_completo="Paciente Ejemplo", telefono="0991234567")
    own = Cita.objects.create(
        paciente=patient,
        especialista=doctor,
        tratamiento=treatment,
        fecha_hora_solicitada=timezone.now() + timedelta(days=1),
    )
    Cita.objects.create(
        paciente=patient,
        especialista=other_doctor,
        tratamiento=treatment,
        fecha_hora_solicitada=timezone.now() + timedelta(days=2),
    )

    client = Client()
    client.force_login(doctor_user)
    response = client.get(reverse("api_citas"))

    assert response.status_code == 200
    assert response.json()["count"] == 1
    assert response.json()["results"][0]["id"] == own.pk


@pytest.mark.django_db
def test_public_reservation_chat_endpoint_is_not_exposed():
    response = Client().post("/citas/chat/", data="{}", content_type="application/json")
    assert response.status_code == 404


@pytest.mark.django_db
@override_settings(VITADENT_RASA_TOKEN="test-internal-token")
def test_internal_booking_rejects_malicious_name_before_writing():
    response = Client().post(
        reverse("api_interna_crear_solicitud"),
        data=json.dumps({
            "nombre": "Aaron'; DROP TABLE pacientes;--",
            "identificacion": "0000000000",
            "telefono": "593991234567",
            "tratamiento": "Consulta",
            "fecha_hora": (timezone.now() + timedelta(days=2)).isoformat(),
            "idempotency_key": "a" * 64,
        }),
        content_type="application/json",
        HTTP_AUTHORIZATION="Bearer test-internal-token",
    )
    assert response.status_code == 400
    assert Paciente.objects.count() == 0


@pytest.mark.django_db
def test_management_inbox_requires_staff_and_can_open_conversation():
    staff = User.objects.create_user(username="admin-inbox", password="Secure-password-2026", is_staff=True)
    conversation = Conversacion.objects.create(identificador_hash="b" * 64, whatsapp_id="593991234567")
    MensajeConversacion.objects.create(
        conversacion=conversation,
        direccion=MensajeConversacion.Direccion.ENTRANTE,
        contenido="Quiero agendar una cita",
    )
    client = Client()

    unauthorized = client.get(reverse("gestion_conversaciones"))
    client.force_login(staff)
    authorized = client.get(reverse("gestion_conversacion_detalle", args=[conversation.pk]))

    assert unauthorized.status_code == 302
    assert authorized.status_code == 200
    assert "Quiero agendar una cita" in authorized.content.decode()


@pytest.mark.django_db
def test_new_message_reopens_closed_conversation():
    conversation = Conversacion.objects.create(
        identificador_hash=hashlib.sha256(b"593991234568").hexdigest(),
        whatsapp_id="593991234568",
        estado=Conversacion.Estado.CERRADA,
    )
    event = {
        "entry": [{"changes": [{"field": "messages", "value": {
            "contacts": [],
            "messages": [{"from": "593991234568", "id": "wamid.test-reopen", "type": "text", "text": {"body": "Quiero información"}}],
        }}]}],
    }
    with patch("web.servicios_whatsapp.enviar_a_rasa", return_value=["Hola"]), patch("web.servicios_whatsapp.enviar_mensaje_whatsapp", return_value=True):
        procesar_evento_whatsapp(event)
    conversation.refresh_from_db()
    assert conversation.estado == Conversacion.Estado.ACTIVA
