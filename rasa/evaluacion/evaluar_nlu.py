"""Evalúa NLU con mensajes revisados y el endpoint local /model/parse."""

import argparse
import csv
import json
import math
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

import requests

COLUMNAS = {"id", "group_id", "split", "text", "intent", "entities_json", "adjudication_status"}


def cargar(path):
    with Path(path).open(encoding="utf-8-sig", newline="") as archivo:
        lector = csv.DictReader(archivo)
        faltantes = COLUMNAS - set(lector.fieldnames or [])
        if faltantes:
            raise ValueError(f"Faltan columnas: {', '.join(sorted(faltantes))}")
        filas = list(lector)
    if len(filas) < 300:
        raise ValueError(f"Corpus incompleto: hay {len(filas)} mensajes; se requieren 300 anotados.")
    ids, grupos = set(), {}
    for fila in filas:
        if not all(fila[c].strip() for c in ("id", "group_id", "split", "text", "intent")):
            raise ValueError("Cada fila debe tener id, group_id, split, text e intent.")
        if fila["id"] in ids:
            raise ValueError(f"ID duplicado: {fila['id']}")
        ids.add(fila["id"])
        if fila["split"] not in {"train", "dev", "test"}:
            raise ValueError(f"Split no permitido en {fila['id']}.")
        grupo = fila["group_id"]
        if grupo in grupos and grupos[grupo] != fila["split"]:
            raise ValueError(f"Fuga entre splits: grupo {grupo} repetido en particiones distintas.")
        grupos[grupo] = fila["split"]
        fila["entities"] = json.loads(fila["entities_json"] or "[]")
        if not isinstance(fila["entities"], list) or any(not isinstance(e, dict) or not {"entity", "value"} <= set(e) for e in fila["entities"]):
            raise ValueError(f"entities_json inválido en {fila['id']}.")
    prueba = [f for f in filas if f["split"] == "test"]
    if not prueba or any(f["adjudication_status"] != "revisado" for f in prueba):
        raise ValueError("El corpus debe incluir filas test con adjudication_status=revisado.")
    return prueba


def _puntaje(tp, fp, fn):
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    return {"precision": precision, "recall": recall, "f1": 2 * precision * recall / (precision + recall) if precision + recall else 0.0}


def evaluar(rasa_url, filas, timeout):
    por_clase, matriz = defaultdict(Counter), defaultdict(Counter)
    entidad, latencias = Counter(), []
    aciertos = fallback = 0
    session = requests.Session()
    for fila in filas:
        inicio = time.perf_counter()
        response = session.post(f"{rasa_url.rstrip('/')}/model/parse", json={"text": fila["text"]}, timeout=timeout)
        response.raise_for_status()
        resultado = response.json()
        latencias.append((time.perf_counter() - inicio) * 1000)
        real = fila["intent"]
        predicha = (resultado.get("intent") or {}).get("name", "")
        aciertos += int(real == predicha)
        fallback += int(predicha == "nlu_fallback")
        matriz[real][predicha] += 1
        for nombre in {real, predicha}:
            por_clase[nombre]["tp"] += int(real == nombre and predicha == nombre)
            por_clase[nombre]["fp"] += int(real != nombre and predicha == nombre)
            por_clase[nombre]["fn"] += int(real == nombre and predicha != nombre)
        real_ent = {(e["entity"], json.dumps(e["value"], ensure_ascii=False, sort_keys=True)) for e in fila["entities"]}
        pred_ent = {(e.get("entity"), json.dumps(e.get("value"), ensure_ascii=False, sort_keys=True)) for e in resultado.get("entities", [])}
        entidad["tp"] += len(real_ent & pred_ent)
        entidad["fp"] += len(pred_ent - real_ent)
        entidad["fn"] += len(real_ent - pred_ent)
    soporte = Counter(f["intent"] for f in filas)
    clases = {k: _puntaje(v["tp"], v["fp"], v["fn"]) | {"support": soporte[k]} for k, v in sorted(por_clase.items())}
    clases_con_soporte = [v["f1"] for k, v in clases.items() if soporte[k]]
    latencias.sort()
    p95 = latencias[max(0, math.ceil(.95 * len(latencias)) - 1)]
    return {
        "test_messages": len(filas),
        "intent_accuracy": aciertos / len(filas),
        "intent_macro_f1": sum(clases_con_soporte) / len(clases_con_soporte),
        "intent_by_class": clases,
        "entity_micro": _puntaje(entidad["tp"], entidad["fp"], entidad["fn"]),
        "confusion_matrix": {k: dict(sorted(v.items())) for k, v in sorted(matriz.items())},
        "fallback_rate": fallback / len(filas),
        "latency_ms_p95": p95,
        "targets": {"intent_f1_min": .85, "entity_f1_min": .80, "latency_ms_p95_max": 1500},
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus", type=Path, default=Path(__file__).with_name("corpus.csv"))
    parser.add_argument("--rasa-url", default="http://127.0.0.1:5005")
    parser.add_argument("--timeout", type=float, default=5)
    parser.add_argument("--output", type=Path, default=Path("rasa/evaluacion/resultados_nlu.json"))
    args = parser.parse_args()
    try:
        filas = cargar(args.corpus)
        resultado = evaluar(args.rasa_url, filas, args.timeout)
    except (OSError, ValueError, requests.RequestException) as error:
        print(f"Evaluación no ejecutada: {error}", file=sys.stderr)
        return 2
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(resultado, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(resultado, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
