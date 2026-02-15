# test_real_llm.py - Tests de integracion con LLM real (sin mocks)
# Verifica uso de .env.local y ejecucion AI-First con provider Gemini real

import sys
import os
import tempfile
import shutil

# Agregar paths necesarios
dir_tests = os.path.dirname(os.path.abspath(__file__))
dir_raiz = os.path.dirname(os.path.dirname(dir_tests))
dir_ai_src = os.path.join(dir_raiz, "ai_first_system", "src")
sys.path.insert(0, dir_ai_src)


def test_provider_real_desde_env():
    # DADO .env.local configurado
    # CUANDO se crea provider Gemini
    # ENTONCES no usa mock y toma modelo real
    print("TEST: test_provider_real_desde_env")

    import run_ai_first
    import config

    ok = True
    if config.GEMINI_API_KEY == None or config.GEMINI_API_KEY == "":
        print("  FALLO: falta GEMINI_API_KEY en .env.local")
        ok = False
    elif config.MODO_MOCK:
        print("  FALLO: AI_FIRST_MOCK no debe estar activo para test real")
        ok = False

    provider = None
    err = None
    if ok:
        provider, err = run_ai_first.crear_llm_provider("gemini")
        if err != None:
            print("  FALLO: error creando provider real: " + str(err))
            ok = False
        elif provider == None:
            print("  FALLO: provider real no fue creado")
            ok = False
        elif provider.nombre != "gemini":
            print("  FALLO: provider debe ser gemini")
            ok = False
        elif provider.modelo != config.GEMINI_GEMMA_MODEL:
            print("  FALLO: modelo no coincide con .env.local")
            ok = False

    if ok:
        print("  OK")
    assert ok


def test_workflow_ai_first_con_llm_real():
    # DADO un dataset con al menos un caso ambiguo
    # CUANDO corre AI-First con provider gemini real
    # ENTONCES usa llm_path y registra metricas de llamadas reales
    print("TEST: test_workflow_ai_first_con_llm_real")

    import run_ai_first
    import config

    ok = True
    if config.GEMINI_API_KEY == None or config.GEMINI_API_KEY == "":
        print("  FALLO: falta GEMINI_API_KEY en .env.local")
        ok = False
    elif config.MODO_MOCK:
        print("  FALLO: AI_FIRST_MOCK no debe estar activo para test real")
        ok = False

    dir_temp = tempfile.mkdtemp()
    ruta_csv = os.path.join(dir_temp, "temp_real_llm.csv")

    # Crear entrada con 1 registro ambiguo + 1 limpio
    arch = open(ruta_csv, "w", encoding="utf-8")
    arch.write(
        "id_solicitud,fecha_solicitud,tipo_producto,id_cliente,monto_o_limite,moneda,pais,flag_prioritario,flag_digital\n"
    )
    arch.write("REAL-001,15 marzo 2025,cta ahorro,CLI-901,50000,pesos,arg,S,N\n")
    arch.write("REAL-002,15/03/2025,CUENTA,CLI-902,70000,ARS,Argentina,N,S\n")
    arch.close()

    resultado = None
    if ok:
        resultado = run_ai_first.run(ruta_csv, provider_nombre="gemini", dir_data=dir_temp)
        if resultado == None:
            print("  FALLO: resultado es None")
            ok = False
        elif resultado.get("status") != "ok":
            print("  FALLO: status esperado ok, se obtuvo " + str(resultado.get("status")))
            ok = False

    if ok:
        enr = resultado.get("enrutamiento", {})
        llm_path = enr.get("llm_path", 0)
        if llm_path < 1:
            print("  FALLO: deberia haber al menos 1 registro por llm_path")
            ok = False

    if ok:
        mlm = resultado.get("metricas_llm", {})
        if mlm.get("provider", "") != "gemini":
            print("  FALLO: metricas_llm.provider deberia ser gemini")
            ok = False
        elif mlm.get("modelo", "") != config.GEMINI_GEMMA_MODEL:
            print("  FALLO: metricas_llm.modelo no coincide con .env.local")
            ok = False
        else:
            llamadas_ok = mlm.get("total_llamadas_exitosas", 0)
            if llamadas_ok <= 0:
                llamadas_tot = mlm.get("total_llamadas", 0)
                llamadas_err = mlm.get("total_llamadas_fallidas", 0)
                if llamadas_tot > llamadas_err:
                    llamadas_ok = llamadas_tot - llamadas_err
            llamadas_err = mlm.get("total_llamadas_fallidas", 0)
            if llamadas_ok < 1:
                print("  FALLO: no hubo llamadas exitosas reales al provider")
                ok = False

    if os.path.exists(dir_temp):
        shutil.rmtree(dir_temp)

    if ok:
        print("  OK")
    assert ok
