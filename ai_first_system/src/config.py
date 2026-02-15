# config.py - Configuracion centralizada del sistema AI-First
# Carga variables de entorno desde .env.local y expone constantes de configuracion

import os
import sys


MODULO = "CONFIG"

# Ruta base del proyecto (raiz del challenge)
DIR_RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
RUTA_ENV_LOCAL = os.path.join(DIR_RAIZ, ".env.local")
ENV_LOCAL_EXISTE = os.path.exists(RUTA_ENV_LOCAL)

# Intentar cargar dotenv si esta disponible
_dotenv_cargado = False
if ENV_LOCAL_EXISTE:
    try:
        from dotenv import load_dotenv

        load_dotenv(RUTA_ENV_LOCAL)
        _dotenv_cargado = True
    except:
        pass


def obtener_variable(nombre, valor_defecto=None):
    # Obtiene una variable de entorno con valor por defecto opcional
    val = os.environ.get(nombre)
    if val == None or val == "":
        return valor_defecto
    return val


def leer_env_local():
    # Lee .env.local manualmente para garantizar fuente de verdad obligatoria
    # Retorna diccionario simple clave->valor
    d = {}
    if not ENV_LOCAL_EXISTE:
        return d
    try:
        arch = open(RUTA_ENV_LOCAL, "r", encoding="utf-8")
        for linea in arch:
            if linea == None:
                continue
            if len(linea) > 0 and linea[-1] == "\n":
                linea = linea[:-1]
            txt = linea.strip()
            if txt == "":
                continue
            if txt[0] == "#":
                continue
            pos = txt.find("=")
            if pos <= 0:
                continue
            clave = txt[:pos].strip()
            valor = txt[pos + 1 :].strip()
            if len(valor) >= 2:
                if valor[0] == '"' and valor[-1] == '"':
                    valor = valor[1:-1]
                elif valor[0] == "'" and valor[-1] == "'":
                    valor = valor[1:-1]
            d[clave] = valor
        arch.close()
    except Exception:
        return {}
    return d


# --- Configuracion de Gemini ---
ENV_LOCAL_VALORES = leer_env_local()
GEMINI_API_KEY = ENV_LOCAL_VALORES.get("GEMINI_API_KEY", "")
GEMINI_GEMMA_MODEL = ENV_LOCAL_VALORES.get("GEMINI_GEMMA_MODEL", "")
GEMINI_EMBEDDING_MODEL = ENV_LOCAL_VALORES.get("GEMINI_EMBEDDING_MODEL", "")

# --- Configuracion de retries y timeouts ---
MAX_RETRIES_LLM = 2
TIMEOUT_LLM_SEGUNDOS = 30

# --- Bandera de modo mock (forzada en False por politica de ejecucion real) ---
MODO_MOCK = False

# --- Monedas y tipos soportados ---
MONEDAS_SOPORTADAS = ["ARS", "USD", "EUR"]
TIPOS_PRODUCTO_CANONICOS = ["CUENTA", "TARJETA", "SERVICIO", "PRESTAMO", "SEGURO"]
PAISES_CANONICOS = [
    "Argentina",
    "Brasil",
    "Chile",
    "Colombia",
    "Mexico",
    "Uruguay",
    "Paraguay",
    "Peru",
    "Ecuador",
    "Bolivia",
]

# --- Campos obligatorios ---
CAMPOS_OBLIGATORIOS = [
    "id_solicitud",
    "fecha_solicitud",
    "tipo_producto",
    "id_cliente",
    "monto_o_limite",
    "moneda",
    "pais",
]

# --- Campos de salida ---
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
    "origen_procesamiento",
]

# --- Sinonimos para deteccion de ambiguedad ---
SINONIMOS_MONEDA = {
    "pesos": "ARS",
    "pesos argentinos": "ARS",
    "dolares": "USD",
    "usd dolares": "USD",
    "dolar": "USD",
    "euros": "EUR",
    "euro": "EUR",
}

SINONIMOS_TIPO_PRODUCTO = {
    "cta": "CUENTA",
    "cta ahorro": "CUENTA",
    "cuenta ahorro": "CUENTA",
    "cuenta corriente": "CUENTA",
    "cta corriente": "CUENTA",
    "tarj": "TARJETA",
    "plastico": "TARJETA",
    "tarjeta credito": "TARJETA",
    "tarjeta debito": "TARJETA",
    "serv": "SERVICIO",
    "prestamo personal": "PRESTAMO",
}

SINONIMOS_PAIS = {
    "arg": "Argentina",
    "arg.": "Argentina",
    "ar": "Argentina",
    "bra": "Brasil",
    "br": "Brasil",
    "cl": "Chile",
    "chi": "Chile",
    "co": "Colombia",
    "col": "Colombia",
    "mx": "Mexico",
    "mex": "Mexico",
    "uy": "Uruguay",
    "uk": "Reino Unido",
    "us": "Estados Unidos",
    "usa": "Estados Unidos",
}


def obtener_errores_config_llm():
    # Retorna una lista de errores de configuracion obligatoria para Gemini real
    errores = []
    if not ENV_LOCAL_EXISTE:
        errores.append("No existe .env.local en la raiz del proyecto")
    if GEMINI_API_KEY == "" or GEMINI_API_KEY == None:
        errores.append("Falta GEMINI_API_KEY en .env.local")
    if GEMINI_GEMMA_MODEL == "" or GEMINI_GEMMA_MODEL == None:
        errores.append("Falta GEMINI_GEMMA_MODEL en .env.local")
    if GEMINI_EMBEDDING_MODEL == "" or GEMINI_EMBEDDING_MODEL == None:
        errores.append("Falta GEMINI_EMBEDDING_MODEL en .env.local")
    return errores


def validar_config_llm():
    # Valida que la configuracion para LLM este completa
    # Retorna True si esta lista, False si falta algo critico
    errores = obtener_errores_config_llm()
    if len(errores) > 0:
        return False
    return True


def obtener_error_config_llm():
    # Retorna mensaje claro de errores de configuracion LLM
    errores = obtener_errores_config_llm()
    if len(errores) == 0:
        return None
    msg = "Configuracion LLM incompleta: "
    i = 0
    while i < len(errores):
        if i > 0:
            msg = msg + " | "
        msg = msg + errores[i]
        i = i + 1
    return msg


def obtener_info_config():
    # Retorna un diccionario con la configuracion actual (sin API key)
    info = {
        "env_local_existe": ENV_LOCAL_EXISTE,
        "dotenv_cargado": _dotenv_cargado,
        "fuente_config_llm": ".env.local",
        "gemini_model": GEMINI_GEMMA_MODEL,
        "embedding_model": GEMINI_EMBEDDING_MODEL,
        "api_key_presente": GEMINI_API_KEY != "" and GEMINI_API_KEY != None,
        "modo_mock": MODO_MOCK,
        "max_retries": MAX_RETRIES_LLM,
        "timeout_segundos": TIMEOUT_LLM_SEGUNDOS,
    }
    return info
