# Servicio conversacional Rasa

Esta carpeta contiene la configuración inicial de Rasa Open Source con DIETClassifier, ejemplos iniciales de intenciones, formulario de reserva y acciones que envían una solicitud validada a Django.

## Estado

El servicio no se inicia automáticamente con Django. La interfaz usa el flujo guiado local mientras `VITADENT_RASA_URL` esté vacío. Al configurar esa variable, Django enviará cada turno a `/webhooks/rest/webhook`; el servidor Rasa y su modelo deben estar ejecutándose para que el chat responda.

Este corpus es un punto inicial, no el corpus de 300 enunciados anotados previsto para la evaluación de la tesis. Debe ampliarse y evaluarse antes de afirmar métricas de precisión. Redis se usa como almacén del estado conversacional; Django conserva las citas y los datos transaccionales.

## Componentes

- `config.yml`: pipeline de texto español, extracción de entidades y DIETClassifier.
- `domain.yml`, `data/nlu.yml` y `data/rules.yml`: intenciones, slots y flujo inicial.
- `actions/actions.py`: revisión del resumen y creación de solicitud mediante API interna.
- `endpoints.yml`: servidor de acciones y almacén Redis del tracker.

La acción de creación requiere `VITADENT_RASA_TOKEN` en Django y en el servidor de acciones. Django rechaza la operación si falta el token y valida de nuevo campos, catálogo y fecha.
