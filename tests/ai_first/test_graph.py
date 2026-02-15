# test_graph.py - Tests para el grafo de workflow LangGraph (RF-04 AI-First)
# Verifica nodos, rutas y ejecucion manual del grafo

import sys
import os
import json

# Agregar paths necesarios
dir_tests = os.path.dirname(os.path.abspath(__file__))
dir_raiz = os.path.dirname(os.path.dirname(dir_tests))
dir_ai_src = os.path.join(dir_raiz, "ai_first_system", "src")
dir_graph = os.path.join(dir_ai_src, "graph")
dir_agents = os.path.join(dir_ai_src, "agents")
dir_adapters = os.path.join(dir_ai_src, "adapters")
dir_guardrails = os.path.join(dir_ai_src, "guardrails")
dir_legacy = os.path.join(dir_raiz, "legacy_system", "src")
sys.path.insert(0, dir_ai_src)
sys.path.insert(0, dir_graph)
sys.path.insert(0, dir_agents)
sys.path.insert(0, dir_adapters)
sys.path.insert(0, dir_guardrails)
sys.path.insert(0, dir_legacy)

CARPETA_TEST = dir_tests

_PROVIDER_REAL = None


def obtener_provider_real():
    # Retorna provider Gemini real usando .env.local
    global _PROVIDER_REAL
    if _PROVIDER_REAL != None:
        return _PROVIDER_REAL

    import run_ai_first

    provider, err = run_ai_first.crear_llm_provider("gemini")
    if err != None or provider == None:
        raise AssertionError(
            "No se pudo crear provider real Gemini para tests de graph: " + str(err)
        )

    _PROVIDER_REAL = provider
    return _PROVIDER_REAL


def test_nodo_preparar_contexto():
    # DADO un estado con registro y clasificacion
    # CUANDO se ejecuta el nodo preparar_contexto
    # ENTONCES actualiza nodo_actual y limpia error
    print("TEST: test_nodo_preparar_contexto")

    import workflow_graph

    estado = {
        "registro": {"id_solicitud": "SOL-001", "fecha_solicitud": "marzo 2025"},
        "clasificacion": {
            "motivos_ambiguedad": ["fecha ambigua: 'marzo 2025'"],
            "campos_ambiguos": ["fecha_solicitud"],
        },
        "error": "",
        "nodo_actual": "",
    }

    resultado = workflow_graph.nodo_preparar_contexto(estado)

    ok = True
    if resultado["nodo_actual"] != "preparar_contexto":
        print("  FALLO: nodo_actual deberia ser 'preparar_contexto'")
        ok = False

    if ok:
        print("  OK")
    assert ok


def test_nodo_normalizacion_llm_con_real():
    # DADO un estado con registro y provider real
    # CUANDO se ejecuta el nodo normalizacion_llm
    # ENTONCES actualiza resultado_llm
    print("TEST: test_nodo_normalizacion_llm_con_real")

    import workflow_graph

    provider = obtener_provider_real()

    estado = {
        "registro": {
            "id_solicitud": "SOL-001",
            "fecha_solicitud": "marzo 2025",
            "tipo_producto": "CUENTA",
            "id_cliente": "CLI-100",
            "monto_o_limite": "50000",
            "moneda": "ARS",
            "pais": "Argentina",
        },
        "llm_provider": provider,
        "resultado_llm": "",
        "error": "",
        "intentos": 0,
    }

    resultado = workflow_graph.nodo_normalizacion_llm(estado)

    ok = True
    if resultado["error"] != "":
        print("  FALLO: no deberia haber error: " + resultado["error"])
        ok = False
    elif resultado["resultado_llm"] == "":
        print("  FALLO: resultado_llm no deberia estar vacio")
        ok = False
    elif resultado["intentos"] != 1:
        print("  FALLO: intentos deberia ser 1")
        ok = False

    if ok:
        print("  OK")
    assert ok


def test_nodo_verificar_schema_valido():
    # DADO un estado con respuesta LLM valida
    # CUANDO se ejecuta verificar_schema
    # ENTONCES se crea registro_normalizado
    print("TEST: test_nodo_verificar_schema_valido")

    import workflow_graph

    texto_llm = json.dumps(
        {
            "id_solicitud": "SOL-001",
            "fecha_solicitud": "15/03/2025",
            "tipo_producto": "CUENTA",
            "id_cliente": "CLI-100",
            "monto_o_limite": "50000",
            "moneda": "ARS",
            "pais": "Argentina",
        }
    )

    estado = {
        "registro": {
            "id_solicitud": "SOL-001",
            "fecha_solicitud": "marzo 2025",
            "tipo_producto": "CUENTA",
            "id_cliente": "CLI-100",
            "monto_o_limite": "50000",
            "moneda": "ARS",
            "pais": "Argentina",
        },
        "resultado_llm": texto_llm,
        "registro_normalizado": {},
        "error": "",
    }

    resultado = workflow_graph.nodo_verificar_schema(estado)

    ok = True
    if resultado["error"] != "":
        print("  FALLO: no deberia haber error: " + resultado["error"])
        ok = False
    elif len(resultado["registro_normalizado"]) == 0:
        print("  FALLO: registro_normalizado no deberia estar vacio")
        ok = False

    if ok:
        print("  OK")
    assert ok


def test_nodo_verificar_schema_invalido():
    # DADO un estado con respuesta LLM invalida (schema)
    # CUANDO se ejecuta verificar_schema
    # ENTONCES hay error
    print("TEST: test_nodo_verificar_schema_invalido")

    import workflow_graph

    texto_llm = json.dumps(
        {
            "id_solicitud": "SOL-001",
            "fecha_solicitud": "fecha invalida",  # formato invalido
            "tipo_producto": "CUENTA",
            "id_cliente": "CLI-100",
            "monto_o_limite": "50000",
            "moneda": "ARS",
            "pais": "Argentina",
        }
    )

    estado = {
        "registro": {
            "id_solicitud": "SOL-001",
            "fecha_solicitud": "marzo 2025",
            "tipo_producto": "CUENTA",
            "id_cliente": "CLI-100",
            "monto_o_limite": "50000",
            "moneda": "ARS",
            "pais": "Argentina",
        },
        "resultado_llm": texto_llm,
        "registro_normalizado": {},
        "error": "",
    }

    resultado = workflow_graph.nodo_verificar_schema(estado)

    ok = True
    if resultado["error"] == "":
        print("  FALLO: deberia haber error por fecha invalida")
        ok = False

    if ok:
        print("  OK")
    assert ok


def test_ruta_despues_de_llm_exito():
    # DADO un estado sin error despues de LLM
    # CUANDO se evalua la ruta
    # ENTONCES va a verificar_schema
    print("TEST: test_ruta_despues_de_llm_exito")

    import workflow_graph

    estado = {"error": "", "intentos": 0, "max_retries": 2}

    ruta = workflow_graph.ruta_despues_de_llm(estado)

    ok = True
    if ruta != "verificar_schema":
        print("  FALLO: deberia ir a verificar_schema, va a: " + ruta)
        ok = False

    if ok:
        print("  OK")
    assert ok


def test_ruta_despues_de_llm_retry():
    # DADO un estado con error pero intentos disponibles
    # CUANDO se evalua la ruta
    # ENTONCES va a retry_llm
    print("TEST: test_ruta_despues_de_llm_retry")

    import workflow_graph

    estado = {"error": "fallo temporal", "intentos": 1, "max_retries": 2}

    ruta = workflow_graph.ruta_despues_de_llm(estado)

    ok = True
    if ruta != "retry_llm":
        print("  FALLO: deberia ir a retry_llm, va a: " + ruta)
        ok = False

    if ok:
        print("  OK")
    assert ok


def test_ruta_despues_de_llm_fallback():
    # DADO un estado con error y sin intentos disponibles
    # CUANDO se evalua la ruta
    # ENTONCES va a fallback
    print("TEST: test_ruta_despues_de_llm_fallback")

    import workflow_graph

    estado = {"error": "fallo persistente", "intentos": 2, "max_retries": 2}

    ruta = workflow_graph.ruta_despues_de_llm(estado)

    ok = True
    if ruta != "fallback":
        print("  FALLO: deberia ir a fallback, va a: " + ruta)
        ok = False

    if ok:
        print("  OK")
    assert ok


def test_nodo_fallback():
    # DADO un estado con error
    # CUANDO se ejecuta el nodo fallback
    # ENTONCES marca como INVALIDO con fallback_aplicado
    print("TEST: test_nodo_fallback")

    import workflow_graph

    estado = {
        "registro": {
            "id_solicitud": "SOL-001",
            "fecha_solicitud": "marzo 2025",
            "tipo_producto": "producto raro",
            "id_cliente": "CLI-100",
            "monto_o_limite": "50k",
            "moneda": "moneda rara",
            "pais": "pais raro",
        },
        "error": "Schema validation failed",
        "intentos": 2,
        "registro_normalizado": {},
        "nodo_actual": "",
        "finalizado": False,
    }

    resultado = workflow_graph.nodo_fallback(estado)

    ok = True
    if resultado["registro_normalizado"]["estado"] != "INVALIDO":
        print("  FALLO: estado deberia ser INVALIDO")
        ok = False
    if resultado["registro_normalizado"]["fallback_aplicado"] != True:
        print("  FALLO: fallback_aplicado deberia ser True")
        ok = False
    if resultado["finalizado"] != True:
        print("  FALLO: finalizado deberia ser True")
        ok = False

    if ok:
        print("  OK")
    assert ok


def test_ejecutar_grafo_manual_exito():
    # DADO un registro ambiguo y provider real
    # CUANDO se ejecuta el grafo manual
    # ENTONCES termina con registro normalizado
    print("TEST: test_ejecutar_grafo_manual_exito")

    import workflow_graph

    provider = obtener_provider_real()

    estado_inicial = {
        "registro": {
            "id_solicitud": "SOL-AMB-01",
            "fecha_solicitud": "marzo 2025",
            "tipo_producto": "cta",
            "id_cliente": "CLI-100",
            "monto_o_limite": "50000",
            "moneda": "pesos",
            "pais": "arg",
        },
        "registro_normalizado": {},
        "clasificacion": {"motivos_ambiguedad": ["fecha ambigua"]},
        "resultado_llm": "",
        "error": "",
        "intentos": 0,
        "max_retries": 2,
        "nodo_actual": "",
        "finalizado": False,
        "llm_provider": provider,
    }

    resultado = workflow_graph.ejecutar_grafo_manual(estado_inicial)

    ok = True
    if resultado["finalizado"] != True:
        print("  FALLO: deberia estar finalizado")
        ok = False
    if resultado["registro_normalizado"]["estado"] == "INVALIDO":
        print("  FALLO: no deberia ser INVALIDO")
        ok = False

    if ok:
        print("  OK")
    assert ok


def test_ejecutar_grafo_manual_real_caso_dificil():
    # DADO un registro ambiguo dificil y provider real
    # CUANDO se ejecuta el grafo manual
    # ENTONCES retorna registro finalizado con salida valida
    print("TEST: test_ejecutar_grafo_manual_real_caso_dificil")

    import workflow_graph

    provider = obtener_provider_real()

    estado_inicial = {
        "registro": {
            "id_solicitud": "SOL-AMB-02",
            "fecha_solicitud": "fecha muy rara",
            "tipo_producto": "producto desconocido",
            "id_cliente": "CLI-100",
            "monto_o_limite": "monto raro",
            "moneda": "moneda desconocida",
            "pais": "pais lejano",
        },
        "registro_normalizado": {},
        "clasificacion": {"motivos_ambiguedad": ["todo es ambiguo"]},
        "resultado_llm": "",
        "error": "",
        "intentos": 0,
        "max_retries": 2,
        "nodo_actual": "",
        "finalizado": False,
        "llm_provider": provider,
    }

    resultado = workflow_graph.ejecutar_grafo_manual(estado_inicial)

    ok = True
    if resultado["finalizado"] != True:
        print("  FALLO: deberia estar finalizado")
        ok = False
    if "estado" not in resultado["registro_normalizado"].keys():
        print("  FALLO: salida deberia incluir estado")
        ok = False

    if ok:
        print("  OK")
    assert ok


def test_procesar_registro_ambiguo():
    # DADO un registro ambiguo
    # CUANDO se procesa con la funcion principal
    # ENTONCES retorna registro procesado (exito o fallback)
    print("TEST: test_procesar_registro_ambiguo")

    import workflow_graph

    provider = obtener_provider_real()

    reg = {
        "id_solicitud": "SOL-AMB-03",
        "fecha_solicitud": "marzo 2025",
        "tipo_producto": "cta",
        "id_cliente": "CLI-100",
        "monto_o_limite": "50000",
        "moneda": "pesos",
        "pais": "arg",
    }

    clasificacion = {"motivos_ambiguedad": ["fecha ambigua: marzo 2025"]}

    resultado = workflow_graph.procesar_registro_ambiguo(reg, clasificacion, provider)

    ok = True
    if resultado == None:
        print("  FALLO: resultado no deberia ser None")
        ok = False
    elif "id_solicitud" not in resultado.keys():
        print("  FALLO: resultado deberia tener id_solicitud")
        ok = False

    if ok:
        print("  OK")
    assert ok


# Ejecutar tests manualmente
if __name__ == "__main__":
    print("=" * 50)
    print("TESTS DE WORKFLOW GRAPH (RF-04 AI-First)")
    print("=" * 50)

    tests = [
        test_nodo_preparar_contexto,
        test_nodo_normalizacion_llm_con_real,
        test_nodo_verificar_schema_valido,
        test_nodo_verificar_schema_invalido,
        test_ruta_despues_de_llm_exito,
        test_ruta_despues_de_llm_retry,
        test_ruta_despues_de_llm_fallback,
        test_nodo_fallback,
        test_ejecutar_grafo_manual_exito,
        test_ejecutar_grafo_manual_real_caso_dificil,
        test_procesar_registro_ambiguo,
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
