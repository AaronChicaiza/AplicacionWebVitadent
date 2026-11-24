# VitaDent

Aplicación web Django en español para el sitio público y la gestión odontológica. Usa plantillas Django, la plantilla Pearl para el sitio público y SRTdash para gestión. No utiliza React ni Vite.

## Flujo del paciente

- El paciente no crea una cuenta. Desde el sitio público pasa al WhatsApp oficial de VitaDent.
- Meta WhatsApp Cloud API recibe el mensaje en el webhook firmado y lo entrega al asistente Rasa.
- Rasa interpreta la intención y el contexto con DIETClassifier. Las acciones solicitan al API interno de Django catálogos, disponibilidad, registro, consulta, cancelación y reprogramación.
- Django valida los datos, aplica las reglas de negocio y guarda pacientes, citas, mensajes y auditoría. Las solicitudes de cita quedan en estado **Solicitada** para revisión y confirmación de recepción; no se presentan como una cita confirmada.
- Administración puede revisar y responder conversaciones desde Gestión → WhatsApp. La respuesta manual requiere las credenciales de Meta y está sujeta a las ventanas y políticas de mensajería de WhatsApp.
- El sistema no ofrece diagnósticos ni recomendaciones clínicas automatizadas.

## Roles y seguridad

- Administración gestiona solicitudes, catálogo, especialistas, horarios, pacientes, conversaciones y auditoría.
- Las secciones de gestión usan DataTables en español para buscar, ordenar y paginar. Los catálogos incluyen exportación; pacientes y citas no se exportan para proteger datos personales. Crear, editar y eliminar se hace dentro del panel, con formularios modales y confirmación.
- Los registros relacionados con citas o historial se desactivan o se conservan en vez de borrarse físicamente.
- Cada especialista inicia sesión con su cuenta propia y ve solo las citas asignadas a su perfil.
- Django valida campos y catálogos en servidor; usa ORM parametrizado, protección CSRF en formularios, Argon2 para contraseñas, limitación de solicitudes, permisos por rol y registros de auditoría.
- El webhook comprueba la firma SHA-256 de Meta. Las rutas internas de Rasa exigen `VITADENT_RASA_TOKEN`.
- Mensajes y conversaciones pueden purgarse con `python manage.py purgar_conversaciones`; la retención predeterminada está configurada en 30 días.

## Ejecutar Django localmente

1. Crea un entorno virtual: `py -m venv .venv` y actívalo con `.venv\\Scripts\\Activate.ps1`.
2. Instala paquetes: `pip install -r requirements.txt`.
3. Copia `.env.example` a `.env` y conserva `DJANGO_DEBUG=True` para desarrollo.
4. Aplica la base y carga el catálogo: `python manage.py migrate` y `python manage.py cargar_catalogo_vitadent`.
5. Crea o usa una cuenta autorizada de administración: `python manage.py createsuperuser`.
6. Inicia Django con `python manage.py runserver` y abre `http://127.0.0.1:8000/`.

La base local usa SQLite. Para habilitar una cuenta de especialista, vincula su usuario con su perfil en Django Admin y configura sus horarios antes de confirmar solicitudes.

## WhatsApp y Rasa

Las variables necesarias están enumeradas en `.env.example`: número público, token de verificación, secreto de aplicación, token de acceso, identificador del número y token interno Rasa. El webhook que se registra en Meta es `https://<dominio-publico>/api/whatsapp/webhook/`; requiere HTTPS y la configuración de la aplicación y número empresarial de VitaDent.

Rasa 3.6 y sus acciones corren en Python 3.10, separado del Django en Python 3.12. Para levantar el stack contenerizado con PostgreSQL y Redis, inicia Docker Desktop y ejecuta `docker compose up --build`. Compose expone Django solo en `127.0.0.1:8000`; Rasa, acciones, Redis y PostgreSQL permanecen en la red privada del proyecto.

## Configuración antes de producción

Configura una `DJANGO_SECRET_KEY` aleatoria de al menos 50 caracteres, `DJANGO_DEBUG=False`, hosts permitidos, credenciales únicas de PostgreSQL, Redis privado, HTTPS y secretos de Meta/Rasa. No publiques `.env`, la base de datos, claves ni datos de pacientes. La recepción debe aportar horarios reales, sucursales y políticas de confirmación/cancelación. Las solicitudes requieren revisión de disponibilidad por el personal; todavía no hay conexión con un proveedor de correo ni recordatorios programados.

## Verificación del proyecto

- Pruebas: `python -m pytest web/tests -q`.
- Revisar configuración Django: `python manage.py check`.
- Verificar esquema API: `python manage.py spectacular --validate --file NUL` (Windows).
- Verificar Compose: `docker compose config --quiet`.

Las pruebas locales cubren el rechazo de solicitudes internas sin token, firmas Meta, validación de campos, privacidad de citas por especialista y acceso del personal a la bandeja de WhatsApp. El modelo DIETClassifier necesita datos de entrenamiento anotados y evaluación antes de usarse en operación.
