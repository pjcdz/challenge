# test_calidad.py - Tests para el modulo de control de calidad (RF-04)
# Verifica generacion del reporte JSON con totales, detalle y porcentajes

import sys
import os
import json

# Agregar src al path
sys.path.insert(
    0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src")
)

import logger
import calidad

# Inicializar logger para tests
logger.inicializar()

CARPETA_TEST = os.path.dirname(os.path.abspath(__file__))


def test_reporte_porcentaje():
    # DADO un lote de 10 registros donde 7 son validos
    # CUANDO se genera el reporte
    # ENTONCES muestra 70% de cumplimiento global
    print("TEST: test_reporte_porcentaje")

    registros = []
    # 7 validos
    i = 0
    while i < 7:
        reg = {
            "id_solicitud": "SOL-C" + str(i),
            "estado": "VALIDO",
            "motivos_falla": "",
            "_detalle_reglas": {"R1": [], "R2": [], "R3": []},
        }
        registros.append(reg)
        i += 1

    # 3 invalidos (1 falla R1, 1 falla R2, 1 falla R3)
    registros.append(
        {
            "id_solicitud": "SOL-C7",
            "estado": "INVALIDO",
            "motivos_falla": "R1: campo vacio",
            "_detalle_reglas": {"R1": ["campo id_cliente vacio"], "R2": [], "R3": []},
        }
    )
    registros.append(
        {
            "id_solicitud": "SOL-C8",
            "estado": "INVALIDO",
            "motivos_falla": "R2: moneda no soportada",
            "_detalle_reglas": {"R1": [], "R2": ["moneda no soportada: GBP"], "R3": []},
        }
    )
    registros.append(
        {
            "id_solicitud": "SOL-C9",
            "estado": "INVALIDO",
            "motivos_falla": "R3: monto fuera de rango",
            "_detalle_reglas": {
                "R1": [],
                "R2": [],
                "R3": ["monto fuera de rango: -500"],
            },
        }
    )

    reporte = calidad.generar_reporte(registros, "test.csv", CARPETA_TEST)

    ok = True
    if reporte["resumen"]["porcentaje_cumplimiento"] != 70.0:
        print(
            "  FALLO: se esperaba 70.0%, se obtuvo "
            + str(reporte["resumen"]["porcentaje_cumplimiento"])
            + "%"
        )
        ok = False
    if reporte["resumen"]["total_validos"] != 7:
        print(
            "  FALLO: se esperaban 7 validos, se obtuvieron "
            + str(reporte["resumen"]["total_validos"])
        )
        ok = False
    if reporte["resumen"]["total_invalidos"] != 3:
        print(
            "  FALLO: se esperaban 3 invalidos, se obtuvieron "
            + str(reporte["resumen"]["total_invalidos"])
        )
        ok = False

    # Limpiar archivo generado
    ruta_reporte = os.path.join(CARPETA_TEST, "reporte_calidad.json")
    if os.path.exists(ruta_reporte):
        os.remove(ruta_reporte)

    if ok:
        print("  OK")
    assert ok


def test_reporte_detalle_reglas():
    # DADO un lote con fallas en R2
    # CUANDO se genera el reporte
    # ENTONCES el detalle de R2 incluye cantidad, porcentajes y ejemplos
    print("TEST: test_reporte_detalle_reglas")

    registros = [
        {
            "id_solicitud": "SOL-D1",
            "estado": "VALIDO",
            "motivos_falla": "",
            "_detalle_reglas": {"R1": [], "R2": [], "R3": []},
        },
        {
            "id_solicitud": "SOL-D2",
            "estado": "INVALIDO",
            "motivos_falla": "R2: moneda no soportada: GBP",
            "_detalle_reglas": {"R1": [], "R2": ["moneda no soportada: GBP"], "R3": []},
        },
    ]

    reporte = calidad.generar_reporte(registros, "test.csv", CARPETA_TEST)

    ok = True
    detalle_r2 = reporte["detalle_reglas"]["R2_formato_fecha_moneda"]
    if detalle_r2["total_fallas"] != 1:
        print(
            "  FALLO: se esperaba 1 falla en R2, se obtuvieron "
            + str(detalle_r2["total_fallas"])
        )
        ok = False
    if detalle_r2["porcentaje_falla_sobre_invalidos"] != 100.0:
        print(
            "  FALLO: se esperaba 100.0% sobre invalidos, se obtuvo "
            + str(detalle_r2["porcentaje_falla_sobre_invalidos"])
            + "%"
        )
        ok = False
    if detalle_r2["porcentaje_falla_sobre_total"] != 50.0:
        print(
            "  FALLO: se esperaba 50.0% sobre total, se obtuvo "
            + str(detalle_r2["porcentaje_falla_sobre_total"])
            + "%"
        )
        ok = False
    if len(detalle_r2["ejemplos"]) == 0:
        print("  FALLO: no hay ejemplos en el detalle de R2")
        ok = False

    # Limpiar
    ruta_reporte = os.path.join(CARPETA_TEST, "reporte_calidad.json")
    if os.path.exists(ruta_reporte):
        os.remove(ruta_reporte)

    if ok:
        print("  OK")
    assert ok


def test_reporte_se_guarda_json():
    # DADO un lote procesado
    # CUANDO se genera el reporte
    # ENTONCES se guarda como archivo JSON
    print("TEST: test_reporte_se_guarda_json")

    registros = [
        {
            "id_solicitud": "SOL-J1",
            "estado": "VALIDO",
            "motivos_falla": "",
            "_detalle_reglas": {"R1": [], "R2": [], "R3": []},
        }
    ]

    calidad.generar_reporte(registros, "test.csv", CARPETA_TEST)

    ruta_reporte = os.path.join(CARPETA_TEST, "reporte_calidad.json")
    ok = True
    if not os.path.exists(ruta_reporte):
        print("  FALLO: archivo reporte_calidad.json no fue creado")
        ok = False
    else:
        # Verificar que es JSON valido
        arch = open(ruta_reporte, "r", encoding="utf-8")
        contenido = arch.read()
        arch.close()
        datos = json.loads(contenido)
        if "resumen" not in datos.keys():
            print("  FALLO: JSON no contiene campo 'resumen'")
            ok = False
        # Limpiar
        os.remove(ruta_reporte)

    if ok:
        print("  OK")
    assert ok


# Ejecutar tests manualmente
if __name__ == "__main__":
    print("=" * 50)
    print("TESTS DE CALIDAD (RF-04)")
    print("=" * 50)

    total = 3
    aprobados = 0

    try:
        test_reporte_porcentaje()
        aprobados += 1
    except AssertionError:
        pass
    try:
        test_reporte_detalle_reglas()
        aprobados += 1
    except AssertionError:
        pass
    try:
        test_reporte_se_guarda_json()
        aprobados += 1
    except AssertionError:
        pass

    print("")
    print("Resultado: " + str(aprobados) + "/" + str(total) + " tests aprobados")
