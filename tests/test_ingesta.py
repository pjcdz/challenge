# test_ingesta.py - Tests para el modulo de ingesta (RF-01)
# Verifica lectura de CSV, archivo inexistente y archivo vacio

import sys
import os

# Agregar src al path
sys.path.insert(
    0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src")
)

import logger
import ingesta

# Inicializar logger para tests
logger.inicializar()

# Carpeta temporal para tests
CARPETA_TEST = os.path.dirname(os.path.abspath(__file__))


def test_lectura_csv_valido():
    # DADO un archivo CSV valido con header
    # CUANDO se ejecuta la ingesta
    # ENTONCES se retorna una lista de diccionarios con los datos
    print("TEST: test_lectura_csv_valido")

    # Crear archivo temporal
    ruta = os.path.join(CARPETA_TEST, "temp_valido.csv")
    arch = open(ruta, "w", encoding="utf-8")
    arch.write("id_solicitud,tipo_producto,moneda\n")
    arch.write("SOL-001,cuenta,ARS\n")
    arch.write("SOL-002,tarjeta,USD\n")
    arch.close()

    resultado = ingesta.leer_solicitudes(ruta)

    ok = True
    if resultado == None:
        print("  FALLO: resultado es None")
        ok = False
    elif len(resultado) != 2:
        print("  FALLO: se esperaban 2 registros, se obtuvieron " + str(len(resultado)))
        ok = False
    elif resultado[0]["id_solicitud"] != "SOL-001":
        print("  FALLO: primer registro no tiene id_solicitud correcto")
        ok = False
    elif resultado[1]["moneda"] != "USD":
        print("  FALLO: segundo registro no tiene moneda correcta")
        ok = False

    # Limpiar
    os.remove(ruta)

    if ok:
        print("  OK")
    assert ok


def test_archivo_inexistente():
    # DADO un archivo CSV inexistente
    # CUANDO se intenta la ingesta
    # ENTONCES se retorna None
    print("TEST: test_archivo_inexistente")

    resultado = ingesta.leer_solicitudes("archivo_que_no_existe.csv")

    ok = True
    if resultado != None:
        print("  FALLO: se esperaba None, se obtuvo " + str(type(resultado)))
        ok = False

    if ok:
        print("  OK")
    assert ok


def test_archivo_vacio():
    # DADO un archivo CSV vacio (solo header)
    # CUANDO se ejecuta la ingesta
    # ENTONCES se retorna lista vacia
    print("TEST: test_archivo_vacio")

    ruta = os.path.join(CARPETA_TEST, "temp_vacio.csv")
    arch = open(ruta, "w", encoding="utf-8")
    arch.write("id_solicitud,tipo_producto,moneda\n")
    arch.close()

    resultado = ingesta.leer_solicitudes(ruta)

    ok = True
    if resultado == None:
        print("  FALLO: resultado es None (deberia ser lista vacia)")
        ok = False
    elif len(resultado) != 0:
        print(
            "  FALLO: se esperaba lista vacia, se obtuvieron "
            + str(len(resultado))
            + " registros"
        )
        ok = False

    # Limpiar
    os.remove(ruta)

    if ok:
        print("  OK")
    assert ok


def test_campo_con_comillas():
    # DADO un CSV con un campo entre comillas que contiene coma
    # CUANDO se ejecuta la ingesta
    # ENTONCES el campo se lee correctamente sin separar por la coma interna
    print("TEST: test_campo_con_comillas")

    ruta = os.path.join(CARPETA_TEST, "temp_comillas.csv")
    arch = open(ruta, "w", encoding="utf-8")
    arch.write("id_solicitud,tipo_producto,moneda\n")
    arch.write('SOL-001,"cuenta, ahorros",ARS\n')
    arch.close()

    resultado = ingesta.leer_solicitudes(ruta)

    ok = True
    if resultado == None:
        print("  FALLO: resultado es None")
        ok = False
    elif len(resultado) != 1:
        print("  FALLO: se esperaba 1 registro, se obtuvieron " + str(len(resultado)))
        ok = False
    elif resultado[0]["tipo_producto"] != "cuenta, ahorros":
        print(
            "  FALLO: tipo_producto deberia ser 'cuenta, ahorros', se obtuvo '"
            + resultado[0]["tipo_producto"]
            + "'"
        )
        ok = False

    # Limpiar
    os.remove(ruta)

    if ok:
        print("  OK")
    assert ok


def test_lineas_vacias_ignoradas():
    # DADO un CSV con lineas vacias intercaladas
    # CUANDO se ejecuta la ingesta
    # ENTONCES las lineas vacias se ignoran y se leen solo los registros
    print("TEST: test_lineas_vacias_ignoradas")

    ruta = os.path.join(CARPETA_TEST, "temp_vacias.csv")
    arch = open(ruta, "w", encoding="utf-8")
    arch.write("id_solicitud,tipo_producto,moneda\n")
    arch.write("\n")
    arch.write("SOL-001,cuenta,ARS\n")
    arch.write("\n")
    arch.write("SOL-002,tarjeta,USD\n")
    arch.close()

    resultado = ingesta.leer_solicitudes(ruta)

    ok = True
    if resultado == None:
        print("  FALLO: resultado es None")
        ok = False
    elif len(resultado) != 2:
        print("  FALLO: se esperaban 2 registros, se obtuvieron " + str(len(resultado)))
        ok = False

    # Limpiar
    os.remove(ruta)

    if ok:
        print("  OK")
    assert ok


# Ejecutar tests manualmente
if __name__ == "__main__":
    print("=" * 50)
    print("TESTS DE INGESTA (RF-01)")
    print("=" * 50)

    total = 5
    aprobados = 0

    try:
        test_lectura_csv_valido()
        aprobados += 1
    except AssertionError:
        pass
    try:
        test_archivo_inexistente()
        aprobados += 1
    except AssertionError:
        pass
    try:
        test_archivo_vacio()
        aprobados += 1
    except AssertionError:
        pass
    try:
        test_campo_con_comillas()
        aprobados += 1
    except AssertionError:
        pass
    try:
        test_lineas_vacias_ignoradas()
        aprobados += 1
    except AssertionError:
        pass

    print("")
    print("Resultado: " + str(aprobados) + "/" + str(total) + " tests aprobados")
