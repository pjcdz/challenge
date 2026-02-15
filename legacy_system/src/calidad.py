# calidad.py - Control de calidad (RF-04)
# Genera reporte JSON con metricas de calidad del procesamiento

import json
import os
from datetime import datetime
import logger

MODULO = "CALIDAD"


def generar_reporte(registros, archivo_entrada, carpeta_salida):
    # Genera un reporte de calidad en formato JSON
    # registros: lista de registros ya validados (con estado y _detalle_reglas)
    # archivo_entrada: nombre del archivo procesado
    # carpeta_salida: donde guardar el reporte

    total = len(registros)
    total_validos = 0
    total_invalidos = 0

    # Nombres descriptivos para las reglas conocidas
    nombres_reglas = {
        "R1": "R1_campos_obligatorios",
        "R2": "R2_formato_fecha_moneda",
        "R3": "R3_rango_monto",
    }

    # Descubrir todas las reglas presentes en los registros
    reglas_encontradas = []
    for reg in registros:
        if "_detalle_reglas" in reg.keys():
            detalle = reg["_detalle_reglas"]
            for clave in detalle.keys():
                if clave not in reglas_encontradas:
                    reglas_encontradas.append(clave)

    # Ordenar las reglas para consistencia (bubble sort manual)
    for x in range(len(reglas_encontradas) - 1):
        for u in range(x + 1, len(reglas_encontradas)):
            if reglas_encontradas[x] > reglas_encontradas[u]:
                aux = reglas_encontradas[x]
                reglas_encontradas[x] = reglas_encontradas[u]
                reglas_encontradas[u] = aux

    # Inicializar contadores por regla
    fallas_por_regla = {}
    ejemplos_por_regla = {}
    for regla in reglas_encontradas:
        fallas_por_regla[regla] = 0
        ejemplos_por_regla[regla] = []

    for reg in registros:
        if reg["estado"] == "VALIDO":
            total_validos += 1
        else:
            total_invalidos += 1

        # Obtener detalle de reglas
        if "_detalle_reglas" in reg.keys():
            detalle = reg["_detalle_reglas"]
        else:
            detalle = {}
        if "id_solicitud" in reg.keys():
            id_sol = reg["id_solicitud"]
        else:
            id_sol = "DESCONOCIDO"

        # Contar fallas por cada regla encontrada
        for regla in reglas_encontradas:
            if regla in detalle.keys() and len(detalle[regla]) > 0:
                fallas_por_regla[regla] = fallas_por_regla[regla] + 1
                for m in detalle[regla]:
                    ej = id_sol + ": " + m
                    if len(ejemplos_por_regla[regla]) < 3:
                        ejemplos_por_regla[regla].append(ej)

    # Calcular porcentajes
    if total > 0:
        pct_global = round((total_validos * 100.0) / total, 1)
    else:
        pct_global = 0.0

    # Construir detalle de reglas dinamicamente
    detalle_reglas = {}
    for regla in reglas_encontradas:
        if total > 0:
            pct_regla_total = round((fallas_por_regla[regla] * 100.0) / total, 1)
        else:
            pct_regla_total = 0.0
        if total_invalidos > 0:
            pct_regla_invalidos = round(
                (fallas_por_regla[regla] * 100.0) / total_invalidos, 1
            )
        else:
            pct_regla_invalidos = 0.0
        # Usar nombre descriptivo si existe, sino usar la clave tal cual
        if regla in nombres_reglas.keys():
            nombre = nombres_reglas[regla]
        else:
            nombre = regla
        detalle_reglas[nombre] = {
            "total_fallas": fallas_por_regla[regla],
            "porcentaje_falla_sobre_invalidos": pct_regla_invalidos,
            "porcentaje_falla_sobre_total": pct_regla_total,
            "ejemplos": ejemplos_por_regla[regla],
        }

    # Construir reporte
    reporte = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "archivo_entrada": archivo_entrada,
        "resumen": {
            "total_procesados": total,
            "total_validos": total_validos,
            "total_invalidos": total_invalidos,
            "porcentaje_cumplimiento": pct_global,
        },
        "detalle_reglas": detalle_reglas,
    }

    # Guardar como JSON
    ruta_reporte = os.path.join(carpeta_salida, "reporte_calidad.json")
    arch = open(ruta_reporte, "w", encoding="utf-8")
    arch.write(json.dumps(reporte, indent=4, ensure_ascii=False))
    arch.close()

    logger.info(MODULO, "Reporte de calidad generado: " + ruta_reporte)
    logger.info(
        MODULO,
        "Cumplimiento global: "
        + str(pct_global)
        + "% ("
        + str(total_validos)
        + "/"
        + str(total)
        + " validos)",
    )

    return reporte
