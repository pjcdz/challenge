# test_main.py - Tests para el orquestador del workflow (RF-05)
# Verifica ejecucion completa (e2e) y abort por archivo invalido/vacio

import sys
import os
import json
import shutil

# Agregar src al path
sys.path.insert(
    0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src")
)

import logger
import main

# Inicializar logger para tests
logger.inicializar()

CARPETA_TEST = os.path.dirname(os.path.abspath(__file__))


def test_workflow_completo_e2e():
    # DADO un archivo CSV con registros validos e invalidos
    # CUANDO se ejecuta el workflow completo
    # ENTONCES genera carpeta de ejecucion con CSV, reporte y log correctos
    print("TEST: test_workflow_completo_e2e")

    # Crear archivo CSV de prueba
    ruta_csv = os.path.join(CARPETA_TEST, "temp_e2e.csv")
    arch = open(ruta_csv, "w", encoding="utf-8")
    arch.write(
        "id_solicitud,fecha_solicitud,tipo_producto,id_cliente,monto_o_limite,moneda,pais,flag_prioritario,flag_digital\n"
    )
    arch.write("SOL-E01,15/03/2025,CUENTA,CLI-100,50000,ARS,Argentina,S,N\n")
    arch.write("SOL-E02,2025-06-20,tarjeta,CLI-200,75000,USD,Brasil,N,S\n")
    arch.write("SOL-E03,10/01/2025,,CLI-300,30000,ARS,Argentina,S,N\n")
    arch.close()

    resultado_main = main.main(
        archivo_entrada_param=ruta_csv,
        dir_data_param=CARPETA_TEST,
    )

    ok = True

    if resultado_main == None:
        print("  FALLO: main.main devolvio None")
        ok = False
    elif resultado_main["status"] != "ok":
        print(
            "  FALLO: status esperado 'ok', se obtuvo '"
            + str(resultado_main["status"])
            + "'"
        )
        ok = False

    if ok:
        carpeta_ejecucion = resultado_main["carpeta_ejecucion"]
        ruta_salida = resultado_main["archivo_salida"]
        ruta_reporte = resultado_main["archivo_reporte"]
        ruta_log = resultado_main["archivo_log"]
    else:
        carpeta_ejecucion = ""
        ruta_salida = ""
        ruta_reporte = ""
        ruta_log = ""

    # Verificar carpeta de ejecucion
    if ok and not os.path.exists(carpeta_ejecucion):
        print("  FALLO: no existe carpeta de ejecucion")
        ok = False
    elif ok and "ejecuciones" not in carpeta_ejecucion:
        print("  FALLO: la carpeta de ejecucion no esta bajo 'ejecuciones'")
        ok = False

    # Verificar CSV de salida (header + 3 registros = 4 lineas)
    if ok and not os.path.exists(ruta_salida):
        print("  FALLO: no se genero el archivo CSV de salida")
        ok = False
    elif ok:
        arch = open(ruta_salida, "r", encoding="utf-8")
        lineas = []
        for linea in arch:
            lineas.append(linea)
        arch.close()
        if len(lineas) < 4:
            print("  FALLO: CSV de salida tiene menos de 4 lineas")
            ok = False
        else:
            tiene_valido = False
            tiene_invalido = False
            i = 1
            while i < len(lineas):
                if "VALIDO" in lineas[i] and "INVALIDO" not in lineas[i]:
                    tiene_valido = True
                if "INVALIDO" in lineas[i]:
                    tiene_invalido = True
                i += 1
            if not tiene_valido:
                print("  FALLO: no hay registros VALIDO en el CSV de salida")
                ok = False
            if not tiene_invalido:
                print("  FALLO: no hay registros INVALIDO (SOL-E03 deberia fallar R1)")
                ok = False

    # Verificar reporte JSON
    if ok and not os.path.exists(ruta_reporte):
        print("  FALLO: no se genero reporte_calidad.json")
        ok = False
    elif ok:
        arch = open(ruta_reporte, "r", encoding="utf-8")
        contenido = arch.read()
        arch.close()
        datos = json.loads(contenido)
        if "resumen" not in datos.keys():
            print("  FALLO: reporte no contiene 'resumen'")
            ok = False
        elif datos["resumen"]["total_procesados"] != 3:
            print(
                "  FALLO: reporte dice "
                + str(datos["resumen"]["total_procesados"])
                + " procesados, se esperaban 3"
            )
            ok = False

    # Verificar log de la ejecucion
    if ok and not os.path.exists(ruta_log):
        print("  FALLO: no se genero workflow.log")
        ok = False
    elif ok:
        arch = open(ruta_log, "r", encoding="utf-8")
        contenido_log = arch.read()
        arch.close()
        if "Workflow completado en " not in contenido_log:
            print("  FALLO: workflow.log no contiene resumen final")
            ok = False

    # Limpiar temporales
    if os.path.exists(ruta_csv):
        os.remove(ruta_csv)
    if carpeta_ejecucion != "" and os.path.exists(carpeta_ejecucion):
        shutil.rmtree(carpeta_ejecucion)

    if ok:
        print("  OK")
    assert ok


def test_abort_archivo_inexistente():
    # DADO un archivo CSV que no existe
    # CUANDO se ejecuta main.main() con esa ruta
    # ENTONCES aborta sin crash y genera solo carpeta + log de ejecucion
    print("TEST: test_abort_archivo_inexistente")

    resultado_main = main.main(
        archivo_entrada_param="archivo_que_no_existe_e2e.csv",
        dir_data_param=CARPETA_TEST,
    )

    ok = True

    if resultado_main == None:
        print("  FALLO: main.main devolvio None")
        ok = False
    elif resultado_main["status"] != "error":
        print(
            "  FALLO: status esperado 'error', se obtuvo '"
            + str(resultado_main["status"])
            + "'"
        )
        ok = False

    if ok:
        carpeta_ejecucion = resultado_main["carpeta_ejecucion"]
        ruta_log = resultado_main["archivo_log"]
    else:
        carpeta_ejecucion = ""
        ruta_log = ""

    if ok and not os.path.exists(carpeta_ejecucion):
        print("  FALLO: no se creo carpeta de ejecucion")
        ok = False
    if ok and not os.path.exists(ruta_log):
        print("  FALLO: no se creo workflow.log")
        ok = False
    if ok and resultado_main["archivo_salida"] != None:
        print("  FALLO: archivo_salida deberia ser None")
        ok = False
    if ok and resultado_main["archivo_reporte"] != None:
        print("  FALLO: archivo_reporte deberia ser None")
        ok = False

    if carpeta_ejecucion != "" and os.path.exists(carpeta_ejecucion):
        shutil.rmtree(carpeta_ejecucion)

    if ok:
        print("  OK")
    assert ok


def test_abort_archivo_vacio():
    # DADO un archivo CSV con solo header (sin datos)
    # CUANDO se ejecuta main.main() con esa ruta
    # ENTONCES aborta sin crash y genera solo carpeta + log de ejecucion
    print("TEST: test_abort_archivo_vacio")

    ruta_csv = os.path.join(CARPETA_TEST, "temp_vacio_main.csv")

    # Crear archivo CSV con solo header
    arch = open(ruta_csv, "w", encoding="utf-8")
    arch.write(
        "id_solicitud,fecha_solicitud,tipo_producto,id_cliente,monto_o_limite,moneda,pais,flag_prioritario,flag_digital\n"
    )
    arch.close()

    resultado_main = main.main(
        archivo_entrada_param=ruta_csv,
        dir_data_param=CARPETA_TEST,
    )

    ok = True

    if resultado_main == None:
        print("  FALLO: main.main devolvio None")
        ok = False
    elif resultado_main["status"] != "empty":
        print(
            "  FALLO: status esperado 'empty', se obtuvo '"
            + str(resultado_main["status"])
            + "'"
        )
        ok = False

    if ok:
        carpeta_ejecucion = resultado_main["carpeta_ejecucion"]
        ruta_log = resultado_main["archivo_log"]
    else:
        carpeta_ejecucion = ""
        ruta_log = ""

    if ok and not os.path.exists(carpeta_ejecucion):
        print("  FALLO: no se creo carpeta de ejecucion")
        ok = False
    if ok and not os.path.exists(ruta_log):
        print("  FALLO: no se creo workflow.log")
        ok = False
    if ok and resultado_main["archivo_salida"] != None:
        print("  FALLO: archivo_salida deberia ser None")
        ok = False
    if ok and resultado_main["archivo_reporte"] != None:
        print("  FALLO: archivo_reporte deberia ser None")
        ok = False

    # Limpiar temporales
    if os.path.exists(ruta_csv):
        os.remove(ruta_csv)
    if carpeta_ejecucion != "" and os.path.exists(carpeta_ejecucion):
        shutil.rmtree(carpeta_ejecucion)

    if ok:
        print("  OK")
    assert ok


def test_exportar_csv():
    # DADO una lista de registros procesados
    # CUANDO se exporta a CSV
    # ENTONCES el archivo tiene header y datos correctos
    print("TEST: test_exportar_csv")

    registros = [
        {
            "id_solicitud": "SOL-X01",
            "fecha_solicitud": "15/03/2025",
            "tipo_producto": "CUENTA",
            "id_cliente": "CLI-100",
            "monto_o_limite": "50000",
            "moneda": "ARS",
            "pais": "Argentina",
            "flag_prioritario": "S",
            "flag_digital": "N",
            "categoria_riesgo": "MEDIO",
            "estado": "VALIDO",
            "motivos_falla": "",
        },
    ]

    carpeta_export = os.path.join(CARPETA_TEST, "temp_export")
    ruta_salida = os.path.join(carpeta_export, "temp_exportar.csv")
    main.exportar_csv(registros, ruta_salida)

    ok = True
    if not os.path.exists(ruta_salida):
        print("  FALLO: no se genero el archivo CSV")
        ok = False
    else:
        arch = open(ruta_salida, "r", encoding="utf-8")
        lineas = []
        for linea in arch:
            if linea[-1] == "\n":
                linea = linea[:-1]
            lineas.append(linea)
        arch.close()

        if len(lineas) < 2:
            print("  FALLO: CSV tiene menos de 2 lineas")
            ok = False
        else:
            if "id_solicitud" not in lineas[0]:
                print("  FALLO: header no contiene 'id_solicitud'")
                ok = False
            if "SOL-X01" not in lineas[1]:
                print("  FALLO: primera linea de datos no contiene 'SOL-X01'")
                ok = False

    # Limpiar
    if os.path.exists(carpeta_export):
        shutil.rmtree(carpeta_export)

    if ok:
        print("  OK")
    assert ok


def test_ejecuciones_consecutivas_no_sobrescriben():
    # DADO el mismo archivo de entrada
    # CUANDO se ejecuta main.main() dos veces consecutivas
    # ENTONCES se generan carpetas de ejecucion distintas
    print("TEST: test_ejecuciones_consecutivas_no_sobrescriben")

    ruta_csv = os.path.join(CARPETA_TEST, "temp_doble_run.csv")
    arch = open(ruta_csv, "w", encoding="utf-8")
    arch.write(
        "id_solicitud,fecha_solicitud,tipo_producto,id_cliente,monto_o_limite,moneda,pais,flag_prioritario,flag_digital\n"
    )
    arch.write("SOL-R01,15/03/2025,CUENTA,CLI-100,50000,ARS,Argentina,S,N\n")
    arch.close()

    r1 = main.main(archivo_entrada_param=ruta_csv, dir_data_param=CARPETA_TEST)
    r2 = main.main(archivo_entrada_param=ruta_csv, dir_data_param=CARPETA_TEST)

    ok = True
    if r1 == None or r2 == None:
        print("  FALLO: alguna ejecucion devolvio None")
        ok = False
    elif r1["status"] != "ok" or r2["status"] != "ok":
        print("  FALLO: ambas ejecuciones deberian terminar en status 'ok'")
        ok = False
    elif r1["carpeta_ejecucion"] == r2["carpeta_ejecucion"]:
        print("  FALLO: ambas ejecuciones escribieron en la misma carpeta")
        ok = False
    elif not os.path.exists(r1["carpeta_ejecucion"]) or not os.path.exists(
        r2["carpeta_ejecucion"]
    ):
        print("  FALLO: alguna carpeta de ejecucion no existe")
        ok = False

    # Limpiar temporales
    if os.path.exists(ruta_csv):
        os.remove(ruta_csv)
    if (
        r1 != None
        and "carpeta_ejecucion" in r1.keys()
        and os.path.exists(r1["carpeta_ejecucion"])
    ):
        shutil.rmtree(r1["carpeta_ejecucion"])
    if (
        r2 != None
        and "carpeta_ejecucion" in r2.keys()
        and os.path.exists(r2["carpeta_ejecucion"])
    ):
        shutil.rmtree(r2["carpeta_ejecucion"])

    if ok:
        print("  OK")
    assert ok


# Ejecutar tests manualmente
if __name__ == "__main__":
    print("=" * 50)
    print("TESTS DE MAIN / ORQUESTADOR (RF-05)")
    print("=" * 50)

    total = 5
    aprobados = 0

    try:
        test_workflow_completo_e2e()
        aprobados += 1
    except AssertionError:
        pass
    try:
        test_abort_archivo_inexistente()
        aprobados += 1
    except AssertionError:
        pass
    try:
        test_abort_archivo_vacio()
        aprobados += 1
    except AssertionError:
        pass
    try:
        test_exportar_csv()
        aprobados += 1
    except AssertionError:
        pass
    try:
        test_ejecuciones_consecutivas_no_sobrescriben()
        aprobados += 1
    except AssertionError:
        pass

    print("")
    print("Resultado: " + str(aprobados) + "/" + str(total) + " tests aprobados")
