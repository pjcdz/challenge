# metricas.py - Calculo de metricas para benchmark comparativo (RF-07 AI-First)
# Compara resultados de legacy vs ai_first sobre el mismo dataset
# Metricas: tiempo, throughput, validos/invalidos, precision ambiguos, LLM %, costo

import os
import sys
import json

MODULO = "METRICAS"


def _texto_metrica(x):
    # Formatea valores para reportes evitando ocultar datos no disponibles
    if x == None:
        return "NO_DISPONIBLE"
    return str(x)


def _texto_metrica_usd(x):
    # Formatea montos USD para reportes
    if x == None:
        return "NO_DISPONIBLE"
    return "$" + str(x)


def calcular_metricas_modo(resultado_modo, ground_truth=None):
    # Calcula metricas para un modo (legacy o ai_first)
    # resultado_modo: diccionario retornado por el runner del modo
    # ground_truth: lista de dicts con estado_esperado (opcional)
    # Retorna diccionario con metricas calculadas

    metricas = {}

    # Tiempo y throughput
    duracion = 0.0
    total = 0
    if "resumen" in resultado_modo.keys():
        resumen = resultado_modo["resumen"]
        duracion = resumen.get("duracion_segundos", 0.0)
        total = resumen.get("total_procesados", 0)
    metricas["tiempo_total_segundos"] = duracion
    metricas["total_procesados"] = total
    if duracion > 0:
        metricas["throughput_registros_seg"] = round(total / duracion, 2)
    else:
        metricas["throughput_registros_seg"] = 0.0

    # Validos e invalidos
    metricas["total_validos"] = 0
    metricas["total_invalidos"] = 0
    if "resumen" in resultado_modo.keys():
        metricas["total_validos"] = resultado_modo["resumen"].get("total_validos", 0)
        metricas["total_invalidos"] = resultado_modo["resumen"].get(
            "total_invalidos", 0
        )

    # Metricas de enrutamiento (solo ai_first)
    metricas["porcentaje_llm"] = 0.0
    metricas["total_llm_path"] = 0
    metricas["total_rule_path"] = 0
    metricas["total_retries"] = 0
    metricas["total_fallbacks"] = 0
    metricas["sinonimos_resueltos"] = 0
    metricas["embeddings_resueltos"] = 0

    if "enrutamiento" in resultado_modo.keys():
        enr = resultado_modo["enrutamiento"]
        metricas["porcentaje_llm"] = enr.get("porcentaje_llm", 0.0)
        metricas["total_llm_path"] = enr.get("llm_path", 0)
        metricas["total_rule_path"] = enr.get("regla_path", 0)
        metricas["sinonimos_resueltos"] = enr.get("sinonimos_resueltos", 0)
        metricas["embeddings_resueltos"] = enr.get("embeddings_resueltos", 0)

    # Metricas del reporte de calidad (si esta disponible)
    if "reporte" in resultado_modo.keys():
        reporte = resultado_modo["reporte"]
        if "ai_first" in reporte.keys():
            ai_info = reporte["ai_first"]
            if "enrutamiento" in ai_info.keys():
                enr_ai = ai_info["enrutamiento"]
                metricas["total_retries"] = enr_ai.get("total_retries_llm", 0)
                metricas["total_fallbacks"] = enr_ai.get("total_fallbacks", 0)

    # Metricas LLM (costo estimado, embedding)
    metricas["llm_calls_totales"] = 0
    metricas["llm_calls_con_tokens"] = 0
    metricas["llm_calls_sin_tokens"] = 0
    metricas["llm_tokens_prompt"] = 0
    metricas["llm_tokens_completion"] = 0
    metricas["llm_tokens_disponibles"] = False
    metricas["llm_tokens_estado"] = "sin_llamadas"
    metricas["llm_costo_estimado_usd"] = 0.0
    metricas["llm_costo_disponible"] = True
    metricas["llm_costo_estado"] = "sin_llamadas"
    metricas["embedding_calls_totales"] = 0
    metricas["embedding_latencia_promedio_ms"] = 0.0

    if (
        "metricas_llm" in resultado_modo.keys()
        and resultado_modo["metricas_llm"] != None
    ):
        mlm = resultado_modo["metricas_llm"]
        metricas["llm_calls_totales"] = mlm.get("total_llamadas", 0)
        metricas["llm_calls_con_tokens"] = mlm.get("total_llamadas_con_tokens", 0)
        metricas["llm_calls_sin_tokens"] = mlm.get("total_llamadas_sin_tokens", 0)
        # Compatibilidad de nombres entre versiones de metricas
        metricas["embedding_calls_totales"] = mlm.get(
            "total_embeddings", mlm.get("total_embedding_calls", 0)
        )

        tokens_prompt = mlm.get("total_tokens_prompt", 0)
        tokens_completion = mlm.get("total_tokens_completion", 0)

        # Determinar disponibilidad real de usage tokens
        if "token_usage_disponible" in mlm.keys():
            metricas["llm_tokens_disponibles"] = bool(mlm["token_usage_disponible"])
        else:
            # Compatibilidad: si hubo llamadas y tokens=0, no asumir 0 real
            if (
                metricas["llm_calls_totales"] > 0
                and tokens_prompt == 0
                and tokens_completion == 0
            ):
                metricas["llm_tokens_disponibles"] = False
            else:
                metricas["llm_tokens_disponibles"] = True

        if "token_usage_estado" in mlm.keys():
            metricas["llm_tokens_estado"] = mlm["token_usage_estado"]
        else:
            if metricas["llm_calls_totales"] == 0:
                metricas["llm_tokens_estado"] = "sin_llamadas"
            elif metricas["llm_tokens_disponibles"]:
                if (
                    metricas["llm_calls_con_tokens"] > 0
                    and metricas["llm_calls_sin_tokens"] > 0
                ):
                    metricas["llm_tokens_estado"] = "parcial"
                else:
                    metricas["llm_tokens_estado"] = "completo"
            else:
                metricas["llm_tokens_estado"] = "sin_datos"

        if metricas["llm_tokens_disponibles"]:
            metricas["llm_tokens_prompt"] = tokens_prompt
            metricas["llm_tokens_completion"] = tokens_completion
        else:
            if metricas["llm_calls_totales"] > 0:
                metricas["llm_tokens_prompt"] = None
                metricas["llm_tokens_completion"] = None
            else:
                metricas["llm_tokens_prompt"] = 0
                metricas["llm_tokens_completion"] = 0

        # Costo estimado (Gemini pricing aprox)
        costo_reportado = False
        if "costo_estimado_estado" in mlm.keys():
            metricas["llm_costo_estado"] = mlm["costo_estimado_estado"]

        if "costo_estimado_usd" in mlm.keys():
            metricas["llm_costo_estimado_usd"] = mlm["costo_estimado_usd"]
            costo_reportado = True

        if metricas["llm_calls_totales"] == 0:
            metricas["llm_costo_disponible"] = True
            metricas["llm_costo_estado"] = "sin_llamadas"
            if metricas["llm_costo_estimado_usd"] == None:
                metricas["llm_costo_estimado_usd"] = 0.0
        elif metricas["llm_tokens_disponibles"]:
            metricas["llm_costo_disponible"] = True
            if not costo_reportado:
                tokens_in = mlm.get("total_tokens_prompt", 0)
                tokens_out = mlm.get("total_tokens_completion", 0)
                costo = (tokens_in * 0.000000075) + (tokens_out * 0.0000003)
                metricas["llm_costo_estimado_usd"] = round(costo, 6)
            if metricas["llm_tokens_estado"] == "parcial":
                metricas["llm_costo_estado"] = "parcial"
            elif metricas["llm_costo_estado"] == "sin_llamadas":
                metricas["llm_costo_estado"] = "completo"
        else:
            metricas["llm_costo_disponible"] = False
            metricas["llm_costo_estado"] = "no_disponible"
            metricas["llm_costo_estimado_usd"] = None

        # Latencia promedio de embedding
        if "latencia_promedio_ms" in mlm.keys():
            metricas["embedding_latencia_promedio_ms"] = mlm["latencia_promedio_ms"]
        elif "latencia_promedio_embedding" in mlm.keys():
            # El provider reporta segundos; convertir a milisegundos
            metricas["embedding_latencia_promedio_ms"] = round(
                mlm["latencia_promedio_embedding"] * 1000.0, 3
            )

    # Precision en subset ambiguo (si hay ground truth)
    metricas["precision_ambiguos"] = None
    if ground_truth != None:
        aciertos = 0
        total_ambiguos = 0
        # Leer registros procesados del CSV de salida
        registros_salida = _leer_csv_salida(resultado_modo)

        # Armar indice por id_solicitud
        d_salida = {}
        for reg in registros_salida:
            if "id_solicitud" in reg.keys():
                d_salida[reg["id_solicitud"]] = reg

        for gt in ground_truth:
            if gt["tipo"] != "ambiguo":
                continue
            total_ambiguos = total_ambiguos + 1
            id_sol = gt["id_solicitud"]
            if id_sol not in d_salida.keys():
                continue
            reg_sal = d_salida[id_sol]

            # Verificar si el estado coincide
            estado_esperado = gt.get("estado_esperado", "")
            if estado_esperado == "depende_resolucion":
                # Solo verificar campos normalizados
                acierto = True
                if gt.get("tipo_producto_normalizado", "") != "requiere_llm":
                    if reg_sal.get("tipo_producto", "") != gt.get(
                        "tipo_producto_normalizado", ""
                    ):
                        acierto = False
                if gt.get("moneda_normalizada", "") != "requiere_llm":
                    if reg_sal.get("moneda", "") != gt.get("moneda_normalizada", ""):
                        acierto = False
                if gt.get("pais_normalizado", "") != "requiere_llm":
                    if reg_sal.get("pais", "") != gt.get("pais_normalizado", ""):
                        acierto = False
                if acierto:
                    aciertos = aciertos + 1
            else:
                if reg_sal.get("estado", "") == estado_esperado:
                    aciertos = aciertos + 1

        if total_ambiguos > 0:
            metricas["precision_ambiguos"] = round(
                (aciertos * 100.0) / total_ambiguos, 1
            )
            metricas["total_ambiguos_evaluados"] = total_ambiguos
            metricas["aciertos_ambiguos"] = aciertos

    return metricas


def _leer_csv_salida(resultado_modo):
    # Lee el CSV de salida de un resultado de modo
    # Retorna lista de diccionarios
    registros = []
    ruta = resultado_modo.get("archivo_salida", "")
    if ruta == "" or not os.path.exists(ruta):
        return registros

    arch = open(ruta, "r", encoding="utf-8")
    primera = True
    header = []

    for linea in arch:
        if linea[-1] == "\n":
            linea = linea[:-1]
        if linea == "":
            continue
        if primera:
            header = linea.split(",")
            primera = False
            continue
        # Parseo simple CSV (sin manejar comillas por simplicidad de benchmark)
        ls = linea.split(",")
        reg = {}
        i = 0
        while i < len(header) and i < len(ls):
            reg[header[i]] = ls[i]
            i = i + 1
        registros.append(reg)

    arch.close()
    return registros


def comparar_modos(metricas_legacy, metricas_ai_first):
    # Compara metricas de ambos modos y genera un analisis
    # Retorna diccionario con comparacion

    comparacion = {}

    # Tiempo
    t_legacy = metricas_legacy.get("tiempo_total_segundos", 0.0)
    t_ai = metricas_ai_first.get("tiempo_total_segundos", 0.0)
    comparacion["tiempo"] = {
        "legacy_segundos": t_legacy,
        "ai_first_segundos": t_ai,
    }
    if t_legacy > 0:
        comparacion["tiempo"]["ratio_ai_vs_legacy"] = round(t_ai / t_legacy, 2)
    else:
        comparacion["tiempo"]["ratio_ai_vs_legacy"] = 0.0

    # Throughput
    th_legacy = metricas_legacy.get("throughput_registros_seg", 0.0)
    th_ai = metricas_ai_first.get("throughput_registros_seg", 0.0)
    comparacion["throughput"] = {
        "legacy_reg_seg": th_legacy,
        "ai_first_reg_seg": th_ai,
    }

    # Validos/invalidos
    comparacion["resultados"] = {
        "legacy_validos": metricas_legacy.get("total_validos", 0),
        "legacy_invalidos": metricas_legacy.get("total_invalidos", 0),
        "ai_first_validos": metricas_ai_first.get("total_validos", 0),
        "ai_first_invalidos": metricas_ai_first.get("total_invalidos", 0),
    }

    # Diferencia en clasificacion
    diff_validos = metricas_ai_first.get("total_validos", 0) - metricas_legacy.get(
        "total_validos", 0
    )
    comparacion["resultados"]["diferencia_validos"] = diff_validos
    if diff_validos > 0:
        comparacion["resultados"]["nota"] = (
            "AI-First recupera "
            + str(diff_validos)
            + " registros mas como validos (posible resolucion de ambiguos)"
        )
    elif diff_validos < 0:
        comparacion["resultados"]["nota"] = (
            "AI-First marca " + str(abs(diff_validos)) + " registros mas como invalidos"
        )
    else:
        comparacion["resultados"]["nota"] = "Misma cantidad de validos en ambos modos"

    # LLM stats (solo ai_first)
    comparacion["llm"] = {
        "porcentaje_registros_llm": metricas_ai_first.get("porcentaje_llm", 0.0),
        "total_llm_calls": metricas_ai_first.get("llm_calls_totales", 0),
        "tokens_estado": metricas_ai_first.get("llm_tokens_estado", "sin_llamadas"),
        "costo_estimado_usd": metricas_ai_first.get("llm_costo_estimado_usd", 0.0),
        "costo_estado": metricas_ai_first.get("llm_costo_estado", "sin_llamadas"),
        "retries": metricas_ai_first.get("total_retries", 0),
        "fallbacks": metricas_ai_first.get("total_fallbacks", 0),
    }

    # Precision en ambiguos (si aplica)
    prec = metricas_ai_first.get("precision_ambiguos", None)
    if prec != None:
        comparacion["precision_ambiguos"] = {
            "porcentaje": prec,
            "evaluados": metricas_ai_first.get("total_ambiguos_evaluados", 0),
            "aciertos": metricas_ai_first.get("aciertos_ambiguos", 0),
        }

    return comparacion


def generar_resumen_markdown(metricas_legacy, metricas_ai_first, comparacion):
    # Genera un resumen en Markdown para el reporte
    # Retorna string con el contenido Markdown

    lineas = []
    lineas.append("# Benchmark: Legacy vs AI-First")
    lineas.append("")
    lineas.append("## Resumen de Performance")
    lineas.append("")
    lineas.append("| Metrica | Legacy | AI-First |")
    lineas.append("|---------|--------|----------|")
    lineas.append(
        "| Tiempo total (seg) | "
        + str(metricas_legacy.get("tiempo_total_segundos", 0))
        + " | "
        + str(metricas_ai_first.get("tiempo_total_segundos", 0))
        + " |"
    )
    lineas.append(
        "| Throughput (reg/seg) | "
        + str(metricas_legacy.get("throughput_registros_seg", 0))
        + " | "
        + str(metricas_ai_first.get("throughput_registros_seg", 0))
        + " |"
    )
    lineas.append(
        "| Total procesados | "
        + str(metricas_legacy.get("total_procesados", 0))
        + " | "
        + str(metricas_ai_first.get("total_procesados", 0))
        + " |"
    )
    lineas.append(
        "| Validos | "
        + str(metricas_legacy.get("total_validos", 0))
        + " | "
        + str(metricas_ai_first.get("total_validos", 0))
        + " |"
    )
    lineas.append(
        "| Invalidos | "
        + str(metricas_legacy.get("total_invalidos", 0))
        + " | "
        + str(metricas_ai_first.get("total_invalidos", 0))
        + " |"
    )
    lineas.append("")

    # Ratio
    ratio = comparacion.get("tiempo", {}).get("ratio_ai_vs_legacy", 0)
    lineas.append("**Ratio tiempo AI/Legacy:** " + str(ratio) + "x")
    lineas.append("")

    # Diferencia
    nota = comparacion.get("resultados", {}).get("nota", "")
    if nota != "":
        lineas.append("**Nota:** " + nota)
        lineas.append("")

    # Metricas LLM
    lineas.append("## Metricas LLM (AI-First)")
    lineas.append("")
    lineas.append("| Metrica | Valor |")
    lineas.append("|---------|-------|")
    lineas.append(
        "| Registros enviados a LLM (%) | "
        + str(metricas_ai_first.get("porcentaje_llm", 0))
        + "% |"
    )
    lineas.append(
        "| Registros rule_path | "
        + str(metricas_ai_first.get("total_rule_path", 0))
        + " |"
    )
    lineas.append(
        "| Registros llm_path | "
        + str(metricas_ai_first.get("total_llm_path", 0))
        + " |"
    )
    lineas.append(
        "| Sinonimos resueltos (sin LLM) | "
        + str(metricas_ai_first.get("sinonimos_resueltos", 0))
        + " |"
    )
    lineas.append(
        "| Resueltos por embedding | "
        + str(metricas_ai_first.get("embeddings_resueltos", 0))
        + " |"
    )
    lineas.append(
        "| Llamadas LLM totales | "
        + str(metricas_ai_first.get("llm_calls_totales", 0))
        + " |"
    )
    lineas.append(
        "| Llamadas con tokens | "
        + str(metricas_ai_first.get("llm_calls_con_tokens", 0))
        + " |"
    )
    lineas.append(
        "| Llamadas sin tokens | "
        + str(metricas_ai_first.get("llm_calls_sin_tokens", 0))
        + " |"
    )
    lineas.append(
        "| Estado usage tokens | "
        + _texto_metrica(metricas_ai_first.get("llm_tokens_estado", "sin_llamadas"))
        + " |"
    )
    lineas.append(
        "| Tokens prompt | "
        + _texto_metrica(metricas_ai_first.get("llm_tokens_prompt", 0))
        + " |"
    )
    lineas.append(
        "| Tokens completion | "
        + _texto_metrica(metricas_ai_first.get("llm_tokens_completion", 0))
        + " |"
    )
    lineas.append(
        "| Costo estimado (USD) | "
        + _texto_metrica_usd(metricas_ai_first.get("llm_costo_estimado_usd", 0))
        + " |"
    )
    lineas.append(
        "| Estado costo LLM | "
        + _texto_metrica(metricas_ai_first.get("llm_costo_estado", "sin_llamadas"))
        + " |"
    )
    lineas.append(
        "| Retries LLM | " + str(metricas_ai_first.get("total_retries", 0)) + " |"
    )
    lineas.append(
        "| Fallbacks | " + str(metricas_ai_first.get("total_fallbacks", 0)) + " |"
    )
    lineas.append(
        "| Embedding calls | "
        + str(metricas_ai_first.get("embedding_calls_totales", 0))
        + " |"
    )
    lineas.append(
        "| Embedding latencia promedio (ms) | "
        + str(metricas_ai_first.get("embedding_latencia_promedio_ms", 0))
        + " |"
    )
    lineas.append("")

    # Precision ambiguos
    if "precision_ambiguos" in comparacion.keys():
        prec = comparacion["precision_ambiguos"]
        lineas.append("## Precision en Registros Ambiguos")
        lineas.append("")
        lineas.append("| Metrica | Valor |")
        lineas.append("|---------|-------|")
        lineas.append("| Total evaluados | " + str(prec.get("evaluados", 0)) + " |")
        lineas.append("| Aciertos | " + str(prec.get("aciertos", 0)) + " |")
        lineas.append("| Precision | " + str(prec.get("porcentaje", 0)) + "% |")
        lineas.append("")

    return "\n".join(lineas)
