from django.core.management.base import BaseCommand

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
            ("Dr. Santiago Romero", "Implantología"),
        ]
        for nombre, especialidad in equipo:
            Especialista.objects.update_or_create(nombre_completo=nombre, defaults={"especialidad": especialidad, "activo": True})

        catalogo = [
            ("Panorámica", "Rayos-X"), ("Periapical", "Rayos-X"),
            ("Lateral de cráneo", "Rayos-X"), ("Carpal", "Rayos-X"),
            ("Diagnóstico general", "Odontología general"), ("Limpieza dental", "Odontología general"),
            ("Extracciones generales", "Odontología general"), ("Sellantes", "Odontología general"),
            ("Diagnóstico y plan de tratamiento de cirugía ortognática", "Ortodoncia"),
            ("Brackets convencionales", "Ortodoncia"), ("Brackets de autoligado", "Ortodoncia"),
            ("Brackets linguales", "Ortodoncia"), ("Invisalign", "Ortodoncia"),
            ("Ortopedia", "Ortodoncia"), ("Técnica 4x2", "Ortodoncia"),
            ("Muelas del juicio", "Cirugía maxilofacial"), ("Frenectomías", "Cirugía maxilofacial"),
            ("Bichectomías", "Cirugía maxilofacial"), ("Lipopapada", "Cirugía maxilofacial"),
            ("Cirugías orales de alta complejidad", "Cirugía maxilofacial"),
            ("Blanqueamiento dental", "Rehabilitación oral"), ("Diseño de sonrisa", "Rehabilitación oral"),
            ("Prótesis total", "Rehabilitación oral"), ("Prótesis removible", "Rehabilitación oral"),
            ("Prótesis fijas", "Rehabilitación oral"),
            ("Aparatos ortopédicos", "Odontopediatría"), ("Endodoncias", "Odontopediatría"),
            ("Brackets para niños", "Odontopediatría"), ("Limpiezas", "Odontopediatría"),
            ("Calzas", "Odontopediatría"), ("Extracciones infantiles", "Odontopediatría"),
            ("Alivio del dolor", "Endodoncia"), ("Apicectomías", "Endodoncia"),
            ("Pernos", "Endodoncia"),
            ("Implantes unitarios", "Implantología"), ("Prótesis sobre implantes", "Implantología"),
            ("Regeneraciones óseas", "Implantología"), ("Injertos", "Implantología"),
        ]
        nombres_activos = [nombre for nombre, _area in catalogo]
        Tratamiento.objects.exclude(nombre__in=nombres_activos).update(activo=False)
        for nombre, area in catalogo:
            tratamiento, creado = Tratamiento.objects.get_or_create(
                nombre=nombre,
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
        self.stdout.write(self.style.SUCCESS(f"Catálogo cargado: {len(equipo)} especialistas y {len(catalogo)} tratamientos; los tiempos siguen editables desde el panel. No se cargaron precios ni horarios individuales."))
