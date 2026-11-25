from django.db import migrations, models


CATALOGO = [
    ("Panorámica", "Rayos-X"), ("Periapical", "Rayos-X"), ("Lateral de cráneo", "Rayos-X"), ("Carpal", "Rayos-X"),
    ("Diagnóstico general", "Odontología general"), ("Limpieza dental", "Odontología general"), ("Extracciones", "Odontología general"), ("Sellantes", "Odontología general"),
    ("Diagnóstico y plan de tratamiento de cirugía ortognática", "Ortodoncia"), ("Brackets convencionales", "Ortodoncia"), ("Brackets de autoligado", "Ortodoncia"), ("Brackets linguales", "Ortodoncia"), ("Invisalign", "Ortodoncia"), ("Ortopedia", "Ortodoncia"), ("Técnica 4x2", "Ortodoncia"),
    ("Muelas del juicio", "Cirugía maxilofacial"), ("Frenectomías", "Cirugía maxilofacial"), ("Bichectomías", "Cirugía maxilofacial"), ("Lipopapada", "Cirugía maxilofacial"), ("Cirugías orales de alta complejidad", "Cirugía maxilofacial"),
    ("Blanqueamiento dental", "Rehabilitación oral"), ("Diseño de sonrisa", "Rehabilitación oral"), ("Prótesis total", "Rehabilitación oral"), ("Prótesis removible", "Rehabilitación oral"), ("Prótesis fijas", "Rehabilitación oral"),
    ("Aparatos ortopédicos", "Odontopediatría"), ("Endodoncias", "Odontopediatría"), ("Brackets para niños", "Odontopediatría"), ("Limpiezas", "Odontopediatría"), ("Calzas", "Odontopediatría"), ("Extracciones", "Odontopediatría"),
    ("Alivio del dolor", "Endodoncia"), ("Apicectomías", "Endodoncia"), ("Pernos", "Endodoncia"),
    ("Implantes unitarios", "Implantología"), ("Prótesis sobre implantes", "Implantología"), ("Regeneraciones óseas", "Implantología"), ("Injertos", "Implantología"),
]


def normalizar_catalogo(apps, schema_editor):
    Tratamiento = apps.get_model("web", "Tratamiento")
    Tratamiento.objects.filter(nombre="Extracciones generales", area="Odontología general").update(nombre="Extracciones")
    Tratamiento.objects.filter(nombre="Extracciones infantiles", area="Odontopediatría").update(nombre="Extracciones")

    pares = set(CATALOGO)
    for tratamiento in Tratamiento.objects.filter(activo=True).iterator():
        if (tratamiento.nombre, tratamiento.area) not in pares:
            tratamiento.activo = False
            tratamiento.save(update_fields=["activo"])

    for nombre, area in CATALOGO:
        tratamiento, creado = Tratamiento.objects.get_or_create(
            nombre=nombre,
            area=area,
            defaults={"activo": True, "duracion_minutos": None},
        )
        if not tratamiento.activo:
            tratamiento.activo = True
            tratamiento.save(update_fields=["activo"])


class Migration(migrations.Migration):
    dependencies = [("web", "0010_vitadent_catalog_duration_rules")]

    operations = [
        migrations.AlterField(
            model_name="tratamiento",
            name="nombre",
            field=models.CharField(max_length=140),
        ),
        migrations.RunPython(normalizar_catalogo, migrations.RunPython.noop),
        migrations.AddConstraint(
            model_name="tratamiento",
            constraint=models.UniqueConstraint(fields=("nombre", "area"), name="tratamiento_nombre_area_unico"),
        ),
    ]
