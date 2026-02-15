# test_guardrails.py - Tests para el modulo guardrails (RF-05 AI-First)
# Verifica schema de salida y verificador de respuestas LLM

import sys
import os
import json

# Agregar paths necesarios
dir_tests = os.path.dirname(os.path.abspath(__file__))
dir_raiz = os.path.dirname(os.path.dirname(dir_tests))
dir_ai_src = os.path.join(dir_raiz, "ai_first_system", "src")
dir_guardrails = os.path.join(dir_ai_src, "guardrails")
sys.path.insert(0, dir_ai_src)
sys.path.insert(0, dir_guardrails)

import schema_salida
import verificador_salida

CARPETA_TEST = dir_tests


def test_registro_a_schema_valido():
    # DADO un diccionario de registro valido
    # CUANDO se convierte a schema
    # ENTONCES retorna el schema sin error
    print("TEST: test_registro_a_schema_valido")

    reg = {
        "id_solicitud": "SOL-001",
        "fecha_solicitud": "15/03/2025",
        "tipo_producto": "CUENTA",
        "id_cliente": "CLI-100",
        "monto_o_limite": "50000",
        "moneda": "ARS",
        "pais": "Argentina",
    }

    schema, error = schema_salida.registro_a_schema(reg)

    ok = True
    if schema == None:
        print("  FALLO: schema es None, error: " + str(error))
        ok = False
    elif error != None:
        print("  FALLO: no deberia haber error: " + str(error))
        ok = False
    elif schema.id_solicitud != "SOL-001":
        print("  FALLO: id_solicitud incorrecto")
        ok = False

    if ok:
        print("  OK")
    assert ok


def test_registro_a_schema_moneda_invalida():
    # DADO un registro con moneda no soportada
    # CUANDO se convierte a schema
    # ENTONCES retorna error de validacion
    print("TEST: test_registro_a_schema_moneda_invalida")

    reg = {
        "id_solicitud": "SOL-001",
        "fecha_solicitud": "15/03/2025",
        "tipo_producto": "CUENTA",
        "id_cliente": "CLI-100",
        "monto_o_limite": "50000",
        "moneda": "GBP",
        "pais": "Argentina",
    }

    schema, error = schema_salida.registro_a_schema(reg)

    ok = True
    if schema != None:
        print("  FALLO: schema deberia ser None para moneda invalida")
        ok = False
    elif error == None:
        print("  FALLO: deberia haber error de validacion")
        ok = False

    if ok:
        print("  OK")
    assert ok


def test_registro_a_schema_fecha_invalida():
    # DADO un registro con fecha en formato invalido
    # CUANDO se convierte a schema
    # ENTONCES retorna error de validacion
    print("TEST: test_registro_a_schema_fecha_invalida")

    reg = {
        "id_solicitud": "SOL-001",
        "fecha_solicitud": "2025-03-15",  # formato YYYY-MM-DD, no DD/MM/YYYY
        "tipo_producto": "CUENTA",
        "id_cliente": "CLI-100",
        "monto_o_limite": "50000",
        "moneda": "ARS",
        "pais": "Argentina",
    }

    schema, error = schema_salida.registro_a_schema(reg)

    ok = True
    if schema != None:
        print("  FALLO: schema deberia ser None para fecha invalida")
        ok = False
    elif error == None:
        print("  FALLO: deberia haber error de validacion")
        ok = False

    if ok:
        print("  OK")
    assert ok


def test_registro_a_schema_tipo_producto_invalido():
    # DADO un registro con tipo de producto no canonico
    # CUANDO se convierte a schema
    # ENTONCES retorna error de validacion
    print("TEST: test_registro_a_schema_tipo_producto_invalido")

    reg = {
        "id_solicitud": "SOL-001",
        "fecha_solicitud": "15/03/2025",
        "tipo_producto": "producto raro",
        "id_cliente": "CLI-100",
        "monto_o_limite": "50000",
        "moneda": "ARS",
        "pais": "Argentina",
    }

    schema, error = schema_salida.registro_a_schema(reg)

    ok = True
    if schema != None:
        print("  FALLO: schema deberia ser None para tipo invalido")
        ok = False
    elif error == None:
        print("  FALLO: deberia haber error de validacion")
        ok = False

    if ok:
        print("  OK")
    assert ok


def test_registro_a_schema_monto_invalido():
    # DADO un registro con monto no numerico
    # CUANDO se convierte a schema
    # ENTONCES retorna error de validacion
    print("TEST: test_registro_a_schema_monto_invalido")

    reg = {
        "id_solicitud": "SOL-001",
        "fecha_solicitud": "15/03/2025",
        "tipo_producto": "CUENTA",
        "id_cliente": "CLI-100",
        "monto_o_limite": "50k",
        "moneda": "ARS",
        "pais": "Argentina",
    }

    schema, error = schema_salida.registro_a_schema(reg)

    ok = True
    if schema != None:
        print("  FALLO: schema deberia ser None para monto invalido")
        ok = False
    elif error == None:
        print("  FALLO: deberia haber error de validacion")
        ok = False

    if ok:
        print("  OK")
    assert ok


def test_schema_a_dict():
    # DADO un schema valido
    # CUANDO se convierte a diccionario
    # ENTONCES tiene todos los campos esperados
    print("TEST: test_schema_a_dict")

    reg = {
        "id_solicitud": "SOL-001",
        "fecha_solicitud": "15/03/2025",
        "tipo_producto": "CUENTA",
        "id_cliente": "CLI-100",
        "monto_o_limite": "50000",
        "moneda": "ARS",
        "pais": "Argentina",
        "estado": "VALIDO",
        "motivos_falla": "",
    }

    schema, error = schema_salida.registro_a_schema(reg)
    if schema == None:
        print("  FALLO: no se pudo crear schema")
        assert False
        return

    d = schema_salida.schema_a_dict(schema)

    ok = True
    if d["id_solicitud"] != "SOL-001":
        print("  FALLO: id_solicitud incorrecto")
        ok = False
    if d["moneda"] != "ARS":
        print("  FALLO: moneda incorrecta")
        ok = False
    if "origen_procesamiento" not in d.keys():
        print("  FALLO: falta origen_procesamiento")
        ok = False

    if ok:
        print("  OK")
    assert ok


def test_extraer_json_de_texto_directo():
    # DADO un texto que es directamente JSON valido
    # CUANDO se extrae
    # ENTONCES retorna el diccionario correctamente
    print("TEST: test_extraer_json_de_texto_directo")

    texto = '{"id_solicitud": "SOL-001", "moneda": "ARS"}'
    datos, error = verificador_salida.extraer_json_de_texto(texto)

    ok = True
    if datos == None:
        print("  FALLO: datos es None, error: " + str(error))
        ok = False
    elif error != None:
        print("  FALLO: no deberia haber error: " + str(error))
        ok = False
    elif datos["id_solicitud"] != "SOL-001":
        print("  FALLO: id_solicitud incorrecto")
        ok = False

    if ok:
        print("  OK")
    assert ok


def test_extraer_json_de_texto_markdown():
    # DADO un texto con JSON dentro de bloque markdown
    # CUANDO se extrae
    # ENTONCES retorna el diccionario correctamente
    print("TEST: test_extraer_json_de_texto_markdown")

    texto = 'Aqui esta el resultado:\n```json\n{"id_solicitud": "SOL-001", "moneda": "ARS"}\n```\nEspero que sirva.'
    datos, error = verificador_salida.extraer_json_de_texto(texto)

    ok = True
    if datos == None:
        print("  FALLO: datos es None, error: " + str(error))
        ok = False
    elif error != None:
        print("  FALLO: no deberia haber error: " + str(error))
        ok = False
    elif datos["id_solicitud"] != "SOL-001":
        print("  FALLO: id_solicitud incorrecto")
        ok = False

    if ok:
        print("  OK")
    assert ok


def test_extraer_json_de_texto_mezclado():
    # DADO un texto con JSON mezclado con texto
    # CUANDO se extrae
    # ENTONCES retorna el diccionario correctamente
    print("TEST: test_extraer_json_de_texto_mezclado")

    texto = 'El resultado procesado es: {"id_solicitud": "SOL-001", "moneda": "ARS"} y eso es todo.'
    datos, error = verificador_salida.extraer_json_de_texto(texto)

    ok = True
    if datos == None:
        print("  FALLO: datos es None, error: " + str(error))
        ok = False
    elif error != None:
        print("  FALLO: no deberia haber error: " + str(error))
        ok = False
    elif datos["id_solicitud"] != "SOL-001":
        print("  FALLO: id_solicitud incorrecto")
        ok = False

    if ok:
        print("  OK")
    assert ok


def test_extraer_json_de_texto_sin_json():
    # DADO un texto sin JSON valido
    # CUANDO se extrae
    # ENTONCES retorna error
    print("TEST: test_extraer_json_de_texto_sin_json")

    texto = "Este texto no tiene JSON valido"
    datos, error = verificador_salida.extraer_json_de_texto(texto)

    ok = True
    if datos != None:
        print("  FALLO: datos deberia ser None")
        ok = False
    elif error == None:
        print("  FALLO: deberia haber error")
        ok = False

    if ok:
        print("  OK")
    assert ok


def test_verificar_respuesta_llm_valida():
    # DADO una respuesta LLM con JSON valido y completo
    # CUANDO se verifica
    # ENTONCES retorna el registro normalizado sin error
    print("TEST: test_verificar_respuesta_llm_valida")

    reg_original = {
        "id_solicitud": "SOL-001",
        "fecha_solicitud": "15/03/2025",
        "tipo_producto": "cta",
        "id_cliente": "CLI-100",
        "monto_o_limite": "50000",
        "moneda": "ARS",
        "pais": "Argentina",
    }

    # LLM devuelve tipo normalizado
    texto_llm = '{"id_solicitud": "SOL-001", "fecha_solicitud": "15/03/2025", "tipo_producto": "CUENTA", "id_cliente": "CLI-100", "monto_o_limite": "50000", "moneda": "ARS", "pais": "Argentina"}'

    resultado, error = verificador_salida.verificar_respuesta_llm(
        texto_llm, reg_original
    )

    ok = True
    if resultado == None:
        print("  FALLO: resultado es None, error: " + str(error))
        ok = False
    elif error != None:
        print("  FALLO: no deberia haber error: " + str(error))
        ok = False
    elif resultado["tipo_producto"] != "CUENTA":
        print("  FALLO: tipo_producto deberia ser CUENTA")
        ok = False

    if ok:
        print("  OK")
    assert ok


def test_verificar_respuesta_llm_parcial():
    # DADO una respuesta LLM con JSON parcial (falta mapear algunos campos)
    # CUANDO se verifica
    # ENTONCES mergea con datos originales
    print("TEST: test_verificar_respuesta_llm_parcial")

    reg_original = {
        "id_solicitud": "SOL-001",
        "fecha_solicitud": "15/03/2025",
        "tipo_producto": "cta",
        "id_cliente": "CLI-100",
        "monto_o_limite": "50000",
        "moneda": "ARS",
        "pais": "Argentina",
    }

    # LLM devuelve solo algunos campos
    texto_llm = '{"id_solicitud": "SOL-001", "tipo_producto": "CUENTA"}'

    resultado, error = verificador_salida.verificar_respuesta_llm(
        texto_llm, reg_original
    )

    ok = True
    if resultado == None:
        print("  FALLO: resultado es None, error: " + str(error))
        ok = False
    elif resultado["id_cliente"] != "CLI-100":
        print("  FALLO: id_cliente deberia preservarse del original")
        ok = False
    elif resultado["tipo_producto"] != "CUENTA":
        print("  FALLO: tipo_producto deberia ser el del LLM")
        ok = False

    if ok:
        print("  OK")
    assert ok


def test_aplicar_fallback():
    # DADO un registro y un error
    # CUANDO se aplica fallback
    # ENTONCES retorna registro marcado como INVALIDO
    print("TEST: test_aplicar_fallback")

    reg_original = {
        "id_solicitud": "SOL-001",
        "fecha_solicitud": "15 de marzo",
        "tipo_producto": "cta",
        "id_cliente": "CLI-100",
        "monto_o_limite": "50k",
        "moneda": "pesos",
        "pais": "arg",
    }

    error = "Schema validation failed"

    resultado = verificador_salida.aplicar_fallback(reg_original, error)

    ok = True
    if resultado["estado"] != "INVALIDO":
        print("  FALLO: estado deberia ser INVALIDO")
        ok = False
    if resultado["fallback_aplicado"] != True:
        print("  FALLO: fallback_aplicado deberia ser True")
        ok = False
    if resultado["origen_procesamiento"] != "llm_path":
        print("  FALLO: origen_procesamiento deberia ser llm_path")
        ok = False
    if "Fallback" not in resultado["motivos_falla"]:
        print("  FALLO: motivos_falla deberia mencionar Fallback")
        ok = False

    if ok:
        print("  OK")
    assert ok


def test_generar_prompt_correctivo():
    # DADO un error y registro original
    # CUANDO se genera prompt correctivo
    # ENTONCES incluye el error y campos esperados
    print("TEST: test_generar_prompt_correctivo")

    reg_original = {
        "id_solicitud": "SOL-001",
        "tipo_producto": "cta",
        "moneda": "pesos",
    }

    error = "Moneda no soportada: pesos"

    prompt = verificador_salida.generar_prompt_correctivo(error, reg_original)

    ok = True
    if "Moneda no soportada" not in prompt:
        print("  FALLO: deberia incluir el mensaje de error")
        ok = False
    if "id_solicitud" not in prompt:
        print("  FALLO: deberia mencionar campos esperados")
        ok = False
    if "JSON" not in prompt:
        print("  FALLO: deberia pedir JSON")
        ok = False

    if ok:
        print("  OK")
    assert ok


# Ejecutar tests manualmente
if __name__ == "__main__":
    print("=" * 50)
    print("TESTS DE GUARDRAILS (RF-05 AI-First)")
    print("=" * 50)

    tests = [
        test_registro_a_schema_valido,
        test_registro_a_schema_moneda_invalida,
        test_registro_a_schema_fecha_invalida,
        test_registro_a_schema_tipo_producto_invalido,
        test_registro_a_schema_monto_invalido,
        test_schema_a_dict,
        test_extraer_json_de_texto_directo,
        test_extraer_json_de_texto_markdown,
        test_extraer_json_de_texto_mezclado,
        test_extraer_json_de_texto_sin_json,
        test_verificar_respuesta_llm_valida,
        test_verificar_respuesta_llm_parcial,
        test_aplicar_fallback,
        test_generar_prompt_correctivo,
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
