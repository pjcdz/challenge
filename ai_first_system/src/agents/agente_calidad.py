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

    reporte_ai = {
        "enrutamiento": {
            "total_registros": total,
            "rule_path": total_rule_path,
            "llm_path": total_llm_path,
            "porcentaje_llm": pct_llm,
            "total_fallbacks": total_fallbacks,
            "total_retries_llm": total_retries,
        },
    }

    # Agregar estadisticas del router si estan disponibles
    if stats_router != None:
        reporte_ai["enrutamiento"]["sinonimos_resueltos"] = stats_router.get(
            "sinonimos_resueltos", 0
        )
        reporte_ai["enrutamiento"]["embeddings_resueltos"] = stats_router.get(
            "embeddings_resueltos", 0
        )

    # Agregar metricas del LLM provider si estan disponibles
    if metricas_llm != None:
        reporte_ai["llm_provider"] = metricas_llm

    # Merge con reporte base
    reporte_base["ai_first"] = reporte_ai

    # Sobreescribir el reporte JSON con la version extendida
    ruta_reporte = os.path.join(carpeta_salida, "reporte_calidad.json")
    arch = open(ruta_reporte, "w", encoding="utf-8")
    arch.write(json.dumps(reporte_base, indent=4, ensure_ascii=False))
    arch.close()

    return reporte_base
