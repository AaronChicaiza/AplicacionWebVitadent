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
    {"nombre": "Rayos-X", "procedimientos": ["Panorámica", "Periapical", "Lateral de cráneo", "Carpal"]},
    {"nombre": "Odontología general", "procedimientos": ["Diagnóstico general", "Limpieza dental", "Extracciones generales", "Sellantes"]},
    {"nombre": "Ortodoncia", "procedimientos": ["Diagnóstico y plan de tratamiento de cirugía ortognática", "Brackets convencionales", "Brackets de autoligado", "Brackets linguales", "Invisalign", "Ortopedia", "Técnica 4x2"]},
    {"nombre": "Cirugía maxilofacial", "procedimientos": ["Muelas del juicio", "Frenectomías", "Bichectomías", "Lipopapada", "Cirugías orales de alta complejidad"]},
    {"nombre": "Rehabilitación oral", "procedimientos": ["Blanqueamiento dental", "Diseño de sonrisa", "Prótesis total", "Prótesis removible", "Prótesis fijas"]},
    {"nombre": "Odontopediatría", "procedimientos": ["Aparatos ortopédicos", "Endodoncias", "Brackets para niños", "Limpiezas", "Calzas", "Extracciones infantiles"]},
    {"nombre": "Endodoncia", "procedimientos": ["Alivio del dolor", "Apicectomías", "Pernos"]},
    {"nombre": "Implantología", "procedimientos": ["Implantes unitarios", "Prótesis sobre implantes", "Regeneraciones óseas", "Injertos"]},
]

ORDEN_AREAS_TRATAMIENTO = [grupo["nombre"] for grupo in GRUPOS_TRATAMIENTOS]
