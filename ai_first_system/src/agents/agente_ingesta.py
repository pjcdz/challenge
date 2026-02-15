# agente_ingesta.py - Agente de ingesta AI-First
# Reutiliza la logica de ingesta legacy pero agrega metadata de origen

import os
import sys

# Paths para imports
dir_src = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
dir_legacy = os.path.join(
    os.path.dirname(os.path.dirname(dir_src)), "legacy_system", "src"
)
sys.path.insert(0, dir_src)
sys.path.insert(0, dir_legacy)

MODULO = "AGENTE_INGESTA"


def ingestar(archivo):
    # Reutiliza la ingesta legacy para leer el archivo
    # Agrega campo origen_procesamiento a cada registro
    # Retorna (registros, None) si ok, (None, error) si falla

    # Importar ingesta legacy
    import ingesta

    registros = ingesta.leer_solicitudes(archivo)
    if registros == None:
        return None, "Error leyendo archivo: " + archivo

    if len(registros) == 0:
        return [], None

    # Agregar campos de tracking a cada registro
    for reg in registros:
        reg["origen_procesamiento"] = ""
        reg["retries_llm"] = 0
        reg["fallback_aplicado"] = False

    return registros, None
