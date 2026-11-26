from django.core.management.base import BaseCommand

from web.datos_demo import GRUPOS_TRATAMIENTOS
from web.models import Especialista, Tratamiento


class Command(BaseCommand):
    help = "Carga el equipo y el catálogo de VitaDent sin precios; conserva las duraciones que se editaron desde el panel."

    def handle(self, *args, **options):
        equipo = [
            ("Dra. Odalis Monar", "Ortodoncia"),
            ("Dra. Verónica Martínez", "Rehabilitación oral y ortodoncia"),
            ("Dra. Daniela Delgado", "Ortodoncia"),
            ("Dr. Adrián Quinatoa", "Cirugía maxilofacial"),
            ("Dra. Mishel Guamán", "Endodoncia"),
            ("Dra. Daysi Amores", "Odontología general"),
            ("Dra. Karen Iza", "Odontología general"),
            ("Dr. Wilson Moya", "Rehabilitación oral"),
        ]
        for nombre, especialidad in equipo:
            Especialista.objects.update_or_create(nombre_completo=nombre, defaults={"especialidad": especialidad, "activo": True})

        Especialista.objects.filter(nombre_completo="Dr. Santiago Romero", activo=True).update(activo=False)

        catalogo = [(procedimiento, grupo["nombre"]) for grupo in GRUPOS_TRATAMIENTOS for procedimiento in grupo["procedimientos"]]
        pares_catalogo = set(catalogo)
        for existente in Tratamiento.objects.filter(activo=True).iterator():
            if (existente.nombre, existente.area) not in pares_catalogo:
                existente.activo = False
                existente.save(update_fields=["activo"])
        for nombre, area in catalogo:
            tratamiento, creado = Tratamiento.objects.get_or_create(
                nombre=nombre,
                area=area,
                defaults={"area": area, "activo": True, "duracion_minutos": None},
            )
            cambios = []
            if tratamiento.area != area:
                tratamiento.area = area
                cambios.append("area")
            if not tratamiento.activo:
                tratamiento.activo = True
                cambios.append("activo")
            if cambios:
                tratamiento.save(update_fields=cambios)
        self.stdout.write(self.style.SUCCESS(f"Catálogo cargado: {len(equipo)} especialistas y {len(catalogo)} tratamientos; categorías y nombres siguen el catálogo oficial. No se cargaron precios ni horarios individuales."))
