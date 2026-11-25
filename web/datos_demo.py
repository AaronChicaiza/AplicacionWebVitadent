"""Datos usados como respaldo mientras se aplica la migración de VitaDent."""

ESPECIALISTAS = [
    {"nombre": "Dra. Verónica Martínez", "especialidad": "Rehabilitación oral y ortodoncia", "iniciales": "VM", "tono": "lime"},
    {"nombre": "Dr. Santiago Romero", "especialidad": "Implantología", "iniciales": "SR", "tono": "blue"},
    {"nombre": "Dra. Daniela Delgado", "especialidad": "Ortodoncia", "iniciales": "DD", "tono": "dark"},
    {"nombre": "Dra. Odalis Monar", "especialidad": "Ortodoncia", "iniciales": "OM", "tono": "rose"},
    {"nombre": "Dra. Karen Iza", "especialidad": "Odontología general", "iniciales": "KI", "tono": "orange"},
    {"nombre": "Dra. Mishel Guamán", "especialidad": "Endodoncia", "iniciales": "MG", "tono": "purple"},
    {"nombre": "Dr. Adrián Quinatoa", "especialidad": "Cirugía maxilofacial", "iniciales": "AQ", "tono": "red"},
    {"nombre": "Dr. Wilson Moya", "especialidad": "Rehabilitación oral", "iniciales": "WM", "tono": "cyan"},
    {"nombre": "Dra. Daysi Amores", "especialidad": "Odontología general", "iniciales": "DA", "tono": "blue"},
]

GRUPOS_TRATAMIENTOS = [
    {"nombre": "Rayos-X", "id": "rayos-x", "imagen": "vendor/pearl/img/case-3-before.jpg", "alt": "Imagen ilustrativa de un especialista revisando radiografías odontológicas", "procedimientos": ["Panorámica", "Periapical", "Lateral de cráneo", "Carpal"]},
    {"nombre": "Odontología general", "id": "odontologia-general", "imagen": "vendor/pearl/img/case-3-after.jpg", "alt": "Imagen ilustrativa de elementos para higiene dental", "procedimientos": ["Diagnóstico general", "Limpieza dental", "Extracciones", "Sellantes"]},
    {"nombre": "Ortodoncia", "id": "ortodoncia", "imagen": "vendor/pearl/img/case-2-after.jpg", "alt": "Imagen ilustrativa de tratamiento de ortodoncia", "procedimientos": ["Diagnóstico y plan de tratamiento de cirugía ortognática", "Brackets convencionales", "Brackets de autoligado", "Brackets linguales", "Invisalign", "Ortopedia", "Técnica 4x2"]},
    {"nombre": "Cirugía maxilofacial", "id": "cirugia-maxilofacial", "imagen": "vendor/pearl/img/case-2-before.jpg", "alt": "Imagen ilustrativa de un procedimiento odontológico", "procedimientos": ["Muelas del juicio", "Frenectomías", "Bichectomías", "Lipopapada", "Cirugías orales de alta complejidad"]},
    {"nombre": "Rehabilitación oral", "id": "rehabilitacion-oral", "imagen": "vendor/pearl/img/dentist-3.jpg", "alt": "Imagen ilustrativa de una sonrisa", "procedimientos": ["Blanqueamiento dental", "Diseño de sonrisa", "Prótesis total", "Prótesis removible", "Prótesis fijas"]},
    {"nombre": "Odontopediatría", "id": "odontopediatria", "imagen": "vendor/pearl/img/treat-kids.jpg", "alt": "Imagen ilustrativa de un espacio de atención odontológica infantil", "procedimientos": ["Aparatos ortopédicos", "Endodoncias", "Brackets para niños", "Limpiezas", "Calzas", "Extracciones"]},
    {"nombre": "Endodoncia", "id": "endodoncia", "imagen": "vendor/pearl/img/treat-emergency.jpg", "alt": "Imagen ilustrativa de un consultorio para atención dental", "procedimientos": ["Alivio del dolor", "Apicectomías", "Pernos"]},
    {"nombre": "Implantología", "id": "implantologia", "imagen": "vendor/pearl/img/treat-implants.jpg", "alt": "Imagen ilustrativa de consulta sobre implantes dentales", "procedimientos": ["Implantes unitarios", "Prótesis sobre implantes", "Regeneraciones óseas", "Injertos"]},
]

ORDEN_AREAS_TRATAMIENTO = [grupo["nombre"] for grupo in GRUPOS_TRATAMIENTOS]
ORDEN_PARES_TRATAMIENTO = [
    (procedimiento, grupo["nombre"])
    for grupo in GRUPOS_TRATAMIENTOS
    for procedimiento in grupo["procedimientos"]
]


def ordenar_catalogo_tratamientos(tratamientos):
    orden = {par: indice for indice, par in enumerate(ORDEN_PARES_TRATAMIENTO)}
    return sorted(list(tratamientos), key=lambda item: (orden.get((item.nombre, item.area), len(orden)), item.area.casefold(), item.nombre.casefold()))
