# agente_normalizador.py - Agente de normalizacion AI-First
# Normalizacion hibrida: reglas deterministicas + LLM para casos ambiguos

import os
import sys
import json

dir_src = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
dir_legacy = os.path.join(
    os.path.dirname(os.path.dirname(dir_src)), "legacy_system", "src"
)
sys.path.insert(0, dir_src)
sys.path.insert(0, dir_legacy)
sys.path.insert(0, os.path.join(dir_src, "guardrails"))
sys.path.insert(0, os.path.join(dir_src, "adapters"))
sys.path.insert(0, os.path.join(dir_src, "graph"))

MODULO = "AGENTE_NORMALIZADOR"


def cargar_prompt_normalizacion():
    # Carga el template de prompt de normalizacion desde archivo
    ruta = os.path.join(dir_src, "prompts", "normalizacion_prompt.md")
    arch = open(ruta, "r", encoding="utf-8")
    contenido = arch.read()
    arch.close()
    return contenido


def normalizar_con_reglas(registros):
    # Aplica normalizacion legacy (deterministica) a los registros
    import normalizador

    return normalizador.normalizar_registros(registros)


def calcular_retries(intentos_totales):
    # retries = intentos adicionales despues del primero
    if intentos_totales <= 1:
        return 0
    return intentos_totales - 1


def normalizar_con_llm(registro, llm_provider):
    # Normaliza un registro ambiguo usando el LLM
    # Retorna (registro_normalizado, error)

    from verificador_salida import (
        verificar_respuesta_llm,
        generar_prompt_correctivo,
        aplicar_fallback,
    )

    # Preparar registro para el prompt (sin campos internos)
    reg_limpio = {}
    for campo in registro.keys():
        if campo[0] != "_":
            reg_limpio[campo] = registro[campo]

    # Cargar y rellenar prompt
    template = cargar_prompt_normalizacion()
    prompt = template.replace(
        "{REGISTRO_JSON}", json.dumps(reg_limpio, ensure_ascii=False, indent=2)
    )

    # Presupuesto total de intentos para todo el flujo de este registro
    max_intentos_total = 1
    if hasattr(llm_provider, "max_retries"):
        max_intentos_total = llm_provider.max_retries
    if max_intentos_total < 1:
        max_intentos_total = 1

    # Intentar normalizacion base con retry acotado del provider
    resultado_llm = llm_provider.generar_con_retry(
        prompt, "", "", max_intentos=max_intentos_total
    )
    intentos_totales = 1
    if "intento" in resultado_llm.keys():
        intentos_totales = resultado_llm["intento"]

    if resultado_llm["error"] != None:
        # Fallo total - aplicar fallback
        reg_fallback = aplicar_fallback(registro, resultado_llm["error"])
        reg_fallback["retries_llm"] = calcular_retries(intentos_totales)
        reg_fallback["fallback_aplicado"] = True
        return reg_fallback, None

    # Verificar respuesta contra schema
    reg_normalizado, error_verificacion = verificar_respuesta_llm(
        resultado_llm["texto"], registro
    )

    if error_verificacion != None:
        # Schema fallo - intentar con prompt correctivo
        intentos_restantes = max_intentos_total - intentos_totales
        if intentos_restantes <= 0:
            reg_fallback = aplicar_fallback(registro, error_verificacion)
            reg_fallback["retries_llm"] = calcular_retries(intentos_totales)
            reg_fallback["fallback_aplicado"] = True
            return reg_fallback, None

        prompt_corr = generar_prompt_correctivo(error_verificacion, reg_limpio)
        prompt_corregido = prompt + "\n\n" + prompt_corr
        resultado_retry = llm_provider.generar_con_retry(
            prompt_corregido, "", "", max_intentos=intentos_restantes
        )
        intentos_nuevo = 1
        if "intento" in resultado_retry.keys():
            intentos_nuevo = resultado_retry["intento"]
        intentos_totales = intentos_totales + intentos_nuevo

        if resultado_retry["error"] != None:
            reg_fallback = aplicar_fallback(registro, resultado_retry["error"])
            reg_fallback["retries_llm"] = calcular_retries(intentos_totales)
            reg_fallback["fallback_aplicado"] = True
            return reg_fallback, None

        reg_normalizado, error_verificacion2 = verificar_respuesta_llm(
            resultado_retry["texto"], registro
        )
        if error_verificacion2 != None:
            reg_fallback = aplicar_fallback(registro, error_verificacion2)
            reg_fallback["retries_llm"] = calcular_retries(intentos_totales)
            reg_fallback["fallback_aplicado"] = True
            return reg_fallback, None

    # Exito
    reg_normalizado["retries_llm"] = calcular_retries(intentos_totales)
    reg_normalizado["fallback_aplicado"] = False
    reg_normalizado["origen_procesamiento"] = "llm_path"
    return reg_normalizado, None


def normalizar_hibrido(registros, llm_provider):
    # Normalizacion hibrida: reglas para limpios, LLM para ambiguos
    # Retorna (registros_normalizados, estadisticas)

    from router_ambiguedad import enrutar_registros
    from workflow_graph import procesar_registro_ambiguo
    from config import MAX_RETRIES_LLM

    # Paso 0: Marcar indice original para preservar orden de salida
    i = 0
    while i < len(registros):
        registros[i]["_idx_original"] = i
        i = i + 1

    # Paso 1: Clasificar registros
    regla_path, llm_path, stats = enrutar_registros(registros, llm_provider)

    # Paso 2: Normalizar regla_path con reglas legacy
    regla_normalizados = normalizar_con_reglas(regla_path)

    # Paso 3: Normalizar llm_path con LLM
    llm_normalizados = []
    total_fallbacks = 0
    total_retries = 0

    for reg in llm_path:
        reg_norm = None
        clasificacion = {}
        if "_clasificacion" in reg.keys():
            clasificacion = reg["_clasificacion"]
        else:
            clasificacion = {
                "motivos_ambiguedad": ["registro marcado ambiguo sin clasificacion"],
                "campos_ambiguos": [],
            }

        try:
            reg_norm = procesar_registro_ambiguo(
                reg, clasificacion, llm_provider, MAX_RETRIES_LLM
            )
        except Exception:
            reg_norm = None

        if reg_norm == None:
            reg_norm, error = normalizar_con_llm(reg, llm_provider)

        if reg_norm != None:
            if "_idx_original" in reg.keys():
                reg_norm["_idx_original"] = reg["_idx_original"]
            if "_clasificacion" in reg.keys():
                reg_norm["_clasificacion"] = reg["_clasificacion"]

            # Aplicar normalizacion legacy adicional sobre resultado LLM
            # (trimming, categoria_riesgo, etc)
            reg_post = normalizar_con_reglas([reg_norm])
            if len(reg_post) > 0:
                reg_post[0]["origen_procesamiento"] = "llm_path"
                if "retries_llm" in reg_norm.keys():
                    reg_post[0]["retries_llm"] = reg_norm["retries_llm"]
                if "fallback_aplicado" in reg_norm.keys():
                    reg_post[0]["fallback_aplicado"] = reg_norm["fallback_aplicado"]
                    if reg_norm["fallback_aplicado"]:
                        total_fallbacks = total_fallbacks + 1
                if "retries_llm" in reg_norm.keys():
                    total_retries = total_retries + reg_norm["retries_llm"]
                llm_normalizados.append(reg_post[0])
            else:
                llm_normalizados.append(reg_norm)

    # Paso 4: Combinar resultados preservando orden original
    combinado = regla_normalizados + llm_normalizados
    d_por_idx = {}
    sin_idx = []
    for reg in combinado:
        if "_idx_original" in reg.keys():
            d_por_idx[reg["_idx_original"]] = reg
        else:
            sin_idx.append(reg)

    resultado = []
    i = 0
    while i < len(registros):
        if i in d_por_idx.keys():
            resultado.append(d_por_idx[i])
        i = i + 1

    for reg in sin_idx:
        resultado.append(reg)

    # Limpiar campos internos de orden/clasificacion antes de devolver
    for reg in resultado:
        if "_idx_original" in reg.keys():
            del reg["_idx_original"]
        if "_clasificacion" in reg.keys():
            del reg["_clasificacion"]

    stats["total_fallbacks"] = total_fallbacks
    stats["total_retries"] = total_retries

    return resultado, stats
