# test_normalizador.py - Tests para el modulo de normalizacion (RF-02)
# Verifica normalizacion de fechas, trimming, mayusculas y categoria de riesgo

import sys
import os

# Agregar legacy_system/src al path
sys.path.insert(
    0,
    os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "legacy_system",
        "src",
    ),
)

import logger
import normalizador

# Inicializar logger para tests
logger.inicializar()


def test_normalizar_fecha_yyyy_mm_dd():
    # DADO un registro con fecha "2025-03-15"
    # CUANDO se normaliza
    # ENTONCES la fecha queda "15/03/2025"
    print("TEST: test_normalizar_fecha_yyyy_mm_dd")

    registros = [
        {
            "id_solicitud": "SOL-T01",
            "fecha_solicitud": "2025-03-15",
            "tipo_producto": "cuenta",
            "moneda": "ARS",
            "pais": "Argentina",
            "monto_o_limite": "50000",
        }
    ]
    resultado = normalizador.normalizar_registros(registros)

    ok = True
    if resultado[0]["fecha_solicitud"] != "15/03/2025":
        print(
            "  FALLO: se esperaba '15/03/2025', se obtuvo '"
            + resultado[0]["fecha_solicitud"]
            + "'"
        )
        ok = False

    if ok:
        print("  OK")
    assert ok


def test_normalizar_trimming_upper():
    # DADO un registro con tipo_producto "  cuenta "
    # CUANDO se normaliza
    # ENTONCES queda "CUENTA"
    print("TEST: test_normalizar_trimming_upper")

    registros = [
        {
            "id_solicitud": "SOL-T02",
            "fecha_solicitud": "15/03/2025",
            "tipo_producto": "  cuenta ",
            "moneda": " ars ",
            "pais": " argentina ",
            "monto_o_limite": "50000",
        }
    ]
    resultado = normalizador.normalizar_registros(registros)

    ok = True
    if resultado[0]["tipo_producto"] != "CUENTA":
        print(
            "  FALLO tipo_producto: se esperaba 'CUENTA', se obtuvo '"
            + resultado[0]["tipo_producto"]
            + "'"
        )
        ok = False
    if resultado[0]["moneda"] != "ARS":
        print(
            "  FALLO moneda: se esperaba 'ARS', se obtuvo '"
            + resultado[0]["moneda"]
            + "'"
        )
        ok = False
    if resultado[0]["pais"] != "Argentina":
        print(
            "  FALLO pais: se esperaba 'Argentina', se obtuvo '"
            + resultado[0]["pais"]
            + "'"
        )
        ok = False

    if ok:
        print("  OK")
    assert ok


def test_categoria_riesgo():
    # DADO registros con diferentes montos
    # CUANDO se normaliza
    # ENTONCES la categoria_riesgo es correcta
    print("TEST: test_categoria_riesgo")

    registros = [
        {
            "id_solicitud": "SOL-T03",
            "fecha_solicitud": "15/03/2025",
            "tipo_producto": "cuenta",
            "moneda": "ARS",
            "pais": "Argentina",
            "monto_o_limite": "30000",
        },
        {
            "id_solicitud": "SOL-T04",
            "fecha_solicitud": "15/03/2025",
            "tipo_producto": "cuenta",
            "moneda": "ARS",
            "pais": "Argentina",
            "monto_o_limite": "75000",
        },
        {
            "id_solicitud": "SOL-T05",
            "fecha_solicitud": "15/03/2025",
            "tipo_producto": "cuenta",
            "moneda": "ARS",
            "pais": "Argentina",
            "monto_o_limite": "600000",
        },
    ]
    resultado = normalizador.normalizar_registros(registros)

    ok = True
    if resultado[0]["categoria_riesgo"] != "BAJO":
        print(
            "  FALLO: monto 30000 deberia ser BAJO, se obtuvo '"
            + resultado[0]["categoria_riesgo"]
            + "'"
        )
        ok = False
    if resultado[1]["categoria_riesgo"] != "MEDIO":
        print(
            "  FALLO: monto 75000 deberia ser MEDIO, se obtuvo '"
            + resultado[1]["categoria_riesgo"]
            + "'"
        )
        ok = False
    if resultado[2]["categoria_riesgo"] != "ALTO":
        print(
            "  FALLO: monto 600000 deberia ser ALTO, se obtuvo '"
            + resultado[2]["categoria_riesgo"]
            + "'"
        )
        ok = False

    if ok:
        print("  OK")
    assert ok


def test_monto_no_numerico_no_crash():
    # DADO un registro con monto no numerico "abc"
    # CUANDO se normaliza
    # ENTONCES no crashea y categoria_riesgo queda vacia
    print("TEST: test_monto_no_numerico_no_crash")

    registros = [
        {
            "id_solicitud": "SOL-T06",
            "fecha_solicitud": "15/03/2025",
            "tipo_producto": "cuenta",
            "moneda": "ARS",
            "pais": "Argentina",
            "monto_o_limite": "abc",
        },
    ]
    resultado = normalizador.normalizar_registros(registros)

    ok = True
    if resultado[0]["categoria_riesgo"] != "":
        print(
            "  FALLO: monto 'abc' deberia dar categoria_riesgo vacia, se obtuvo '"
            + resultado[0]["categoria_riesgo"]
            + "'"
        )
        ok = False

    if ok:
        print("  OK")
    assert ok


def test_monto_solo_espacios_no_crash():
    # DADO un registro con monto "   " (solo espacios)
    # CUANDO se normaliza
    # ENTONCES no crashea y categoria_riesgo queda vacia
    print("TEST: test_monto_solo_espacios_no_crash")

    registros = [
        {
            "id_solicitud": "SOL-T07",
            "fecha_solicitud": "15/03/2025",
            "tipo_producto": "cuenta",
            "moneda": "ARS",
            "pais": "Argentina",
            "monto_o_limite": "   ",
        },
    ]
    resultado = normalizador.normalizar_registros(registros)

    ok = True
    # Monto "   " despues de strip se vuelve "", no deberia crashear
    if resultado[0]["categoria_riesgo"] != "":
        print(
            "  FALLO: monto '   ' deberia dar categoria vacia, se obtuvo '"
            + resultado[0]["categoria_riesgo"]
            + "'"
        )
        ok = False

    if ok:
        print("  OK")
    assert ok


def test_fecha_formato_dd_mm_yyyy():
    # DADO un registro con fecha ya en formato DD-MM-YYYY (con guiones)
    # CUANDO se normaliza
    # ENTONCES la fecha queda en formato DD/MM/YYYY (con barras)
    print("TEST: test_fecha_formato_dd_mm_yyyy")

    registros = [
        {
            "id_solicitud": "SOL-T08",
            "fecha_solicitud": "20-06-2025",
            "tipo_producto": "cuenta",
            "moneda": "ARS",
            "pais": "Argentina",
            "monto_o_limite": "50000",
        },
    ]
    resultado = normalizador.normalizar_registros(registros)

    ok = True
    if resultado[0]["fecha_solicitud"] != "20/06/2025":
        print(
            "  FALLO: se esperaba '20/06/2025', se obtuvo '"
            + resultado[0]["fecha_solicitud"]
            + "'"
        )
        ok = False

    if ok:
        print("  OK")
    assert ok


# Ejecutar tests manualmente
if __name__ == "__main__":
    print("=" * 50)
    print("TESTS DE NORMALIZADOR (RF-02)")
    print("=" * 50)

    total = 6
    aprobados = 0

    try:
        test_normalizar_fecha_yyyy_mm_dd()
        aprobados += 1
    except AssertionError:
        pass
    try:
        test_normalizar_trimming_upper()
        aprobados += 1
    except AssertionError:
        pass
    try:
        test_categoria_riesgo()
        aprobados += 1
    except AssertionError:
        pass
    try:
        test_monto_no_numerico_no_crash()
        aprobados += 1
    except AssertionError:
        pass
    try:
        test_monto_solo_espacios_no_crash()
        aprobados += 1
    except AssertionError:
        pass
    try:
        test_fecha_formato_dd_mm_yyyy()
        aprobados += 1
    except AssertionError:
        pass

    print("")
    print("Resultado: " + str(aprobados) + "/" + str(total) + " tests aprobados")
