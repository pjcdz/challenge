# test_benchmark_runner.py - Tests para benchmark_runner (RF-08 AI-First)
# Verifica generacion de artefactos JSON/Markdown y estructura basica del resultado

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

import benchmark_runner


def test_benchmark_runner_genera_reportes():
    # DADO un benchmark real con provider Gemini
    # CUANDO corre ejecutar_benchmark
    # ENTONCES genera reporte JSON y Markdown validos
    print("TEST: test_benchmark_runner_genera_reportes")

    dir_temp = tempfile.mkdtemp()
    ruta_input = os.path.join(dir_temp, "input.csv")
    arch = open(ruta_input, "w", encoding="utf-8")
    arch.write(
        "id_solicitud,fecha_solicitud,tipo_producto,id_cliente,monto_o_limite,moneda,pais,flag_prioritario,flag_digital\n"
    )
    # Registro ambiguo para forzar llm_path y llamada real a Gemini
    arch.write("BM-001,15 marzo 2025,cta especial,CLI-100,50k,pesos,arg,S,N\n")
    arch.write("BM-002,15/03/2025,CUENTA,CLI-200,50000,ARS,Argentina,N,S\n")
    arch.close()

    dir_reports_orig = benchmark_runner.DIR_REPORTS

    benchmark_runner.DIR_REPORTS = os.path.join(dir_temp, "reports")

    resultado = None
    try:
        resultado = benchmark_runner.ejecutar_benchmark(
            ruta_input, ruta_ground_truth=None, provider="gemini"
        )
    finally:
        benchmark_runner.DIR_REPORTS = dir_reports_orig

    ok = True
    if resultado == None:
        print("  FALLO: resultado es None")
        ok = False
    else:
        ruta_json = resultado.get("ruta_json", "")
        ruta_md = resultado.get("ruta_md", "")
        if ruta_json == "" or not os.path.exists(ruta_json):
            print("  FALLO: no se genero reporte JSON")
            ok = False
        elif ruta_md == "" or not os.path.exists(ruta_md):
            print("  FALLO: no se genero reporte Markdown")
            ok = False
        else:
            arch_json = open(ruta_json, "r", encoding="utf-8")
            datos = json.loads(arch_json.read())
            arch_json.close()
            if datos.get("provider", "") != "gemini":
                print("  FALLO: provider esperado gemini")
                ok = False
            elif "legacy" not in datos.keys() or "ai_first" not in datos.keys():
                print("  FALLO: faltan secciones legacy/ai_first")
                ok = False
            elif datos["ai_first"].get("status", "") != "ok":
                print("  FALLO: ai_first deberia terminar en status ok")
                ok = False
            else:
                m_ai = datos["ai_first"].get("metricas", {})
                if m_ai.get("total_llm_path", 0) < 1:
                    print("  FALLO: total_llm_path deberia ser >= 1")
                    ok = False
                elif m_ai.get("llm_calls_totales", 0) < 1:
                    print("  FALLO: llm_calls_totales deberia ser >= 1")
                    ok = False
                elif (
                    m_ai.get("llm_calls_totales", 0) > 0
                    and m_ai.get("llm_tokens_prompt", 0) == 0
                    and m_ai.get("llm_tokens_completion", 0) == 0
                    and m_ai.get("llm_costo_estimado_usd", 0.0) == 0.0
                ):
                    print(
                        "  FALLO: subreporte detectado (llm_calls>0 con tokens/costo en 0)"
                    )
                    ok = False

    if os.path.exists(dir_temp):
        shutil.rmtree(dir_temp)

    if ok:
        print("  OK")
    assert ok
