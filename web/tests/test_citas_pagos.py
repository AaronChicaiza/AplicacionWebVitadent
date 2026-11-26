from datetime import timedelta
from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone

from web.models import Cita, Especialista, Paciente, Tratamiento


@pytest.mark.django_db
def test_cita_muestra_nota_pagado_y_saldo_y_permite_editar_importes(client):
    admin = get_user_model().objects.create_user(username="admin_pagos", password="prueba", is_staff=True)
    client.force_login(admin)
    paciente = Paciente.objects.create(nombre_completo="Paciente de prueba", telefono="0991234567")
    tratamiento = Tratamiento.objects.create(nombre="Consulta de prueba", area="Odontología", duracion_minutos=30)
    especialista = Especialista.objects.create(nombre_completo="Dra. Prueba", especialidad="Odontología")
    fecha = timezone.now() - timedelta(days=1)
    cita = Cita.objects.create(
        paciente=paciente, tratamiento=tratamiento, especialista=especialista,
        fecha_hora_solicitada=fecha, estado=Cita.Estado.ATENDIDA, atendida_en=timezone.now(),
    )

    respuesta = client.post(reverse("gestion_citas"), {
        "accion": "editar", "registro_id": cita.pk,
        "paciente": paciente.pk, "tratamiento": tratamiento.pk, "especialista": especialista.pk,
        "sucursal": "", "fecha_hora_solicitada": timezone.localtime(fecha).strftime("%Y-%m-%dT%H:%M"),
        "comentario": "Abonó en recepción", "monto_total": "100.00", "monto_ingreso": "40.00",
    })
    assert respuesta.status_code == 302
    cita.refresh_from_db()
    assert cita.comentario == "Abonó en recepción"
    assert cita.monto_ingreso == Decimal("40.00")
    assert cita.saldo_pendiente == Decimal("60.00")

    contenido = client.get(reverse("gestion_citas")).content.decode()
    assert "Abonó en recepción" in contenido
    assert "Saldo pendiente" in contenido
    assert "$60" in contenido


@pytest.mark.django_db
def test_cita_rechaza_pago_superior_al_total(client):
    admin = get_user_model().objects.create_user(username="admin_validacion", password="prueba", is_staff=True)
    client.force_login(admin)
    paciente = Paciente.objects.create(nombre_completo="Paciente de prueba", telefono="0991234567")
    tratamiento = Tratamiento.objects.create(nombre="Consulta de prueba", area="Odontología", duracion_minutos=30)
    fecha = timezone.localtime(timezone.now() + timedelta(days=2)).strftime("%Y-%m-%dT%H:%M")
    respuesta = client.post(reverse("gestion_citas"), {
        "accion": "crear", "paciente": paciente.pk, "tratamiento": tratamiento.pk,
        "especialista": "", "sucursal": "", "fecha_hora_solicitada": fecha,
        "comentario": "Pago incompleto", "monto_total": "20.00", "monto_ingreso": "30.00",
    })
    assert respuesta.status_code == 302
    assert not Cita.objects.exists()
