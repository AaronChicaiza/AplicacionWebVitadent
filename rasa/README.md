# Servicio conversacional Rasa

Esta carpeta contiene la configuración inicial de Rasa Open Source con DIETClassifier, ejemplos iniciales de intenciones, formulario de reserva y acciones que envían una solicitud validada a Django.

## Estado auditado

Django recibe el webhook de Meta, verifica `X-Hub-Signature-256`, deduplica mensajes por ID del proveedor, aplica límites de solicitudes y envía texto a Rasa REST. Rasa mantiene el diálogo en Redis y llama al servidor de acciones. Django protege las operaciones de cita con `VITADENT_RASA_TOKEN`, valida la identidad y los catálogos, serializa reservas concurrentes y deja las solicitudes en estado pendiente hasta que recepción las confirme.

Se mantuvo DIETClassifier. Las acciones de catálogo y disponibilidad ahora también consultan endpoints internos autenticados; el API público de lectura sigue disponible para las páginas públicas. La consulta de estado tiene una intención propia y una corrección durante la reserva conserva los demás campos.

El corpus de `data/nlu.yml` es inicial. No hay 300 mensajes anotados en `evaluacion/corpus.csv`, así que no se publican métricas de calidad ni de latencia. `Tesis_VITADENT_mejorada.docx` se revisó como copia relacionada; no se encontró la versión exacta `Tesis_VITADENT_revisada_FINAL_v3.2` ni la guía PDF indicada.

## Componentes

- `config.yml`: pipeline de texto español, extracción de entidades y DIETClassifier.
- `domain.yml`, `data/nlu.yml` y `data/rules.yml`: intenciones, slots y flujo inicial.
- `actions/actions.py`: consultas de catálogo y disponibilidad autenticadas, revisión del resumen y operaciones de cita mediante la API interna.
- `endpoints.yml`: servidor de acciones y almacén Redis del tracker.
- `evaluacion/corpus.csv`: plantilla vacía para el corpus anotado; no contiene frases de prueba inventadas.
- `evaluacion/evaluar_nlu.py`: cálculo reproducible de métricas NLU y p95 cuando se complete el corpus y se entrene el modelo.

## Flujo

```text
WhatsApp Cloud API → webhook Django firmado → Rasa REST → action server
                    → endpoints Django internos con token → PostgreSQL
                    ← estado/resultado validado ← Rasa ← respuesta WhatsApp
```

Django sigue siendo la autoridad para identidad, horarios, catálogo, disponibilidad, transacciones y estado de cita. Ninguna respuesta del bot debe llamar confirmada a una reserva hasta que el personal la confirme.

## Configuración y ejecución local

1. Configura en el `.env` del proyecto `DJANGO_SECRET_KEY`, `POSTGRES_PASSWORD`, `VITADENT_RASA_TOKEN`, `REDIS_URL` y credenciales oficiales de WhatsApp. Para pruebas, usa valores exclusivos de desarrollo. No guardes `.env` en Git.
2. Con Docker disponible, inicia los componentes:

   ```powershell
   docker compose up --build
   ```

   Compose entrena el modelo Rasa y arranca Django, PostgreSQL, Redis y las acciones. El webhook público necesita URL HTTPS de Meta y credenciales válidas para recibir mensajes reales.
3. Para ejecutar y validar Rasa fuera de Compose, usa el Python compatible con la versión fijada (3.10):

   ```powershell
   cd rasa
   pip install -r actions/requirements.txt rasa==3.6.21
   $env:REDIS_HOST = '127.0.0.1'
   $env:REDIS_PORT = '6379'
   $env:REDIS_PASSWORD = ''
   $env:VITADENT_RASA_TOKEN = '<secreto-local-compartido-con-Django>'
   $env:VITADENT_DJANGO_INTERNAL_URL = 'http://127.0.0.1:8000'
   rasa data validate --domain domain.yml --data data --config config.yml
   rasa train
   rasa run actions --actions actions --port 5055
   rasa run --enable-api --credentials credentials.yml --endpoints endpoints.yml --port 5005 --host 127.0.0.1
   ```

   Ejecuta el servidor de acciones y Rasa en terminales separadas. Django debe tener el mismo token interno y `VITADENT_RASA_URL=http://127.0.0.1:5005`. En Docker, se usan los nombres de servicio configurados en Compose.

## Conversar con el bot desde VS Code en Windows

`rasa shell` abre una conversación en la terminal integrada. Este proyecto fija Rasa 3.6.21 y el Dockerfile usa Python 3.10; el Python 3.14 instalado en algunos equipos no sirve para ese entorno. Rasa 3.x documenta soporte hasta Python 3.10, pero Python 3.10 llegó al fin de soporte de seguridad el 1 de octubre de 2026. Usa este runtime aislado solo para una prueba local y no expongas el servidor a Internet ni lo despliegues así. Instala Python 3.10 desde python.org y confirma que el launcher lo detecte con `py -3.10 --version`.

En una copia limpia también prepara el entorno Django que usa la primera tarea de VS Code:

```powershell
py -3.10 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
$env:DJANGO_DATABASE_ENGINE = 'sqlite'
$env:SQLITE_NAME = Join-Path (Get-Location).Path 'rasa\vitadent_vscode.sqlite3'
python manage.py migrate
deactivate
```

Luego, desde la raíz del proyecto, crea el entorno Rasa e instala las versiones fijadas:

```powershell
py -3.10 -m venv rasa\.venv
.\rasa\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install rasa==3.6.21 rasa-sdk==3.6.2 requests
.\rasa\.venv\Scripts\rasa.exe data validate --domain rasa\domain.yml --data rasa\data --config rasa\config.yml
.\rasa\.venv\Scripts\rasa.exe train --domain rasa\domain.yml --data rasa\data --config rasa\config.yml
```

Para probar solo clasificación NLU y entidades, basta con `rasa shell nlu`. Para conversar con el flujo completo, el proyecto incluye tareas de VS Code. Abre `Ver > Paleta de comandos...` (o `Ctrl+Mayús+P`), escribe `Tasks: Run Task` y elige esa opción. Ejecuta, en orden, `VitaDent: 1. Iniciar Django (SQLite local)`, `VitaDent: 2. Iniciar acciones del bot` y `VitaDent: 3. Conversar con el bot`. Espera a que las dos primeras terminales indiquen que los servicios están activos; déjalas abiertas. Escribe mensajes en la tercera terminal; usa `/stop` para salir.

Las tareas usan una SQLite aislada y un token local de prueba. Si prefieres iniciarlo a mano, abre tres terminales integradas en VS Code. En la primera levanta Django con esa SQLite; así no dependes de una instancia PostgreSQL ni tocas datos reales. Ejecuta esto desde la raíz del proyecto:

```powershell
.\.venv\Scripts\Activate.ps1
$env:DJANGO_DATABASE_ENGINE = 'sqlite'
$env:SQLITE_NAME = Join-Path $env:TEMP 'vitadent_vscode.sqlite3'
$env:VITADENT_RASA_TOKEN = 'token-local-solo-pruebas'
$env:VITADENT_RASA_URL = 'http://127.0.0.1:5005'
python manage.py migrate
python manage.py runserver 127.0.0.1:8000
```

En las dos terminales restantes, define el mismo token local de prueba y ejecuta:

```powershell
# Terminal de acciones, desde la carpeta rasa
$env:VITADENT_RASA_TOKEN = 'token-local-solo-pruebas'
$env:VITADENT_DJANGO_INTERNAL_URL = 'http://127.0.0.1:8000'
rasa run actions --actions actions --port 5055
```

```powershell
# Terminal de conversación, desde la raíz del proyecto
$env:VITADENT_RASA_TOKEN = 'token-local-solo-pruebas'
.\rasa\.venv\Scripts\rasa.exe shell --endpoints rasa\endpoints.vscode.yml
```

Ejecuta el último bloque desde la raíz del proyecto, no desde la carpeta `rasa`: tanto el entrenamiento de arriba como la conversación usan la carpeta `models` en la raíz. Si vuelves a entrenar desde otra carpeta, inicia la conversación desde esa misma carpeta o especifica el modelo con `--model`.

Si Django escucha en un puerto distinto, cambia `VITADENT_DJANGO_INTERNAL_URL` en la terminal de acciones. El token del ejemplo es solo para una máquina local y no se debe reutilizar en producción ni subir a Git.

Empieza con preguntas administrativas, como “¿qué tratamientos ofrecen?” o “¿qué horarios hay?”. Para crear una solicitud, el catálogo y la agenda deben tener datos activos en la base local; una cita quedará pendiente hasta que recepción la confirme. `rasa shell nlu` no llama a Django ni prueba reservas. El canal real de WhatsApp seguirá indicando que falta configurar el número y las credenciales de Meta.
4. Con el servicio local arriba y un corpus revisado de 300 mensajes:

   ```powershell
   python evaluacion/evaluar_nlu.py --rasa-url http://127.0.0.1:5005
   ```

   El reporte mide F1 macro y por intención, F1 micro de entidades, matriz de confusión, tasa de fallback y p95. Los criterios de referencia son F1 de intención ≥ 0,85, F1 de entidades ≥ 0,80 y p95 ≤ 1,5 s por turno. Son metas, no resultados. La evaluación debe ejecutarse solo con el conjunto aislado de prueba.

5. Verificaciones Django disponibles:

   ```powershell
   python manage.py check
   python -m pytest web/tests -q
   ```

## Etiquetado del corpus

Completa una fila por mensaje en `evaluacion/corpus.csv`. Usa IDs anónimos, contenido sintético o anonimizado y no incluyas teléfonos, identificaciones reales, códigos de cita ni información clínica identificable. `group_id` debe identificar una familia de expresiones equivalentes; todas sus variantes van juntas en un único `split` (`train`, `dev` o `test`) para evitar fuga por paráfrasis. Dos personas deben revisar las etiquetas del conjunto de prueba y marcarlo `revisado` tras resolver desacuerdos. La especificación adjunta solicita tres particiones; la tesis disponible describe 70 % entrenamiento y 30 % prueba, así que se debe acordar la proporción de `dev` antes de congelar el corpus.

El evaluador necesita al menos 300 filas y no mide diálogos completos, operaciones concurrentes ni una conversación real de WhatsApp. Esas comprobaciones deben ejecutarse aparte sobre una base de datos de pruebas aislada y credenciales Meta de sandbox; no se reportan como aprobadas en esta revisión.

## Datos reales pendientes de VitaDent

- Meta WhatsApp Cloud API: `WHATSAPP_VERIFY_TOKEN`, `WHATSAPP_APP_SECRET`, `WHATSAPP_ACCESS_TOKEN`, `WHATSAPP_PHONE_NUMBER_ID`, `VITADENT_WHATSAPP_NUMBER` y versión Graph API autorizada.
- Despliegue: `DJANGO_SECRET_KEY`, `POSTGRES_PASSWORD`, `VITADENT_RASA_TOKEN` y el secreto requerido para Redis si el servidor se configura con autenticación.
- Operación institucional: horarios semanales reales de cada especialista, política de cancelación y texto aprobado para derivación a recepción.
- Documentos: la tesis exacta v3.2 y la guía PDF nombrada para contrastar el diseño con la fuente correcta.
