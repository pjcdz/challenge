# workflow_graph.py - Grafo de workflow LangGraph (RF-07 AI-First)
# Define el grafo de estado tipado con 5 nodos + rutas condicionales
# NOTA: LangGraph requiere TypedDict/type hints - excepcion justificada por framework

import os
import sys
import json
import time

dir_src = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, dir_src)
sys.path.insert(0, os.path.join(dir_src, "agents"))
sys.path.insert(0, os.path.join(dir_src, "adapters"))
sys.path.insert(0, os.path.join(dir_src, "guardrails"))

MODULO = "WORKFLOW_GRAPH"


# --- Estado del grafo (TypedDict requerido por LangGraph) ---
# Nota: usamos typing para el estado del grafo (requerimiento del framework)

from typing import TypedDict, List, Optional, Any


class EstadoWorkflow(TypedDict):
    # Estado compartido entre nodos del grafo
    registro: dict
    registro_normalizado: dict
    clasificacion: dict
    resultado_llm: str
    prompt_correctivo: str
    error: str
    intentos: int
    max_retries: int
    nodo_actual: str
    finalizado: bool
    llm_provider: Any


# --- Nodos del grafo ---


def nodo_preparar_contexto(estado):
    # Nodo 1: Preparar contexto del registro ambiguo para el LLM
    reg = estado["registro"]
    clasificacion = estado["clasificacion"]

    # Construir contexto con informacion de ambiguedad
    contexto = "Campos ambiguos detectados:\n"
    for mot in clasificacion["motivos_ambiguedad"]:
        contexto = contexto + "- " + mot + "\n"

    estado["nodo_actual"] = "preparar_contexto"
    estado["error"] = ""
    estado["prompt_correctivo"] = ""
    return estado


def nodo_normalizacion_llm(estado):
    # Nodo 2: Normalizacion semantica via LLM
    from agente_normalizador import cargar_prompt_normalizacion

    reg = estado["registro"]
    llm_provider = estado["llm_provider"]

    # Preparar registro limpio
    reg_limpio = {}
    for campo in reg.keys():
        if (
            campo[0] != "_"
            and campo != "origen_procesamiento"
            and campo != "retries_llm"
            and campo != "fallback_aplicado"
        ):
            reg_limpio[campo] = reg[campo]

    # Cargar prompt
    template = cargar_prompt_normalizacion()
    prompt = template.replace(
        "{REGISTRO_JSON}", json.dumps(reg_limpio, ensure_ascii=False, indent=2)
    )

    # Si hay un prompt correctivo activo, usarlo en el reintento
    if "prompt_correctivo" in estado.keys():
        if estado["prompt_correctivo"] != "":
            prompt = prompt + "\n\n" + estado["prompt_correctivo"]

    # Generar con LLM (1 intento por nodo; los reintentos los maneja el grafo)
    resultado = llm_provider.generar_con_retry(prompt, "", "", max_intentos=1)
    intento_nodo = 1
    if "intento" in resultado.keys():
        intento_nodo = resultado["intento"]
    estado["intentos"] = estado["intentos"] + intento_nodo

    if resultado["error"] != None:
        estado["error"] = resultado["error"]
        estado["resultado_llm"] = ""
    else:
        estado["resultado_llm"] = resultado["texto"]
        estado["error"] = ""

    estado["nodo_actual"] = "normalizacion_llm"
    return estado


def nodo_verificar_schema(estado):
    # Nodo 3: Verificacion de schema estricto
    from verificador_salida import verificar_respuesta_llm, generar_prompt_correctivo

    texto_llm = estado["resultado_llm"]
    reg_original = estado["registro"]

    if texto_llm == "":
        estado["error"] = "Respuesta LLM vacia"
        estado["nodo_actual"] = "verificar_schema"
        return estado

    reg_normalizado, error = verificar_respuesta_llm(texto_llm, reg_original)

    if error != None:
        estado["error"] = error
        estado["registro_normalizado"] = {}
        estado["prompt_correctivo"] = generar_prompt_correctivo(error, reg_original)
    else:
        estado["registro_normalizado"] = reg_normalizado
        estado["error"] = ""
        estado["prompt_correctivo"] = ""

    estado["nodo_actual"] = "verificar_schema"
    return estado


def nodo_validacion_dura(estado):
    # Nodo 4: Validacion dura post-LLM (R1/R2/R3)
    from agente_validador import validar

    reg_norm = estado["registro_normalizado"]
    if len(reg_norm.keys()) == 0:
        estado["error"] = "No hay registro normalizado para validar"
        estado["nodo_actual"] = "validacion_dura"
        return estado

    # Aplicar validaciones duras
    resultados = validar([reg_norm])
    if len(resultados) > 0:
        estado["registro_normalizado"] = resultados[0]
        estado["error"] = ""
        estado["prompt_correctivo"] = ""
    else:
        estado["error"] = "Validacion no retorno resultados"

    estado["nodo_actual"] = "validacion_dura"
    return estado


def nodo_calidad_explicativa(estado):
    # Nodo 5: Calidad explicativa (motivos y trazas)
    reg = estado["registro_normalizado"]
    if len(reg.keys()) == 0:
        estado["nodo_actual"] = "calidad_explicativa"
        estado["finalizado"] = True
        return estado

    # Agregar trazas de procesamiento
    reg["origen_procesamiento"] = "llm_path"
    retries = 0
    if estado["intentos"] > 1:
        retries = estado["intentos"] - 1
    reg["retries_llm"] = retries
    reg["fallback_aplicado"] = False

    estado["registro_normalizado"] = reg
    estado["nodo_actual"] = "calidad_explicativa"
    estado["finalizado"] = True
    return estado


# --- Rutas condicionales ---


def ruta_despues_de_llm(estado):
    # Decide si ir a verificar schema o retry
    if estado["error"] != "":
        if estado["intentos"] < estado["max_retries"]:
            return "retry_llm"
        else:
            return "fallback"
    return "verificar_schema"


def ruta_despues_de_schema(estado):
    # Decide si ir a validacion dura o retry
    if estado["error"] != "":
        if estado["intentos"] < estado["max_retries"]:
            return "retry_llm"
        else:
            return "fallback"
    return "validacion_dura"


def nodo_fallback(estado):
    # Nodo de fallback: marca como INVALIDO con motivo tecnico
    from verificador_salida import aplicar_fallback

    reg_original = estado["registro"]
    error = estado["error"]

    reg_fallback = aplicar_fallback(reg_original, error)
    retries = 0
    if estado["intentos"] > 1:
        retries = estado["intentos"] - 1
    reg_fallback["retries_llm"] = retries

    estado["registro_normalizado"] = reg_fallback
    estado["nodo_actual"] = "fallback"
    estado["finalizado"] = True
    estado["prompt_correctivo"] = ""
    return estado


# --- Constructor del grafo ---


def crear_grafo():
    # Crea y retorna el grafo de workflow
    # Usa langgraph si esta disponible, sino usa implementacion manual

    try:
        from langgraph.graph import StateGraph, END

        grafo = StateGraph(EstadoWorkflow)

        # Agregar nodos
        grafo.add_node("preparar_contexto", nodo_preparar_contexto)
        grafo.add_node("normalizacion_llm", nodo_normalizacion_llm)
        grafo.add_node("verificar_schema", nodo_verificar_schema)
        grafo.add_node("validacion_dura", nodo_validacion_dura)
        grafo.add_node("calidad_explicativa", nodo_calidad_explicativa)
        grafo.add_node("fallback", nodo_fallback)
        grafo.add_node("retry_llm", nodo_normalizacion_llm)

        # Definir flujo
        grafo.set_entry_point("preparar_contexto")
        grafo.add_edge("preparar_contexto", "normalizacion_llm")

        grafo.add_conditional_edges(
            "normalizacion_llm",
            ruta_despues_de_llm,
            {
                "verificar_schema": "verificar_schema",
                "retry_llm": "retry_llm",
                "fallback": "fallback",
            },
        )

        grafo.add_conditional_edges(
            "verificar_schema",
            ruta_despues_de_schema,
            {
                "validacion_dura": "validacion_dura",
                "retry_llm": "retry_llm",
                "fallback": "fallback",
            },
        )

        grafo.add_conditional_edges(
            "retry_llm",
            ruta_despues_de_llm,
            {
                "verificar_schema": "verificar_schema",
                "retry_llm": "fallback",  # evitar loop infinito
                "fallback": "fallback",
            },
        )

        grafo.add_edge("validacion_dura", "calidad_explicativa")
        grafo.add_edge("calidad_explicativa", END)
        grafo.add_edge("fallback", END)

        return grafo.compile()

    except ImportError:
        # Fallback: implementacion manual sin LangGraph
        return None


def ejecutar_grafo_manual(estado):
    # Implementacion manual del grafo cuando LangGraph no esta disponible
    # Sigue la misma logica de nodos y rutas condicionales

    # Nodo 1: Preparar contexto
    estado = nodo_preparar_contexto(estado)

    # Nodo 2: Normalizacion LLM
    estado = nodo_normalizacion_llm(estado)

    # Ruta condicional despues de LLM
    ruta = ruta_despues_de_llm(estado)

    if ruta == "retry_llm":
        estado = nodo_normalizacion_llm(estado)
        ruta = ruta_despues_de_llm(estado)

    if ruta == "fallback":
        estado = nodo_fallback(estado)
        return estado

    # Nodo 3: Verificar schema
    estado = nodo_verificar_schema(estado)

    ruta2 = ruta_despues_de_schema(estado)
    if ruta2 == "retry_llm":
        estado = nodo_normalizacion_llm(estado)
        ruta_retry = ruta_despues_de_llm(estado)
        if ruta_retry != "verificar_schema":
            estado = nodo_fallback(estado)
            return estado
        estado = nodo_verificar_schema(estado)
        ruta2 = ruta_despues_de_schema(estado)
        if ruta2 != "validacion_dura":
            estado = nodo_fallback(estado)
            return estado

    if ruta2 == "fallback":
        estado = nodo_fallback(estado)
        return estado

    # Nodo 4: Validacion dura
    estado = nodo_validacion_dura(estado)

    # Nodo 5: Calidad explicativa
    estado = nodo_calidad_explicativa(estado)

    return estado


def procesar_registro_ambiguo(registro, clasificacion, llm_provider, max_retries=2):
    # Procesa un registro ambiguo a traves del grafo de workflow
    # Retorna el registro normalizado (o fallback)

    from config import MAX_RETRIES_LLM

    estado_inicial = {
        "registro": registro,
        "registro_normalizado": {},
        "clasificacion": clasificacion,
        "resultado_llm": "",
        "prompt_correctivo": "",
        "error": "",
        "intentos": 0,
        "max_retries": max_retries,
        "nodo_actual": "",
        "finalizado": False,
        "llm_provider": llm_provider,
    }

    # Intentar usar grafo LangGraph
    grafo = crear_grafo()
    if grafo != None:
        try:
            resultado = grafo.invoke(estado_inicial)
            return resultado["registro_normalizado"]
        except Exception as e:
            # Si falla LangGraph, caer al manual
            pass

    # Usar implementacion manual
    resultado = ejecutar_grafo_manual(estado_inicial)
    return resultado["registro_normalizado"]
