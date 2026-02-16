# agente_calidad.py - Agente de calidad AI-First
# Genera reporte de calidad extendido con metricas de LLM
# Reutiliza calidad legacy y agrega metricas ai_first

import os
import sys
import json
from datetime import datetime

dir_src = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
dir_legacy = os.path.join(
    os.path.dirname(os.path.dirname(dir_src)), "legacy_system", "src"
)
sys.path.insert(0, dir_src)
sys.path.insert(0, dir_legacy)

MODULO = "AGENTE_CALIDAD"


def generar_reporte(
    registros, archivo_entrada, carpeta_salida, stats_router, metricas_llm
):
    # Genera reporte de calidad extendido para el modo AI-First
    # Incluye metricas legacy + metricas de enrutamiento y LLM

    import calidad

    # Generar reporte base (legacy)
    reporte_base = calidad.generar_reporte(registros, archivo_entrada, carpeta_salida)

    # Agregar metricas AI-First
    total_rule_path = 0
    total_llm_path = 0
    total_fallbacks = 0
    total_retries = 0

    for reg in registros:
        if "origen_procesamiento" in reg.keys():
            if reg["origen_procesamiento"] == "rule_path":
                total_rule_path = total_rule_path + 1
            elif reg["origen_procesamiento"] == "llm_path":
                total_llm_path = total_llm_path + 1
        if "fallback_aplicado" in reg.keys() and reg["fallback_aplicado"]:
            total_fallbacks = total_fallbacks + 1
        if "retries_llm" in reg.keys():
            total_retries = total_retries + reg["retries_llm"]

    total = len(registros)
    pct_llm = 0.0
    if total > 0:
        pct_llm = round((total_llm_path * 100.0) / total, 1)

    reporte_ai = {"enrutamiento": {}}
    reporte_ai["enrutamiento"]["total_registros"] = total
    reporte_ai["enrutamiento"]["rule_path"] = total_rule_path
    reporte_ai["enrutamiento"]["llm_path"] = total_llm_path
    reporte_ai["enrutamiento"]["porcentaje_llm"] = pct_llm
    reporte_ai["enrutamiento"]["total_fallbacks"] = total_fallbacks
    reporte_ai["enrutamiento"]["total_retries_llm"] = total_retries

    # Agregar estadisticas del router si estan disponibles
    if stats_router != None:
        reporte_ai["enrutamiento"]["sinonimos_resueltos"] = stats_router.get(
            "sinonimos_resueltos", 0
        )
        reporte_ai["enrutamiento"]["embeddings_resueltos"] = stats_router.get(
            "embeddings_resueltos", 0
        )
        reporte_ai["enrutamiento"]["validos_directos"] = stats_router.get(
            "validos_directos", 0
        )
        reporte_ai["enrutamiento"]["invalidos_directos"] = stats_router.get(
            "invalidos_directos", 0
        )
        reporte_ai["enrutamiento"]["ambiguous_detected"] = stats_router.get(
            "ambiguous_detected", 0
        )
        reporte_ai["enrutamiento"]["ambiguous_sent_llm"] = stats_router.get(
            "ambiguous_sent_llm", 0
        )
        reporte_ai["enrutamiento"]["batches_total"] = stats_router.get(
            "batches_total", 0
        )
        reporte_ai["enrutamiento"]["batch_size_promedio"] = stats_router.get(
            "batch_size_promedio", 0.0
        )
        reporte_ai["enrutamiento"]["rounds_total"] = stats_router.get(
            "rounds_total", 0
        )
        reporte_ai["enrutamiento"]["llm_calls_totales"] = stats_router.get(
            "llm_calls_totales", 0
        )

        reporte_ai["performance"] = {
            "tiempo_total": stats_router.get("tiempo_total", 0.0),
            "tiempo_preclasificacion": stats_router.get(
                "tiempo_preclasificacion", 0.0
            ),
            "tiempo_llm": stats_router.get("tiempo_llm", 0.0),
            "tiempo_postproceso": stats_router.get("tiempo_postproceso", 0.0),
        }

    # Agregar metricas del LLM provider si estan disponibles
    if metricas_llm != None:
        reporte_ai["llm_provider"] = metricas_llm

    # Trazabilidad por registro
    trazas = []
    for reg in registros:
        traza = {
            "id_solicitud": reg.get("id_solicitud", ""),
            "estado_final": reg.get("estado", ""),
            "origen_procesamiento": reg.get("origen_procesamiento", ""),
            "retries_llm": reg.get("retries_llm", 0),
            "fallback_aplicado": reg.get("fallback_aplicado", False),
        }
        if "_traza_ai" in reg.keys() and type(reg["_traza_ai"]) == dict:
            d = reg["_traza_ai"]
            traza["clasificacion"] = d.get("clasificacion", "")
            traza["motivo_clasificacion"] = d.get("motivo_clasificacion", "")
            traza["reglas_afectadas"] = d.get("reglas_afectadas", [])
            traza["motivos_ambiguedad"] = d.get("motivos_ambiguedad", [])
            traza["motivos_invalidacion"] = d.get("motivos_invalidacion", [])
            traza["ronda_llm"] = d.get("ronda_llm", 0)
            traza["batch_llm"] = d.get("batch_llm", 0)
            traza["estado_llm"] = d.get("estado_llm", "")
            traza["motivo_llm"] = d.get("motivo_llm", "")
        trazas.append(traza)

    reporte_ai["trazabilidad_registros"] = trazas

    # Merge con reporte base
    reporte_base["ai_first"] = reporte_ai

    # Sobreescribir el reporte JSON con la version extendida
    ruta_reporte = os.path.join(carpeta_salida, "reporte_calidad.json")
    arch = open(ruta_reporte, "w", encoding="utf-8")
    arch.write(json.dumps(reporte_base, indent=4, ensure_ascii=False))
    arch.close()

    return reporte_base
