# test_data_generator.py - Tests para el generador de datos sinteticos (RF-07)
# Verifica generacion de datasets con diferentes tipos de registros

import sys
import os
import json

# Agregar paths necesarios
dir_tests = os.path.dirname(os.path.abspath(__file__))
dir_raiz = os.path.dirname(os.path.dirname(dir_tests))
dir_metrics = os.path.join(dir_raiz, "metrics")
sys.path.insert(0, dir_metrics)
sys.path.insert(0, dir_raiz)

import data_generator

CARPETA_TEST = dir_tests


def test_generar_registro_limpio():
    # DADO un numero de solicitud y cliente
    # CUANDO se genera un registro limpio
    # ENTONCES tiene todos los campos validos y ground truth correcto
    print("TEST: test_generar_registro_limpio")

    reg, gt = data_generator.generar_registro_limpio(1, 100)

    ok = True
    if "id_solicitud" not in reg.keys():
        print("  FALLO: falta id_solicitud")
        ok = False
    elif "estado_esperado" not in gt.keys():
        print("  FALLO: falta estado_esperado en GT")
        ok = False
    elif gt["estado_esperado"] != "VALIDO":
        print("  FALLO: estado_esperado deberia ser VALIDO")
        ok = False
    elif gt["tipo"] != "limpio":
        print("  FALLO: tipo deberia ser limpio")
        ok = False
    elif gt["origen_esperado"] != "rule_path":
        print("  FALLO: origen_esperado deberia ser rule_path")
        ok = False

    if ok:
        print("  OK")
    assert ok


def test_generar_registro_sucio():
    # DADO un numero de solicitud y cliente
    # CUANDO se genera un registro sucio
    # ENTONCES tiene problemas de formato y ground trackea resolucion
    print("TEST: test_generar_registro_sucio")

    reg, gt = data_generator.generar_registro_sucio(2, 200)

    ok = True
    if "id_solicitud" not in reg.keys():
        print("  FALLO: falta id_solicitud")
        ok = False
    elif gt["tipo"] != "sucio":
        print("  FALLO: tipo deberia ser sucio")
        ok = False
    elif "tipo_producto_normalizado" not in gt.keys():
        print("  FALLO: falta tipo_producto_normalizado en GT")
        ok = False
    elif "moneda_normalizada" not in gt.keys():
        print("  FALLO: falta moneda_normalizada en GT")
        ok = False

    if ok:
        print("  OK")
    assert ok


def test_generar_registro_ambiguo():
    # DADO un numero de solicitud y cliente
    # CUANDO se genera un registro ambiguo
    # ENTONCES tiene campos semanticamente ambiguos y ground trackea resolucion
    print("TEST: test_generar_registro_ambiguo")

    reg, gt = data_generator.generar_registro_ambiguo(3, 300)

    ok = True
    if "id_solicitud" not in reg.keys():
        print("  FALLO: falta id_solicitud")
        ok = False
    elif gt["tipo"] != "ambiguo":
        print("  FALLO: tipo deberia ser ambiguo")
        ok = False
    elif "campos_ambiguos" not in gt.keys():
        print("  FALLO: falta campos_ambiguos en GT")
        ok = False
    elif len(gt["campos_ambiguos"]) == 0:
        print("  FALLO: deberia haber al menos 1 campo ambiguo")
        ok = False
    elif gt["origen_esperado"] != "llm_path":
        print("  FALLO: origen_esperado deberia ser llm_path")
        ok = False

    if ok:
        print("  OK")
    assert ok


def test_generar_dataset():
    # DADO una cantidad, seed y ratios
    # CUANDO se genera un dataset
    # ENTONCEs tiene la distribucion correcta y es reproducible
    print("TEST: test_generar_dataset")

    cantidad = 100
    seed = 42
    ratio_limpio = 0.5
    ratio_sucio = 0.3
    ratio_ambiguo = 0.2

    registros, ground_truth = data_generator.generar_dataset(
        cantidad, seed, ratio_limpio, ratio_sucio, ratio_ambiguo
    )

    ok = True
    if len(registros) != cantidad:
        print(
            "  FALLO: deberian ser "
            + str(cantidad)
            + " registros, hay "
            + str(len(registros))
        )
        ok = False
    elif len(ground_truth) != cantidad:
        print("  FALLO: ground truth deberia tener " + str(cantidad))
        ok = False

    # Verificar distribucion
    if ok:
        cant_limpio = 0
        cant_sucio = 0
        cant_ambiguo = 0
        for gt in ground_truth:
            if gt["tipo"] == "limpio":
                cant_limpio = cant_limpio + 1
            elif gt["tipo"] == "sucio":
                cant_sucio = cant_sucio + 1
            elif gt["tipo"] == "ambiguo":
                cant_ambiguo = cant_ambiguo + 1

        esperado_limpio = int(cantidad * ratio_limpio)
        esperado_sucio = int(cantidad * ratio_sucio)
        esperado_ambiguo = cantidad - esperado_limpio - esperado_sucio

        if cant_limpio != esperado_limpio:
            print(
                "  FALLO: limpios: esperado "
                + str(esperado_limpio)
                + ", obtuve "
                + str(cant_limpio)
            )
            ok = False
        if cant_sucio != esperado_sucio:
            print(
                "  FALLO: sucios: esperado "
                + str(esperado_sucio)
                + ", obtuve "
                + str(cant_sucio)
            )
            ok = False
        if cant_ambiguo != esperado_ambiguo:
            print(
                "  FALLO: ambiguos: esperado "
                + str(esperado_ambiguo)
                + ", obtuve "
                + str(cant_ambiguo)
            )
            ok = False

    if ok:
        print("  OK")
    assert ok


def test_reproducibilidad_con_seed():
    # DADA la misma seed
    # CUANDO se genera el dataset dos veces
    # ENTONCES ambos son identicos
    print("TEST: test_reproducibilidad_con_seed")

    cantidad = 50
    seed = 12345
    ratio_limpio = 0.5
    ratio_sucio = 0.3
    ratio_ambiguo = 0.2

    reg1, gt1 = data_generator.generar_dataset(
        cantidad, seed, ratio_limpio, ratio_sucio, ratio_ambiguo
    )
    reg2, gt2 = data_generator.generar_dataset(
        cantidad, seed, ratio_limpio, ratio_sucio, ratio_ambiguo
    )

    ok = True
    if len(reg1) != len(reg2):
        print("  FALLO: cantidad distinta entre generaciones")
        ok = False

    if ok:
        i = 0
        while i < len(reg1):
            if reg1[i]["id_solicitud"] != reg2[i]["id_solicitud"]:
                print("  FALLO: id_solicitud distinta en posicion " + str(i))
                ok = False
            i = i + 1

    if ok:
        print("  OK")
    assert ok


def test_exportar_csv():
    # DADO una lista de registros
    # CUANDO se exporta a CSV
    # ENTONCES crea el archivo con formato correcto
    print("TEST: test_exportar_csv")

    registros = [
        {
            "id_solicitud": "SOL-001",
            "tipo_producto": "CUENTA",
            "moneda": "ARS",
        },
        {
            "id_solicitud": "SOL-002",
            "tipo_producto": "TARJETA",
            "moneda": "USD",
        },
    ]

    ruta = os.path.join(CARPETA_TEST, "temp_gen_export.csv")
    data_generator.exportar_csv(registros, ruta)

    ok = True
    if not os.path.exists(ruta):
        print("  FALLO: archivo no se creo")
        ok = False

    if ok:
        arch = open(ruta, "r", encoding="utf-8")
        lineas = []
        for linea in arch:
            lineas.append(linea)
        arch.close()

        if len(lineas) != 3:  # header + 2 registros
            print("  FALLO: deberian ser 3 lineas, hay " + str(len(lineas)))
            ok = False
        elif "id_solicitud" not in lineas[0]:
            print("  FALLO: header incorrecto")
            ok = False

    os.remove(ruta)

    if ok:
        print("  OK")
    assert ok


def test_exportar_json():
    # DADO una lista de registros
    # CUANDO se exporta a JSON
    # ENTONCES crea el archivo con formato correcto
    print("TEST: test_exportar_json")

    registros = [
        {
            "id_solicitud": "SOL-001",
            "tipo_producto": "CUENTA",
            "moneda": "ARS",
        },
    ]

    ruta = os.path.join(CARPETA_TEST, "temp_gen_export.json")
    data_generator.exportar_json(registros, ruta)

    ok = True
    if not os.path.exists(ruta):
        print("  FALLO: archivo no se creo")
        ok = False

    if ok:
        arch = open(ruta, "r", encoding="utf-8")
        contenido = arch.read()
        arch.close()

        try:
            datos_json = json.loads(contenido)
            if len(datos_json) != 1:
                print("  FALLO: deberia haber 1 registro en JSON")
                ok = False
        except:
            print("  FALLO: JSON no valido")
            ok = False

    os.remove(ruta)

    if ok:
        print("  OK")
    assert ok


def test_exportar_txt():
    # DADO una lista de registros
    # CUANDO se exporta a TXT (pipe delimitado)
    # ENTONCES crea el archivo con formato correcto
    print("TEST: test_exportar_txt")

    registros = [
        {
            "id_solicitud": "SOL-001",
            "tipo_producto": "CUENTA",
            "moneda": "ARS",
        },
        {
            "id_solicitud": "SOL-002",
            "tipo_producto": "TARJETA",
            "moneda": "USD",
        },
    ]

    ruta = os.path.join(CARPETA_TEST, "temp_gen_export.txt")
    data_generator.exportar_txt(registros, ruta)

    ok = True
    if not os.path.exists(ruta):
        print("  FALLO: archivo no se creo")
        ok = False

    if ok:
        arch = open(ruta, "r", encoding="utf-8")
        lineas = []
        for linea in arch:
            lineas.append(linea)
        arch.close()

        if len(lineas) != 3:  # header + 2 registros
            print("  FALLO: deberian ser 3 lineas, hay " + str(len(lineas)))
            ok = False
        elif "|" not in lineas[1]:
            print("  FALLO: deberia usar pipe como delimitador")
            ok = False

    os.remove(ruta)

    if ok:
        print("  OK")
    assert ok


def test_generar_completo():
    # DADA una cantidad y formato
    # CUANDO se llama a generar()
    # ENTONCEs crea archivos de dataset y ground truth
    print("TEST: test_generar_completo")

    cantidad = 20
    seed = 42
    formato = "csv"

    resultado = data_generator.generar(cantidad, seed, 0.5, 0.3, 0.2, formato)

    ok = True
    if "error" in resultado.keys():
        print("  FALLO: hubo error: " + resultado["error"])
        ok = False
    elif "ruta_dataset" not in resultado.keys():
        print("  FALLO: falta ruta_dataset")
        ok = False
    elif "ruta_ground_truth" not in resultado.keys():
        print("  FALLO: falta ruta_ground_truth")
        ok = False
    elif not os.path.exists(resultado["ruta_dataset"]):
        print("  FALLO: dataset no existe")
        ok = False
    elif not os.path.exists(resultado["ruta_ground_truth"]):
        print("  FALLO: ground truth no existe")
        ok = False
    elif resultado["cantidad_total"] != cantidad:
        print("  FALLO: cantidad_total incorrecta")
        ok = False

    # Verificar ground truth
    if ok:
        arch = open(resultado["ruta_ground_truth"], "r", encoding="utf-8")
        gt_json = json.load(arch)
        arch.close()

        if len(gt_json) != cantidad:
            print("  FALLO: ground truth deberia tener " + str(cantidad))
            ok = False

    # Limpiar
    if ok:
        os.remove(resultado["ruta_dataset"])
        os.remove(resultado["ruta_ground_truth"])

    if ok:
        print("  OK")
    assert ok


def test_ratios_que_suman_1():
    # DADO ratios que suman 1.0
    # CUANDO se genera
    # ENTONCEs no hay error
    print("TEST: test_ratios_que_suman_1")

    resultado = data_generator.generar(100, 42, 0.5, 0.3, 0.2, "csv")

    ok = True
    if "error" in resultado.keys():
        print("  FALLO: error inesperado: " + resultado["error"])
        ok = False

    # Limpiar
    if ok:
        if os.path.exists(resultado["ruta_dataset"]):
            os.remove(resultado["ruta_dataset"])
        if os.path.exists(resultado["ruta_ground_truth"]):
            os.remove(resultado["ruta_ground_truth"])

    if ok:
        print("  OK")
    assert ok


def test_ratios_que_no_suman_1():
    # DADO ratios que no suman 1.0
    # CUANDO se genera
    # ENTONCEs retorna error
    print("TEST: test_ratios_que_no_suman_1")

    # Suman 1.5
    resultado = data_generator.generar(100, 42, 0.5, 0.5, 0.5, "csv")

    ok = True
    if "error" not in resultado.keys():
        print("  FALLO: deberia haber error")
        ok = False

    if ok:
        print("  OK")
    assert ok


# Ejecutar tests manualmente
if __name__ == "__main__":
    print("=" * 50)
    print("TESTS DE DATA GENERATOR (RF-07)")
    print("=" * 50)

    tests = [
        test_generar_registro_limpio,
        test_generar_registro_sucio,
        test_generar_registro_ambiguo,
        test_generar_dataset,
        test_reproducibilidad_con_seed,
        test_exportar_csv,
        test_exportar_json,
        test_exportar_txt,
        test_generar_completo,
        test_ratios_que_suman_1,
        test_ratios_que_no_suman_1,
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
