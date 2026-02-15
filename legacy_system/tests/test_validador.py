# test_validador.py - Tests para el modulo de validacion (RF-03)
# Verifica las 3 reglas: R1 (obligatorios), R2 (fecha/moneda), R3 (monto)

import sys
import os

# Agregar src al path
sys.path.insert(
    0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src")
)

import logger
import validador

# Inicializar logger para tests
logger.inicializar()


def hacer_registro(id_sol, fecha, tipo, cliente, monto, moneda, pais):
    # Crea un registro de prueba con los campos dados
    reg = {
        "id_solicitud": id_sol,
        "fecha_solicitud": fecha,
        "tipo_producto": tipo,
        "id_cliente": cliente,
        "monto_o_limite": monto,
        "moneda": moneda,
        "pais": pais,
        "flag_prioritario": "S",
        "flag_digital": "N",
        "categoria_riesgo": "BAJO",
    }
    return reg


def test_registro_valido():
    # DADO un registro con todos los campos completos y validos
    # CUANDO se valida
    # ENTONCES pasa todas las reglas
    print("TEST: test_registro_valido")

    reg = hacer_registro(
        "SOL-V01", "15/03/2025", "CUENTA", "CLI-100", "50000", "ARS", "Argentina"
    )
    resultado = validador.validar_registros([reg])

    ok = True
    if resultado[0]["estado"] != "VALIDO":
        print("  FALLO: se esperaba VALIDO, se obtuvo " + resultado[0]["estado"])
        ok = False

    if ok:
        print("  OK")
    assert ok


def test_r1_campo_vacio():
    # DADO un registro con id_cliente vacio
    # CUANDO se valida R1
    # ENTONCES falla
    print("TEST: test_r1_campo_vacio")

    reg = hacer_registro(
        "SOL-V02", "15/03/2025", "CUENTA", "", "50000", "ARS", "Argentina"
    )
    resultado = validador.validar_registros([reg])

    ok = True
    if resultado[0]["estado"] != "INVALIDO":
        print("  FALLO: se esperaba INVALIDO, se obtuvo " + resultado[0]["estado"])
        ok = False
    elif "R1:" not in resultado[0]["motivos_falla"]:
        print("  FALLO: motivo no menciona R1:")
        ok = False

    if ok:
        print("  OK")
    assert ok


def test_r2_moneda_no_soportada():
    # DADO un registro con moneda "GBP"
    # CUANDO se valida R2
    # ENTONCES falla con motivo "moneda no soportada"
    print("TEST: test_r2_moneda_no_soportada")

    reg = hacer_registro(
        "SOL-V03", "15/03/2025", "CUENTA", "CLI-100", "50000", "GBP", "Argentina"
    )
    resultado = validador.validar_registros([reg])

    ok = True
    if resultado[0]["estado"] != "INVALIDO":
        print("  FALLO: se esperaba INVALIDO, se obtuvo " + resultado[0]["estado"])
        ok = False
    elif "R2: moneda no soportada" not in resultado[0]["motivos_falla"]:
        print("  FALLO: motivo no menciona 'R2: moneda no soportada'")
        ok = False

    if ok:
        print("  OK")
    assert ok


def test_r3_monto_negativo():
    # DADO un registro con monto -500
    # CUANDO se valida R3
    # ENTONCES falla con motivo "monto fuera de rango"
    print("TEST: test_r3_monto_negativo")

    reg = hacer_registro(
        "SOL-V04", "15/03/2025", "CUENTA", "CLI-100", "-500", "ARS", "Argentina"
    )
    resultado = validador.validar_registros([reg])

    ok = True
    if resultado[0]["estado"] != "INVALIDO":
        print("  FALLO: se esperaba INVALIDO, se obtuvo " + resultado[0]["estado"])
        ok = False
    elif "R3: monto fuera de rango" not in resultado[0]["motivos_falla"]:
        print("  FALLO: motivo no menciona 'R3: monto fuera de rango'")
        ok = False

    if ok:
        print("  OK")
    assert ok


def test_multiples_fallas():
    # DADO un registro que falla multiples reglas
    # CUANDO se valida
    # ENTONCES se registran TODOS los motivos
    print("TEST: test_multiples_fallas")

    reg = hacer_registro(
        "SOL-V05", "32/13/2025", "", "CLI-100", "-500", "GBP", "Argentina"
    )
    resultado = validador.validar_registros([reg])

    ok = True
    if resultado[0]["estado"] != "INVALIDO":
        print("  FALLO: se esperaba INVALIDO")
        ok = False
    else:
        motivos = resultado[0]["motivos_falla"]
        tiene_r1 = "R1:" in motivos
        tiene_r2 = "R2:" in motivos
        tiene_r3 = "R3:" in motivos
        if not tiene_r1:
            print("  FALLO: no detecta falla R1 (campo vacio)")
            ok = False
        if not tiene_r2:
            print("  FALLO: no detecta falla R2 (moneda/fecha)")
            ok = False
        if not tiene_r3:
            print("  FALLO: no detecta falla R3 (monto)")
            ok = False

    if ok:
        print("  OK")
    assert ok


def test_monto_limite_superior():
    # DADO un registro con monto en el limite exacto 999999999
    # CUANDO se valida R3
    # ENTONCES pasa la validacion (monto es valido)
    print("TEST: test_monto_limite_superior")

    reg = hacer_registro(
        "SOL-V06", "15/03/2025", "CUENTA", "CLI-100", "999999999", "ARS", "Argentina"
    )
    resultado = validador.validar_registros([reg])

    ok = True
    if resultado[0]["estado"] != "VALIDO":
        print(
            "  FALLO: monto 999999999 deberia ser valido, se obtuvo "
            + resultado[0]["estado"]
        )
        ok = False

    if ok:
        print("  OK")
    assert ok


def test_monto_excede_limite():
    # DADO un registro con monto 1000000000 (supera el limite)
    # CUANDO se valida R3
    # ENTONCES falla con motivo "monto fuera de rango"
    print("TEST: test_monto_excede_limite")

    reg = hacer_registro(
        "SOL-V07", "15/03/2025", "CUENTA", "CLI-100", "1000000000", "ARS", "Argentina"
    )
    resultado = validador.validar_registros([reg])

    ok = True
    if resultado[0]["estado"] != "INVALIDO":
        print("  FALLO: monto 1000000000 deberia ser invalido")
        ok = False
    elif "R3: monto fuera de rango" not in resultado[0]["motivos_falla"]:
        print("  FALLO: motivo no menciona 'R3: monto fuera de rango'")
        ok = False

    if ok:
        print("  OK")
    assert ok


def test_monto_cero():
    # DADO un registro con monto 0
    # CUANDO se valida R3
    # ENTONCES falla porque monto debe ser > 0
    print("TEST: test_monto_cero")

    reg = hacer_registro(
        "SOL-V08", "15/03/2025", "CUENTA", "CLI-100", "0", "ARS", "Argentina"
    )
    resultado = validador.validar_registros([reg])

    ok = True
    if resultado[0]["estado"] != "INVALIDO":
        print("  FALLO: monto 0 deberia ser invalido")
        ok = False
    elif "R3: monto fuera de rango" not in resultado[0]["motivos_falla"]:
        print("  FALLO: motivo no menciona 'R3: monto fuera de rango'")
        ok = False

    if ok:
        print("  OK")
    assert ok


def test_monto_no_numerico():
    # DADO un registro con monto "abc"
    # CUANDO se valida R3
    # ENTONCES falla con motivo "monto no es numerico"
    print("TEST: test_monto_no_numerico")

    reg = hacer_registro(
        "SOL-V09", "15/03/2025", "CUENTA", "CLI-100", "abc", "ARS", "Argentina"
    )
    resultado = validador.validar_registros([reg])

    ok = True
    if resultado[0]["estado"] != "INVALIDO":
        print("  FALLO: monto 'abc' deberia ser invalido")
        ok = False
    elif "R3: monto no es numerico" not in resultado[0]["motivos_falla"]:
        print("  FALLO: motivo no menciona 'R3: monto no es numerico'")
        ok = False

    if ok:
        print("  OK")
    assert ok


def test_monto_solo_espacios():
    # DADO un registro con monto "   " (solo espacios)
    # CUANDO se valida R3
    # ENTONCES falla con motivo apropiado (no crash)
    print("TEST: test_monto_solo_espacios")

    reg = hacer_registro(
        "SOL-V10", "15/03/2025", "CUENTA", "CLI-100", "   ", "ARS", "Argentina"
    )
    resultado = validador.validar_registros([reg])

    ok = True
    if resultado[0]["estado"] != "INVALIDO":
        print("  FALLO: monto '   ' deberia ser invalido")
        ok = False

    if ok:
        print("  OK")
    assert ok


def test_monto_solo_signo_menos():
    # DADO un registro con monto "-"
    # CUANDO se valida R3
    # ENTONCES falla como no numerico (no crash)
    print("TEST: test_monto_solo_signo_menos")

    reg = hacer_registro(
        "SOL-V11", "15/03/2025", "CUENTA", "CLI-100", "-", "ARS", "Argentina"
    )
    resultado = validador.validar_registros([reg])

    ok = True
    if resultado[0]["estado"] != "INVALIDO":
        print("  FALLO: monto '-' deberia ser invalido")
        ok = False
    elif "R3: monto no es numerico" not in resultado[0]["motivos_falla"]:
        print("  FALLO: motivo no menciona 'R3: monto no es numerico'")
        ok = False

    if ok:
        print("  OK")
    assert ok


def test_fecha_dia_31_mes_invalido():
    # DADO un registro con fecha 31/02/2025 (febrero no tiene 31 dias)
    # CUANDO se valida R2
    # ENTONCES pasa porque la validacion solo chequea formato, no calendario
    # (Esto documenta el comportamiento actual - no valida calendario)
    print("TEST: test_fecha_dia_31_mes_invalido")

    reg = hacer_registro(
        "SOL-V12", "31/02/2025", "CUENTA", "CLI-100", "50000", "ARS", "Argentina"
    )
    resultado = validador.validar_registros([reg])

    ok = True
    # El validador actual solo chequea formato DD/MM/YYYY, no calendario
    # Dia 31 esta en rango 1-31 y mes 02 esta en rango 1-12, asi que pasa
    if resultado[0]["estado"] != "VALIDO":
        print("  FALLO: formato DD/MM/YYYY es valido para el validador actual")
        ok = False

    if ok:
        print("  OK")
    assert ok


# Ejecutar tests manualmente
if __name__ == "__main__":
    print("=" * 50)
    print("TESTS DE VALIDADOR (RF-03)")
    print("=" * 50)

    total = 12
    aprobados = 0

    try:
        test_registro_valido()
        aprobados += 1
    except AssertionError:
        pass
    try:
        test_r1_campo_vacio()
        aprobados += 1
    except AssertionError:
        pass
    try:
        test_r2_moneda_no_soportada()
        aprobados += 1
    except AssertionError:
        pass
    try:
        test_r3_monto_negativo()
        aprobados += 1
    except AssertionError:
        pass
    try:
        test_multiples_fallas()
        aprobados += 1
    except AssertionError:
        pass
    try:
        test_monto_limite_superior()
        aprobados += 1
    except AssertionError:
        pass
    try:
        test_monto_excede_limite()
        aprobados += 1
    except AssertionError:
        pass
    try:
        test_monto_cero()
        aprobados += 1
    except AssertionError:
        pass
    try:
        test_monto_no_numerico()
        aprobados += 1
    except AssertionError:
        pass
    try:
        test_monto_solo_espacios()
        aprobados += 1
    except AssertionError:
        pass
    try:
        test_monto_solo_signo_menos()
        aprobados += 1
    except AssertionError:
        pass
    try:
        test_fecha_dia_31_mes_invalido()
        aprobados += 1
    except AssertionError:
        pass

    print("")
    print("Resultado: " + str(aprobados) + "/" + str(total) + " tests aprobados")
