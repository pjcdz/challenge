# test_ingesta.py - Tests para el modulo de ingesta (RF-01)
# Verifica lectura de CSV, archivo inexistente y archivo vacio

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

import json
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


def test_lectura_json_valido():
    # DADO un archivo JSON valido con un array de objetos
    # CUANDO se ejecuta la ingesta
    # ENTONCES se retorna una lista de diccionarios con los datos
    print("TEST: test_lectura_json_valido")

    ruta = os.path.join(CARPETA_TEST, "temp_valido.json")
    datos = [
        {"id_solicitud": "SOL-001", "tipo_producto": "cuenta", "moneda": "ARS"},
        {"id_solicitud": "SOL-002", "tipo_producto": "tarjeta", "moneda": "USD"},
    ]
    arch = open(ruta, "w", encoding="utf-8")
    arch.write(json.dumps(datos))
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


def test_lectura_txt_valido():
    # DADO un archivo TXT delimitado por pipe con header y datos
    # CUANDO se ejecuta la ingesta
    # ENTONCES se retorna una lista de diccionarios con los datos
    print("TEST: test_lectura_txt_valido")

    ruta = os.path.join(CARPETA_TEST, "temp_valido.txt")
    arch = open(ruta, "w", encoding="utf-8")
    arch.write("id_solicitud|tipo_producto|moneda\n")
    arch.write("SOL-001|cuenta|ARS\n")
    arch.write("SOL-002|tarjeta|USD\n")
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


def test_formato_no_soportado():
    # DADO un archivo con extension no soportada (.xlsx)
    # CUANDO se intenta la ingesta
    # ENTONCES se retorna None
    print("TEST: test_formato_no_soportado")

    ruta = os.path.join(CARPETA_TEST, "temp_invalido.xlsx")
    arch = open(ruta, "w", encoding="utf-8")
    arch.write("datos de prueba")
    arch.close()

    resultado = ingesta.leer_solicitudes(ruta)

    ok = True
    if resultado != None:
        print("  FALLO: se esperaba None, se obtuvo " + str(type(resultado)))
        ok = False

    # Limpiar
    os.remove(ruta)

    if ok:
        print("  OK")
    assert ok


def test_json_tipos_nativos():
    # DADO un archivo JSON con valores como int, float y bool (no string)
    # CUANDO se ejecuta la ingesta
    # ENTONCES se convierten a string y no explota el normalizador
    print("TEST: test_json_tipos_nativos")

    ruta = os.path.join(CARPETA_TEST, "temp_tipos.json")
    # Escribir JSON con tipos nativos (no strings)
    datos = [
        {
            "id_solicitud": "SOL-T01",
            "fecha_solicitud": "15/03/2025",
            "tipo_producto": "CUENTA",
            "id_cliente": "CLI-100",
            "monto_o_limite": 50000,
            "moneda": "ARS",
            "pais": "Argentina",
            "flag_prioritario": True,
            "flag_digital": False,
        },
        {
            "id_solicitud": "SOL-T02",
            "fecha_solicitud": "20/03/2025",
            "tipo_producto": "tarjeta",
            "id_cliente": "CLI-200",
            "monto_o_limite": 75000.5,
            "moneda": "USD",
            "pais": "Brasil",
            "flag_prioritario": False,
            "flag_digital": True,
        },
    ]
    arch = open(ruta, "w", encoding="utf-8")
    arch.write(json.dumps(datos))
    arch.close()

    resultado = ingesta.leer_solicitudes(ruta)

    ok = True
    if resultado == None:
        print("  FALLO: resultado es None")
        ok = False
    elif len(resultado) != 2:
        print("  FALLO: se esperaban 2 registros, se obtuvieron " + str(len(resultado)))
        ok = False

    # Verificar que todos los valores son string o None
    if ok:
        for reg in resultado:
            for campo in reg.keys():
                valor = reg[campo]
                if valor != None and type(valor) != str:
                    print(
                        "  FALLO: campo '"
                        + campo
                        + "' tiene tipo "
                        + str(type(valor))
                        + " en vez de str"
                    )
                    ok = False

    # Verificar conversion especifica
    if ok:
        if resultado[0]["monto_o_limite"] != "50000":
            print(
                "  FALLO: monto_o_limite deberia ser '50000', es '"
                + str(resultado[0]["monto_o_limite"])
                + "'"
            )
            ok = False
        if resultado[0]["flag_prioritario"] != "True":
            print(
                "  FALLO: flag_prioritario deberia ser 'True', es '"
                + str(resultado[0]["flag_prioritario"])
                + "'"
            )
            ok = False

    # Limpiar
    os.remove(ruta)

    if ok:
        print("  OK")
    assert ok


def test_json_vacio():
    # DADO un archivo JSON con un array vacio []
    # CUANDO se ejecuta la ingesta
    # ENTONCES se retorna lista vacia
    print("TEST: test_json_vacio")

    ruta = os.path.join(CARPETA_TEST, "temp_vacio.json")
    arch = open(ruta, "w", encoding="utf-8")
    arch.write("[]")
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


# Ejecutar tests manualmente
if __name__ == "__main__":
    print("=" * 50)
    print("TESTS DE INGESTA (RF-01)")
    print("=" * 50)

    total = 10
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
    try:
        test_lectura_json_valido()
        aprobados += 1
    except AssertionError:
        pass
    try:
        test_lectura_txt_valido()
        aprobados += 1
    except AssertionError:
        pass
    try:
        test_formato_no_soportado()
        aprobados += 1
    except AssertionError:
        pass
    try:
        test_json_tipos_nativos()
        aprobados += 1
    except AssertionError:
        pass
    try:
        test_json_vacio()
        aprobados += 1
    except AssertionError:
        pass

    print("")
    print("Resultado: " + str(aprobados) + "/" + str(total) + " tests aprobados")
