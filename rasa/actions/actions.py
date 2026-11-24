"""Acciones Rasa: consultan API Django y delegan toda mutación al servidor."""

import hashlib
import json
import os
from datetime import datetime

import requests
from rasa_sdk import Action, Tracker
from rasa_sdk.events import EventType, SlotSet
from rasa_sdk.executor import CollectingDispatcher


def _base() -> str:
    return os.environ.get("VITADENT_DJANGO_INTERNAL_URL", "http://host.docker.internal:8000").rstrip("/")


def _headers() -> dict:
    token = os.environ.get("VITADENT_RASA_TOKEN", "")
    return {"Authorization": f"Bearer {token}"} if token else {}


def _telefono_whatsapp(tracker: Tracker) -> str:
    return "".join(c for c in str(tracker.sender_id or "") if c.isdigit())


def _limpiar_operacion() -> list[EventType]:
    return [
        SlotSet("esperando_confirmacion", False),
        SlotSet("accion_pendiente", None),
        SlotSet("nueva_fecha_hora", None),
    ]


def _respuesta_error(dispatcher: CollectingDispatcher, respuesta: requests.Response) -> None:
    try:
        error = respuesta.json().get("error", "No se pudo validar la operación.")
    except (ValueError, AttributeError):
        error = "No se pudo completar la operación. Inténtalo de nuevo o pide hablar con recepción."
    dispatcher.utter_message(text=str(error)[:500])


class ActionRevisarReserva(Action):
    def name(self) -> str:
        return "action_revisar_reserva"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: dict) -> list[EventType]:
        nombre = str(tracker.get_slot("nombre") or "").strip()
        identificacion = str(tracker.get_slot("identificacion") or "").strip()
        tratamiento = str(tracker.get_slot("tratamiento") or "").strip()
        especialista = str(tracker.get_slot("especialista") or "cualquiera").strip()
        fecha = str(tracker.get_slot("fecha_hora") or "").strip()
        try:
            datetime.strptime(fecha, "%d/%m/%Y %H:%M")
        except ValueError:
            dispatcher.utter_message(text="La fecha debe tener el formato DD/MM/AAAA HH:MM. Revísala para continuar.")
            return [SlotSet("esperando_confirmacion", False)]
        if not nombre or not identificacion or not tratamiento:
            dispatcher.utter_message(text="Falta un dato obligatorio. Escribe reservar cita para completar la solicitud.")
            return [SlotSet("esperando_confirmacion", False)]
        correo = str(tracker.get_slot("correo") or "No indicado")
        sucursal = str(tracker.get_slot("sucursal") or "Única sucursal configurada")
        resumen = (
            f"Revisa tu solicitud: {nombre}; tratamiento {tratamiento}; profesional {especialista}; "
            f"fecha y hora {fecha}; sucursal {sucursal}; correo {correo}. "
            "El teléfono será el de este WhatsApp. Si todo está correcto, responde sí."
        )
        dispatcher.utter_message(response="utter_preguntar_confirmacion", resumen_solicitud=resumen)
        return [SlotSet("accion_pendiente", "reservar"), SlotSet("esperando_confirmacion", True)]


class ActionRevisarCancelacion(Action):
    def name(self) -> str:
        return "action_revisar_cancelacion"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: dict) -> list[EventType]:
        telefono = _telefono_whatsapp(tracker)
        payload = {"codigo": tracker.get_slot("codigo_cita"), "identificacion": tracker.get_slot("identificacion"), "telefono": telefono}
        try:
            response = requests.post(f"{_base()}/api/interna/citas/consultar/", json=payload, headers=_headers(), timeout=(3, 8), allow_redirects=False)
            if response.status_code != 200:
                _respuesta_error(dispatcher, response)
                return [SlotSet("esperando_confirmacion", False)]
            cita = response.json()
        except (requests.RequestException, ValueError):
            dispatcher.utter_message(text="No pude consultar la cita. Inténtalo más tarde; no se modificó ningún registro.")
            return [SlotSet("esperando_confirmacion", False)]
        dispatcher.utter_message(text=f"¿Confirmas que deseas cancelar la cita {cita['codigo']} de {cita['tratamiento']} para {cita['fecha_hora']}? Responde sí para cancelarla.")
        return [SlotSet("accion_pendiente", "cancelar"), SlotSet("esperando_confirmacion", True)]


class ActionRevisarReprogramacion(Action):
    def name(self) -> str:
        return "action_revisar_reprogramacion"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: dict) -> list[EventType]:
        try:
            nueva = datetime.strptime(str(tracker.get_slot("nueva_fecha_hora") or ""), "%d/%m/%Y %H:%M")
        except ValueError:
            dispatcher.utter_message(text="La fecha nueva debe usar DD/MM/AAAA HH:MM.")
            return [SlotSet("esperando_confirmacion", False)]
        payload = {"codigo": tracker.get_slot("codigo_cita"), "identificacion": tracker.get_slot("identificacion"), "telefono": _telefono_whatsapp(tracker)}
        try:
            response = requests.post(f"{_base()}/api/interna/citas/consultar/", json=payload, headers=_headers(), timeout=(3, 8), allow_redirects=False)
            if response.status_code != 200:
                _respuesta_error(dispatcher, response)
                return [SlotSet("esperando_confirmacion", False)]
            cita = response.json()
        except (requests.RequestException, ValueError):
            dispatcher.utter_message(text="No pude consultar la cita. No se cambió ningún registro; inténtalo más tarde.")
            return [SlotSet("esperando_confirmacion", False)]
        resumen = f"La cita {cita['codigo']} está para {cita['fecha_hora']}. ¿Quieres solicitar el cambio a {nueva.strftime('%d/%m/%Y %H:%M')}? Recepción tendrá que revisar el nuevo horario. Responde sí para enviar la solicitud."
        dispatcher.utter_message(text=resumen)
        return [SlotSet("accion_pendiente", "reprogramar"), SlotSet("esperando_confirmacion", True)]


class ActionConfirmarOperacion(Action):
    def name(self) -> str:
        return "action_confirmar_operacion"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: dict) -> list[EventType]:
        if tracker.get_slot("esperando_confirmacion") is not True:
            dispatcher.utter_message(text="No hay una operación pendiente de confirmación. Escribe qué gestión necesitas.")
            return []
        accion = tracker.get_slot("accion_pendiente")
        telefono = _telefono_whatsapp(tracker)
        if not 7 <= len(telefono) <= 15:
            dispatcher.utter_message(text="No pude validar el número de esta conversación de WhatsApp.")
            return _limpiar_operacion()

        if accion == "reservar":
            try:
                fecha = datetime.strptime(str(tracker.get_slot("fecha_hora") or ""), "%d/%m/%Y %H:%M").isoformat() + "-05:00"
            except ValueError:
                dispatcher.utter_message(text="La fecha ya no es válida. Inicia de nuevo la solicitud.")
                return _limpiar_operacion()
            payload = {
                "nombre": tracker.get_slot("nombre"),
                "identificacion": tracker.get_slot("identificacion"),
                "telefono": telefono,
                "correo": tracker.get_slot("correo") or "",
                "tratamiento": tracker.get_slot("tratamiento"),
                "especialista": tracker.get_slot("especialista") or "",
                "fecha_hora": fecha,
                "sucursal": tracker.get_slot("sucursal") or "",
            }
            base_key = json.dumps({"sender": tracker.sender_id, **payload}, sort_keys=True, ensure_ascii=False)
            payload["idempotency_key"] = hashlib.sha256(base_key.encode("utf-8")).hexdigest()
            ruta = "/api/interna/solicitudes/"
        elif accion in {"cancelar", "reprogramar"}:
            payload = {"codigo": tracker.get_slot("codigo_cita"), "identificacion": tracker.get_slot("identificacion"), "telefono": telefono}
            if accion == "reprogramar":
                try:
                    payload["nueva_fecha_hora"] = datetime.strptime(str(tracker.get_slot("nueva_fecha_hora") or ""), "%d/%m/%Y %H:%M").isoformat() + "-05:00"
                except ValueError:
                    dispatcher.utter_message(text="La fecha nueva ya no es válida. Inicia de nuevo la solicitud.")
                    return _limpiar_operacion()
                ruta = "/api/interna/citas/reprogramar/"
            else:
                ruta = "/api/interna/citas/cancelar/"
        else:
            dispatcher.utter_message(text="No identifiqué una operación pendiente. No se modificó ninguna cita.")
            return _limpiar_operacion()

        if not os.environ.get("VITADENT_RASA_TOKEN"):
            dispatcher.utter_message(text="La conexión segura con VitaDent no está configurada. No se aplicó el cambio.")
            return _limpiar_operacion()
        try:
            response = requests.post(f"{_base()}{ruta}", json=payload, headers=_headers(), timeout=(3, 8), allow_redirects=False)
            resultado = response.json()
        except (requests.RequestException, ValueError):
            dispatcher.utter_message(text="No pude conectar con VitaDent. No puedo confirmar si se aplicó la operación; consulta a recepción antes de repetirla.")
            return _limpiar_operacion()
        if response.status_code not in {200, 201}:
            _respuesta_error(dispatcher, response)
            return _limpiar_operacion()

        if accion == "reservar":
            dispatcher.utter_message(text=f"Solicitud registrada con el código {resultado['codigo']}. Todavía no es una cita confirmada; recepción verificará la disponibilidad y te responderá por WhatsApp.")
        elif accion == "cancelar":
            dispatcher.utter_message(text=f"La cita {resultado['codigo']} quedó cancelada.")
        else:
            dispatcher.utter_message(text=f"Recibimos la solicitud para cambiar la cita {resultado['codigo']}. El nuevo horario queda pendiente de revisión de recepción.")
        return _limpiar_operacion()


class ActionConsultarCita(Action):
    def name(self) -> str:
        return "action_consultar_cita"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: dict) -> list[EventType]:
        payload = {"codigo": tracker.get_slot("codigo_cita"), "identificacion": tracker.get_slot("identificacion"), "telefono": _telefono_whatsapp(tracker)}
        try:
            response = requests.post(f"{_base()}/api/interna/citas/consultar/", json=payload, headers=_headers(), timeout=(3, 8), allow_redirects=False)
            if response.status_code != 200:
                _respuesta_error(dispatcher, response)
                return []
            cita = response.json()
        except (requests.RequestException, ValueError):
            dispatcher.utter_message(text="No pude consultar la cita. Inténtalo más tarde o solicita atención de recepción.")
            return []
        dispatcher.utter_message(text=f"La cita {cita['codigo']} está en estado {cita['estado']} para {cita['fecha_hora']} con {cita['especialista']}.")
        return []


class ActionConsultarCatalogo(Action):
    def name(self) -> str:
        return "action_consultar_catalogo"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: dict) -> list[EventType]:
        intent = (tracker.latest_message.get("intent") or {}).get("name")
        if intent == "consultar_tratamientos":
            endpoint, etiqueta, campo = "tratamientos", "tratamientos", "nombre"
        else:
            endpoint, etiqueta, campo = "especialistas", "especialistas", "nombre_completo"
        try:
            response = requests.get(f"{_base()}/api/v1/{endpoint}/", timeout=(3, 8), allow_redirects=False)
            response.raise_for_status()
            data = response.json()
            elementos = data.get("results", []) if isinstance(data, dict) else data
            if endpoint == "especialistas":
                texto = "; ".join(f"{item[campo]} ({item['especialidad']})" for item in elementos[:30])
            else:
                texto = "; ".join(f"{item[campo]} — {item['area']}" for item in elementos[:30])
            dispatcher.utter_message(text=f"Catálogo VitaDent: {texto or 'No hay registros activos en el catálogo.'}")
        except (requests.RequestException, ValueError, KeyError, TypeError):
            dispatcher.utter_message(text=f"No pude consultar el catálogo de {etiqueta}. Inténtalo de nuevo más tarde.")
        return []


class ActionConsultarDisponibilidad(Action):
    def name(self) -> str:
        return "action_consultar_disponibilidad"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: dict) -> list[EventType]:
        try:
            fecha_hora = datetime.strptime(str(tracker.get_slot("fecha_hora") or ""), "%d/%m/%Y %H:%M")
            response_tratamientos = requests.get(f"{_base()}/api/v1/tratamientos/", timeout=(3, 8), allow_redirects=False)
            response_especialistas = requests.get(f"{_base()}/api/v1/especialistas/", timeout=(3, 8), allow_redirects=False)
            response_tratamientos.raise_for_status(); response_especialistas.raise_for_status()
            tratamientos = response_tratamientos.json().get("results", [])
            especialistas = response_especialistas.json().get("results", [])
            tratamiento = next((x for x in tratamientos if x["nombre"].casefold() == str(tracker.get_slot("tratamiento") or "").casefold()), None)
            especialista = next((x for x in especialistas if x["nombre_completo"].casefold() == str(tracker.get_slot("especialista") or "").casefold()), None)
            if not tratamiento or not especialista:
                dispatcher.utter_message(text="No encontré ese tratamiento o especialista en el catálogo activo. Pide el catálogo para revisar los nombres.")
                return []
            response = requests.get(
                f"{_base()}/api/v1/disponibilidad/",
                params={"fecha": fecha_hora.date().isoformat(), "especialista": especialista["id"], "tratamiento": tratamiento["id"]},
                timeout=(3, 8),
                allow_redirects=False,
            )
            response.raise_for_status()
            bloques = response.json().get("bloques", [])
            hora_pedida = fecha_hora.strftime("%H:%M")
            horas = [datetime.fromisoformat(b["inicio"]).strftime("%H:%M") for b in bloques]
            if hora_pedida in horas:
                dispatcher.utter_message(text=f"Ese horario aparece disponible en la agenda de {especialista['nombre_completo']}. Para solicitarlo, inicia una reserva; la clínica debe confirmarlo.")
            else:
                opciones = ", ".join(horas[:6])
                dispatcher.utter_message(text=f"Ese horario no aparece disponible. Horas que puedes consultar para esa fecha: {opciones or 'no hay bloques registrados'}. La reserva debe confirmarla la clínica.")
        except (ValueError, KeyError, TypeError, requests.RequestException):
            dispatcher.utter_message(text="No pude comprobar la agenda. Inténtalo más tarde o pide atención a recepción.")
        return []


class ActionCancelarSolicitud(Action):
    def name(self) -> str:
        return "action_cancelar_solicitud"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: dict) -> list[EventType]:
        dispatcher.utter_message(response="utter_no_enviada")
        return _limpiar_operacion() + [
            SlotSet("nombre", None), SlotSet("identificacion", None), SlotSet("tratamiento", None),
            SlotSet("especialista", None), SlotSet("fecha_hora", None), SlotSet("correo", None),
            SlotSet("sucursal", None), SlotSet("codigo_cita", None),
        ]
