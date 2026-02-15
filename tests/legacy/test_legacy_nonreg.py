# test_legacy_nonreg.py - Tests de no-regresion para legacy_system
# Verifica comportamiento estable del baseline legacy
# Corre el workflow legacy y verifica resultados contra esperados

import sys
import os
import json

# Agregar paths
dir_tests = os.path.dirname(os.path.abspath(__file__))
dir_raiz = os.path.dirname(os.path.dirname(dir_tests))
dir_legacy_src = os.path.join(dir_raiz, "legacy_system", "src")
sys.path.insert(0, dir_legacy_src)

import logger

# Inicializar logger
logger.inicializar()

CARPETA_TEST = dir_tests


def test_legacy_ingesta_csv():
    # DADO un archivo CSV valido
    # CUANDO se lee con ingesta legacy
    # ENTONCES se retorna lista de diccionarios correcta
    print("TEST: test_legacy_ingesta_csv")

    import ingesta

    ruta = os.path.join(CARPETA_TEST, "temp_leg_csv.csv")
    arch = open(ruta, "w", encoding="utf-8")
    arch.write(
        "id_solicitud,fecha_solicitud,tipo_producto,id_cliente,monto_o_limite,moneda,pais,flag_prioritario,flag_digital\n"
    )
    arch.write("SOL-001,15/03/2025,CUENTA,CLI-100,50000,ARS,Argentina,S,N\n")
    arch.write("SOL-002,20/06/2025,TARJETA,CLI-200,75000,USD,Brasil,N,S\n")
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
        print("  FALLO: primer id_solicitud incorrecto")
        ok = False

    os.remove(ruta)

    if ok:
        print("  OK")
    assert ok


def test_legacy_normalizador():
    # DADO una lista de registros con datos sucios
    # CUANDO se normalizan con normalizador legacy
    # ENTONCES los registros quedan en formato canonico
    print("TEST: test_legacy_normalizador")

    import normalizador

    registros = [
        {
            "id_solicitud": "SOL-001",
            "fecha_solicitud": "2025-03-15",
            "tipo_producto": "  cuenta  ",
            "id_cliente": "CLI-100",
            "monto_o_limite": " 50000 ",
            "moneda": " ars ",
            "pais": " argentina ",
            "flag_prioritario": "S",
            "flag_digital": "N",
        }
    ]

    resultado = normalizador.normalizar_registros(registros)

    ok = True
    if resultado == None:
        print("  FALLO: resultado es None")
        ok = False
    elif len(resultado) != 1:
        print("  FALLO: se esperaba 1 registro normalizado")
        ok = False
    elif resultado[0]["moneda"] != "ARS":
        print("  FALLO: moneda deberia ser ARS, es " + str(resultado[0]["moneda"]))
        ok = False
    elif resultado[0]["fecha_solicitud"] != "15/03/2025":
        print(
            "  FALLO: fecha deberia ser 15/03/2025, es "
            + str(resultado[0]["fecha_solicitud"])
        )
        ok = False

    if ok:
        print("  OK")
    assert ok


def test_legacy_validador():
    # DADO registros normalizados
    # CUANDO se validan con validador legacy
    # ENTONCES se aplican las 3 reglas correctamente
    print("TEST: test_legacy_validador")

    import validador

    # Registro valido
    reg_valido = {
        "id_solicitud": "SOL-001",
        "fecha_solicitud": "15/03/2025",
        "tipo_producto": "CUENTA",
        "id_cliente": "CLI-100",
        "monto_o_limite": "50000",
        "moneda": "ARS",
        "pais": "Argentina",
        "flag_prioritario": "S",
        "flag_digital": "N",
        "categoria_riesgo": "BAJO",
    }

    # Registro con campo vacio (falla R1)
    reg_r1 = {
        "id_solicitud": "SOL-002",
        "fecha_solicitud": "15/03/2025",
        "tipo_producto": "",
        "id_cliente": "CLI-200",
        "monto_o_limite": "50000",
        "moneda": "ARS",
        "pais": "Argentina",
        "flag_prioritario": "S",
        "flag_digital": "N",
        "categoria_riesgo": "BAJO",
    }

    resultado = validador.validar_registros([reg_valido, reg_r1])

    ok = True
    if len(resultado) != 2:
        print("  FALLO: se esperaban 2 resultados")
        ok = False
    elif resultado[0]["estado"] != "VALIDO":
        print("  FALLO: primer registro deberia ser VALIDO")
        ok = False
    elif resultado[1]["estado"] != "INVALIDO":
        print("  FALLO: segundo registro deberia ser INVALIDO")
        ok = False

    if ok:
        print("  OK")
    assert ok


def test_legacy_calidad():
    # DADO registros validados
    # CUANDO se genera el reporte de calidad
    # ENTONCES tiene totales correctos
    print("TEST: test_legacy_calidad")

    import calidad

    registros = [
        {
            "id_solicitud": "SOL-001",
            "estado": "VALIDO",
            "motivos_falla": "",
        },
        {
            "id_solicitud": "SOL-002",
            "estado": "INVALIDO",
            "motivos_falla": "R1: campo vacio",
        },
        {
            "id_solicitud": "SOL-003",
            "estado": "VALIDO",
            "motivos_falla": "",
        },
    ]

    carpeta = CARPETA_TEST
    reporte = calidad.generar_reporte(registros, "test.csv", carpeta)

    ok = True
    if reporte == None:
        print("  FALLO: reporte es None")
        ok = False
    elif reporte["resumen"]["total_procesados"] != 3:
        print("  FALLO: total_procesados deberia ser 3")
        ok = False
    elif reporte["resumen"]["total_validos"] != 2:
        print("  FALLO: total_validos deberia ser 2")
        ok = False

    # Limpiar reporte generado
    ruta_reporte = os.path.join(carpeta, "reporte_calidad.json")
    if os.path.exists(ruta_reporte):
        os.remove(ruta_reporte)

    if ok:
        print("  OK")
    assert ok


def test_legacy_workflow_completo():
    # DADO un archivo CSV de entrada
    # CUANDO se ejecuta el workflow legacy completo
    # ENTONCES genera CSV salida y reporte JSON
    print("TEST: test_legacy_workflow_completo")

    import importlib

    # Limpiar modulos para reimportar
    for mod in ["main", "ingesta", "normalizador", "validador", "calidad", "logger"]:
        if mod in sys.modules.keys():
            del sys.modules[mod]

    sys.path.insert(0, dir_legacy_src)
    import main as main_legacy

    # Crear archivo temporal
    ruta_entrada = os.path.join(CARPETA_TEST, "temp_leg_workflow.csv")
    arch = open(ruta_entrada, "w", encoding="utf-8")
    arch.write(
        "id_solicitud,fecha_solicitud,tipo_producto,id_cliente,monto_o_limite,moneda,pais,flag_prioritario,flag_digital\n"
    )
    arch.write("SOL-001,15/03/2025,CUENTA,CLI-100,50000,ARS,Argentina,S,N\n")
    arch.write("SOL-002,20/06/2025,TARJETA,CLI-200,75000,USD,Brasil,N,S\n")
    arch.close()

    # Carpeta temporal para ejecucion
    import tempfile

    dir_temp = tempfile.mkdtemp()

    resultado = main_legacy.main(
        archivo_entrada_param=ruta_entrada,
        dir_data_param=dir_temp,
    )

    ok = True
    if resultado == None:
        print("  FALLO: resultado es None")
        ok = False
    elif resultado["status"] != "ok":
        print("  FALLO: status deberia ser ok, es " + str(resultado["status"]))
        ok = False
    elif resultado["resumen"]["total_procesados"] != 2:
        print("  FALLO: total_procesados deberia ser 2")
        ok = False

    # Verificar que se crearon archivos de salida
    if ok:
        carpeta_ej = resultado.get("carpeta_ejecucion", "")
        ruta_csv = os.path.join(carpeta_ej, "solicitudes_limpias.csv")
        ruta_json = os.path.join(carpeta_ej, "reporte_calidad.json")
        if not os.path.exists(ruta_csv):
            print("  FALLO: no se creo solicitudes_limpias.csv")
            ok = False
        if not os.path.exists(ruta_json):
            print("  FALLO: no se creo reporte_calidad.json")
            ok = False

    # Limpiar
    os.remove(ruta_entrada)
    import shutil

    if os.path.exists(dir_temp):
        shutil.rmtree(dir_temp)

    # Limpiar modulos
    for mod in ["main", "ingesta", "normalizador", "validador", "calidad", "logger"]:
        if mod in sys.modules.keys():
            del sys.modules[mod]

    if ok:
        print("  OK")
    assert ok


# Ejecutar tests manualmente
if __name__ == "__main__":
    print("=" * 50)
    print("TESTS DE NO-REGRESION LEGACY")
    print("=" * 50)

    tests = [
        test_legacy_ingesta_csv,
        test_legacy_normalizador,
        test_legacy_validador,
        test_legacy_calidad,
        test_legacy_workflow_completo,
    ]

    aprobados = 0
    for t in tests:
        try:
            t()
            aprobados = aprobados + 1
        except AssertionError:
            pass

    print("")
    print("Resultado: " + str(aprobados) + "/" + str(len(tests)) + " tests aprobados")
