# test_contract.py - Tests de contrato entre legacy y AI-First (RF-01)
# Verifica que ambos sistemas producen el mismo esquema de salida

import sys
import os
import json
import tempfile
import shutil

# Agregar paths necesarios
dir_tests = os.path.dirname(os.path.abspath(__file__))
dir_raiz = os.path.dirname(os.path.dirname(dir_tests))
dir_legacy = os.path.join(dir_raiz, "legacy_system", "src")
sys.path.insert(0, dir_legacy)

CARPETA_TEST = dir_tests

# Campos de salida esperados (comunes entre legacy y ai_first)
CAMPOS_SALIDA_LEGACY = [
    "id_solicitud",
    "fecha_solicitud",
    "tipo_producto",
    "id_cliente",
    "monto_o_limite",
    "moneda",
    "pais",
    "flag_prioritario",
    "flag_digital",
    "categoria_riesgo",
    "estado",
    "motivos_falla",
]

# AI-First agrega origen_procesamiento
CAMPOS_SALIDA_AI_FIRST = CAMPOS_SALIDA_LEGACY + ["origen_procesamiento"]


def crear_provider_real():
    # Crea provider real Gemini usando configuracion de .env.local
    dir_ai_src = os.path.join(dir_raiz, "ai_first_system", "src")
    dir_adapters = os.path.join(dir_ai_src, "adapters")
    if dir_ai_src not in sys.path:
        sys.path.insert(0, dir_ai_src)
    if dir_adapters not in sys.path:
        sys.path.insert(0, dir_adapters)

    from config import GEMINI_API_KEY

    if GEMINI_API_KEY == None or GEMINI_API_KEY == "":
        raise AssertionError("Falta GEMINI_API_KEY en .env.local para tests reales")

    from adapters.gemini_adapter import GeminiAdapter

    provider = GeminiAdapter()
    return provider


def test_legacy_campos_salida():
    # DADO el sistema legacy
    # CUANDO se ejecuta el workflow
    # ENTONCES el CSV de salida tiene los campos esperados
    print("TEST: test_legacy_campos_salida")

    import logger
    import ingesta
    import normalizador
    import validador

    logger.inicializar()

    # Crear archivo temporal
    ruta = os.path.join(CARPETA_TEST, "temp_contrato_legacy.csv")
    arch = open(ruta, "w", encoding="utf-8")
    arch.write(
        "id_solicitud,fecha_solicitud,tipo_producto,id_cliente,monto_o_limite,moneda,pais,flag_prioritario,flag_digital\n"
    )
    arch.write("SOL-001,15/03/2025,CUENTA,CLI-100,50000,ARS,Argentina,S,N\n")
    arch.close()

    registros = ingesta.leer_solicitudes(ruta)
    registros_norm = normalizador.normalizar_registros(registros)
    registros_val = validador.validar_registros(registros_norm)

    ok = True
    if len(registros_val) != 1:
        print("  FALLO: deberia haber 1 registro")
        ok = False
    else:
        reg = registros_val[0]
        for campo in CAMPOS_SALIDA_LEGACY:
            if campo not in reg.keys():
                print("  FALLO: falta campo " + campo + " en salida legacy")
                ok = False

    os.remove(ruta)

    if ok:
        print("  OK")
    assert ok


def test_ai_first_campos_salida():
    # DADO el sistema AI-First
    # CUANDO se ejecuta el workflow con provider real
    # ENTONCES el CSV de salida tiene los campos esperados + origen_procesamiento
    print("TEST: test_ai_first_campos_salida")

    # Limpiar modulos
    for mod in ["main", "logger", "ingesta", "normalizador", "validador", "calidad"]:
        if mod in sys.modules.keys():
            del sys.modules[mod]

    # Crear archivo temporal
    ruta = os.path.join(CARPETA_TEST, "temp_contrato_estado.csv")
    arch = open(ruta, "w", encoding="utf-8")
    arch.write(
        "id_solicitud,fecha_solicitud,tipo_producto,id_cliente,monto_o_limite,moneda,pais,flag_prioritario,flag_digital\n"
    )
    arch.write("SOL-001,15/03/2025,CUENTA,CLI-100,50000,ARS,Argentina,S,N\n")
    arch.close()

    dir_ai_src = os.path.join(dir_raiz, "ai_first_system", "src")
    dir_adapters = os.path.join(dir_ai_src, "adapters")
    dir_agents = os.path.join(dir_ai_src, "agents")
    sys.path.insert(0, dir_ai_src)
    sys.path.insert(0, dir_adapters)
    sys.path.insert(0, dir_agents)

    provider = crear_provider_real()

    import agente_ingesta
    import agente_normalizador
    import agente_validador

    reg_ai, error = agente_ingesta.ingestar(ruta)
    reg_ai, stats = agente_normalizador.normalizar_hibrido(reg_ai, provider)
    reg_ai = agente_validador.validar(reg_ai)

    ok = True
    if len(reg_ai) != 1:
        print("  FALLO: deberia haber 1 registro en AI-First")
        ok = False
    else:
        reg = reg_ai[0]
        for campo in CAMPOS_SALIDA_AI_FIRST:
            if campo not in reg.keys():
                print("  FALLO: falta campo " + campo + " en salida AI-First")
                ok = False

    os.remove(ruta)

    if ok:
        print("  OK")
    assert ok


def test_ai_first_llm_real_en_contrato():
    # DADO registros con un caso ambiguo
    # CUANDO se ejecuta AI-First con Gemini real
    # ENTONCES usa llm_path y aumenta llamadas reales al provider
    print("TEST: test_ai_first_llm_real_en_contrato")

    # Limpiar modulos
    for mod in ["main", "logger", "ingesta", "normalizador", "validador", "calidad"]:
        if mod in sys.modules.keys():
            del sys.modules[mod]

    # Crear archivo temporal: 1 ambiguo (fecha textual) + 1 limpio
    ruta = os.path.join(CARPETA_TEST, "temp_contrato_llm_real.csv")
    arch = open(ruta, "w", encoding="utf-8")
    arch.write(
        "id_solicitud,fecha_solicitud,tipo_producto,id_cliente,monto_o_limite,moneda,pais,flag_prioritario,flag_digital\n"
    )
    arch.write("SOL-LLM-001,15 marzo 2025,CUENTA,CLI-100,50000,ARS,Argentina,S,N\n")
    arch.write("SOL-RULE-001,15/03/2025,CUENTA,CLI-200,80000,ARS,Argentina,N,S\n")
    arch.close()

    dir_ai_src = os.path.join(dir_raiz, "ai_first_system", "src")
    dir_adapters = os.path.join(dir_ai_src, "adapters")
    dir_agents = os.path.join(dir_ai_src, "agents")
    if dir_ai_src not in sys.path:
        sys.path.insert(0, dir_ai_src)
    if dir_adapters not in sys.path:
        sys.path.insert(0, dir_adapters)
    if dir_agents not in sys.path:
        sys.path.insert(0, dir_agents)

    provider = crear_provider_real()
    metricas_antes = provider.obtener_metricas()
    llamadas_antes = metricas_antes.get("total_llamadas", 0)

    import agente_ingesta
    import agente_normalizador
    import agente_validador

    reg_ai, error = agente_ingesta.ingestar(ruta)
    reg_ai, stats = agente_normalizador.normalizar_hibrido(reg_ai, provider)
    reg_ai = agente_validador.validar(reg_ai)

    metricas_despues = provider.obtener_metricas()
    llamadas_despues = metricas_despues.get("total_llamadas", 0)

    ok = True
    if len(reg_ai) != 2:
        print("  FALLO: deberian procesarse 2 registros")
        ok = False
    elif stats.get("llm_path", 0) < 1:
        print("  FALLO: stats.llm_path deberia ser mayor a 0")
        ok = False
    elif llamadas_despues <= llamadas_antes:
        print("  FALLO: total_llamadas del provider no aumento")
        ok = False
    else:
        tiene_llm = False
        for reg in reg_ai:
            if reg.get("origen_procesamiento", "") == "llm_path":
                tiene_llm = True
        if not tiene_llm:
            print("  FALLO: no hay registros marcados con origen llm_path")
            ok = False

    os.remove(ruta)

    if ok:
        print("  OK")
    assert ok


def test_ambos_mismo_estado_valido():
    # DADO un registro valido
    # CUANDO se procesa en legacy y AI-First
    # ENTONCES ambos marcan estado VALIDO
    print("TEST: test_ambos_mismo_estado_valido")

    # Limpiar modulos
    for mod in ["main", "logger", "ingesta", "normalizador", "validador", "calidad"]:
        if mod in sys.modules.keys():
            del sys.modules[mod]

    dir_legacy = os.path.join(dir_raiz, "legacy_system", "src")
    sys.path.insert(0, dir_legacy)

    import logger
    import ingesta
    import normalizador
    import validador

    logger.inicializar()

    # Crear archivo temporal
    ruta = os.path.join(CARPETA_TEST, "temp_contrato_estado.csv")
    arch = open(ruta, "w", encoding="utf-8")
    arch.write(
        "id_solicitud,fecha_solicitud,tipo_producto,id_cliente,monto_o_limite,moneda,pais,flag_prioritario,flag_digital\n"
    )
    arch.write("SOL-001,15/03/2025,CUENTA,CLI-100,50000,ARS,Argentina,S,N\n")
    arch.close()

    # Legacy
    reg_leg = ingesta.leer_solicitudes(ruta)
    reg_leg = normalizador.normalizar_registros(reg_leg)
    reg_leg = validador.validar_registros(reg_leg)

    # AI-First
    for mod in ["main", "logger", "ingesta", "normalizador", "validador", "calidad"]:
        if mod in sys.modules.keys():
            del sys.modules[mod]

    dir_ai_src = os.path.join(dir_raiz, "ai_first_system", "src")
    dir_adapters = os.path.join(dir_ai_src, "adapters")
    dir_agents = os.path.join(dir_ai_src, "agents")
    sys.path.insert(0, dir_ai_src)
    sys.path.insert(0, dir_adapters)
    sys.path.insert(0, dir_agents)

    provider = crear_provider_real()

    import agente_ingesta
    import agente_normalizador
    import agente_validador

    reg_ai, error = agente_ingesta.ingestar(ruta)
    reg_ai, stats = agente_normalizador.normalizar_hibrido(reg_ai, provider)
    reg_ai = agente_validador.validar(reg_ai)

    ok = True
    if len(reg_leg) != 1 or len(reg_ai) != 1:
        print("  FALLO: deberia haber 1 registro en cada sistema")
        ok = False
    elif reg_leg[0]["estado"] != "VALIDO":
        print("  FALLO: legacy deberia ser VALIDO")
        ok = False
    elif reg_ai[0]["estado"] != "VALIDO":
        print("  FALLO: AI-First deberia ser VALIDO")
        ok = False

    os.remove(ruta)

    if ok:
        print("  OK")
    assert ok


def test_ambos_mismo_estado_invalido_r1():
    # DADO un registro con campo obligatorio vacio
    # CUANDO se procesa en legacy y AI-First
    # ENTONCES ambos marcan estado INVALIDO
    print("TEST: test_ambos_mismo_estado_invalido_r1")

    # Limpiar modulos
    for mod in ["main", "logger", "ingesta", "normalizador", "validador", "calidad"]:
        if mod in sys.modules.keys():
            del sys.modules[mod]

    dir_legacy = os.path.join(dir_raiz, "legacy_system", "src")
    sys.path.insert(0, dir_legacy)

    import logger
    import ingesta
    import normalizador
    import validador

    logger.inicializar()

    # Crear archivo temporal con campo vacio
    ruta = os.path.join(CARPETA_TEST, "temp_contrato_r1.csv")
    arch = open(ruta, "w", encoding="utf-8")
    arch.write(
        "id_solicitud,fecha_solicitud,tipo_producto,id_cliente,monto_o_limite,moneda,pais,flag_prioritario,flag_digital\n"
    )
    arch.write(
        "SOL-001,15/03/2025,,CLI-100,50000,ARS,Argentina,S,N\n"
    )  # tipo_producto vacio
    arch.close()

    # Legacy
    reg_leg = ingesta.leer_solicitudes(ruta)
    reg_leg = normalizador.normalizar_registros(reg_leg)
    reg_leg = validador.validar_registros(reg_leg)

    # AI-First
    for mod in ["main", "logger", "ingesta", "normalizador", "validador", "calidad"]:
        if mod in sys.modules.keys():
            del sys.modules[mod]

    dir_ai_src = os.path.join(dir_raiz, "ai_first_system", "src")
    dir_adapters = os.path.join(dir_ai_src, "adapters")
    dir_agents = os.path.join(dir_ai_src, "agents")
    sys.path.insert(0, dir_ai_src)
    sys.path.insert(0, dir_adapters)
    sys.path.insert(0, dir_agents)

    provider = crear_provider_real()

    import agente_ingesta
    import agente_normalizador
    import agente_validador

    reg_ai, error = agente_ingesta.ingestar(ruta)
    reg_ai, stats = agente_normalizador.normalizar_hibrido(reg_ai, provider)
    reg_ai = agente_validador.validar(reg_ai)

    ok = True
    if len(reg_leg) != 1 or len(reg_ai) != 1:
        print("  FALLO: deberia haber 1 registro en cada sistema")
        ok = False
    elif reg_leg[0]["estado"] != "INVALIDO":
        print("  FALLO: legacy deberia ser INVALIDO")
        ok = False
    elif reg_ai[0]["estado"] != "INVALIDO":
        print("  FALLO: AI-First deberia ser INVALIDO")
        ok = False
    elif "R1" not in reg_leg[0]["motivos_falla"]:
        print("  FALLO: legacy deberia tener R1 en motivos_falla")
        ok = False
    elif "R1" not in reg_ai[0]["motivos_falla"]:
        print("  FALLO: AI-First deberia tener R1 en motivos_falla")
        ok = False

    os.remove(ruta)

    if ok:
        print("  OK")
    assert ok


def test_ambos_mismo_campo_normalizado():
    # DADO un registro con datos que requieren normalizacion
    # CUANDO se procesa en legacy y AI-First
    # ENTONCES ambos normalizan igual (moneda a mayusculas, etc)
    print("TEST: test_ambos_mismo_campo_normalizado")

    # Limpiar modulos
    for mod in ["main", "logger", "ingesta", "normalizador", "validador", "calidad"]:
        if mod in sys.modules.keys():
            del sys.modules[mod]

    dir_legacy = os.path.join(dir_raiz, "legacy_system", "src")
    sys.path.insert(0, dir_legacy)

    import logger
    import ingesta
    import normalizador
    import validador

    logger.inicializar()

    # Crear archivo temporal con datos sucios
    ruta = os.path.join(CARPETA_TEST, "temp_contrato_norm.csv")
    arch = open(ruta, "w", encoding="utf-8")
    arch.write(
        "id_solicitud,fecha_solicitud,tipo_producto,id_cliente,monto_o_limite,moneda,pais,flag_prioritario,flag_digital\n"
    )
    arch.write("SOL-001,2025-03-15,  cuenta  ,CLI-100, 50000 , ars , argentina ,S,N\n")
    arch.close()

    # Legacy
    reg_leg = ingesta.leer_solicitudes(ruta)
    reg_leg = normalizador.normalizar_registros(reg_leg)
    reg_leg = validador.validar_registros(reg_leg)

    # AI-First
    for mod in ["main", "logger", "ingesta", "normalizador", "validador", "calidad"]:
        if mod in sys.modules.keys():
            del sys.modules[mod]

    dir_ai_src = os.path.join(dir_raiz, "ai_first_system", "src")
    dir_adapters = os.path.join(dir_ai_src, "adapters")
    dir_agents = os.path.join(dir_ai_src, "agents")
    sys.path.insert(0, dir_ai_src)
    sys.path.insert(0, dir_adapters)
    sys.path.insert(0, dir_agents)

    provider = crear_provider_real()

    import agente_ingesta
    import agente_normalizador
    import agente_validador

    reg_ai, error = agente_ingesta.ingestar(ruta)
    reg_ai, stats = agente_normalizador.normalizar_hibrido(reg_ai, provider)
    reg_ai = agente_validador.validar(reg_ai)

    ok = True
    if len(reg_leg) != 1 or len(reg_ai) != 1:
        print("  FALLO: deberia haber 1 registro en cada sistema")
        ok = False
    elif reg_leg[0]["moneda"] != reg_ai[0]["moneda"]:
        print(
            "  FALLO: moneda deberia ser igual. Legacy: "
            + reg_leg[0]["moneda"]
            + ", AI: "
            + reg_ai[0]["moneda"]
        )
        ok = False
    elif reg_leg[0]["tipo_producto"] != reg_ai[0]["tipo_producto"]:
        print(
            "  FALLO: tipo_producto deberia ser igual. Legacy: "
            + reg_leg[0]["tipo_producto"]
            + ", AI: "
            + reg_ai[0]["tipo_producto"]
        )
        ok = False
    elif reg_leg[0]["fecha_solicitud"] != reg_ai[0]["fecha_solicitud"]:
        print(
            "  FALLO: fecha deberia ser igual. Legacy: "
            + reg_leg[0]["fecha_solicitud"]
            + ", AI: "
            + reg_ai[0]["fecha_solicitud"]
        )
        ok = False

    os.remove(ruta)

    if ok:
        print("  OK")
    assert ok


# Ejecutar tests manualmente
if __name__ == "__main__":
    print("=" * 50)
    print("TESTS DE CONTRATO LEGACY vs AI-FIRST (RF-01)")
    print("=" * 50)

    tests = [
        test_legacy_campos_salida,
        test_ai_first_campos_salida,
        test_ai_first_llm_real_en_contrato,
        test_ambos_mismo_estado_valido,
        test_ambos_mismo_estado_invalido_r1,
        test_ambos_mismo_campo_normalizado,
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
