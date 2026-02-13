# ingesta.py - Ingesta de archivos CSV (RF-01)
# Lee archivos CSV de solicitudes y retorna lista de diccionarios

import os
import logger

MODULO = "INGESTA"

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


def leer_solicitudes(archivo):
    # Lee un archivo CSV y retorna una lista de diccionarios
    # Cada diccionario tiene las claves del header

    # Verificar que el archivo existe
    if not os.path.exists(archivo):
        logger.error(MODULO, "Archivo no encontrado: " + archivo)
        return None

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
        logger.warn(MODULO, "Archivo CSV vacio (solo header): " + archivo)
        return registros

    logger.info(
        MODULO,
        "Ingesta completada - "
        + str(len(registros))
        + " registros leidos de "
        + archivo,
    )
    return registros
