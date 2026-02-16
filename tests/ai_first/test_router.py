# test_router.py - Tests para el modulo router_ambiguedad (RF-03 AI-First)
# Verifica deteccion de ambiguedad y enrutamiento hibrido

import sys
import os

# Agregar paths necesarios
dir_tests = os.path.dirname(os.path.abspath(__file__))
dir_raiz = os.path.dirname(os.path.dirname(dir_tests))
dir_ai_src = os.path.join(dir_raiz, "ai_first_system", "src")
sys.path.insert(0, dir_ai_src)

import router_ambiguedad

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
            "No se pudo crear provider real Gemini para tests de router: " + str(err)
        )

    _PROVIDER_REAL = provider
    return _PROVIDER_REAL


def test_es_fecha_parseable_ddmmyyyy():
    # DADO una fecha en formato DD/MM/YYYY
    # CUANDO se verifica si es parseable
    # ENTONCES retorna True
    print("TEST: test_es_fecha_parseable_ddmmyyyy")

    fecha = "15/03/2025"
    resultado = router_ambiguedad.es_fecha_parseable(fecha)

    ok = True
    if resultado != True:
        print("  FALLO: fecha DD/MM/YYYY deberia ser parseable")
        ok = False

    if ok:
        print("  OK")
    assert ok


def test_es_fecha_parseable_yyyymmdd():
    # DADO una fecha en formato YYYY-MM-DD
    # CUANDO se verifica si es parseable
    # ENTONCES retorna True
    print("TEST: test_es_fecha_parseable_yyyymmdd")

    fecha = "2025-03-15"
    resultado = router_ambiguedad.es_fecha_parseable(fecha)

    ok = True
    if resultado != True:
        print("  FALLO: fecha YYYY-MM-DD deberia ser parseable")
        ok = False

    if ok:
        print("  OK")
    assert ok


def test_es_fecha_parseable_ddmmyyyy_guion():
    # DADO una fecha en formato DD-MM-YYYY
    # CUANDO se verifica si es parseable
    # ENTONCES retorna True
    print("TEST: test_es_fecha_parseable_ddmmyyyy_guion")

    fecha = "15-03-2025"
    resultado = router_ambiguedad.es_fecha_parseable(fecha)

    ok = True
    if resultado != True:
        print("  FALLO: fecha DD-MM-YYYY deberia ser parseable")
        ok = False

    if ok:
        print("  OK")
    assert ok


def test_es_fecha_ambigua_texto():
    # DADO una fecha en formato textual
    # CUANDO se verifica si es parseable
    # ENTONCES retorna False (es ambigua)
    print("TEST: test_es_fecha_ambigua_texto")

    fecha = "15 de marzo del 2025"
    resultado = router_ambiguedad.es_fecha_parseable(fecha)

    ok = True
    if resultado != False:
        print("  FALLO: fecha textual deberia ser ambigua")
        ok = False

    if ok:
        print("  OK")
    assert ok


def test_es_fecha_ambigua_formato_raro():
    # DADO una fecha en formato no reconocido
    # CUANDO se verifica si es parseable
    # ENTONCES retorna False
    print("TEST: test_es_fecha_ambigua_formato_raro")

    fecha = "2025/03/15"
    resultado = router_ambiguedad.es_fecha_parseable(fecha)

    ok = True
    if resultado != False:
        print("  FALLO: fecha con formato YYYY/MM/DD deberia ser ambigua")
        ok = False

    if ok:
        print("  OK")
    assert ok


def test_es_fecha_vacia_parseable():
    # DADO una fecha vacia
    # CUANDO se verifica si es parseable
    # ENTONCES retorna True (no es ambigua, es vacia)
    print("TEST: test_es_fecha_vacia_parseable")

    resultado1 = router_ambiguedad.es_fecha_parseable("")
    resultado2 = router_ambiguedad.es_fecha_parseable(None)

    ok = True
    if resultado1 != True:
        print("  FALLO: fecha vacia deberia ser parseable (se detecta en R1)")
        ok = False
    if resultado2 != True:
        print("  FALLO: fecha None deberia ser parseable (se detecta en R1)")
        ok = False

    if ok:
        print("  OK")
    assert ok


def test_es_moneda_canonica():
    # DADO una moneda canonica
    # CUANDO se verifica
    # ENTONCES retorna (True, moneda_upper)
    print("TEST: test_es_moneda_canonica")

    es_canon1, val1 = router_ambiguedad.es_moneda_canonica("ARS")
    es_canon2, val2 = router_ambiguedad.es_moneda_canonica("usd")
    es_canon3, val3 = router_ambiguedad.es_moneda_canonica("Eur")

    ok = True
    if es_canon1 != True or val1 != "ARS":
        print("  FALLO: ARS deberia ser canonica")
        ok = False
    if es_canon2 != True or val2 != "USD":
        print("  FALLO: usd deberia ser canonica")
        ok = False
    if es_canon3 != True or val3 != "EUR":
        print("  FALLO: Eur deberia ser canonica")
        ok = False

    if ok:
        print("  OK")
    assert ok


def test_es_moneda_sinonimo():
    # DADO una moneda sinonimo conocido
    # CUANDO se verifica
    # ENTONCES retorna (True, valor_canonico)
    print("TEST: test_es_moneda_sinonimo")

    es_canon1, val1 = router_ambiguedad.es_moneda_canonica("pesos")
    es_canon2, val2 = router_ambiguedad.es_moneda_canonica("dolares")
    es_canon3, val3 = router_ambiguedad.es_moneda_canonica("euros")

    ok = True
    if es_canon1 != True or val1 != "ARS":
        print("  FALLO: pesos deberia resolverse a ARS")
        ok = False
    if es_canon2 != True or val2 != "USD":
        print("  FALLO: dolares deberia resolverse a USD")
        ok = False
    if es_canon3 != True or val3 != "EUR":
        print("  FALLO: euros deberia resolverse a EUR")
        ok = False

    if ok:
        print("  OK")
    assert ok


def test_es_moneda_ambigua():
    # DADO una moneda no canonica ni sinonimo
    # CUANDO se verifica
    # ENTONCES retorna (False, moneda_original)
    print("TEST: test_es_moneda_ambigua")

    es_canon, val = router_ambiguedad.es_moneda_canonica("moneda local")

    ok = True
    if es_canon != False:
        print("  FALLO: 'moneda local' deberia ser ambigua")
        ok = False
    if val != "moneda local":
        print("  FALLO: valor deberia ser la moneda original")
        ok = False

    if ok:
        print("  OK")
    assert ok


def test_es_tipo_producto_canonico():
    # DADO un tipo de producto canonico
    # CUANDO se verifica
    # ENTONCES retorna (True, tipo_upper)
    print("TEST: test_es_tipo_producto_canonico")

    es_canon1, val1 = router_ambiguedad.es_tipo_producto_canonico("CUENTA")
    es_canon2, val2 = router_ambiguedad.es_tipo_producto_canonico("tarjeta")
    es_canon3, val3 = router_ambiguedad.es_tipo_producto_canonico("SERVICIO")

    ok = True
    if es_canon1 != True or val1 != "CUENTA":
        print("  FALLO: CUENTA deberia ser canonico")
        ok = False
    if es_canon2 != True or val2 != "TARJETA":
        print("  FALLO: tarjeta deberia ser canonico")
        ok = False
    if es_canon3 != True or val3 != "SERVICIO":
        print("  FALLO: SERVICIO deberia ser canonico")
        ok = False

    if ok:
        print("  OK")
    assert ok


def test_es_tipo_producto_sinonimo():
    # DADO un tipo de producto sinonimo conocido
    # CUANDO se verifica
    # ENTONCES retorna (True, valor_canonico)
    print("TEST: test_es_tipo_producto_sinonimo")

    es_canon1, val1 = router_ambiguedad.es_tipo_producto_canonico("cta")
    es_canon2, val2 = router_ambiguedad.es_tipo_producto_canonico("tarj")
    es_canon3, val3 = router_ambiguedad.es_tipo_producto_canonico("plastico")

    ok = True
    if es_canon1 != True or val1 != "CUENTA":
        print("  FALLO: cta deberia resolverse a CUENTA")
        ok = False
    if es_canon2 != True or val2 != "TARJETA":
        print("  FALLO: tarj deberia resolverse a TARJETA")
        ok = False
    if es_canon3 != True or val3 != "TARJETA":
        print("  FALLO: plastico deberia resolverse a TARJETA")
        ok = False

    if ok:
        print("  OK")
    assert ok


def test_es_tipo_producto_ambiguo():
    # DADO un tipo de producto no canonico ni sinonimo
    # CUANDO se verifica
    # ENTONCES retorna (False, tipo_original)
    print("TEST: test_es_tipo_producto_ambiguo")

    es_canon, val = router_ambiguedad.es_tipo_producto_canonico("producto especial")

    ok = True
    if es_canon != False:
        print("  FALLO: 'producto especial' deberia ser ambiguo")
        ok = False
    if val != "producto especial":
        print("  FALLO: valor deberia ser el tipo original")
        ok = False

    if ok:
        print("  OK")
    assert ok


def test_es_pais_canonico():
    # DADO un pais canonico
    # CUANDO se verifica
    # ENTONCES retorna (True, pais_titulo)
    print("TEST: test_es_pais_canonico")

    es_canon1, val1 = router_ambiguedad.es_pais_canonico("Argentina")
    es_canon2, val2 = router_ambiguedad.es_pais_canonico("brasil")
    es_canon3, val3 = router_ambiguedad.es_pais_canonico("CHILE")

    ok = True
    if es_canon1 != True or val1 != "Argentina":
        print("  FALLO: Argentina deberia ser canonico")
        ok = False
    if es_canon2 != True or val2 != "Brasil":
        print("  FALLO: brasil deberia ser canonico con titulo")
        ok = False
    if es_canon3 != True or val3 != "Chile":
        print("  FALLO: CHILE deberia ser canonico con titulo")
        ok = False

    if ok:
        print("  OK")
    assert ok


def test_es_pais_sinonimo():
    # DADO un pais sinonimo conocido
    # CUANDO se verifica
    # ENTONCES retorna (True, valor_canonico)
    print("TEST: test_es_pais_sinonimo")

    es_canon1, val1 = router_ambiguedad.es_pais_canonico("arg")
    es_canon2, val2 = router_ambiguedad.es_pais_canonico("mx")
    es_canon3, val3 = router_ambiguedad.es_pais_canonico("bra")

    ok = True
    if es_canon1 != True or val1 != "Argentina":
        print("  FALLO: arg deberia resolverse a Argentina")
        ok = False
    if es_canon2 != True or val2 != "Mexico":
        print("  FALLO: mx deberia resolverse a Mexico")
        ok = False
    if es_canon3 != True or val3 != "Brasil":
        print("  FALLO: bra deberia resolverse a Brasil")
        ok = False

    if ok:
        print("  OK")
    assert ok


def test_es_pais_ambiguo():
    # DADO un pais no canonico ni sinonimo
    # CUANDO se verifica
    # ENTONCES retorna (False, pais_original)
    print("TEST: test_es_pais_ambiguo")

    es_canon, val = router_ambiguedad.es_pais_canonico("republica oriental")

    ok = True
    if es_canon != False:
        print("  FALLO: 'republica oriental' deberia ser ambiguo")
        ok = False
    if val != "republica oriental":
        print("  FALLO: valor deberia ser el pais original")
        ok = False

    if ok:
        print("  OK")
    assert ok


def test_es_monto_numerico():
    # DADO un monto numerico valido
    # CUANDO se verifica
    # ENTONCES retorna True
    print("TEST: test_es_monto_numerico")

    r1 = router_ambiguedad.es_monto_numerico("50000")
    r2 = router_ambiguedad.es_monto_numerico("0")
    r3 = router_ambiguedad.es_monto_numerico("-100")

    ok = True
    if r1 != True:
        print("  FALLO: 50000 deberia ser numerico")
        ok = False
    if r2 != True:
        print("  FALLO: 0 deberia ser numerico")
        ok = False
    if r3 != True:
        print("  FALLO: -100 deberia ser numerico")
        ok = False

    if ok:
        print("  OK")
    assert ok


def test_es_monto_no_numerico():
    # DADO un monto no numerico
    # CUANDO se verifica
    # ENTONCES retorna False
    print("TEST: test_es_monto_no_numerico")

    r1 = router_ambiguedad.es_monto_numerico("50k")
    r2 = router_ambiguedad.es_monto_numerico("cinco mil")
    r3 = router_ambiguedad.es_monto_numerico("100.5")

    ok = True
    if r1 != False:
        print("  FALLO: 50k no deberia ser numerico")
        ok = False
    if r2 != False:
        print("  FALLO: cinco mil no deberia ser numerico")
        ok = False
    if r3 != False:
        print("  FALLO: 100.5 no deberia ser numerico (solo enteros)")
        ok = False

    if ok:
        print("  OK")
    assert ok


def test_clasificar_registro_limpio():
    # DADO un registro completamente limpio
    # CUANDO se clasifica
    # ENTONCES no es ambiguo
    print("TEST: test_clasificar_registro_limpio")

    reg = {
        "id_solicitud": "SOL-001",
        "fecha_solicitud": "15/03/2025",
        "tipo_producto": "CUENTA",
        "id_cliente": "CLI-100",
        "monto_o_limite": "50000",
        "moneda": "ARS",
        "pais": "Argentina",
    }

    resultado = router_ambiguedad.clasificar_registro(reg)

    ok = True
    if resultado["es_ambiguo"] != False:
        print("  FALLO: registro limpio no deberia ser ambiguo")
        ok = False
    if len(resultado["motivos_ambiguedad"]) != 0:
        print("  FALLO: no deberia haber motivos de ambiguedad")
        ok = False

    if ok:
        print("  OK")
    assert ok


def test_clasificar_registro_ambiguo():
    # DADO un registro con campos ambiguos
    # CUANDO se clasifica
    # ENTONCES es ambiguo con motivos correctos
    print("TEST: test_clasificar_registro_ambiguo")

    reg = {
        "id_solicitud": "SOL-AMB-01",
        "fecha_solicitud": "15 de marzo",
        "tipo_producto": "cta especial",
        "id_cliente": "CLI-100",
        "monto_o_limite": "50k",
        "moneda": "u.s. dollar",
        "pais": "republica oriental",
    }

    resultado = router_ambiguedad.clasificar_registro(reg)

    ok = True
    if resultado["es_ambiguo"] != True:
        print("  FALLO: registro con datos ambiguos deberia ser ambiguo")
        ok = False
    if len(resultado["motivos_ambiguedad"]) == 0:
        print("  FALLO: deberia haber motivos de ambiguedad")
        ok = False
    if "fecha_solicitud" not in resultado["campos_ambiguos"]:
        print("  FALLO: fecha_solicitud deberia estar en campos ambiguos")
        ok = False

    if ok:
        print("  OK")
    assert ok


def test_clasificar_registro_sinonimo_resuelto():
    # DADO un registro con sinonimos conocidos
    # CUANDO se clasifica
    # ENTONCES no es ambiguo y tiene resolucion
    print("TEST: test_clasificar_registro_sinonimo_resuelto")

    reg = {
        "id_solicitud": "SOL-002",
        "fecha_solicitud": "15/03/2025",
        "tipo_producto": "cta",
        "id_cliente": "CLI-100",
        "monto_o_limite": "50000",
        "moneda": "pesos",
        "pais": "arg",
    }

    resultado = router_ambiguedad.clasificar_registro(reg)

    ok = True
    if resultado["es_ambiguo"] != False:
        print("  FALLO: registro con sinonimos conocidos no deberia ser ambiguo")
        ok = False
    if "tipo_producto" not in resultado["resolucion_sinonimos"].keys():
        print("  FALLO: deberia tener resolucion de tipo_producto")
        ok = False
    if resultado["resolucion_sinonimos"]["tipo_producto"] != "CUENTA":
        print("  FALLO: cta deberia resolverse a CUENTA")
        ok = False

    if ok:
        print("  OK")
    assert ok


def test_enrutar_registros():
    # DADO una lista de registros mixtos
    # CUANDO se enrutan
    # ENTONCES se separan en regla_path y llm_path correctamente
    print("TEST: test_enrutar_registros")

    registros = [
        # Limpio - regla_path
        {
            "id_solicitud": "SOL-001",
            "fecha_solicitud": "15/03/2025",
            "tipo_producto": "CUENTA",
            "id_cliente": "CLI-100",
            "monto_o_limite": "50000",
            "moneda": "ARS",
            "pais": "Argentina",
        },
        # Ambiguo - llm_path
        {
            "id_solicitud": "SOL-002",
            "fecha_solicitud": "15 marzo 2025",
            "tipo_producto": "producto raro",
            "id_cliente": "CLI-200",
            "monto_o_limite": "50k",
            "moneda": "u.s. dollar",
            "pais": "pais lejano",
        },
        # Sinonimo - regla_path
        {
            "id_solicitud": "SOL-003",
            "fecha_solicitud": "2025-03-15",
            "tipo_producto": "cta",
            "id_cliente": "CLI-300",
            "monto_o_limite": "75000",
            "moneda": "dolares",
            "pais": "mx",
        },
    ]

    regla_path, llm_path, stats = router_ambiguedad.enrutar_registros(registros)

    ok = True
    if len(regla_path) != 2:
        print(
            "  FALLO: deberian haber 2 registros en regla_path, hay "
            + str(len(regla_path))
        )
        ok = False
    if len(llm_path) != 1:
        print(
            "  FALLO: deberia haber 1 registro en llm_path, hay " + str(len(llm_path))
        )
        ok = False
    if stats["total"] != 3:
        print("  FALLO: total deberia ser 3")
        ok = False
    if regla_path[0]["origen_procesamiento"] != "rule_path":
        print(
            "  FALLO: registro en regla_path deberia tener origen_procesamiento = rule_path"
        )
        ok = False
    if llm_path[0]["origen_procesamiento"] != "llm_path":
        print(
            "  FALLO: registro en llm_path deberia tener origen_procesamiento = llm_path"
        )
        ok = False

    if ok:
        print("  OK")
    assert ok


def test_enrutar_registros_vacio():
    # DADO una lista vacia
    # CUANDO se enruta
    # ENTONCES retorna listas vacias y stats en 0
    print("TEST: test_enrutar_registros_vacio")

    regla_path, llm_path, stats = router_ambiguedad.enrutar_registros([])

    ok = True
    if len(regla_path) != 0:
        print("  FALLO: regla_path deberia estar vacio")
        ok = False
    if len(llm_path) != 0:
        print("  FALLO: llm_path deberia estar vacio")
        ok = False
    if stats["total"] != 0:
        print("  FALLO: total deberia ser 0")
        ok = False

    if ok:
        print("  OK")
    assert ok


def test_clasificar_registro_no_usa_embeddings_runtime():
    # DADO una moneda no canonica ni sinonimo
    # CUANDO se clasifica en AI-First
    # ENTONCES se marca ambiguo sin usar embeddings en runtime
    print("TEST: test_clasificar_registro_no_usa_embeddings_runtime")

    reg = {
        "id_solicitud": "SOL-EMB-01",
        "fecha_solicitud": "15/03/2025",
        "tipo_producto": "CUENTA",
        "id_cliente": "CLI-100",
        "monto_o_limite": "50000",
        "moneda": "u.s. dollar",
        "pais": "Argentina",
    }

    resultado = router_ambiguedad.clasificar_registro(reg, None, None)

    ok = True
    if resultado == None:
        print("  FALLO: resultado no deberia ser None")
        ok = False
    elif resultado.get("clasificacion", "") != "AMBIGUO_REQUIERE_IA":
        print("  FALLO: deberia clasificar como AMBIGUO_REQUIERE_IA")
        ok = False
    elif "moneda" not in resultado.get("campos_ambiguos", []):
        print("  FALLO: moneda deberia estar en campos ambiguos")
        ok = False

    if ok:
        print("  OK")
    assert ok


# Ejecutar tests manualmente
if __name__ == "__main__":
    print("=" * 50)
    print("TESTS DE ROUTER AMBIGUEDAD (RF-03 AI-First)")
    print("=" * 50)

    tests = [
        test_es_fecha_parseable_ddmmyyyy,
        test_es_fecha_parseable_yyyymmdd,
        test_es_fecha_parseable_ddmmyyyy_guion,
        test_es_fecha_ambigua_texto,
        test_es_fecha_ambigua_formato_raro,
        test_es_fecha_vacia_parseable,
        test_es_moneda_canonica,
        test_es_moneda_sinonimo,
        test_es_moneda_ambigua,
        test_es_tipo_producto_canonico,
        test_es_tipo_producto_sinonimo,
        test_es_tipo_producto_ambiguo,
        test_es_pais_canonico,
        test_es_pais_sinonimo,
        test_es_pais_ambiguo,
        test_es_monto_numerico,
        test_es_monto_no_numerico,
        test_clasificar_registro_limpio,
        test_clasificar_registro_ambiguo,
        test_clasificar_registro_sinonimo_resuelto,
        test_enrutar_registros,
        test_enrutar_registros_vacio,
        test_clasificar_registro_no_usa_embeddings_runtime,
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
