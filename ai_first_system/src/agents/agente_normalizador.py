# agente_normalizador.py - Agente de normalizacion AI-First
# Normalizacion hibrida: reglas deterministicas + IA por lotes para ambiguos reales

import os
import sys
import json
import time
from concurrent.futures import ThreadPoolExecutor, wait


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
    # Carga el template de prompt de normalizacion individual desde archivo
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
    # Normaliza un registro ambiguo usando el LLM (modo individual compat)
    # Retorna (registro_normalizado, error)

    from verificador_salida import (
        verificar_respuesta_llm,
        generar_prompt_correctivo,
        aplicar_fallback,
    )

    reg_limpio = {}
    for campo in registro.keys():
        if campo[0] != "_":
            reg_limpio[campo] = registro[campo]

    template = cargar_prompt_normalizacion()
    prompt = template.replace(
        "{REGISTRO_JSON}", json.dumps(reg_limpio, ensure_ascii=False, indent=2)
    )

    max_intentos_total = 1
    if hasattr(llm_provider, "max_retries"):
        max_intentos_total = llm_provider.max_retries
    if max_intentos_total < 1:
        max_intentos_total = 1

    resultado_llm = llm_provider.generar_con_retry(
        prompt, "", "", max_intentos=max_intentos_total
    )
    intentos_totales = 1
    if "intento" in resultado_llm.keys():
        intentos_totales = resultado_llm["intento"]

    if resultado_llm["error"] != None:
        reg_fallback = aplicar_fallback(registro, resultado_llm["error"])
        reg_fallback["retries_llm"] = calcular_retries(intentos_totales)
        reg_fallback["fallback_aplicado"] = True
        return reg_fallback, None

    reg_normalizado, error_verificacion = verificar_respuesta_llm(
        resultado_llm["texto"], registro
    )

    if error_verificacion != None:
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

    reg_normalizado["retries_llm"] = calcular_retries(intentos_totales)
    reg_normalizado["fallback_aplicado"] = False
    reg_normalizado["origen_procesamiento"] = "llm_path"
    return reg_normalizado, None


def construir_payload_minimo_ambiguo(reg, clasificacion):
    # Construye payload minimo para enviar un ambiguo al LLM
    reglas = []
    if clasificacion != None and "reglas_afectadas" in clasificacion.keys():
        reglas = clasificacion["reglas_afectadas"]

    campos_amb = []
    if clasificacion != None and "campos_ambiguos" in clasificacion.keys():
        campos_amb = clasificacion["campos_ambiguos"]

    payload = {
        "id_solicitud": reg.get("id_solicitud", ""),
        "fecha_solicitud": reg.get("fecha_solicitud", ""),
        "tipo_producto": reg.get("tipo_producto", ""),
        "monto_o_limite": reg.get("monto_o_limite", ""),
        "moneda": reg.get("moneda", ""),
        "pais": reg.get("pais", ""),
        "reglas_a_validar": reglas,
        "campos_ambiguos": campos_amb,
    }
    return payload


def estimar_tokens_payload(payload):
    # Estima tokens aproximados de un payload
    txt = json.dumps(payload, ensure_ascii=False)
    n_chars = len(txt)
    n = int(n_chars / 4)
    n = n + 40
    if n < 60:
        n = 60
    return n


def construir_batches_ambiguos(registros, batch_size, max_tokens):
    # Arma lotes respetando tamano y presupuesto estimado de tokens
    lotes = []
    lote_actual = []
    tokens_actual = 0

    i = 0
    while i < len(registros):
        reg = registros[i]
        clasif = {}
        if "_clasificacion" in reg.keys():
            clasif = reg["_clasificacion"]

        payload = construir_payload_minimo_ambiguo(reg, clasif)
        tok = estimar_tokens_payload(payload)

        necesita_corte = False
        if len(lote_actual) > 0:
            if len(lote_actual) >= batch_size:
                necesita_corte = True
            elif tokens_actual + tok > max_tokens:
                necesita_corte = True

        if necesita_corte:
            lotes.append(lote_actual)
            lote_actual = []
            tokens_actual = 0

        item = {
            "registro": reg,
            "payload": payload,
            "tokens_estimados": tok,
        }
        lote_actual.append(item)
        tokens_actual = tokens_actual + tok

        i = i + 1

    if len(lote_actual) > 0:
        lotes.append(lote_actual)

    return lotes


def construir_prompt_batch(lote, ronda, nro_lote):
    # Construye prompt estricto para normalizacion por lote
    registros_payload = []
    i = 0
    while i < len(lote):
        registros_payload.append(lote[i]["payload"])
        i = i + 1

    entrada = {
        "ronda": ronda,
        "batch": nro_lote,
        "registros": registros_payload,
    }

    prompt = "Sos un normalizador estricto de solicitudes financieras.\n"
    prompt = prompt + "Solo resuelve registros ambiguos.\n"
    prompt = prompt + "No inventes valores. Si no se puede resolver, marca NO_RESUELTO.\n"
    prompt = prompt + "\n"
    prompt = prompt + "Devuelve UNICAMENTE JSON valido con esta estructura exacta:\n"
    prompt = prompt + "{\"resultados\":[{\"id_solicitud\":\"...\",\"fecha_solicitud\":\"...\",\"tipo_producto\":\"...\",\"monto_o_limite\":\"...\",\"moneda\":\"...\",\"pais\":\"...\",\"estado_ia\":\"RESUELTO|NO_RESUELTO\",\"motivo_ia\":\"...\"}]}\n"
    prompt = prompt + "\n"
    prompt = prompt + "Reglas:\n"
    prompt = prompt + "- fecha_solicitud: preferir DD/MM/YYYY\n"
    prompt = prompt + "- tipo_producto: CUENTA/TARJETA/SERVICIO/PRESTAMO/SEGURO\n"
    prompt = prompt + "- moneda: ARS/USD/EUR\n"
    prompt = prompt + "- monto_o_limite: entero en string\n"
    prompt = prompt + "- pais: nombre canonico\n"
    prompt = prompt + "\n"
    prompt = prompt + "Entrada lote:\n"
    prompt = prompt + json.dumps(entrada, ensure_ascii=False)

    return prompt


def _buscar_resultado_por_id(resultados, id_solicitud):
    # Busca resultado por id_solicitud en lista de resultados del LLM
    i = 0
    while i < len(resultados):
        item = resultados[i]
        if type(item) == dict:
            if "id_solicitud" in item.keys():
                if str(item["id_solicitud"]) == str(id_solicitud):
                    return item
        i = i + 1
    return None


def _actualizar_traza_llm(reg, ronda, batch, estado, motivo):
    # Actualiza trazabilidad AI por registro
    if "_traza_ai" not in reg.keys() or type(reg["_traza_ai"]) != dict:
        reg["_traza_ai"] = {}

    traza = reg["_traza_ai"]
    traza["paso_llm"] = True
    traza["ronda_llm"] = ronda
    traza["batch_llm"] = batch
    traza["estado_llm"] = estado
    traza["motivo_llm"] = motivo
    reg["_traza_ai"] = traza


def procesar_lote_llm(lote, llm_provider, ronda, nro_lote, max_intentos_batch):
    # Procesa un lote ambiguo contra LLM y retorna resueltos/pendientes
    from verificador_salida import verificar_respuesta_llm, extraer_json_de_texto

    prompt = construir_prompt_batch(lote, ronda, nro_lote)
    respuesta = llm_provider.generar_con_retry(
        prompt,
        "",
        "",
        max_intentos=max_intentos_batch,
    )

    salida = {
        "resueltos": [],
        "pendientes": [],
        "error": None,
        "batch": nro_lote,
        "ronda": ronda,
    }

    if respuesta["error"] != None:
        salida["error"] = respuesta["error"]
        i = 0
        while i < len(lote):
            reg = lote[i]["registro"]
            _actualizar_traza_llm(reg, ronda, nro_lote, "ERROR", respuesta["error"])
            salida["pendientes"].append(
                {
                    "registro": reg,
                    "motivo": "error_batch: " + str(respuesta["error"]),
                }
            )
            i = i + 1
        return salida

    datos_json, error_json = extraer_json_de_texto(respuesta["texto"])
    if error_json != None:
        salida["error"] = "error_parseo_json: " + str(error_json)
        i = 0
        while i < len(lote):
            reg = lote[i]["registro"]
            _actualizar_traza_llm(reg, ronda, nro_lote, "ERROR", str(error_json))
            salida["pendientes"].append(
                {
                    "registro": reg,
                    "motivo": "error_parseo_json: " + str(error_json),
                }
            )
            i = i + 1
        return salida

    resultados = []
    if type(datos_json) == dict:
        if "resultados" in datos_json.keys() and type(datos_json["resultados"]) == list:
            resultados = datos_json["resultados"]
    elif type(datos_json) == list:
        resultados = datos_json

    if len(resultados) == 0:
        salida["error"] = "respuesta_batch_sin_resultados"
        i = 0
        while i < len(lote):
            reg = lote[i]["registro"]
            _actualizar_traza_llm(reg, ronda, nro_lote, "ERROR", "sin_resultados")
            salida["pendientes"].append(
                {
                    "registro": reg,
                    "motivo": "respuesta_batch_sin_resultados",
                }
            )
            i = i + 1
        return salida

    i = 0
    while i < len(lote):
        item_lote = lote[i]
        reg_original = item_lote["registro"]
        id_sol = reg_original.get("id_solicitud", "")

        item_res = _buscar_resultado_por_id(resultados, id_sol)
        if item_res == None:
            _actualizar_traza_llm(
                reg_original,
                ronda,
                nro_lote,
                "PENDIENTE",
                "id_solicitud no devuelto por IA",
            )
            salida["pendientes"].append(
                {
                    "registro": reg_original,
                    "motivo": "id_solicitud no devuelto por IA",
                }
            )
            i = i + 1
            continue

        estado_ia = "RESUELTO"
        if "estado_ia" in item_res.keys():
            estado_ia = str(item_res["estado_ia"]).strip().upper()

        motivo_ia = ""
        if "motivo_ia" in item_res.keys():
            motivo_ia = str(item_res["motivo_ia"])

        if estado_ia == "NO_RESUELTO":
            _actualizar_traza_llm(reg_original, ronda, nro_lote, "PENDIENTE", motivo_ia)
            salida["pendientes"].append(
                {
                    "registro": reg_original,
                    "motivo": "no_resuelto_ia: " + motivo_ia,
                }
            )
            i = i + 1
            continue

        d_verificar = {}
        campos = [
            "id_solicitud",
            "fecha_solicitud",
            "tipo_producto",
            "id_cliente",
            "monto_o_limite",
            "moneda",
            "pais",
        ]
        j = 0
        while j < len(campos):
            c = campos[j]
            if c in item_res.keys():
                d_verificar[c] = item_res[c]
            j = j + 1

        txt_verificar = json.dumps(d_verificar, ensure_ascii=False)
        reg_norm, err_ver = verificar_respuesta_llm(txt_verificar, reg_original)

        if err_ver != None:
            _actualizar_traza_llm(
                reg_original,
                ronda,
                nro_lote,
                "PENDIENTE",
                "schema_error: " + str(err_ver),
            )
            salida["pendientes"].append(
                {
                    "registro": reg_original,
                    "motivo": "schema_error: " + str(err_ver),
                }
            )
            i = i + 1
            continue

        reg_norm["origen_procesamiento"] = "llm_path"
        reg_norm["retries_llm"] = calcular_retries(ronda)
        reg_norm["fallback_aplicado"] = False

        if "_idx_original" in reg_original.keys():
            reg_norm["_idx_original"] = reg_original["_idx_original"]
        if "_clasificacion" in reg_original.keys():
            reg_norm["_clasificacion"] = reg_original["_clasificacion"]
        if "_traza_ai" in reg_original.keys():
            reg_norm["_traza_ai"] = reg_original["_traza_ai"]

        _actualizar_traza_llm(reg_norm, ronda, nro_lote, "RESUELTO", motivo_ia)

        salida["resueltos"].append(reg_norm)
        i = i + 1

    return salida


def _deduplicar_pendientes(pendientes):
    # Deduplica pendientes por id_solicitud preservando ultimo motivo
    d = {}
    orden = []

    i = 0
    while i < len(pendientes):
        item = pendientes[i]
        reg = item["registro"]
        id_sol = str(reg.get("id_solicitud", ""))

        if id_sol not in d.keys():
            orden.append(id_sol)

        d[id_sol] = item
        i = i + 1

    res = []
    j = 0
    while j < len(orden):
        id_sol = orden[j]
        res.append(d[id_sol])
        j = j + 1

    return res


def normalizar_ambiguos_por_lotes(registros_ambiguos, llm_provider):
    # Procesa ambiguos en lotes paralelos y por rondas
    # Retorna (registros_resueltos, stats_llm)

    import logger
    from config import (
        BATCH_TAMANO,
        BATCH_MAX_TOKENS_ESTIMADOS,
        BATCH_MAX_WORKERS,
        BATCH_TIMEOUT_SEGUNDOS,
        BATCH_MAX_RONDAS,
        BATCH_REINTENTOS_POR_BATCH,
        BATCH_BACKOFF_SEGUNDOS,
    )
    from verificador_salida import aplicar_fallback

    inicio_llm = time.time()

    metricas_ini = llm_provider.obtener_metricas()
    calls_ini = metricas_ini.get("total_llamadas", 0)

    pendientes = []
    i = 0
    while i < len(registros_ambiguos):
        pendientes.append({"registro": registros_ambiguos[i], "motivo": "pendiente"})
        i = i + 1

    resueltos = []
    total_batches = 0
    total_registros_en_batches = 0
    rondas_ejecutadas = 0

    ronda = 1
    while len(pendientes) > 0 and ronda <= BATCH_MAX_RONDAS:
        rondas_ejecutadas = ronda

        regs_pendientes = []
        i = 0
        while i < len(pendientes):
            regs_pendientes.append(pendientes[i]["registro"])
            i = i + 1

        lotes = construir_batches_ambiguos(
            regs_pendientes,
            BATCH_TAMANO,
            BATCH_MAX_TOKENS_ESTIMADOS,
        )

        total_batches = total_batches + len(lotes)
        i = 0
        while i < len(lotes):
            total_registros_en_batches = total_registros_en_batches + len(lotes[i])
            i = i + 1

        logger.info(
            MODULO,
            "Ronda "
            + str(ronda)
            + " -> "
            + str(len(regs_pendientes))
            + " pendientes en "
            + str(len(lotes))
            + " batches",
        )

        pendientes_siguiente = []

        if len(lotes) == 0:
            break

        with ThreadPoolExecutor(max_workers=BATCH_MAX_WORKERS) as ex:
            futuros = {}

            i = 0
            while i < len(lotes):
                nro_lote = i + 1
                fut = ex.submit(
                    procesar_lote_llm,
                    lotes[i],
                    llm_provider,
                    ronda,
                    nro_lote,
                    BATCH_REINTENTOS_POR_BATCH,
                )
                futuros[fut] = {"lote": lotes[i], "nro_lote": nro_lote}
                i = i + 1

            lista_futuros = []
            for f in futuros.keys():
                lista_futuros.append(f)

            done, not_done = wait(lista_futuros, timeout=BATCH_TIMEOUT_SEGUNDOS)

            for fut in done:
                meta = futuros[fut]
                try:
                    r = fut.result()
                except Exception as e:
                    lote_error = meta["lote"]
                    j = 0
                    while j < len(lote_error):
                        reg = lote_error[j]["registro"]
                        _actualizar_traza_llm(
                            reg,
                            ronda,
                            meta["nro_lote"],
                            "ERROR",
                            "excepcion_batch: " + str(e),
                        )
                        pendientes_siguiente.append(
                            {
                                "registro": reg,
                                "motivo": "excepcion_batch: " + str(e),
                            }
                        )
                        j = j + 1
                    continue

                j = 0
                while j < len(r["resueltos"]):
                    resueltos.append(r["resueltos"][j])
                    j = j + 1

                j = 0
                while j < len(r["pendientes"]):
                    pendientes_siguiente.append(r["pendientes"][j])
                    j = j + 1

            for fut in not_done:
                meta = futuros[fut]
                lote_timeout = meta["lote"]
                j = 0
                while j < len(lote_timeout):
                    reg = lote_timeout[j]["registro"]
                    _actualizar_traza_llm(
                        reg,
                        ronda,
                        meta["nro_lote"],
                        "TIMEOUT",
                        "timeout lote",
                    )
                    pendientes_siguiente.append(
                        {
                            "registro": reg,
                            "motivo": "timeout lote",
                        }
                    )
                    j = j + 1

                try:
                    fut.cancel()
                except Exception:
                    pass

        pendientes = _deduplicar_pendientes(pendientes_siguiente)

        if len(pendientes) > 0 and ronda < BATCH_MAX_RONDAS:
            if BATCH_BACKOFF_SEGUNDOS > 0:
                time.sleep(BATCH_BACKOFF_SEGUNDOS)

        ronda = ronda + 1

    # Pendientes agotados por rondas -> fallback tecnico
    pendientes_tecnicos = 0
    i = 0
    while i < len(pendientes):
        item_p = pendientes[i]
        reg_orig = item_p["registro"]
        motivo = item_p.get("motivo", "error tecnico")
        msg = (
            "timeout/error tecnico tras "
            + str(BATCH_MAX_RONDAS)
            + " rondas. Ultimo motivo: "
            + str(motivo)
        )

        reg_fb = aplicar_fallback(reg_orig, msg)
        reg_fb["retries_llm"] = calcular_retries(BATCH_MAX_RONDAS)
        reg_fb["fallback_aplicado"] = True

        if "_idx_original" in reg_orig.keys():
            reg_fb["_idx_original"] = reg_orig["_idx_original"]
        if "_clasificacion" in reg_orig.keys():
            reg_fb["_clasificacion"] = reg_orig["_clasificacion"]
        if "_traza_ai" in reg_orig.keys():
            reg_fb["_traza_ai"] = reg_orig["_traza_ai"]

        _actualizar_traza_llm(
            reg_fb,
            BATCH_MAX_RONDAS,
            0,
            "FALLBACK_TECNICO",
            msg,
        )

        resueltos.append(reg_fb)
        pendientes_tecnicos = pendientes_tecnicos + 1
        i = i + 1

    # Post-normalizar cada salida LLM/fallback con reglas legacy
    salida_final = []
    total_fallbacks = 0
    total_retries = 0

    i = 0
    while i < len(resueltos):
        reg_norm = resueltos[i]

        reg_post = normalizar_con_reglas([reg_norm])
        if len(reg_post) > 0:
            reg_out = reg_post[0]
        else:
            reg_out = reg_norm

        reg_out["origen_procesamiento"] = "llm_path"

        if "retries_llm" in reg_norm.keys():
            reg_out["retries_llm"] = reg_norm["retries_llm"]
            total_retries = total_retries + reg_norm["retries_llm"]

        if "fallback_aplicado" in reg_norm.keys():
            reg_out["fallback_aplicado"] = reg_norm["fallback_aplicado"]
            if reg_norm["fallback_aplicado"]:
                total_fallbacks = total_fallbacks + 1

        if "_idx_original" in reg_norm.keys():
            reg_out["_idx_original"] = reg_norm["_idx_original"]
        if "_clasificacion" in reg_norm.keys():
            reg_out["_clasificacion"] = reg_norm["_clasificacion"]
        if "_traza_ai" in reg_norm.keys():
            reg_out["_traza_ai"] = reg_norm["_traza_ai"]

        salida_final.append(reg_out)
        i = i + 1

    metricas_fin = llm_provider.obtener_metricas()
    calls_fin = metricas_fin.get("total_llamadas", 0)
    llm_calls_totales = calls_fin - calls_ini
    if llm_calls_totales < 0:
        llm_calls_totales = 0

    batch_prom = 0.0
    if total_batches > 0:
        batch_prom = round((total_registros_en_batches * 1.0) / total_batches, 2)

    fin_llm = time.time()
    tiempo_llm = round(fin_llm - inicio_llm, 4)

    stats_llm = {
        "batches_total": total_batches,
        "batch_size_promedio": batch_prom,
        "rounds_total": rondas_ejecutadas,
        "total_fallbacks": total_fallbacks,
        "total_retries": total_retries,
        "pendientes_tecnicos": pendientes_tecnicos,
        "llm_calls_totales": llm_calls_totales,
        "tiempo_llm": tiempo_llm,
    }

    return salida_final, stats_llm


def normalizar_hibrido(registros, llm_provider):
    # Normalizacion hibrida optimizada: clasificacion deterministica + IA por batch
    # Retorna (registros_normalizados, estadisticas)

    from router_ambiguedad import enrutar_registros

    inicio_total = time.time()

    # Paso 0: Marcar indice original para preservar orden de salida
    i = 0
    while i < len(registros):
        registros[i]["_idx_original"] = i
        i = i + 1

    # Paso 1: Preclasificacion deterministica
    t_pre_ini = time.time()
    regla_path, llm_path, stats = enrutar_registros(registros, llm_provider)
    t_pre_fin = time.time()

    # Paso 2: Normalizar regla_path con reglas legacy
    regla_normalizados = normalizar_con_reglas(regla_path)

    # Paso 3: Normalizar llm_path con lotes paralelos por rondas
    llm_normalizados = []
    stats_llm = {
        "batches_total": 0,
        "batch_size_promedio": 0.0,
        "rounds_total": 0,
        "total_fallbacks": 0,
        "total_retries": 0,
        "pendientes_tecnicos": 0,
        "llm_calls_totales": 0,
        "tiempo_llm": 0.0,
    }

    if len(llm_path) > 0:
        llm_normalizados, stats_llm = normalizar_ambiguos_por_lotes(llm_path, llm_provider)

    # Paso 4: Combinar resultados preservando orden original
    t_post_ini = time.time()

    combinado = regla_normalizados + llm_normalizados
    d_por_idx = {}
    sin_idx = []
    i = 0
    while i < len(combinado):
        reg = combinado[i]
        if "_idx_original" in reg.keys():
            d_por_idx[reg["_idx_original"]] = reg
        else:
            sin_idx.append(reg)
        i = i + 1

    resultado = []
    i = 0
    while i < len(registros):
        if i in d_por_idx.keys():
            resultado.append(d_por_idx[i])
        i = i + 1

    i = 0
    while i < len(sin_idx):
        resultado.append(sin_idx[i])
        i = i + 1

    # Limpiar campo interno de orden (se conserva trazabilidad _traza_ai)
    i = 0
    while i < len(resultado):
        if "_idx_original" in resultado[i].keys():
            del resultado[i]["_idx_original"]
        if "_clasificacion" in resultado[i].keys():
            del resultado[i]["_clasificacion"]
        i = i + 1

    t_post_fin = time.time()
    fin_total = time.time()

    stats["total_fallbacks"] = stats_llm.get("total_fallbacks", 0)
    stats["total_retries"] = stats_llm.get("total_retries", 0)
    stats["batches_total"] = stats_llm.get("batches_total", 0)
    stats["batch_size_promedio"] = stats_llm.get("batch_size_promedio", 0.0)
    stats["rounds_total"] = stats_llm.get("rounds_total", 0)
    stats["llm_calls_totales"] = stats_llm.get("llm_calls_totales", 0)
    stats["tiempo_preclasificacion"] = round(t_pre_fin - t_pre_ini, 4)
    stats["tiempo_llm"] = round(stats_llm.get("tiempo_llm", 0.0), 4)
    stats["tiempo_postproceso"] = round(t_post_fin - t_post_ini, 4)
    stats["tiempo_total"] = round(fin_total - inicio_total, 4)

    return resultado, stats
