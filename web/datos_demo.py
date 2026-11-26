"""Datos usados como respaldo mientras se aplica la migración de VitaDent."""

ESPECIALISTAS = [
    {"nombre": "Dra. Verónica Martínez", "especialidad": "Rehabilitación oral y ortodoncia", "iniciales": "VM", "tono": "lime"},
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

# Orientación general; cada plan se determina tras la valoración clínica.
DESCRIPCIONES_PROCEDIMIENTOS = {
    "Panorámica": "Una toma extraoral muestra ambos maxilares y dientes en una sola imagen para apoyar la valoración general.",
    "Periapical": "Una imagen localizada permite observar el diente completo y la zona que rodea su raíz.",
    "Lateral de cráneo": "La imagen lateral del cráneo ayuda a analizar relaciones óseas y dentales durante la planificación.",
    "Carpal": "Una imagen de la mano y muñeca puede aportar información sobre maduración ósea cuando está indicada.",
    "Diagnóstico general": "El profesional revisa antecedentes, dientes y encías; puede solicitar estudios adicionales antes de proponer un plan.",
    "Limpieza dental": "Se retiran depósitos de placa y cálculo y se pulen las superficies según la valoración periodontal.",
    "Extracciones": "Tras valorar la pieza y aplicar anestesia local cuando corresponde, se retira el diente y se indican cuidados posteriores.",
    "Sellantes": "Se limpia la superficie masticatoria y se coloca un material protector sobre sus surcos.",
    "Diagnóstico y plan de tratamiento de cirugía ortognática": "Se analizan la mordida, el rostro y las imágenes para coordinar el plan entre ortodoncia y cirugía.",
    "Brackets convencionales": "Se fijan brackets a los dientes y se conectan con arcos que se ajustan durante los controles.",
    "Brackets de autoligado": "Los brackets sujetan el arco mediante un mecanismo integrado; el profesional programa los ajustes.",
    "Brackets linguales": "Los dispositivos se colocan en la cara interna de los dientes y se revisan periódicamente.",
    "Invisalign": "Se planifica el movimiento dental y se usan alineadores removibles en una secuencia supervisada.",
    "Ortopedia": "Se valoran crecimiento y mordida para indicar aparatos que orienten el desarrollo cuando corresponde.",
    "Técnica 4x2": "Se colocan brackets en cuatro incisivos y bandas o tubos en dos molares para movimientos seleccionados.",
    "Muelas del juicio": "Se evalúa la posición con imágenes y se planifica la extracción cuando existe indicación clínica.",
    "Frenectomías": "Se modifica el frenillo labial o lingual tras valorar su efecto funcional o periodontal.",
    "Bichectomías": "Se evalúa la indicación y, si procede, se retira parte de la grasa bucal mediante un abordaje interno.",
    "Lipopapada": "Se valora la zona submentoniana y la técnica apropiada antes de realizar el procedimiento.",
    "Cirugías orales de alta complejidad": "El cirujano estudia el caso con imágenes y planifica el abordaje, anestesia y seguimiento.",
    "Blanqueamiento dental": "Se evalúa la salud bucal y se aplica un agente blanqueador con protección de tejidos según la técnica indicada.",
    "Diseño de sonrisa": "Se analizan forma, color y posición dental para elaborar un plan individual de mejora estética.",
    "Prótesis total": "Se toman registros de la boca para fabricar y ajustar una prótesis que sustituya todos los dientes de una arcada.",
    "Prótesis removible": "Se registran los tejidos y se fabrica una prótesis que el paciente puede retirar para higiene.",
    "Prótesis fijas": "Se preparan los apoyos indicados, se toman registros y se coloca una restauración fija ajustada.",
    "Aparatos ortopédicos": "Se valora el crecimiento del niño y se adapta un aparato para guiar la relación de los maxilares.",
    "Endodoncias": "Se limpia y sella el interior del diente afectado para conservarlo cuando es posible.",
    "Brackets para niños": "Se evalúa la dentición en desarrollo antes de decidir si un tratamiento ortodóntico temprano está indicado.",
    "Limpiezas": "Se retiran depósitos y se refuerzan hábitos de higiene adaptados a la edad del niño.",
    "Calzas": "Se retira el tejido afectado por caries y se reconstruye la forma del diente con material restaurador.",
    "Alivio del dolor": "Se identifica la causa del dolor y se indica la intervención apropiada tras la valoración.",
    "Apicectomías": "Se accede a la punta de la raíz y se trata la zona cuando el caso requiere cirugía endodóntica.",
    "Pernos": "Tras evaluar la estructura remanente, se coloca un soporte intrarradicular cuando la restauración lo requiere.",
    "Implantes unitarios": "Se planifica la posición y se coloca un implante que servirá de soporte para una corona posterior.",
    "Prótesis sobre implantes": "Se registran los implantes y se fabrica una prótesis que se ajusta a sus conexiones.",
    "Regeneraciones óseas": "Se evalúa el defecto óseo y se aplica una técnica de regeneración antes o durante la rehabilitación.",
    "Injertos": "Se planifica el aumento de tejido necesario y se coloca un injerto según la valoración del sitio.",
}
