# agente_validador.py - Agente de validacion AI-First
# Aplica validaciones duras R1/R2/R3 a los registros normalizados
# Reutiliza la logica de validacion legacy

import os
import sys

dir_src = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
dir_legacy = os.path.join(
    os.path.dirname(os.path.dirname(dir_src)), "legacy_system", "src"
)
sys.path.insert(0, dir_src)
sys.path.insert(0, dir_legacy)

MODULO = "AGENTE_VALIDADOR"


def validar(registros):
    # Aplica las 3 reglas de validacion legacy a los registros
    # Los registros ya vienen normalizados (por reglas o por LLM)
    # Retorna la lista con estado y motivos_falla agregados

    import validador
    import logger

    # Guardar motivo tecnico de fallback para no perderlo al validar R1/R2/R3
    motivos_fallback = []
    for reg in registros:
        motivo = ""
        if "fallback_aplicado" in reg.keys() and reg["fallback_aplicado"]:
            if "motivos_falla" in reg.keys():
                motivo = reg["motivos_falla"]
        motivos_fallback.append(motivo)

    registros_validados = validador.validar_registros(registros)

    # Si hubo fallback tecnico de LLM, siempre debe quedar INVALIDO
    total_forzados_por_fallback = 0
    i = 0
    while i < len(registros_validados):
        reg = registros_validados[i]
        if "fallback_aplicado" in reg.keys() and reg["fallback_aplicado"]:
            reg["estado"] = "INVALIDO"
            total_forzados_por_fallback = total_forzados_por_fallback + 1
            motivo_tec = motivos_fallback[i]
            if motivo_tec == None or motivo_tec == "":
                motivo_tec = "Fallback: LLM no pudo normalizar"
            reg["motivos_falla"] = motivo_tec

            if "_detalle_reglas" not in reg.keys():
                reg["_detalle_reglas"] = {}
            reg["_detalle_reglas"]["R_TECH"] = [motivo_tec]
        i = i + 1

    total_validos_final = 0
    total_invalidos_final = 0
    for reg in registros_validados:
        if "estado" in reg.keys() and reg["estado"] == "VALIDO":
            total_validos_final = total_validos_final + 1
        else:
            total_invalidos_final = total_invalidos_final + 1

    if total_forzados_por_fallback > 0:
        logger.warn(
            MODULO,
            "Se forzaron "
            + str(total_forzados_por_fallback)
            + " registros a INVALIDO por fallback tecnico",
        )

    logger.info(
        MODULO,
        "Validacion AI-First final - "
        + str(total_validos_final)
        + " validos, "
        + str(total_invalidos_final)
        + " invalidos",
    )

    return registros_validados
