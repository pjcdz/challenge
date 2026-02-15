# router_ambiguedad.py - Enrutamiento hibrido (RF-05 AI-First)
# Determina si un registro puede resolverse con reglas deterministicas
# o necesita el flujo LLM para normalizacion semantica

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import (
    MONEDAS_SOPORTADAS,
    TIPOS_PRODUCTO_CANONICOS,
    PAISES_CANONICOS,
    SINONIMOS_MONEDA,
    SINONIMOS_TIPO_PRODUCTO,
    SINONIMOS_PAIS,
)

MODULO = "ROUTER"
UMBRAL_SIMILITUD_EMBEDDING = 0.82


def calcular_similitud_coseno(embedding_a, embedding_b):
    # Calcula similitud coseno entre dos embeddings
    # Retorna float entre -1 y 1
    if embedding_a == None or embedding_b == None:
        return 0.0
    if len(embedding_a) != len(embedding_b):
        return 0.0

    dot = 0.0
    norm_a = 0.0
    norm_b = 0.0
    i = 0
    while i < len(embedding_a):
        dot = dot + (embedding_a[i] * embedding_b[i])
        norm_a = norm_a + (embedding_a[i] * embedding_a[i])
        norm_b = norm_b + (embedding_b[i] * embedding_b[i])
        i = i + 1

    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0

    norm_a = norm_a**0.5
    norm_b = norm_b**0.5
    return dot / (norm_a * norm_b)


def obtener_embedding_con_cache(texto, llm_provider, cache_embeddings):
    # Obtiene embedding con cache para evitar llamadas repetidas
    if cache_embeddings == None:
        cache_embeddings = {}

    clave = texto.strip().lower()
    if clave in cache_embeddings.keys():
        return cache_embeddings[clave], None

    if not hasattr(llm_provider, "generar_embedding"):
        return None, "Provider no soporta embeddings"

    resultado = llm_provider.generar_embedding(texto)
    if resultado == None:
        cache_embeddings[clave] = None
        return None, "Respuesta embedding vacia"
    if "error" in resultado.keys() and resultado["error"] != None:
        cache_embeddings[clave] = None
        return None, resultado["error"]
    if "embedding" not in resultado.keys():
        cache_embeddings[clave] = None
        return None, "Respuesta embedding sin campo embedding"

    cache_embeddings[clave] = resultado["embedding"]
    return resultado["embedding"], None


def resolver_canonico_por_embeddings(
    valor, candidatos_canonicos, llm_provider, cache_embeddings
):
    # Intenta resolver un valor ambiguo por similitud semantica de embeddings
    # Retorna (resuelto_bool, valor_resuelto, similitud)
    if llm_provider == None:
        return False, valor, 0.0
    if valor == None:
        return False, valor, 0.0

    texto = valor.strip()
    if texto == "":
        return False, valor, 0.0

    emb_valor, err_valor = obtener_embedding_con_cache(
        texto, llm_provider, cache_embeddings
    )
    if err_valor != None or emb_valor == None:
        return False, valor, 0.0

    mejor_candidato = ""
    mejor_similitud = -1.0

    for candidato in candidatos_canonicos:
        emb_candidato, err_candidato = obtener_embedding_con_cache(
            candidato, llm_provider, cache_embeddings
        )
        if err_candidato != None or emb_candidato == None:
            continue

        sim = 0.0
        if hasattr(llm_provider, "calcular_similitud"):
            sim = llm_provider.calcular_similitud(emb_valor, emb_candidato)
        else:
            sim = calcular_similitud_coseno(emb_valor, emb_candidato)

        if sim > mejor_similitud:
            mejor_similitud = sim
            mejor_candidato = candidato

    if mejor_candidato == "":
        return False, valor, 0.0

    if mejor_similitud >= UMBRAL_SIMILITUD_EMBEDDING:
        return True, mejor_candidato, round(mejor_similitud, 4)

    return False, valor, round(mejor_similitud, 4)


def es_fecha_parseable(fecha):
    # Verifica si la fecha tiene un formato deterministico reconocido
    # DD/MM/YYYY, YYYY-MM-DD, DD-MM-YYYY
    # Retorna True si se puede parsear con reglas, False si es ambigua
    if fecha == None or fecha == "":
        return True  # campo vacio se detecta en validacion R1, no es ambiguo

    fecha = fecha.strip()

    # Formato DD/MM/YYYY
    if len(fecha) == 10 and fecha[2] == "/" and fecha[5] == "/":
        dia = fecha[0:2]
        mes = fecha[3:5]
        anio = fecha[6:10]
        if dia.isdigit() and mes.isdigit() and anio.isdigit():
            return True

    # Formato YYYY-MM-DD
    if len(fecha) == 10 and fecha[4] == "-" and fecha[7] == "-":
        anio = fecha[0:4]
        mes = fecha[5:7]
        dia = fecha[8:10]
        if dia.isdigit() and mes.isdigit() and anio.isdigit():
            return True

    # Formato DD-MM-YYYY
    if len(fecha) == 10 and fecha[2] == "-" and fecha[5] == "-":
        dia = fecha[0:2]
        mes = fecha[3:5]
        anio = fecha[6:10]
        if dia.isdigit() and mes.isdigit() and anio.isdigit():
            return True

    # Cualquier otro formato es ambiguo (texto, meses en letras, etc.)
    return False


def es_moneda_canonica(moneda):
    # Verifica si la moneda es canonica o resoluble con sinonimos
    # Retorna (es_canonica, valor_canonico)
    if moneda == None or moneda == "":
        return True, ""

    moneda_upper = moneda.strip().upper()

    # Es directamente canonica
    if moneda_upper in MONEDAS_SOPORTADAS:
        return True, moneda_upper

    # Es un sinonimo conocido
    moneda_lower = moneda.strip().lower()
    if moneda_lower in SINONIMOS_MONEDA.keys():
        return True, SINONIMOS_MONEDA[moneda_lower]

    return False, moneda


def es_tipo_producto_canonico(tipo):
    # Verifica si el tipo de producto es canonico o resoluble con sinonimos
    # Retorna (es_canonico, valor_canonico)
    if tipo == None or tipo == "":
        return True, ""

    tipo_upper = tipo.strip().upper()

    # Es directamente canonico
    if tipo_upper in TIPOS_PRODUCTO_CANONICOS:
        return True, tipo_upper

    # Es un sinonimo conocido
    tipo_lower = tipo.strip().lower()
    if tipo_lower in SINONIMOS_TIPO_PRODUCTO.keys():
        return True, SINONIMOS_TIPO_PRODUCTO[tipo_lower]

    return False, tipo


def es_pais_canonico(pais):
    # Verifica si el pais es canonico o resoluble con sinonimos
    # Retorna (es_canonico, valor_canonico)
    if pais == None or pais == "":
        return True, ""

    pais_stripped = pais.strip()

    # Comparar con paises canonicos (case insensitive)
    for p in PAISES_CANONICOS:
        if pais_stripped.lower() == p.lower():
            return True, p

    # Es un sinonimo conocido
    pais_lower = pais_stripped.lower()
    if pais_lower in SINONIMOS_PAIS.keys():
        return True, SINONIMOS_PAIS[pais_lower]

    return False, pais


def es_monto_numerico(monto):
    # Verifica si el monto es numerico puro
    # Retorna True si es parseable como entero
    if monto == None or monto == "":
        return True  # vacio se detecta en R1

    val = monto.strip()
    if val == "":
        return True

    # Numero entero (puede ser negativo)
    if val[0] == "-":
        rest = val[1:]
        if rest == "":
            return False
        return rest.isdigit()
    return val.isdigit()


def clasificar_registro(reg, llm_provider=None, cache_embeddings=None):
    # Analiza un registro y determina si es resoluble por reglas o necesita LLM
    # Retorna un diccionario con:
    #   "es_ambiguo": bool
    #   "motivos_ambiguedad": lista de strings explicando que campos son ambiguos
    #   "resolucion_sinonimos": dict con campos resueltos por sinonimos
    #   "campos_ambiguos": lista de nombres de campos ambiguos

    motivos = []
    campos_ambiguos = []
    resolucion = {}
    resolucion_embeddings = {}

    # Verificar fecha
    fecha = ""
    if "fecha_solicitud" in reg.keys():
        fecha = reg["fecha_solicitud"]
    if not es_fecha_parseable(fecha):
        motivos.append("fecha ambigua: '" + str(fecha) + "'")
        campos_ambiguos.append("fecha_solicitud")

    # Verificar moneda
    moneda = ""
    if "moneda" in reg.keys():
        moneda = reg["moneda"]
    es_canon_moneda, moneda_resuelta = es_moneda_canonica(moneda)
    if not es_canon_moneda:
        resuelto_emb, moneda_emb, score_emb = resolver_canonico_por_embeddings(
            str(moneda), MONEDAS_SOPORTADAS, llm_provider, cache_embeddings
        )
        if resuelto_emb:
            resolucion["moneda"] = moneda_emb
            resolucion_embeddings["moneda"] = score_emb
        else:
            motivos.append("moneda no canonica: '" + str(moneda) + "'")
            campos_ambiguos.append("moneda")
    elif moneda_resuelta != "" and moneda_resuelta != moneda.strip().upper():
        resolucion["moneda"] = moneda_resuelta

    # Verificar tipo de producto
    tipo = ""
    if "tipo_producto" in reg.keys():
        tipo = reg["tipo_producto"]
    es_canon_tipo, tipo_resuelto = es_tipo_producto_canonico(tipo)
    if not es_canon_tipo:
        resuelto_emb, tipo_emb, score_emb = resolver_canonico_por_embeddings(
            str(tipo), TIPOS_PRODUCTO_CANONICOS, llm_provider, cache_embeddings
        )
        if resuelto_emb:
            resolucion["tipo_producto"] = tipo_emb
            resolucion_embeddings["tipo_producto"] = score_emb
        else:
            motivos.append("tipo producto no canonico: '" + str(tipo) + "'")
            campos_ambiguos.append("tipo_producto")
    elif tipo_resuelto != "" and tipo_resuelto != tipo.strip().upper():
        resolucion["tipo_producto"] = tipo_resuelto

    # Verificar pais
    pais = ""
    if "pais" in reg.keys():
        pais = reg["pais"]
    es_canon_pais, pais_resuelto = es_pais_canonico(pais)
    if not es_canon_pais:
        resuelto_emb, pais_emb, score_emb = resolver_canonico_por_embeddings(
            str(pais), PAISES_CANONICOS, llm_provider, cache_embeddings
        )
        if resuelto_emb:
            resolucion["pais"] = pais_emb
            resolucion_embeddings["pais"] = score_emb
        else:
            motivos.append("pais no canonico: '" + str(pais) + "'")
            campos_ambiguos.append("pais")
    elif pais_resuelto != "" and pais_resuelto != pais.strip():
        resolucion["pais"] = pais_resuelto

    # Verificar monto
    monto = ""
    if "monto_o_limite" in reg.keys():
        monto = reg["monto_o_limite"]
    if not es_monto_numerico(monto):
        motivos.append("monto no numerico: '" + str(monto) + "'")
        campos_ambiguos.append("monto_o_limite")

    es_ambiguo = len(motivos) > 0

    resultado = {
        "es_ambiguo": es_ambiguo,
        "motivos_ambiguedad": motivos,
        "resolucion_sinonimos": resolucion,
        "resolucion_embeddings": resolucion_embeddings,
        "campos_ambiguos": campos_ambiguos,
    }
    return resultado


def aplicar_resolucion_sinonimos(reg, resolucion):
    # Aplica las resoluciones de sinonimos al registro
    # Modifica el registro in-place y retorna el registro modificado
    for campo in resolucion.keys():
        reg[campo] = resolucion[campo]
    return reg


def enrutar_registros(registros, llm_provider=None):
    # Clasifica todos los registros y separa en dos listas:
    # - regla_path: resolubles por reglas deterministicas
    # - llm_path: requieren LLM para normalizacion semantica
    # Retorna (regla_path, llm_path, estadisticas)

    regla_path = []
    llm_path = []
    total_sinonimos_resueltos = 0
    total_embeddings_resueltos = 0
    cache_embeddings = {}

    for reg in registros:
        clasificacion = clasificar_registro(reg, llm_provider, cache_embeddings)

        if clasificacion["es_ambiguo"]:
            # Necesita LLM
            reg["_clasificacion"] = clasificacion
            reg["origen_procesamiento"] = "llm_path"
            llm_path.append(reg)
        else:
            # Resoluble por reglas
            # Aplicar sinonimos si los hay
            if len(clasificacion["resolucion_sinonimos"].keys()) > 0:
                reg = aplicar_resolucion_sinonimos(
                    reg, clasificacion["resolucion_sinonimos"]
                )
                total_sinonimos_resueltos = total_sinonimos_resueltos + 1
            if len(clasificacion["resolucion_embeddings"].keys()) > 0:
                total_embeddings_resueltos = total_embeddings_resueltos + 1
            reg["origen_procesamiento"] = "rule_path"
            regla_path.append(reg)

    estadisticas = {
        "total": len(registros),
        "regla_path": len(regla_path),
        "llm_path": len(llm_path),
        "sinonimos_resueltos": total_sinonimos_resueltos,
        "embeddings_resueltos": total_embeddings_resueltos,
        "porcentaje_llm": 0.0,
    }
    if len(registros) > 0:
        estadisticas["porcentaje_llm"] = round(
            (len(llm_path) * 100.0) / len(registros), 1
        )

    return regla_path, llm_path, estadisticas
