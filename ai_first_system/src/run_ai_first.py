# run_ai_first.py - Runner principal del sistema AI-First
# Orquesta todo el workflow: ingesta -> enrutamiento -> normalizacion hibrida -> validacion -> calidad

import os
import sys
import time
import json
from datetime import datetime

dir_src = os.path.dirname(os.path.abspath(__file__))
dir_raiz = os.path.dirname(os.path.dirname(dir_src))
dir_legacy = os.path.join(dir_raiz, "legacy_system", "src")

sys.path.insert(0, dir_src)
sys.path.insert(0, dir_legacy)
sys.path.insert(0, os.path.join(dir_src, "agents"))
sys.path.insert(0, os.path.join(dir_src, "adapters"))
sys.path.insert(0, os.path.join(dir_src, "guardrails"))
sys.path.insert(0, os.path.join(dir_src, "graph"))

from config import MODO_MOCK, validar_config_llm, obtener_info_config, obtener_error_config_llm

MODULO = "RUN_AI_FIRST"


def crear_llm_provider(provider_nombre="gemini"):
    # Crea el provider de LLM segun configuracion
    # En ejecucion real no se permite modo mock
    if provider_nombre == None or provider_nombre == "":
        provider_nombre = "gemini"

    if MODO_MOCK:
        return (
            None,
            "AI_FIRST_MOCK=true no permitido en runtime. Usar GEMINI_API_KEY y modelos de .env.local",
        )

    # Validar config
    if not validar_config_llm():
        msg_error = obtener_error_config_llm()
        if msg_error == None or msg_error == "":
            msg_error = (
                "Configuracion LLM incompleta. Verifica GEMINI_API_KEY, GEMINI_GEMMA_MODEL y GEMINI_EMBEDDING_MODEL en .env.local"
            )
        return (
            None,
            msg_error,
        )

    if provider_nombre == "gemini":
        from gemini_adapter import GeminiAdapter

        adapter = GeminiAdapter()
        return adapter, None

    return None, "Provider no soportado: " + provider_nombre


def crear_carpeta_ejecucion(dir_data, archivo_entrada):
    # Crea carpeta unica por ejecucion del modo ai_first
    nombre_entrada = os.path.basename(archivo_entrada)
    base_sin_ext = os.path.splitext(nombre_entrada)[0]
    # Limpiar nombre
    salida = ""
    i = 0
    while i < len(base_sin_ext):
        c = base_sin_ext[i]
        if c.isalnum() or c == "_" or c == "-":
            salida = salida + c
        elif c == " ":
            salida = salida + "_"
        i = i + 1
    if salida == "":
        salida = "entrada"

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    dir_ejecuciones = os.path.join(dir_data, "ejecuciones")
    if not os.path.exists(dir_ejecuciones):
        os.makedirs(dir_ejecuciones)

    nombre_base = "ejecucion_" + timestamp + "_" + salida
    carpeta = os.path.join(dir_ejecuciones, nombre_base)
    idx = 1
    while os.path.exists(carpeta):
        carpeta = os.path.join(dir_ejecuciones, nombre_base + "_" + str(idx))
        idx = idx + 1

    os.makedirs(carpeta)
    return carpeta


def exportar_csv_ai_first(registros, ruta_salida):
    # Exporta registros a CSV con campos extendidos para AI-First
    campos = [
        "id_solicitud",
        "fecha_solicitud",
        "tipo_producto",
        "id_cliente",
        "monto_o_limite",
        "moneda",
        "pais",
        "flag_prioritario",
        "flag_digital",
        "categoria_riesgo",
        "estado",
        "motivos_falla",
        "origen_procesamiento",
    ]

    arch = open(ruta_salida, "w", encoding="utf-8")

    # Header
    linea_header = ""
    i = 0
    for campo in campos:
        if i > 0:
            linea_header = linea_header + ","
        linea_header = linea_header + campo
        i = i + 1
    arch.write(linea_header + "\n")

    # Datos
    for reg in registros:
        linea = ""
        idx = 0
        for campo in campos:
            if campo in reg.keys():
                val = reg[campo]
            else:
                val = ""
            if val == None:
                val = ""
            # Escapar comas en valores
            val_str = str(val)
            necesita_comillas = False
            j = 0
            while j < len(val_str):
                if val_str[j] == "," or val_str[j] == '"' or val_str[j] == "\n":
                    necesita_comillas = True
                j = j + 1
            if necesita_comillas:
                val_escapado = ""
                j = 0
                while j < len(val_str):
                    if val_str[j] == '"':
                        val_escapado = val_escapado + '""'
                    else:
                        val_escapado = val_escapado + val_str[j]
                    j = j + 1
                val_str = '"' + val_escapado + '"'
            if idx > 0:
                linea = linea + ","
            linea = linea + val_str
            idx = idx + 1
        arch.write(linea + "\n")

    arch.close()


def run(archivo_entrada, provider_nombre="gemini", dir_data=None):
    # Ejecuta el workflow AI-First completo
    # Retorna diccionario con resultados y metricas

    import logger

    inicio = time.time()

    # Paths
    if dir_data == None:
        dir_data = os.path.join(dir_raiz, "data")

    # Crear carpeta de ejecucion
    carpeta = crear_carpeta_ejecucion(dir_data, archivo_entrada)

    # Inicializar logger
    archivo_log = logger.inicializar(carpeta, "workflow.log")
    logger.info(MODULO, "Inicio workflow AI-First - archivo: " + archivo_entrada)
    logger.info(MODULO, "Provider: " + provider_nombre)

    # Info de config
    info = obtener_info_config()
    logger.info(MODULO, "Config: " + json.dumps(info, ensure_ascii=False))

    # Paso 1: Crear LLM provider
    logger.info(MODULO, "--- PASO 0: CONFIGURAR LLM ---")
    llm_provider, error_llm = crear_llm_provider(provider_nombre)
    if error_llm != None:
        logger.error(MODULO, "Error creando LLM provider: " + error_llm)
        return {
            "status": "error",
            "error": error_llm,
            "archivo_entrada": archivo_entrada,
            "carpeta_ejecucion": carpeta,
            "archivo_log": archivo_log,
        }

    # Paso 2: Ingesta
    logger.info(MODULO, "--- PASO 1: INGESTA ---")
    from agente_ingesta import ingestar

    registros, error_ingesta = ingestar(archivo_entrada)
    if error_ingesta != None:
        logger.error(MODULO, "Error en ingesta: " + error_ingesta)
        return {
            "status": "error",
            "error": error_ingesta,
            "archivo_entrada": archivo_entrada,
            "carpeta_ejecucion": carpeta,
            "archivo_log": archivo_log,
        }
    if len(registros) == 0:
        logger.warn(MODULO, "Sin registros para procesar")
        return {
            "status": "empty",
            "archivo_entrada": archivo_entrada,
            "carpeta_ejecucion": carpeta,
            "archivo_log": archivo_log,
        }

    logger.info(MODULO, "Registros leidos: " + str(len(registros)))

    # Paso 3: Normalizacion hibrida (reglas + LLM)
    logger.info(MODULO, "--- PASO 2: NORMALIZACION HIBRIDA ---")
    from agente_normalizador import normalizar_hibrido

    registros_norm, stats = normalizar_hibrido(registros, llm_provider)

    logger.info(MODULO, "Enrutamiento: " + json.dumps(stats, ensure_ascii=False))
    logger.info(MODULO, "Rule path: " + str(stats["regla_path"]) + " registros")
    logger.info(MODULO, "LLM path: " + str(stats["llm_path"]) + " registros")
    logger.info(
        MODULO,
        "Performance normalizacion -> preclasificacion: "
        + str(stats.get("tiempo_preclasificacion", 0.0))
        + "s, llm: "
        + str(stats.get("tiempo_llm", 0.0))
        + "s, postproceso: "
        + str(stats.get("tiempo_postproceso", 0.0))
        + "s",
    )

    # Paso 4: Validacion dura
    logger.info(MODULO, "--- PASO 3: VALIDACION ---")
    from agente_validador import validar

    registros_validados = validar(registros_norm)

    # Paso 5: Control de calidad
    logger.info(MODULO, "--- PASO 4: CONTROL DE CALIDAD ---")
    from agente_calidad import generar_reporte

    metricas_llm = llm_provider.obtener_metricas()
    nombre_entrada = os.path.basename(archivo_entrada)
    reporte = generar_reporte(
        registros_validados, nombre_entrada, carpeta, stats, metricas_llm
    )

    # Paso 6: Exportar CSV
    logger.info(MODULO, "--- PASO 5: EXPORTAR SALIDA ---")
    ruta_csv = os.path.join(carpeta, "solicitudes_limpias.csv")
    exportar_csv_ai_first(registros_validados, ruta_csv)
    logger.info(MODULO, "CSV exportado: " + ruta_csv)

    # Resumen
    fin = time.time()
    duracion = round(fin - inicio, 2)

    total = len(registros_validados)
    validos = 0
    invalidos = 0
    for reg in registros_validados:
        if "estado" in reg.keys() and reg["estado"] == "VALIDO":
            validos = validos + 1
        else:
            invalidos = invalidos + 1

    logger.info(
        MODULO,
        "Workflow AI-First completado en "
        + str(duracion)
        + "s - "
        + str(total)
        + " procesados, "
        + str(validos)
        + " validos, "
        + str(invalidos)
        + " invalidos",
    )

    resultado = {
        "status": "ok",
        "archivo_entrada": archivo_entrada,
        "carpeta_ejecucion": carpeta,
        "archivo_salida": ruta_csv,
        "archivo_reporte": os.path.join(carpeta, "reporte_calidad.json"),
        "archivo_log": archivo_log,
        "resumen": {
            "total_procesados": total,
            "total_validos": validos,
            "total_invalidos": invalidos,
            "duracion_segundos": duracion,
            "tiempo_preclasificacion": stats.get("tiempo_preclasificacion", 0.0),
            "tiempo_llm": stats.get("tiempo_llm", 0.0),
            "tiempo_postproceso": stats.get("tiempo_postproceso", 0.0),
        },
        "enrutamiento": stats,
        "metricas_llm": metricas_llm,
        "reporte": reporte,
    }

    return resultado
