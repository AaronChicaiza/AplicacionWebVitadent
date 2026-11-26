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

# Texto informativo para pacientes. La indicación concreta siempre depende de la valoración clínica.
PROPOSITOS_PROCEDIMIENTOS = {
    "Panorámica": "Ofrece una vista conjunta de dientes y maxilares para orientar el diagnóstico y la planificación.",
    "Periapical": "Ayuda a examinar una pieza dental, su raíz y el hueso cercano.",
    "Lateral de cráneo": "Apoya el análisis de la relación entre los maxilares, especialmente al planificar ortodoncia.",
    "Carpal": "Puede ayudar a valorar la etapa de crecimiento óseo en determinados planes de ortodoncia.",
    "Diagnóstico general": "Permite reconocer necesidades de atención y decidir si hacen falta otros estudios.",
    "Limpieza dental": "Ayuda a controlar los depósitos que favorecen problemas de encías y dientes.",
    "Extracciones": "Permite retirar una pieza cuando conservarla no es viable o existe otra indicación clínica.",
    "Sellantes": "Protege los surcos de las muelas para reducir el riesgo de caries.",
    "Diagnóstico y plan de tratamiento de cirugía ortognática": "Permite coordinar la corrección de problemas de posición de los maxilares.",
    "Brackets convencionales": "Mueven los dientes de forma progresiva para mejorar su alineación y la mordida.",
    "Brackets de autoligado": "Permiten guiar movimientos dentales mediante arcos sujetos por el propio bracket.",
    "Brackets linguales": "Corrigen la posición dental con aparatos colocados detrás de los dientes.",
    "Invisalign": "Busca alinear los dientes mediante alineadores transparentes y removibles, si el caso lo permite.",
    "Ortopedia": "Orienta el crecimiento de los maxilares cuando el paciente aún está en desarrollo.",
    "Técnica 4x2": "Permite realizar movimientos dentales tempranos en casos seleccionados.",
    "Muelas del juicio": "Resuelve problemas asociados a terceros molares cuando se indica su extracción.",
    "Frenectomías": "Busca mejorar una limitación funcional o una condición de los tejidos causada por el frenillo.",
    "Bichectomías": "Modifica el volumen de la zona de las mejillas cuando la evaluación justifica el procedimiento.",
    "Lipopapada": "Busca reducir tejido graso bajo el mentón tras una valoración individual.",
    "Cirugías orales de alta complejidad": "Atiende problemas que requieren un abordaje quirúrgico planificado y seguimiento.",
    "Blanqueamiento dental": "Busca aclarar el color de los dientes naturales con supervisión profesional.",
    "Diseño de sonrisa": "Permite planificar cambios estéticos de acuerdo con la boca y las expectativas del paciente.",
    "Prótesis total": "Sustituye los dientes ausentes de una arcada y ayuda a recuperar funciones orales.",
    "Prótesis removible": "Reemplaza dientes ausentes con una estructura que puede retirarse para su limpieza.",
    "Prótesis fijas": "Reemplazan o restauran dientes con una estructura que permanece colocada en boca.",
    "Aparatos ortopédicos": "Ayudan a orientar el crecimiento maxilar en niños cuando el profesional lo indica.",
    "Endodoncias": "Busca conservar un diente infantil afectado cuando su estado lo permite.",
    "Brackets para niños": "Ayudan a corregir problemas de posición dental durante el desarrollo, si se indican.",
    "Limpiezas": "Ayudan a mantener dientes y encías saludables durante la infancia.",
    "Calzas": "Restauran dientes dañados por caries para recuperar su forma y función.",
    "Alivio del dolor": "Busca tratar la causa del dolor dental, no solo el síntoma.",
    "Apicectomías": "Puede ayudar a conservar un diente cuando persiste un problema en el extremo de la raíz.",
    "Pernos": "Pueden dar soporte a una reconstrucción cuando queda poca estructura dental.",
    "Implantes unitarios": "Sustituyen la raíz de un diente perdido y sirven de apoyo para una corona.",
    "Prótesis sobre implantes": "Reemplazan dientes ausentes con apoyo en implantes previamente colocados.",
    "Regeneraciones óseas": "Buscan recuperar volumen de hueso necesario para una rehabilitación planificada.",
    "Injertos": "Aportan tejido en zonas donde se necesita mejorar el soporte para el tratamiento.",
}

FUENTES_AREAS = {
    "rayos-x": [("Asociación Dental Americana: radiografías dentales", "https://www.mouthhealthy.org/all-topics-a-z/x-rays/")],
    "odontologia-general": [("Asociación Dental Americana: sellantes", "https://www.mouthhealthy.org/all-topics-a-z/sealants")],
    "ortodoncia": [("Asociación Americana de Ortodoncistas: brackets", "https://aaoinfo.org/treatments/braces/"), ("Alineadores", "https://aaoinfo.org/treatments/aligners/")],
    "cirugia-maxilofacial": [("Asociación Americana de Ortodoncistas: cirugía ortognática", "https://aaoinfo.org/treatments/orthodontic-surgery/")],
    "rehabilitacion-oral": [("Asociación Dental Americana: prótesis dentales", "https://www.mouthhealthy.org/all-topics-a-z/dentures")],
    "odontopediatria": [("Asociación Americana de Ortodoncistas: atención infantil", "https://aaoinfo.org/child-orthodontics/")],
    "endodoncia": [("Asociación Americana de Endodoncistas: tratamiento de conducto", "https://www.aae.org/patients/root-canal-treatment/what-is-a-root-canal/root-canal-explained/"), ("Cirugía endodóntica", "https://www.aae.org/patients/root-canal-treatment/endodontic-treatment-options/endodontic-surgery/endodontic-surgery-explained/")],
    "implantologia": [("Asociación Americana de Endodoncistas: opciones de tratamiento", "https://www.aae.org/patients/root-canal-treatment/endodontic-treatment-options/dental-implants/treatment-options-diseased-tooth/")],
}
