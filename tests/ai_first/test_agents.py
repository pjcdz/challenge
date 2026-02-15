# test_agents.py - Tests para los agentes AI-First (RF-04)
# Verifica agentes de ingesta, normalizador, validador y calidad

import sys
import os

# Agregar paths necesarios
dir_tests = os.path.dirname(os.path.abspath(__file__))
dir_raiz = os.path.dirname(os.path.dirname(dir_tests))
dir_ai_src = os.path.join(dir_raiz, "ai_first_system", "src")
dir_agents = os.path.join(dir_ai_src, "agents")
dir_adapters = os.path.join(dir_ai_src, "adapters")
dir_legacy = os.path.join(dir_raiz, "legacy_system", "src")
sys.path.insert(0, dir_ai_src)
sys.path.insert(0, dir_agents)
sys.path.insert(0, dir_adapters)
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
            "No se pudo crear provider real Gemini para tests AI-First: " + str(err)
        )

    _PROVIDER_REAL = provider
    return _PROVIDER_REAL


def test_agente_ingesta_csv():
    # DADO un archivo CSV valido
    # CUANDO se ingestar con agente_ingesta
    # ENTONCES retorna registros con campos de tracking
    print("TEST: test_agente_ingesta_csv")

    import agente_ingesta

    # Crear archivo temporal
    ruta = os.path.join(CARPETA_TEST, "temp_agent_ing.csv")
    arch = open(ruta, "w", encoding="utf-8")
    arch.write(
        "id_solicitud,fecha_solicitud,tipo_producto,id_cliente,monto_o_limite,moneda,pais,flag_prioritario,flag_digital\n"
    )
    arch.write("SOL-001,15/03/2025,CUENTA,CLI-100,50000,ARS,Argentina,S,N\n")
    arch.close()

    registros, error = agente_ingesta.ingestar(ruta)

    ok = True
    if registros == None:
        print("  FALLO: registros es None, error: " + str(error))
        ok = False
    elif len(registros) != 1:
        print("  FALLO: deberia haber 1 registro")
        ok = False
    elif "origen_procesamiento" not in registros[0].keys():
        print("  FALLO: deberia tener campo origen_procesamiento")
        ok = False
    elif "retries_llm" not in registros[0].keys():
        print("  FALLO: deberia tener campo retries_llm")
        ok = False

    os.remove(ruta)

    if ok:
        print("  OK")
    assert ok


def test_agente_ingesta_vacio():
    # DADO un archivo vacio
    # CUANDO se ingestar
    # ENTONCES retorna lista vacia sin error
    print("TEST: test_agente_ingesta_vacio")

    import agente_ingesta

    ruta = os.path.join(CARPETA_TEST, "temp_agent_vacio.csv")
    arch = open(ruta, "w", encoding="utf-8")
    arch.write(
        "id_solicitud,fecha_solicitud,tipo_producto,id_cliente,monto_o_limite,moneda,pais,flag_prioritario,flag_digital\n"
    )
    arch.close()

    registros, error = agente_ingesta.ingestar(ruta)

    ok = True
    if registros == None:
        print("  FALLO: registros es None")
        ok = False
    elif len(registros) != 0:
        print("  FALLO: deberia ser lista vacia")
        ok = False

    os.remove(ruta)

    if ok:
        print("  OK")
    assert ok


def test_agente_normalizar_con_reglas():
    # DADO registros con datos sucios
    # CUANDO se normalizan con reglas
    # ENTONCES quedan en formato canonico
    print("TEST: test_agente_normalizar_con_reglas")

    import agente_normalizador

    registros = [
        {
            "id_solicitud": "SOL-001",
            "fecha_solicitud": "2025-03-15",  # YYYY-MM-DD
            "tipo_producto": "  cuenta  ",
            "id_cliente": "CLI-100",
            "monto_o_limite": " 50000 ",
            "moneda": " ars ",
            "pais": " argentina ",
            "flag_prioritario": "S",
            "flag_digital": "N",
        }
    ]

    resultado = agente_normalizador.normalizar_con_reglas(registros)

    ok = True
    if resultado == None:
        print("  FALLO: resultado es None")
        ok = False
    elif len(resultado) != 1:
        print("  FALLO: deberia haber 1 registro")
        ok = False
    elif resultado[0]["moneda"] != "ARS":
        print("  FALLO: moneda deberia ser ARS")
        ok = False
    elif resultado[0]["fecha_solicitud"] != "15/03/2025":
        print("  FALLO: fecha deberia ser 15/03/2025")
        ok = False

    if ok:
        print("  OK")
    assert ok


def test_agente_normalizar_con_llm_real():
    # DADO un registro ambiguo y provider real Gemini
    # CUANDO se normaliza con LLM
    # ENTONCES retorna resultado consistente sin fallback tecnico
    print("TEST: test_agente_normalizar_con_llm_real")

    import agente_normalizador

    provider = obtener_provider_real()

    reg = {
        "id_solicitud": "SOL-AMB-01",
        "fecha_solicitud": "15 de marzo",
        "tipo_producto": "cta",
        "id_cliente": "CLI-100",
        "monto_o_limite": "50k",
        "moneda": "pesos",
        "pais": "arg",
    }

    resultado, error = agente_normalizador.normalizar_con_llm(reg, provider)

    ok = True
    if resultado == None:
        print("  FALLO: resultado es None, error: " + str(error))
        ok = False
    elif resultado.get("origen_procesamiento", "") != "llm_path":
        print("  FALLO: origen_procesamiento deberia ser llm_path")
        ok = False
    elif resultado.get("fallback_aplicado", True):
        print("  FALLO: no deberia aplicar fallback para este caso")
        ok = False
    elif resultado.get("retries_llm", -1) < 0:
        print("  FALLO: retries_llm deberia ser >= 0")
        ok = False

    if ok:
        print("  OK")
    assert ok


def test_agente_normalizar_con_llm_real_retries():
    # DADO un registro ambiguo con provider real
    # CUANDO se normaliza con LLM
    # ENTONCES retries_llm queda en rango permitido
    print("TEST: test_agente_normalizar_con_llm_real_retries")

    import agente_normalizador

    provider = obtener_provider_real()

    reg = {
        "id_solicitud": "SOL-AMB-CORR",
        "fecha_solicitud": "15 marzo 2025",
        "tipo_producto": "cta ahorro",
        "id_cliente": "CLI-100",
        "monto_o_limite": "50000",
        "moneda": "pesos",
        "pais": "arg",
    }

    resultado, error = agente_normalizador.normalizar_con_llm(reg, provider)

    ok = True
    if resultado == None:
        print("  FALLO: resultado es None, error: " + str(error))
        ok = False
    elif resultado.get("retries_llm", -1) < 0:
        print("  FALLO: retries_llm no puede ser negativo")
        ok = False
    elif resultado.get("retries_llm", 999) > 2:
        print("  FALLO: retries_llm excede maximo configurado")
        ok = False
    elif "fallback_aplicado" not in resultado.keys():
        print("  FALLO: falta campo fallback_aplicado")
        ok = False

    if ok:
        print("  OK")
    assert ok


def test_agente_normalizar_con_llm_real_registro_dificil():
    # DADO un registro ambiguo dificil con provider real
    # CUANDO se normaliza con LLM
    # ENTONCES retorna un registro estructuralmente valido
    print("TEST: test_agente_normalizar_con_llm_real_registro_dificil")

    import agente_normalizador

    provider = obtener_provider_real()

    reg = {
        "id_solicitud": "SOL-AMB-02",
        "fecha_solicitud": "fecha rara",
        "tipo_producto": "producto raro",
        "id_cliente": "CLI-100",
        "monto_o_limite": "monto raro",
        "moneda": "moneda rara",
        "pais": "pais raro",
    }

    resultado, error = agente_normalizador.normalizar_con_llm(reg, provider)

    ok = True
    if resultado == None:
        print("  FALLO: resultado no deberia ser None")
        ok = False
    elif "estado" not in resultado.keys():
        print("  FALLO: falta campo estado")
        ok = False
    elif "fallback_aplicado" not in resultado.keys():
        print("  FALLO: falta campo fallback_aplicado")
        ok = False
    elif resultado.get("retries_llm", -1) > 2:
        print("  FALLO: retries_llm excede presupuesto configurado")
        ok = False

    if ok:
        print("  OK")
    assert ok


def test_agente_normalizar_hibrido_usa_workflow_graph():
    # DADO un registro ambiguo
    # CUANDO se normaliza en modo hibrido
    # ENTONCES procesa llm_path con Gemini real sin stubs
    print("TEST: test_agente_normalizar_hibrido_usa_workflow_graph")

    import agente_normalizador

    provider = obtener_provider_real()
    metricas_antes = provider.obtener_metricas()
    llamadas_antes = metricas_antes.get("total_llamadas", 0)

    registros = [
        {
            "id_solicitud": "WG-001",
            "fecha_solicitud": "15 marzo 2025",
            "tipo_producto": "producto especial",
            "id_cliente": "CLI-500",
            "monto_o_limite": "50k",
            "moneda": "moneda local",
            "pais": "pais no canonico",
            "flag_prioritario": "S",
            "flag_digital": "N",
        }
    ]

    resultado, stats = agente_normalizador.normalizar_hibrido(registros, provider)
    metricas_despues = provider.obtener_metricas()
    llamadas_despues = metricas_despues.get("total_llamadas", 0)

    ok = True
    if len(resultado) != 1:
        print("  FALLO: deberia haber 1 registro de salida")
        ok = False
    elif stats.get("llm_path", 0) != 1:
        print("  FALLO: stats.llm_path deberia ser 1")
        ok = False
    elif resultado[0].get("origen_procesamiento", "") != "llm_path":
        print("  FALLO: origen_procesamiento deberia ser llm_path")
        ok = False
    elif llamadas_despues <= llamadas_antes:
        print("  FALLO: deberia haber al menos 1 llamada real a Gemini")
        ok = False

    if ok:
        print("  OK")
    assert ok


def test_agente_normalizar_hibrido_preserva_orden():
    # DADO mezcla de rule_path y llm_path
    # CUANDO se normaliza en modo hibrido
    # ENTONCES la salida mantiene el orden original
    print("TEST: test_agente_normalizar_hibrido_preserva_orden")

    import agente_normalizador

    provider = obtener_provider_real()

    registros = [
        {
            "id_solicitud": "ORD-001",
            "fecha_solicitud": "15 marzo 2025",
            "tipo_producto": "cta ahorro",
            "id_cliente": "CLI-101",
            "monto_o_limite": "50000",
            "moneda": "pesos",
            "pais": "arg",
        },
        {
            "id_solicitud": "ORD-002",
            "fecha_solicitud": "15/03/2025",
            "tipo_producto": "CUENTA",
            "id_cliente": "CLI-102",
            "monto_o_limite": "60000",
            "moneda": "ARS",
            "pais": "Argentina",
        },
        {
            "id_solicitud": "ORD-003",
            "fecha_solicitud": "Q1 2025",
            "tipo_producto": "plastico raro",
            "id_cliente": "CLI-103",
            "monto_o_limite": "70000",
            "moneda": "dolares",
            "pais": "bra",
        },
    ]

    resultado, stats = agente_normalizador.normalizar_hibrido(registros, provider)

    ok = True
    if len(resultado) != 3:
        print("  FALLO: deberia haber 3 registros")
        ok = False
    else:
        ids = []
        for reg in resultado:
            ids.append(reg.get("id_solicitud", ""))
        if ids[0] != "ORD-001" or ids[1] != "ORD-002" or ids[2] != "ORD-003":
            print("  FALLO: orden alterado: " + str(ids))
            ok = False

    if ok:
        print("  OK")
    assert ok


def test_agente_normalizar_hibrido_solo_reglas():
    # DADO registros limpios y provider real
    # CUANDO se normaliza hibrido
    # ENTONCES todo va por rule_path, sin llamadas LLM
    print("TEST: test_agente_normalizar_hibrido_solo_reglas")

    import agente_normalizador

    provider = obtener_provider_real()

    registros = [
        {
            "id_solicitud": "SOL-001",
            "fecha_solicitud": "15/03/2025",
            "tipo_producto": "CUENTA",
            "id_cliente": "CLI-100",
            "monto_o_limite": "50000",
            "moneda": "ARS",
            "pais": "Argentina",
        }
    ]

    resultado, stats = agente_normalizador.normalizar_hibrido(registros, provider)

    ok = True
    if len(resultado) != 1:
        print("  FALLO: deberia haber 1 registro")
        ok = False
    elif stats["llm_path"] != 0:
        print("  FALLO: llm_path deberia ser 0")
        ok = False
    elif stats["regla_path"] != 1:
        print("  FALLO: regla_path deberia ser 1")
        ok = False

    if ok:
        print("  OK")
    assert ok


def test_agente_validador():
    # DADO registros normalizados
    # CUANDO se validan
    # ENTONCES se aplican las reglas R1/R2/R3
    print("TEST: test_agente_validador")

    import agente_validador

    registros = [
        # Valido
        {
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
        },
        # Invalido R1 (campo vacio)
        {
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
        },
    ]

    resultado = agente_validador.validar(registros)

    ok = True
    if len(resultado) != 2:
        print("  FALLO: deberia haber 2 registros")
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


def test_agente_validador_preserva_fallback_tecnico():
    # DADO un registro fallback_aplicado con campos validos
    # CUANDO pasa por validador AI-First
    # ENTONCES conserva estado INVALIDO y motivo tecnico
    print("TEST: test_agente_validador_preserva_fallback_tecnico")

    import agente_validador

    registros = [
        {
            "id_solicitud": "SOL-FB-01",
            "fecha_solicitud": "15/03/2025",
            "tipo_producto": "CUENTA",
            "id_cliente": "CLI-999",
            "monto_o_limite": "50000",
            "moneda": "ARS",
            "pais": "Argentina",
            "flag_prioritario": "N",
            "flag_digital": "S",
            "categoria_riesgo": "BAJO",
            "estado": "INVALIDO",
            "motivos_falla": "Fallback: LLM no pudo normalizar - error tecnico",
            "fallback_aplicado": True,
            "retries_llm": 2,
            "origen_procesamiento": "llm_path",
        }
    ]

    resultado = agente_validador.validar(registros)

    ok = True
    if len(resultado) != 1:
        print("  FALLO: deberia haber 1 registro")
        ok = False
    elif resultado[0].get("estado", "") != "INVALIDO":
        print("  FALLO: fallback tecnico debe quedar INVALIDO")
        ok = False
    elif "Fallback: LLM no pudo normalizar" not in resultado[0].get("motivos_falla", ""):
        print("  FALLO: deberia conservar motivo tecnico de fallback")
        ok = False
    elif "_detalle_reglas" not in resultado[0].keys():
        print("  FALLO: deberia conservar detalle de reglas")
        ok = False
    elif "R_TECH" not in resultado[0]["_detalle_reglas"].keys():
        print("  FALLO: deberia registrar R_TECH en detalle")
        ok = False

    if ok:
        print("  OK")
    assert ok


def test_agente_calidad():
    # DADO registros validados
    # CUANDO se genera reporte
    # ENTONCES tiene metricas de AI-First
    print("TEST: test_agente_calidad")

    import agente_calidad

    registros = [
        {
            "id_solicitud": "SOL-001",
            "estado": "VALIDO",
            "origen_procesamiento": "rule_path",
            "motivos_falla": "",
            "fallback_aplicado": False,
            "retries_llm": 0,
        },
        {
            "id_solicitud": "SOL-002",
            "estado": "VALIDO",
            "origen_procesamiento": "llm_path",
            "motivos_falla": "",
            "fallback_aplicado": False,
            "retries_llm": 1,
        },
        {
            "id_solicitud": "SOL-003",
            "estado": "INVALIDO",
            "origen_procesamiento": "llm_path",
            "motivos_falla": "R1: campo vacio",
            "fallback_aplicado": True,
            "retries_llm": 2,
        },
    ]

    stats_router = {"sinonimos_resueltos": 1}
    metricas_llm = {"total_llamadas": 2}

    reporte = agente_calidad.generar_reporte(
        registros, "test.csv", CARPETA_TEST, stats_router, metricas_llm
    )

    ok = True
    if reporte == None:
        print("  FALLO: reporte es None")
        ok = False
    elif "ai_first" not in reporte.keys():
        print("  FALLO: deberia tener seccion ai_first")
        ok = False
    elif reporte["ai_first"]["enrutamiento"]["rule_path"] != 1:
        print("  FALLO: rule_path deberia ser 1")
        ok = False
    elif reporte["ai_first"]["enrutamiento"]["llm_path"] != 2:
        print("  FALLO: llm_path deberia ser 2")
        ok = False

    # Limpiar
    ruta_reporte = os.path.join(CARPETA_TEST, "reporte_calidad.json")
    if os.path.exists(ruta_reporte):
        os.remove(ruta_reporte)

    if ok:
        print("  OK")
    assert ok


# Ejecutar tests manualmente
if __name__ == "__main__":
    print("=" * 50)
    print("TESTS DE AGENTES AI-FIRST (RF-04)")
    print("=" * 50)

    tests = [
        test_agente_ingesta_csv,
        test_agente_ingesta_vacio,
        test_agente_normalizar_con_reglas,
        test_agente_normalizar_con_llm_real,
        test_agente_normalizar_con_llm_real_retries,
        test_agente_normalizar_con_llm_real_registro_dificil,
        test_agente_normalizar_hibrido_usa_workflow_graph,
        test_agente_normalizar_hibrido_preserva_orden,
        test_agente_normalizar_hibrido_solo_reglas,
        test_agente_validador,
        test_agente_validador_preserva_fallback_tecnico,
        test_agente_calidad,
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
