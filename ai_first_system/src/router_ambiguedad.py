# router_ambiguedad.py - Enrutamiento deterministico AI-First (RF-03)
# Clasifica cada registro en:
# - VALIDO_DIRECTO
# - INVALIDO_DIRECTO
# - AMBIGUO_REQUIERE_IA
# Objetivo: evitar uso de LLM en casos no ambiguos reales

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
    CAMPOS_OBLIGATORIOS,
)

MODULO = "ROUTER"

CLASIFICACION_VALIDO_DIRECTO = "VALIDO_DIRECTO"
CLASIFICACION_INVALIDO_DIRECTO = "INVALIDO_DIRECTO"
CLASIFICACION_AMBIGUO_REQUIERE_IA = "AMBIGUO_REQUIERE_IA"


MESES_TEXTO = [
    "enero",
    "febrero",
    "marzo",
    "abril",
    "mayo",
    "junio",
    "julio",
    "agosto",
    "septiembre",
    "setiembre",
    "octubre",
    "noviembre",
    "diciembre",
    "jan",
    "feb",
    "mar",
    "apr",
    "may",
    "jun",
    "jul",
    "aug",
    "sep",
    "oct",
    "nov",
    "dec",
]

MESES_NUMEROS = {
    "enero": "01",
    "febrero": "02",
    "marzo": "03",
    "abril": "04",
    "mayo": "05",
    "junio": "06",
    "julio": "07",
    "agosto": "08",
    "septiembre": "09",
    "setiembre": "09",
    "octubre": "10",
    "noviembre": "11",
    "diciembre": "12",
    "jan": "01",
    "january": "01",
    "feb": "02",
    "february": "02",
    "mar": "03",
    "march": "03",
    "apr": "04",
    "april": "04",
    "may": "05",
    "jun": "06",
    "june": "06",
    "jul": "07",
    "july": "07",
    "aug": "08",
    "august": "08",
    "sep": "09",
    "september": "09",
    "oct": "10",
    "october": "10",
    "nov": "11",
    "november": "11",
    "dec": "12",
    "december": "12",
}

PALABRAS_MONTO_SEMANTICO = [
    "k",
    "m",
    "mil",
    "miles",
    "millon",
    "millon",
    "millones",
    "thousand",
    "million",
]


def _a_texto(x):
    # Convierte valores a string seguro
    if x == None:
        return ""
    return str(x)


def _contiene_letras(txt):
    # Detecta si el string tiene letras ASCII
    i = 0
    while i < len(txt):
        c = txt[i]
        if (c >= "a" and c <= "z") or (c >= "A" and c <= "Z"):
            return True
        i = i + 1
    return False


def _es_numero_entero(txt):
    # Valida entero con opcion de signo negativo
    if txt == "":
        return False
    if txt[0] == "-":
        rest = txt[1:]
        if rest == "":
            return False
        return rest.isdigit()
    return txt.isdigit()


def _tiene_palabra_meses(txt_lower):
    # Detecta meses escritos en texto
    i = 0
    while i < len(MESES_TEXTO):
        if MESES_TEXTO[i] in txt_lower:
            return True
        i = i + 1
    return False


def _tokenizar_texto(txt):
    # Tokeniza texto simple reemplazando separadores comunes
    t = txt
    t = t.replace(",", " ")
    t = t.replace(".", " ")
    t = t.replace("/", " ")
    t = t.replace("-", " ")
    t = t.replace("(", " ")
    t = t.replace(")", " ")
    t = t.replace(";", " ")
    t = t.replace(":", " ")
    ls = t.split()
    return ls


def _dos_digitos(n):
    # Convierte entero a 2 digitos
    if n < 10:
        return "0" + str(n)
    return str(n)


def _dividir_fecha_canonica(fecha):
    # Retorna (dia, mes, anio, formato) o ("", "", "", "")
    if len(fecha) != 10:
        return "", "", "", ""

    # DD/MM/YYYY
    if fecha[2] == "/" and fecha[5] == "/":
        dia = fecha[0:2]
        mes = fecha[3:5]
        anio = fecha[6:10]
        return dia, mes, anio, "DD/MM/YYYY"

    # YYYY-MM-DD
    if fecha[4] == "-" and fecha[7] == "-":
        anio = fecha[0:4]
        mes = fecha[5:7]
        dia = fecha[8:10]
        return dia, mes, anio, "YYYY-MM-DD"

    # DD-MM-YYYY
    if fecha[2] == "-" and fecha[5] == "-":
        dia = fecha[0:2]
        mes = fecha[3:5]
        anio = fecha[6:10]
        return dia, mes, anio, "DD-MM-YYYY"

    return "", "", "", ""


def _fecha_canonica_valida(fecha):
    # Retorna (es_valida, motivo_error)
    dia, mes, anio, formato = _dividir_fecha_canonica(fecha)
    if formato == "":
        return False, "no_canonica"

    if not dia.isdigit() or not mes.isdigit() or not anio.isdigit():
        return False, "componentes_no_numericos"

    n_dia = int(dia)
    n_mes = int(mes)
    n_anio = int(anio)

    if n_anio < 1900 or n_anio > 2100:
        return False, "anio_fuera_de_rango"
    if n_mes < 1 or n_mes > 12:
        return False, "mes_fuera_de_rango"
    if n_dia < 1 or n_dia > 31:
        return False, "dia_fuera_de_rango"

    return True, ""


def _resolver_fecha_numerica_con_separador(fecha, sep):
    # Resuelve formatos numericos no canonicos con separador
    # Retorna ("", "") si no aplica o (fecha_norm, "")
    txt = _a_texto(fecha).strip()
    if txt == "":
        return "", ""

    ls = txt.split(sep)
    if len(ls) != 3:
        return "", ""

    a = ls[0].strip()
    b = ls[1].strip()
    c = ls[2].strip()

    # YYYY/ MM / DD
    if len(a) == 4 and len(b) == 2 and len(c) == 2:
        if a.isdigit() and b.isdigit() and c.isdigit():
            fecha_norm = c + "/" + b + "/" + a
            ok, _ = _fecha_canonica_valida(fecha_norm)
            if ok:
                return fecha_norm, ""

    # DD / MM / YYYY
    if len(a) == 2 and len(b) == 2 and len(c) == 4:
        if a.isdigit() and b.isdigit() and c.isdigit():
            fecha_norm = a + "/" + b + "/" + c
            ok, _ = _fecha_canonica_valida(fecha_norm)
            if ok:
                return fecha_norm, ""

    return "", ""


def _resolver_fecha_textual(fecha):
    # Resuelve fechas textuales comunes
    txt = _a_texto(fecha).strip()
    if txt == "":
        return "", ""

    txt_lower = txt.lower()
    ls = _tokenizar_texto(txt_lower)
    if len(ls) < 3:
        return "", ""

    # Patron: DD de mes de YYYY / DD de mes del YYYY
    if len(ls) >= 4:
        if ls[0].isdigit() and ls[1] == "de":
            dia = int(ls[0])
            mes_txt = ls[2]
            anio = ls[len(ls) - 1]
            if mes_txt in MESES_NUMEROS.keys() and anio.isdigit() and len(anio) == 4:
                fecha_norm = _dos_digitos(dia) + "/" + MESES_NUMEROS[mes_txt] + "/" + anio
                ok, _ = _fecha_canonica_valida(fecha_norm)
                if ok:
                    return fecha_norm, ""

    # Patron: Mon DD YYYY (ej: Mar 15, 2025)
    if len(ls) >= 3:
        mes_txt = ls[0]
        dia_txt = ls[1]
        anio = ls[2]
        if mes_txt in MESES_NUMEROS.keys() and dia_txt.isdigit() and anio.isdigit():
            if len(anio) == 4:
                dia = int(dia_txt)
                fecha_norm = _dos_digitos(dia) + "/" + MESES_NUMEROS[mes_txt] + "/" + anio
                ok, _ = _fecha_canonica_valida(fecha_norm)
                if ok:
                    return fecha_norm, ""

    return "", ""


def _fecha_incompleta_semantica(fecha):
    # Detecta fechas semanticas sin dia explicito (invalidas directas)
    txt = _a_texto(fecha).strip().lower()
    if txt == "":
        return False

    if "trimestre" in txt or "q1" in txt or "q2" in txt or "q3" in txt or "q4" in txt:
        return True

    if _tiene_palabra_meses(txt):
        ls = _tokenizar_texto(txt)
        tiene_dia = False
        i = 0
        while i < len(ls):
            tok = ls[i]
            if tok.isdigit() and len(tok) <= 2:
                n = int(tok)
                if n >= 1 and n <= 31:
                    tiene_dia = True
            i = i + 1
        if not tiene_dia:
            return True

    return False


def resolver_fecha_deterministica(fecha):
    # Intenta resolver fecha no canonica con reglas deterministicas
    # Retorna (resuelta_bool, fecha_norm)
    txt = _a_texto(fecha).strip()
    if txt == "":
        return False, ""

    # Formatos con separador no canonico
    if "/" in txt:
        fecha_norm, _ = _resolver_fecha_numerica_con_separador(txt, "/")
        if fecha_norm != "":
            return True, fecha_norm

    if "." in txt:
        fecha_norm, _ = _resolver_fecha_numerica_con_separador(txt, ".")
        if fecha_norm != "":
            return True, fecha_norm

    # Fechas textuales
    fecha_norm, _ = _resolver_fecha_textual(txt)
    if fecha_norm != "":
        return True, fecha_norm

    return False, ""


def es_fecha_parseable(fecha):
    # Compatibilidad: True solo para fechas canonicas validas
    if fecha == None or fecha == "":
        return True
    txt = _a_texto(fecha).strip()
    ok, _ = _fecha_canonica_valida(txt)
    return ok


def analizar_fecha_preclasificacion(fecha):
    # Retorna (estado, motivo, fecha_resuelta)
    # estado: VALIDA / VALIDA_RESUELTA / INVALIDA / AMBIGUA / VACIA
    txt = _a_texto(fecha).strip()
    if txt == "":
        return "VACIA", "fecha vacia (R1)", ""

    ok, motivo = _fecha_canonica_valida(txt)
    if ok:
        return "VALIDA", "fecha canonica", ""

    # Fechas no canonicas pero resolubles por reglas deterministicas
    resuelta, fecha_norm = resolver_fecha_deterministica(txt)
    if resuelta:
        return "VALIDA_RESUELTA", "fecha no canonica resuelta por reglas", fecha_norm

    if motivo != "no_canonica":
        return "INVALIDA", "R2: formato fecha invalido: '" + txt + "'", ""

    if _fecha_incompleta_semantica(txt):
        return "INVALIDA", "R2: fecha incompleta o no determinable: '" + txt + "'", ""

    txt_lower = txt.lower()
    if _contiene_letras(txt) or _tiene_palabra_meses(txt_lower):
        return "AMBIGUA", "fecha en lenguaje natural o semantica", ""

    if "." in txt or "/" in txt or "-" in txt:
        return "AMBIGUA", "fecha no canonica pero interpretable", ""

    return "AMBIGUA", "fecha no canonica", ""


def es_moneda_canonica(moneda):
    # Verifica si la moneda es canonica o resoluble por sinonimos
    # Retorna (es_canonica, valor_canonico)
    if moneda == None or moneda == "":
        return True, ""

    moneda_upper = _a_texto(moneda).strip().upper()

    if moneda_upper in MONEDAS_SOPORTADAS:
        return True, moneda_upper

    moneda_lower = _a_texto(moneda).strip().lower()
    if moneda_lower in SINONIMOS_MONEDA.keys():
        return True, SINONIMOS_MONEDA[moneda_lower]

    return False, _a_texto(moneda)


def es_moneda_invalida_directa(moneda):
    # Detecta monedas no ambiguas que deben invalidarse sin IA
    txt = _a_texto(moneda).strip()
    if txt == "":
        return False

    txt_upper = txt.upper()
    if len(txt_upper) == 3 and txt_upper.isalpha():
        if txt_upper not in MONEDAS_SOPORTADAS:
            return True

    txt_lower = txt.lower()
    if txt_lower == "moneda local" or txt_lower == "divisa extranjera":
        return True

    return False


def es_tipo_producto_canonico(tipo):
    # Verifica si el tipo de producto es canonico o resoluble por sinonimos
    # Retorna (es_canonico, valor_canonico)
    if tipo == None or tipo == "":
        return True, ""

    tipo_upper = _a_texto(tipo).strip().upper()

    if tipo_upper in TIPOS_PRODUCTO_CANONICOS:
        return True, tipo_upper

    tipo_lower = _a_texto(tipo).strip().lower()
    if tipo_lower in SINONIMOS_TIPO_PRODUCTO.keys():
        return True, SINONIMOS_TIPO_PRODUCTO[tipo_lower]

    return False, _a_texto(tipo)


def es_pais_canonico(pais):
    # Verifica si el pais es canonico o resoluble por sinonimos
    # Retorna (es_canonico, valor_canonico)
    if pais == None or pais == "":
        return True, ""

    pais_stripped = _a_texto(pais).strip()

    i = 0
    while i < len(PAISES_CANONICOS):
        p = PAISES_CANONICOS[i]
        if pais_stripped.lower() == p.lower():
            return True, p
        i = i + 1

    pais_lower = pais_stripped.lower()
    if pais_lower in SINONIMOS_PAIS.keys():
        return True, SINONIMOS_PAIS[pais_lower]

    return False, _a_texto(pais)


def es_monto_numerico(monto):
    # Compatibilidad: valida si monto es entero parseable
    if monto == None or monto == "":
        return True

    val = _a_texto(monto).strip()
    if val == "":
        return True

    return _es_numero_entero(val)


def es_monto_potencialmente_semantico(monto):
    # Detecta montos no canonicos pero potencialmente inferibles por IA
    txt = _a_texto(monto).strip()
    if txt == "":
        return False

    txt_lower = txt.lower()

    if "$" in txt or "," in txt or "." in txt:
        return True

    i = 0
    while i < len(PALABRAS_MONTO_SEMANTICO):
        if PALABRAS_MONTO_SEMANTICO[i] in txt_lower:
            return True
        i = i + 1

    tiene_digitos = False
    j = 0
    while j < len(txt):
        c = txt[j]
        if c >= "0" and c <= "9":
            tiene_digitos = True
            break
        j = j + 1

    if tiene_digitos and _contiene_letras(txt):
        return True

    return False


def clasificar_registro(reg, llm_provider=None, cache_embeddings=None):
    # Clasifica un registro en 3 estados deterministas
    # Retorna diccionario con trazabilidad y resoluciones

    motivos_amb = []
    motivos_inv = []
    reglas = []
    campos_amb = []
    resolucion = {}

    # 1) R1 directo: campos obligatorios vacios
    i = 0
    while i < len(CAMPOS_OBLIGATORIOS):
        campo = CAMPOS_OBLIGATORIOS[i]
        valor = ""
        if campo in reg.keys():
            valor = _a_texto(reg[campo]).strip()
        if valor == "":
            motivos_inv.append("R1: campo " + campo + " vacio")
            if "R1" not in reglas:
                reglas.append("R1")
        i = i + 1

    if len(motivos_inv) > 0:
        return {
            "clasificacion": CLASIFICACION_INVALIDO_DIRECTO,
            "es_ambiguo": False,
            "motivos_ambiguedad": [],
            "motivos_invalidacion": motivos_inv,
            "resolucion_sinonimos": resolucion,
            "resolucion_embeddings": {},
            "campos_ambiguos": [],
            "reglas_afectadas": reglas,
            "motivo_clasificacion": "Fallo deterministico de reglas obligatorias",
        }

    # 2) Fecha
    fecha = ""
    if "fecha_solicitud" in reg.keys():
        fecha = reg["fecha_solicitud"]
    estado_fecha, motivo_fecha, fecha_resuelta = analizar_fecha_preclasificacion(fecha)
    if estado_fecha == "INVALIDA":
        motivos_inv.append(motivo_fecha)
        if "R2" not in reglas:
            reglas.append("R2")
    elif estado_fecha == "VALIDA_RESUELTA":
        resolucion["fecha_solicitud"] = fecha_resuelta
    elif estado_fecha == "AMBIGUA":
        motivos_amb.append("fecha ambigua: '" + _a_texto(fecha) + "'")
        campos_amb.append("fecha_solicitud")
        if "R2" not in reglas:
            reglas.append("R2")

    # 3) Moneda
    moneda = ""
    if "moneda" in reg.keys():
        moneda = reg["moneda"]
    es_canon_moneda, moneda_resuelta = es_moneda_canonica(moneda)
    if es_canon_moneda:
        if moneda_resuelta != "" and moneda_resuelta != _a_texto(moneda).strip().upper():
            resolucion["moneda"] = moneda_resuelta
    else:
        if es_moneda_invalida_directa(moneda):
            motivos_inv.append("R2: moneda no soportada: " + _a_texto(moneda).strip().upper())
            if "R2" not in reglas:
                reglas.append("R2")
        else:
            motivos_amb.append("moneda no canonica: '" + _a_texto(moneda) + "'")
            campos_amb.append("moneda")
            if "R2" not in reglas:
                reglas.append("R2")

    # 4) Tipo producto
    tipo = ""
    if "tipo_producto" in reg.keys():
        tipo = reg["tipo_producto"]
    es_canon_tipo, tipo_resuelto = es_tipo_producto_canonico(tipo)
    if es_canon_tipo:
        if tipo_resuelto != "" and tipo_resuelto != _a_texto(tipo).strip().upper():
            resolucion["tipo_producto"] = tipo_resuelto
    else:
        motivos_amb.append("tipo producto no canonico: '" + _a_texto(tipo) + "'")
        campos_amb.append("tipo_producto")

    # 5) Pais
    pais = ""
    if "pais" in reg.keys():
        pais = reg["pais"]
    es_canon_pais, pais_resuelto = es_pais_canonico(pais)
    if es_canon_pais:
        if pais_resuelto != "" and pais_resuelto != _a_texto(pais).strip():
            resolucion["pais"] = pais_resuelto
    else:
        motivos_amb.append("pais no canonico: '" + _a_texto(pais) + "'")
        campos_amb.append("pais")

    # 6) Monto
    monto = ""
    if "monto_o_limite" in reg.keys():
        monto = reg["monto_o_limite"]
    monto_txt = _a_texto(monto).strip()
    if _es_numero_entero(monto_txt):
        n_monto = int(monto_txt)
        if n_monto <= 0 or n_monto > 999999999:
            motivos_inv.append(
                "R3: monto fuera de rango: " + str(n_monto) + " (debe ser >0 y <=999999999)"
            )
            if "R3" not in reglas:
                reglas.append("R3")
    else:
        if es_monto_potencialmente_semantico(monto_txt):
            motivos_amb.append("monto parcialmente interpretable: '" + monto_txt + "'")
            campos_amb.append("monto_o_limite")
            if "R3" not in reglas:
                reglas.append("R3")
        else:
            motivos_inv.append("R3: monto no numerico: '" + monto_txt + "'")
            if "R3" not in reglas:
                reglas.append("R3")

    # Resultado final
    if len(motivos_inv) > 0:
        return {
            "clasificacion": CLASIFICACION_INVALIDO_DIRECTO,
            "es_ambiguo": False,
            "motivos_ambiguedad": [],
            "motivos_invalidacion": motivos_inv,
            "resolucion_sinonimos": resolucion,
            "resolucion_embeddings": {},
            "campos_ambiguos": [],
            "reglas_afectadas": reglas,
            "motivo_clasificacion": "Fallo deterministico de reglas R2/R3",
        }

    if len(motivos_amb) > 0:
        return {
            "clasificacion": CLASIFICACION_AMBIGUO_REQUIERE_IA,
            "es_ambiguo": True,
            "motivos_ambiguedad": motivos_amb,
            "motivos_invalidacion": [],
            "resolucion_sinonimos": resolucion,
            "resolucion_embeddings": {},
            "campos_ambiguos": campos_amb,
            "reglas_afectadas": reglas,
            "motivo_clasificacion": "Caso ambiguo requiere validacion semantica IA",
        }

    return {
        "clasificacion": CLASIFICACION_VALIDO_DIRECTO,
        "es_ambiguo": False,
        "motivos_ambiguedad": [],
        "motivos_invalidacion": [],
        "resolucion_sinonimos": resolucion,
        "resolucion_embeddings": {},
        "campos_ambiguos": [],
        "reglas_afectadas": [],
        "motivo_clasificacion": "Registro deterministico resoluble por reglas",
    }


def aplicar_resolucion_sinonimos(reg, resolucion):
    # Aplica resoluciones deterministicas al registro
    for campo in resolucion.keys():
        reg[campo] = resolucion[campo]
    return reg


def _agregar_traza_preclasificacion(reg, clasificacion, paso_llm):
    # Guarda trazabilidad de clasificacion por registro
    traza = {
        "clasificacion": clasificacion.get("clasificacion", ""),
        "motivo_clasificacion": clasificacion.get("motivo_clasificacion", ""),
        "motivos_ambiguedad": clasificacion.get("motivos_ambiguedad", []),
        "motivos_invalidacion": clasificacion.get("motivos_invalidacion", []),
        "reglas_afectadas": clasificacion.get("reglas_afectadas", []),
        "paso_llm": paso_llm,
        "ronda_llm": 0,
        "batch_llm": 0,
    }
    reg["_traza_ai"] = traza


def enrutar_registros(registros, llm_provider=None):
    # Clasifica y enruta registros en rule_path y llm_path
    # Retorna (regla_path, llm_path, estadisticas)

    regla_path = []
    llm_path = []

    total_sinonimos_resueltos = 0
    total_embeddings_resueltos = 0
    total_validos_directos = 0
    total_invalidos_directos = 0
    total_ambiguos = 0

    for reg in registros:
        clasificacion = clasificar_registro(reg, llm_provider, None)

        # Aplicar sinonimos deterministas antes de enrutar
        if len(clasificacion["resolucion_sinonimos"].keys()) > 0:
            reg = aplicar_resolucion_sinonimos(reg, clasificacion["resolucion_sinonimos"])
            total_sinonimos_resueltos = total_sinonimos_resueltos + 1

        clase = clasificacion.get("clasificacion", "")

        if clase == CLASIFICACION_AMBIGUO_REQUIERE_IA:
            reg["_clasificacion"] = clasificacion
            reg["origen_procesamiento"] = "llm_path"
            _agregar_traza_preclasificacion(reg, clasificacion, True)
            llm_path.append(reg)
            total_ambiguos = total_ambiguos + 1
        else:
            reg["_clasificacion"] = clasificacion
            reg["origen_procesamiento"] = "rule_path"
            _agregar_traza_preclasificacion(reg, clasificacion, False)
            regla_path.append(reg)
            if clase == CLASIFICACION_VALIDO_DIRECTO:
                total_validos_directos = total_validos_directos + 1
            elif clase == CLASIFICACION_INVALIDO_DIRECTO:
                total_invalidos_directos = total_invalidos_directos + 1

    estadisticas = {
        "total": len(registros),
        "regla_path": len(regla_path),
        "llm_path": len(llm_path),
        "sinonimos_resueltos": total_sinonimos_resueltos,
        "embeddings_resueltos": total_embeddings_resueltos,
        "porcentaje_llm": 0.0,
        "validos_directos": total_validos_directos,
        "invalidos_directos": total_invalidos_directos,
        "ambiguous_detected": total_ambiguos,
        "ambiguous_sent_llm": len(llm_path),
    }

    if len(registros) > 0:
        estadisticas["porcentaje_llm"] = round((len(llm_path) * 100.0) / len(registros), 1)

    return regla_path, llm_path, estadisticas
