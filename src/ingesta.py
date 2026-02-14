# ingesta.py - Ingesta de archivos CSV, JSON y TXT (RF-01)
# Lee archivos CSV, JSON y TXT de solicitudes y retorna lista de diccionarios

import os
import json
import logger

MODULO = "INGESTA"

# Formatos de archivo soportados
FORMATOS_SOPORTADOS = ["csv", "json", "txt"]

# Campos esperados en el CSV
CAMPOS = [
    "id_solicitud",
    "fecha_solicitud",
    "tipo_producto",
    "id_cliente",
    "monto_o_limite",
    "moneda",
    "pais",
    "flag_prioritario",
    "flag_digital",
]


def separar_campos(linea):
    # Separa una linea CSV en campos
    # Si un campo tiene comillas, respeta las comas dentro de comillas
    # Maneja comillas escapadas CSV ("" se convierte en ")
    campos = []
    campo_actual = ""
    dentro_comillas = False
    i = 0
    while i < len(linea):
        c = linea[i]
        if c == '"':
            if dentro_comillas:
                # Dentro de comillas: verificar si es comilla escapada ("")
                if i + 1 < len(linea) and linea[i + 1] == '"':
                    # Comilla escapada: agregar una comilla literal y saltar la siguiente
                    campo_actual = campo_actual + '"'
                    i += 2
                    continue
                else:
                    # Cierre de comillas
                    dentro_comillas = False
            else:
                # Apertura de comillas
                dentro_comillas = True
        elif c == "," and not dentro_comillas:
            campos.append(campo_actual)
            campo_actual = ""
        else:
            campo_actual = campo_actual + c
        i += 1
    campos.append(campo_actual)
    return campos


def detectar_formato(archivo):
    # Detecta el formato del archivo segun su extension
    # Retorna: "csv", "json", "txt" o None si no es soportado
    partes = os.path.splitext(archivo)
    if len(partes) < 2:
        return None
    ext = partes[1]
    # Quitar el punto y convertir a minusculas
    if len(ext) > 0 and ext[0] == ".":
        ext = ext[1:]
    ext = ext.lower()
    if ext in FORMATOS_SOPORTADOS:
        return ext
    else:
        return None


def leer_json(archivo):
    # Lee un archivo JSON y retorna una lista de diccionarios
    # El JSON debe contener un array de objetos
    registros = []
    arch = open(archivo, "r", encoding="utf-8")
    contenido = arch.read()
    arch.close()

    # Intentar parsear el JSON
    datos = None
    try:
        datos = json.loads(contenido)
    except:
        logger.error(MODULO, "Error al parsear archivo JSON: " + archivo)
        return None

    # Validar que datos sea una lista
    if type(datos) != list:
        logger.error(MODULO, "El archivo JSON debe contener un array: " + archivo)
        return None

    # Procesar cada elemento
    for elem in datos:
        if type(elem) != dict:
            logger.warn(MODULO, "Elemento no es un diccionario, se omite")
            continue
        registros.append(elem)

    if len(registros) == 0:
        logger.warn(MODULO, "Archivo vacio (solo header o sin datos): " + archivo)
        return registros

    logger.info(
        MODULO,
        "Ingesta completada - "
        + str(len(registros))
        + " registros leidos de "
        + archivo,
    )
    return registros


def leer_txt(archivo):
    # Lee un archivo TXT delimitado por pipe (|) y retorna una lista de diccionarios
    # Primera linea es el header, lineas siguientes son datos
    registros = []
    arch = open(archivo, "r", encoding="utf-8")
    primera = True
    header = []

    for linea in arch:
        if linea[-1] == "\n":
            linea = linea[:-1]

        # Saltar lineas vacias
        if linea == "":
            continue

        # Leer el header (primera linea)
        if primera:
            ls = linea.split("|")
            i = 0
            while i < len(ls):
                header.append(ls[i].strip())
                i += 1
            primera = False
            continue

        # Leer datos
        ls = linea.split("|")
        reg = {}
        i = 0
        while i < len(header) and i < len(ls):
            reg[header[i]] = ls[i].strip()
            i += 1
        registros.append(reg)

    arch.close()

    # Verificar si el archivo estaba vacio (solo header)
    if len(registros) == 0:
        logger.warn(MODULO, "Archivo vacio (solo header o sin datos): " + archivo)
        return registros

    logger.info(
        MODULO,
        "Ingesta completada - "
        + str(len(registros))
        + " registros leidos de "
        + archivo,
    )
    return registros


def leer_solicitudes(archivo):
    # Lee un archivo CSV, JSON o TXT y retorna una lista de diccionarios
    # Cada diccionario tiene las claves del header

    # Verificar que el archivo existe
    if not os.path.exists(archivo):
        logger.error(MODULO, "Archivo no encontrado: " + archivo)
        return None

    # Detectar formato del archivo
    formato = detectar_formato(archivo)
    if formato == None:
        logger.error(MODULO, "Formato de archivo no soportado: " + archivo)
        return None

    # Procesar segun el formato
    if formato == "csv":
        # Logica original para CSV
        registros = []
        arch = open(archivo, "r", encoding="utf-8")
        primera = True
        header = []

        for linea in arch:
            if linea[-1] == "\n":
                linea = linea[:-1]

            # Saltar lineas vacias
            if linea == "":
                continue

            # Leer el header (primera linea)
            if primera:
                header = separar_campos(linea)
                primera = False
                continue

            # Leer datos
            ls = separar_campos(linea)
            reg = {}
            i = 0
            while i < len(header) and i < len(ls):
                reg[header[i]] = ls[i]
                i += 1
            registros.append(reg)

        arch.close()

        # Verificar si el archivo estaba vacio (solo header)
        if len(registros) == 0:
            logger.warn(MODULO, "Archivo vacio (solo header o sin datos): " + archivo)
            return registros

        logger.info(
            MODULO,
            "Ingesta completada - "
            + str(len(registros))
            + " registros leidos de "
            + archivo,
        )
        return registros
    elif formato == "json":
        return leer_json(archivo)
    elif formato == "txt":
        return leer_txt(archivo)
