# Alcance del prototipo frontend

Este archivo traduce el texto de requisitos del sistema a las pantallas de esta fase. Indica lo que representa la interfaz y lo que aún necesita backend; no afirma que esas funciones ya estén conectadas.

## Pantallas incluidas

| Requisito | Vista en el prototipo | Estado |
| --- | --- | --- |
| Sitio público, catálogo y equipo | Inicio, tratamientos y especialistas | Maqueta navegable con información del manual |
| Solicitar cita por conversación | Chatbot en `/citas/` | Interfaz de demostración; sin conexión a Rasa |
| Contacto por WhatsApp | Contacto señalado como pendiente | Falta el número oficial; no es un canal para agendar en esta propuesta |
| Acceso administrativo | `/acceso/` y panel `/gestion/` | Pantalla y panel visual; autenticación desactivada |
| Acceso de cada especialista | `/acceso/` y portal `/doctor/` | Vista profesional ficticia; sin credenciales ni permisos reales |
| Pacientes | Directorio administrativo y lista profesional | Solo filas ficticias; el filtro por asignación requiere autorización del servidor |
| Reservas, cancelación y reprogramación | Solicitudes, estados y acciones de ejemplo | Controles desactivados; faltan reglas de negocio y persistencia |
| Disponibilidad | Agenda y horarios | Horario general del manual; falta disponibilidad individual por especialista |
| Notificaciones | `/gestion/notificaciones/` | Estado vacío ilustrativo |
| Auditoría | `/gestion/auditoria/` | Estado vacío ilustrativo |

## Chatbot Rasa previsto

La pantalla permite probar visualmente categorías para reservar, consultar disponibilidad, confirmar, cancelar o reprogramar, consultar tratamientos/especialistas y pedir atención humana. Saludo, despedida y mensajes fuera de alcance se escribirán como mensajes libres. La interfaz explica que el flujo debe pedir solo los datos faltantes, conservar el contexto, permitir correcciones, presentar un resumen para confirmación y derivar casos ambiguos a recepción.

Las entidades previstas por el requisito son nombre, identificación, teléfono, correo, tratamiento, especialista, fecha, hora, sucursal y código de cita. No se solicitan datos reales en esta maqueta. Rasa aún no interpreta mensajes: las respuestas locales son demostrativas.

## Controles que requieren backend

Autenticación individual, roles y autorización por objeto; protección contra IDOR; validación de servidor; CSRF, XSS y encabezados seguros; almacenamiento, auditoría, límites con Redis; reglas de disponibilidad y transacciones contra doble reserva; API/documentación; notificaciones; entrenamiento e integración real de Rasa. La validación o el filtrado visual nunca sustituye estos controles.

## Información pendiente de la clínica

Número oficial de WhatsApp, dirección/sucursal, correo, calendario por especialista, reglas de cancelación/reprogramación, duración y políticas de reserva, y fotos institucionales. El manual contiene horarios generales y duraciones orientativas; no confirma turnos disponibles.
