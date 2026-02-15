# verificador_salida.py - Verificador de salida LLM (RF-06)
# Parsea la respuesta del LLM y verifica contra el schema estricto

import os
import sys
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

MODULO = "VERIFICADOR_SALIDA"


def extraer_json_de_texto(texto):
    # Extrae un JSON valido de una respuesta de texto del LLM
    # El LLM puede devolver JSON dentro de markdown (```json ... ```)
    # o mezclado con texto explicativo
    # Retorna (dict, None) si ok, (None, error_str) si falla

    texto = texto.strip()

    # Caso 1: El texto es directamente un JSON valido
    try:
        datos = json.loads(texto)
        return datos, None
    except:
        pass

    # Caso 2: JSON dentro de bloque markdown ```json ... ```
    inicio_json = texto.find("```json")
    if inicio_json >= 0:
        inicio_contenido = texto.find("\n", inicio_json)
        if inicio_contenido >= 0:
            fin_contenido = texto.find("```", inicio_contenido + 1)
            if fin_contenido >= 0:
                fragmento = texto[inicio_contenido + 1 : fin_contenido].strip()
                try:
                    datos = json.loads(fragmento)
                    return datos, None
                except:
                    pass

    # Caso 3: JSON dentro de bloque ``` ... ``` (sin especificar json)
    inicio_bloque = texto.find("```")
    if inicio_bloque >= 0:
        inicio_contenido = texto.find("\n", inicio_bloque)
        if inicio_contenido >= 0:
            fin_contenido = texto.find("```", inicio_contenido + 1)
            if fin_contenido >= 0:
                fragmento = texto[inicio_contenido + 1 : fin_contenido].strip()
                try:
                    datos = json.loads(fragmento)
                    return datos, None
                except:
                    pass

    # Caso 4: Buscar primer { y ultimo } en el texto
    inicio_llave = texto.find("{")
    fin_llave = texto.rfind("}")
    if inicio_llave >= 0 and fin_llave > inicio_llave:
        fragmento = texto[inicio_llave : fin_llave + 1]
        try:
            datos = json.loads(fragmento)
            return datos, None
        except:
            pass

    return None, "No se encontro JSON valido en la respuesta del LLM"


def verificar_respuesta_llm(texto_llm, registro_original):
    # Verifica la respuesta del LLM contra el schema
    # Intenta parsear el JSON y crear un SolicitudNormalizada
    # Retorna (registro_normalizado, None) si ok, (None, error_str) si falla

    from schema_salida import registro_a_schema, schema_a_dict

    # Paso 1: Extraer JSON
    datos_json, error_json = extraer_json_de_texto(texto_llm)
    if error_json != None:
        return None, "Error extrayendo JSON: " + error_json

    # Paso 2: Merge con datos originales (el LLM puede no devolver todos los campos)
    registro_merged = {}
    for campo in registro_original.keys():
        if campo[0] != "_":
            registro_merged[campo] = registro_original[campo]

    # Sobreescribir con lo que devolvio el LLM
    for campo in datos_json.keys():
        registro_merged[campo] = str(datos_json[campo])

    # Marcar origen
    registro_merged["origen_procesamiento"] = "llm_path"

    # Paso 3: Validar contra schema
    schema, error_schema = registro_a_schema(registro_merged)
    if error_schema != None:
        return None, "Error de schema: " + error_schema

    # Paso 4: Convertir a dict plano
    resultado = schema_a_dict(schema)
    return resultado, None


def generar_prompt_correctivo(error, registro_original):
    # Genera un prompt correctivo para reintentar cuando el schema fallo
    prompt = "Tu respuesta anterior no cumplio con el schema requerido.\n"
    prompt = prompt + "Error: " + str(error) + "\n\n"
    prompt = prompt + "Registro original:\n"
    prompt = (
        prompt + json.dumps(registro_original, ensure_ascii=False, indent=2) + "\n\n"
    )
    prompt = (
        prompt
        + "Por favor, responde SOLO con un JSON valido que tenga exactamente estos campos:\n"
    )
    prompt = prompt + "- id_solicitud: string\n"
    prompt = prompt + "- fecha_solicitud: string en formato DD/MM/YYYY\n"
    prompt = (
        prompt + "- tipo_producto: uno de CUENTA, TARJETA, SERVICIO, PRESTAMO, SEGURO\n"
    )
    prompt = prompt + "- id_cliente: string\n"
    prompt = prompt + "- monto_o_limite: string numerico\n"
    prompt = prompt + "- moneda: uno de ARS, USD, EUR\n"
    prompt = prompt + "- pais: nombre canonico del pais\n"
    prompt = prompt + "\nResponde SOLO con el JSON, sin texto adicional."
    return prompt


def aplicar_fallback(registro_original, error):
    # Cuando el LLM falla despues de todos los reintentos
    # Marcar como INVALIDO con motivo tecnico
    resultado = {}
    campos = [
        "id_solicitud",
        "fecha_solicitud",
        "tipo_producto",
        "id_cliente",
        "monto_o_limite",
        "moneda",
        "pais",
        "flag_prioritario",
        "flag_digital",
    ]
    for campo in campos:
        if campo in registro_original.keys():
            resultado[campo] = registro_original[campo]
        else:
            resultado[campo] = ""

    resultado["estado"] = "INVALIDO"
    resultado["motivos_falla"] = "Fallback: LLM no pudo normalizar - " + str(error)
    resultado["origen_procesamiento"] = "llm_path"
    resultado["categoria_riesgo"] = ""
    resultado["retries_llm"] = 0
    resultado["fallback_aplicado"] = True
    return resultado
