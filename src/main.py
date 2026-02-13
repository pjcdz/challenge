# main.py - Orquestador del workflow (RF-05)
# Ejecuta secuencialmente todas las etapas del workflow

import os
import sys
import time
from datetime import datetime

# Agregar el directorio src al path para los imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import logger
import ingesta
import normalizador
import validador
import calidad

MODULO = "MAIN"


def escapar_campo_csv(valor):
    # Escapa un campo para CSV: si contiene comas, comillas o saltos de linea
    # lo envuelve en comillas dobles y duplica las comillas internas
    necesita_comillas = False
    i = 0
    while i < len(valor):
        c = valor[i]
        if c == "," or c == '"' or c == "\n":
            necesita_comillas = True
        i += 1
    if not necesita_comillas:
        return valor
    # Duplicar comillas internas
    resultado = ""
    i = 0
    while i < len(valor):
        c = valor[i]
        if c == '"':
            resultado = resultado + '""'
        else:
            resultado = resultado + c
        i += 1
    return '"' + resultado + '"'


def normalizar_nombre_para_ruta(nombre):
    # Deja solo letras, numeros, "_" y "-" para usar en nombres de carpeta
    salida = ""
    i = 0
    while i < len(nombre):
        c = nombre[i]
        if c.isalnum() or c == "_" or c == "-":
            salida = salida + c
        elif c == " ":
            salida = salida + "_"
        i += 1
    if salida == "":
        salida = "entrada"
    return salida


def crear_carpeta_ejecucion(dir_data, archivo_entrada):
    # Crea carpeta unica por ejecucion: data/ejecuciones/ejecucion_YYYYMMDD_HHMMSS_archivo
    nombre_entrada = os.path.basename(archivo_entrada)
    base_sin_ext = os.path.splitext(nombre_entrada)[0]
    base_sin_ext = normalizar_nombre_para_ruta(base_sin_ext)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    dir_ejecuciones = os.path.join(dir_data, "ejecuciones")
    if not os.path.exists(dir_ejecuciones):
        os.makedirs(dir_ejecuciones)

    nombre_base = "ejecucion_" + timestamp + "_" + base_sin_ext
    carpeta = os.path.join(dir_ejecuciones, nombre_base)
    idx = 1
    while os.path.exists(carpeta):
        carpeta = os.path.join(dir_ejecuciones, nombre_base + "_" + str(idx))
        idx += 1

    os.makedirs(carpeta)
    return carpeta


# Campos para el CSV de salida
CAMPOS_SALIDA = [
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
]


def exportar_csv(registros, ruta_salida):
    # Exporta los registros normalizados y validados a un CSV de salida
    dir_salida = os.path.dirname(ruta_salida)
    if dir_salida != "" and not os.path.exists(dir_salida):
        os.makedirs(dir_salida)
    arch = open(ruta_salida, "w", encoding="utf-8")

    # Escribir header
    linea_header = ""
    i = 0
    for campo in CAMPOS_SALIDA:
        if i > 0:
            linea_header = linea_header + ","
        linea_header = linea_header + escapar_campo_csv(campo)
        i += 1
    arch.write(linea_header + "\n")

    # Escribir registros
    for reg in registros:
        linea = ""
        idx = 0
        for campo in CAMPOS_SALIDA:
            if campo in reg.keys():
                val = reg[campo]
            else:
                val = ""
            if val == None:
                val = ""
            if idx > 0:
                linea = linea + ","
            linea = linea + escapar_campo_csv(str(val))
            idx += 1
        arch.write(linea + "\n")

    arch.close()
    logger.info(MODULO, "Datos exportados a: " + ruta_salida)


def main(archivo_entrada_param=None, archivo_salida_param=None, dir_data_param=None):
    # Orquestador principal del workflow
    # Acepta rutas opcionales para testing; si no se pasan, usa las por defecto
    inicio = time.time()

    # Rutas
    if dir_data_param != None:
        dir_data = dir_data_param
    else:
        dir_base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        dir_data = os.path.join(dir_base, "data")
    if archivo_entrada_param != None:
        archivo_entrada = archivo_entrada_param
    else:
        archivo_entrada = os.path.join(dir_data, "solicitudes.csv")

    # Crear carpeta unica de ejecucion y centralizar todos los artefactos ahi
    carpeta_ejecucion = crear_carpeta_ejecucion(dir_data, archivo_entrada)

    if archivo_salida_param != None:
        archivo_salida = archivo_salida_param
    else:
        archivo_salida = os.path.join(carpeta_ejecucion, "solicitudes_limpias.csv")

    archivo_reporte = os.path.join(carpeta_ejecucion, "reporte_calidad.json")

    # Inicializar logger de esta ejecucion
    archivo_log = logger.inicializar(carpeta_ejecucion, "workflow.log")

    # Paso 0: Inicio
    logger.info(
        MODULO,
        "Inicio del workflow - archivo: "
        + archivo_entrada
        + " - carpeta ejecucion: "
        + carpeta_ejecucion,
    )

    # Paso 1: Ingesta
    logger.info(MODULO, "--- PASO 1: INGESTA ---")
    registros = ingesta.leer_solicitudes(archivo_entrada)
    if registros == None:
        logger.error(MODULO, "No se pudo leer el archivo. Workflow detenido.")
        return {
            "status": "error",
            "archivo_entrada": archivo_entrada,
            "carpeta_ejecucion": carpeta_ejecucion,
            "archivo_salida": None,
            "archivo_reporte": None,
            "archivo_log": archivo_log,
        }
    if len(registros) == 0:
        logger.warn(MODULO, "No hay registros para procesar. Workflow detenido.")
        return {
            "status": "empty",
            "archivo_entrada": archivo_entrada,
            "carpeta_ejecucion": carpeta_ejecucion,
            "archivo_salida": None,
            "archivo_reporte": None,
            "archivo_log": archivo_log,
        }

    # Paso 2: Normalizacion
    logger.info(MODULO, "--- PASO 2: NORMALIZACION ---")
    registros = normalizador.normalizar_registros(registros)

    # Paso 3: Validacion
    logger.info(MODULO, "--- PASO 3: VALIDACION ---")
    registros = validador.validar_registros(registros)

    # Paso 4: Control de calidad
    logger.info(MODULO, "--- PASO 4: CONTROL DE CALIDAD ---")
    nombre_entrada = os.path.basename(archivo_entrada)
    reporte = calidad.generar_reporte(registros, nombre_entrada, carpeta_ejecucion)

    # Paso 5: Exportar datos
    logger.info(MODULO, "--- PASO 5: EXPORTAR SALIDA ---")
    exportar_csv(registros, archivo_salida)

    # Resumen final
    fin = time.time()
    duracion = round(fin - inicio, 2)
    total = len(registros)
    validos = 0
    invalidos = 0
    for reg in registros:
        if reg["estado"] == "VALIDO":
            validos += 1
        else:
            invalidos += 1

    logger.info(
        MODULO,
        "Workflow completado en "
        + str(duracion)
        + "s - "
        + str(total)
        + " procesados, "
        + str(validos)
        + " validos, "
        + str(invalidos)
        + " invalidos",
    )
    logger.info(
        MODULO,
        "Artefactos generados en: "
        + carpeta_ejecucion
        + " (CSV, reporte y log de esta ejecucion)",
    )

    return {
        "status": "ok",
        "archivo_entrada": archivo_entrada,
        "carpeta_ejecucion": carpeta_ejecucion,
        "archivo_salida": archivo_salida,
        "archivo_reporte": archivo_reporte,
        "archivo_log": archivo_log,
        "resumen": {
            "total_procesados": total,
            "total_validos": validos,
            "total_invalidos": invalidos,
        },
        "reporte": reporte,
    }


# Ejecutar el workflow
if __name__ == "__main__":
    main()
