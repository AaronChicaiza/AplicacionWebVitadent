from django.core.management.base import BaseCommand

from web.models import Especialista, Tratamiento


class Command(BaseCommand):
    help = "Carga el equipo y los tiempos de atención que constan en el manual VitaDent, sin precios."

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
            ("Dr. Santiago Romero", "Implantología"),
        ]
        for nombre, especialidad in equipo:
            Especialista.objects.update_or_create(nombre_completo=nombre, defaults={"especialidad": especialidad, "activo": True})

        catalogo = [
            ("Tratamiento en niños", "Odontología infantil", 60),
            ("Diagnóstico general", "Odontología general", 60),
            ("Diagnóstico de especialidad", "Especialidades", 60),
            ("Diagnóstico de ortodoncia", "Ortodoncia", 60),
            ("Profilaxis", "Odontología general", 30),
            ("Sellantes / restauraciones (1–2)", "Odontología infantil", 30),
            ("Sellantes / restauraciones (3–5)", "Odontología infantil", 60),
            ("Restauraciones (5–7)", "Odontología general", 90),
            ("Reconstrucción", "Rehabilitación oral", 60),
            ("Exodoncia (1–2)", "Cirugía oral", 60),
            ("Dolor de muela (alivio del dolor o exodoncia)", "Odontología general", 60),
            ("Blanqueamiento", "Odontología general", 60),
            ("Dos terceros molares superiores", "Cirugía oral", 60),
            ("Cuatro terceros molares", "Cirugía oral", 120),
            ("Control", "Odontología general", 30),
            ("Colocación", "Ortodoncia", 60),
            ("Retiro de brackets + profilaxis", "Ortodoncia", 60),
        ]
        for nombre, area, duracion in catalogo:
            Tratamiento.objects.update_or_create(nombre=nombre, defaults={"area": area, "duracion_minutos": duracion, "activo": True})
        self.stdout.write(self.style.SUCCESS(f"Catálogo cargado: {len(equipo)} especialistas y {len(catalogo)} tratamientos. No se cargaron precios ni horarios individuales."))
