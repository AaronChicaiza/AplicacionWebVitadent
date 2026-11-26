import pytest
from django.contrib.staticfiles import finders
from django.urls import reverse

from web.datos_demo import GRUPOS_TRATAMIENTOS


@pytest.mark.django_db
def test_catalogo_enlaza_areas_y_cada_procedimiento_tiene_ilustracion(client):
    catalogo = client.get(reverse("tratamientos"))
    assert catalogo.status_code == 200

    for grupo in GRUPOS_TRATAMIENTOS:
        assert grupo["imagen"].startswith("web/img/areas/")
        assert finders.find(grupo["imagen"])
        ruta = reverse("detalle_area_tratamiento", args=[grupo["id"]])
        assert ruta in catalogo.content.decode()
        respuesta = client.get(ruta)
        assert respuesta.status_code == 200
        pagina = respuesta.content.decode()
        for indice, nombre in enumerate(grupo["procedimientos"], start=1):
            imagen = f"web/img/procedimientos/{grupo['id']}-{indice:02}.svg"
            assert nombre in pagina
            assert imagen in pagina
            assert finders.find(imagen)
        assert "¿Qué es?" in pagina
        assert "¿Para qué sirve?" in pagina


@pytest.mark.django_db
def test_area_inexistente_devuelve_404(client):
    respuesta = client.get(reverse("detalle_area_tratamiento", args=["no-existe"]))
    assert respuesta.status_code == 404
