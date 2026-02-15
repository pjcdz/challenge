# logger.py - Sistema de logging (RNF-01)
# Registra eventos del workflow con timestamps y niveles

import os
from datetime import datetime

# Carpeta de logs por defecto para uso manual (fuera de main.py)
CARPETA_LOGS_DEFAULT = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data",
    "ejecuciones",
    "sesion_default",
)

# Archivo de log activo
ARCHIVO_LOG = ""


def inicializar(carpeta_logs=None, nombre_archivo=None):
    # Crea carpeta de logs y define archivo destino.
    # Si no se pasa carpeta/nombre, usa ubicacion por defecto en data/ejecuciones.
    global ARCHIVO_LOG

    if carpeta_logs == None:
        carpeta_logs = CARPETA_LOGS_DEFAULT
    if nombre_archivo == None:
        nombre_archivo = "workflow.log"

    if not os.path.exists(carpeta_logs):
        os.makedirs(carpeta_logs)

    ARCHIVO_LOG = os.path.join(carpeta_logs, nombre_archivo)
    return ARCHIVO_LOG


def registrar(nivel, modulo, mensaje):
    # Registra un evento en el log
    # Formato: [YYYY-MM-DD HH:MM:SS] [NIVEL] [MODULO] Mensaje
    global ARCHIVO_LOG
    if ARCHIVO_LOG == "":
        inicializar()
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    linea = "[" + ts + "] [" + nivel + "] [" + modulo + "] " + mensaje
    print(linea)
    dir_log = os.path.dirname(ARCHIVO_LOG)
    if dir_log != "" and not os.path.exists(dir_log):
        os.makedirs(dir_log)
    arch = open(ARCHIVO_LOG, "a", encoding="utf-8")
    arch.write(linea + "\n")
    arch.close()
    return linea


def info(modulo, mensaje):
    # Atajo para registrar nivel INFO
    return registrar("INFO", modulo, mensaje)


def warn(modulo, mensaje):
    # Atajo para registrar nivel WARN
    return registrar("WARN", modulo, mensaje)


def error(modulo, mensaje):
    # Atajo para registrar nivel ERROR
    return registrar("ERROR", modulo, mensaje)
