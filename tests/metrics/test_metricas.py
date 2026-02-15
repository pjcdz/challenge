# test_metricas.py - Tests para el modulo de metricas (RF-06 AI-First)
# Verifica calculo de metricas y comparacion de modos

import sys
import os
import json
import tempfile
import shutil

# Agregar paths necesarios
dir_tests = os.path.dirname(os.path.abspath(__file__))
dir_raiz = os.path.dirname(os.path.dirname(dir_tests))
dir_metrics = os.path.join(dir_raiz, "metrics")
sys.path.insert(0, dir_metrics)
sys.path.insert(0, dir_raiz)

import metricas

CARPETA_TEST = dir_tests


def test_calcular_metricas_modo():
    # DADO un resultado de modo con resumen
    # CUANDO se calculan metricas
    # ENTONCEs tiene tiempo, throughput y conteos correctos
    print("TEST: test_calcular_metricas_modo")

    resultado_modo = {
        "status": "ok",
        "resumen": {
            "total_procesados": 100,
            "total_validos": 85,
            "total_invalidos": 15,
            "duracion_segundos": 5.0,
        },
    }

    metricas_calc = metricas.calcular_metricas_modo(resultado_modo)

    ok = True
    if metricas_calc["tiempo_total_segundos"] != 5.0:
        print("  FALLO: tiempo incorrecto")
        ok = False
    elif metricas_calc["total_procesados"] != 100:
        print("  FALLO: total_procesados incorrecto")
        ok = False
    elif metricas_calc["throughput_registros_seg"] != 20.0:
        print("  FALLO: throughput deberia ser 20.0 (100/5)")
        ok = False
    elif metricas_calc["total_validos"] != 85:
        print("  FALLO: total_validos incorrecto")
        ok = False
    elif metricas_calc["total_invalidos"] != 15:
        print("  FALLO: total_invalidos incorrecto")
        ok = False

    if ok:
        print("  OK")
    assert ok


def test_calcular_metricas_ai_first():
    # DADO un resultado AI-First con enrutamiento y metricas LLM
    # CUANDO se calculan metricas
    # ENTONCEs incluye porcentaje LLM, tokens y costo
    print("TEST: test_calcular_metricas_ai_first")

    resultado_modo = {
        "status": "ok",
        "resumen": {
            "total_procesados": 100,
            "total_validos": 90,
            "total_invalidos": 10,
            "duracion_segundos": 10.0,
        },
        "enrutamiento": {
            "total": 100,
            "regla_path": 80,
            "llm_path": 20,
            "porcentaje_llm": 20.0,
        },
        "metricas_llm": {
            "total_llamadas": 20,
            "total_tokens_prompt": 2000,
            "total_tokens_completion": 1000,
        },
    }

    metricas_calc = metricas.calcular_metricas_modo(resultado_modo)

    ok = True
    if metricas_calc["porcentaje_llm"] != 20.0:
        print("  FALLO: porcentaje_llm incorrecto")
        ok = False
    elif metricas_calc["total_llm_path"] != 20:
        print("  FALLO: total_llm_path incorrecto")
        ok = False
    elif metricas_calc["total_rule_path"] != 80:
        print("  FALLO: total_rule_path incorrecto")
        ok = False
    elif metricas_calc["llm_calls_totales"] != 20:
        print("  FALLO: llm_calls_totales incorrecto")
        ok = False
    elif metricas_calc["llm_tokens_prompt"] != 2000:
        print("  FALLO: llm_tokens_prompt incorrecto")
        ok = False

    if ok:
        print("  OK")
    assert ok


def test_calcular_metricas_costo_estimado():
    # DADO metricas LLM con tokens
    # CUANDO se calculan metricas
    # ENTONCEs calcula costo estimado correctamente
    print("TEST: test_calcular_metricas_costo_estimado")

    # 1000 tokens prompt * 0.000000075 = 0.000075
    # 500 tokens completion * 0.0000003 = 0.00015
    # Total = 0.000225 ~ 0.0002
    resultado_modo = {
        "status": "ok",
        "resumen": {
            "total_procesados": 10,
            "total_validos": 10,
            "total_invalidos": 0,
            "duracion_segundos": 1.0,
        },
        "metricas_llm": {
            "total_llamadas": 5,
            "total_tokens_prompt": 1000,
            "total_tokens_completion": 500,
        },
    }

    metricas_calc = metricas.calcular_metricas_modo(resultado_modo)

    ok = True
    # El costo deberia ser aprox 0.000225 (con redondeo a 6 decimales)
    costo = metricas_calc["llm_costo_estimado_usd"]
    if costo < 0.0002 or costo > 0.0003:
        print("  FALLO: costo estimado incorrecto: " + str(costo))
        ok = False

    if ok:
        print("  OK")
    assert ok


def test_calcular_metricas_tokens_no_disponibles():
    # DADO llamadas LLM reales sin usage metadata de tokens
    # CUANDO se calculan metricas
    # ENTONCES tokens/costo quedan explicitamente NO_DISPONIBLE
    print("TEST: test_calcular_metricas_tokens_no_disponibles")

    resultado_modo = {
        "status": "ok",
        "resumen": {
            "total_procesados": 5,
            "total_validos": 4,
            "total_invalidos": 1,
            "duracion_segundos": 2.0,
        },
        "metricas_llm": {
            "total_llamadas": 2,
            "total_tokens_prompt": 0,
            "total_tokens_completion": 0,
            "costo_estimado_usd": 0.0,
        },
    }

    metricas_calc = metricas.calcular_metricas_modo(resultado_modo)

    ok = True
    if metricas_calc.get("llm_calls_totales", 0) != 2:
        print("  FALLO: llm_calls_totales deberia ser 2")
        ok = False
    elif metricas_calc.get("llm_tokens_disponibles", True):
        print("  FALLO: llm_tokens_disponibles deberia ser False")
        ok = False
    elif metricas_calc.get("llm_tokens_prompt", "X") != None:
        print("  FALLO: llm_tokens_prompt deberia ser None")
        ok = False
    elif metricas_calc.get("llm_tokens_completion", "X") != None:
        print("  FALLO: llm_tokens_completion deberia ser None")
        ok = False
    elif metricas_calc.get("llm_costo_estimado_usd", "X") != None:
        print("  FALLO: llm_costo_estimado_usd deberia ser None")
        ok = False
    elif metricas_calc.get("llm_costo_estado", "") != "no_disponible":
        print("  FALLO: llm_costo_estado deberia ser no_disponible")
        ok = False

    if ok:
        print("  OK")
    assert ok


def test_comparar_modos():
    # DADO metricas de legacy y AI-First
    # CUANDO se comparan
    # ENTONCEs genera analisis con ratios
    print("TEST: test_comparar_modos")

    metricas_legacy = {
        "tiempo_total_segundos": 5.0,
        "throughput_registros_seg": 20.0,
        "total_procesados": 100,
        "total_validos": 85,
        "total_invalidos": 15,
    }

    metricas_ai_first = {
        "tiempo_total_segundos": 10.0,
        "throughput_registros_seg": 10.0,
        "total_procesados": 100,
        "total_validos": 90,
        "total_invalidos": 10,
        "porcentaje_llm": 20.0,
        "total_llm_path": 20,
        "total_rule_path": 80,
        "llm_calls_totales": 20,
        "llm_costo_estimado_usd": 0.01,
    }

    comparacion = metricas.comparar_modos(metricas_legacy, metricas_ai_first)

    ok = True
    if "tiempo" not in comparacion.keys():
        print("  FALLO: falta seccion tiempo")
        ok = False
    elif "resultados" not in comparacion.keys():
        print("  FALLO: falta seccion resultados")
        ok = False
    elif "llm" not in comparacion.keys():
        print("  FALLO: falta seccion llm")
        ok = False

    if ok:
        ratio = comparacion["tiempo"]["ratio_ai_vs_legacy"]
        if ratio != 2.0:  # 10.0 / 5.0 = 2.0
            print("  FALLO: ratio incorrecto: " + str(ratio))
            ok = False

        diff_validos = comparacion["resultados"]["diferencia_validos"]
        if diff_validos != 5:  # 90 - 85 = 5
            print("  FALLO: diferencia_validos incorrecto: " + str(diff_validos))
            ok = False

    if ok:
        print("  OK")
    assert ok


def test_generar_resumen_markdown():
    # DADO metricas de ambos modos y comparacion
    # CUANDO se genera resumen
    # ENTONCEs tiene formato markdown con tablas
    print("TEST: test_generar_resumen_markdown")

    metricas_legacy = {
        "tiempo_total_segundos": 5.0,
        "throughput_registros_seg": 20.0,
        "total_procesados": 100,
        "total_validos": 85,
        "total_invalidos": 15,
    }

    metricas_ai_first = {
        "tiempo_total_segundos": 10.0,
        "throughput_registros_seg": 10.0,
        "total_procesados": 100,
        "total_validos": 90,
        "total_invalidos": 10,
        "porcentaje_llm": 20.0,
        "total_llm_path": 20,
        "total_rule_path": 80,
    }

    comparacion = metricas.comparar_modos(metricas_legacy, metricas_ai_first)
    markdown = metricas.generar_resumen_markdown(
        metricas_legacy, metricas_ai_first, comparacion
    )

    ok = True
    if "# Benchmark: Legacy vs AI-First" not in markdown:
        print("  FALLO: falta titulo")
        ok = False
    elif "## Resumen de Performance" not in markdown:
        print("  FALLO: falta seccion resumen")
        ok = False
    elif "| Metrica | Legacy | AI-First |" not in markdown:
        print("  FALLO: falta tabla de metricas")
        ok = False
    elif "## Metricas LLM (AI-First)" not in markdown:
        print("  FALLO: falta seccion LLM")
        ok = False

    if ok:
        print("  OK")
    assert ok


def test_precision_ambiguos_con_ground_truth():
    # DADO resultado de modo y ground truth
    # CUANDO se calculan metricas con ground truth
    # ENTONCEs calcula precision en subset ambiguo
    print("TEST: test_precision_ambiguos_con_ground_truth")

    # Crear CSV de salida temporal
    dir_temp = tempfile.mkdtemp()
    ruta_csv = os.path.join(dir_temp, "salida.csv")
    arch = open(ruta_csv, "w", encoding="utf-8")
    arch.write("id_solicitud,fecha_solicitud,tipo_producto,moneda,pais,estado\n")
    # Registro ambiguo normalizado correctamente
    arch.write("SYNTH-001,15/03/2025,CUENTA,ARS,Argentina,VALIDO\n")
    arch.write("SYNTH-002,20/06/2025,TARJETA,USD,Brasil,VALIDO\n")
    arch.close()

    resultado_modo = {
        "status": "ok",
        "archivo_salida": ruta_csv,
        "resumen": {
            "total_procesados": 2,
            "total_validos": 2,
            "total_invalidos": 0,
        },
    }

    ground_truth = [
        {
            "id_solicitud": "SYNTH-001",
            "tipo": "ambiguo",
            "estado_esperado": "depende_resolucion",
            "tipo_producto_normalizado": "CUENTA",
            "moneda_normalizada": "ARS",
            "pais_normalizado": "Argentina",
        },
        {
            "id_solicitud": "SYNTH-002",
            "tipo": "ambiguo",
            "estado_esperado": "depende_resolucion",
            "tipo_producto_normalizado": "TARJETA",
            "moneda_normalizada": "USD",
            "pais_normalizado": "Brasil",
        },
    ]

    metricas_calc = metricas.calcular_metricas_modo(resultado_modo, ground_truth)

    ok = True
    if metricas_calc["precision_ambiguos"] == None:
        print("  FALLO: precision_ambiguos deberia estar calculada")
        ok = False
    elif metricas_calc["precision_ambiguos"] != 100.0:
        print(
            "  FALLO: precision deberia ser 100.0, es "
            + str(metricas_calc["precision_ambiguos"])
        )
        ok = False

    # Limpiar
    shutil.rmtree(dir_temp)

    if ok:
        print("  OK")
    assert ok


# Ejecutar tests manualmente
if __name__ == "__main__":
    print("=" * 50)
    print("TESTS DE METRICAS (RF-06 AI-First)")
    print("=" * 50)

    tests = [
        test_calcular_metricas_modo,
        test_calcular_metricas_ai_first,
        test_calcular_metricas_costo_estimado,
        test_calcular_metricas_tokens_no_disponibles,
        test_comparar_modos,
        test_generar_resumen_markdown,
        test_precision_ambiguos_con_ground_truth,
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
