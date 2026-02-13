# normalizador.py - Normalizacion de campos (RF-02)
# Normaliza fechas, trimming, mayusculas/minusculas y campo calculado

import logger

MODULO = "NORMALIZADOR"

# Formatos de fecha que acepta el sistema
# DD/MM/YYYY, YYYY-MM-DD, DD-MM-YYYY


def detectar_formato_fecha(fecha):
    # Detecta el formato de una fecha y retorna sus partes (dia, mes, anio)
    # Retorna None si no se puede parsear
    fecha = fecha.strip()

    # Formato YYYY-MM-DD
    if len(fecha) == 10 and fecha[4] == "-" and fecha[7] == "-":
        anio = fecha[0:4]
        mes = fecha[5:7]
        dia = fecha[8:10]
        return dia, mes, anio

    # Formato DD/MM/YYYY
    if len(fecha) == 10 and fecha[2] == "/" and fecha[5] == "/":
        dia = fecha[0:2]
        mes = fecha[3:5]
        anio = fecha[6:10]
        return dia, mes, anio

    # Formato DD-MM-YYYY
    if len(fecha) == 10 and fecha[2] == "-" and fecha[5] == "-":
        dia = fecha[0:2]
        mes = fecha[3:5]
        anio = fecha[6:10]
        return dia, mes, anio

    return None


def normalizar_fecha(fecha, id_sol):
    # Convierte una fecha a formato DD/MM/YYYY
    # Retorna la fecha normalizada o la original si no se puede convertir
    partes = detectar_formato_fecha(fecha)
    if partes == None:
        logger.warn(
            MODULO,
            "Formato de fecha no reconocido en registro "
            + id_sol
            + ": '"
            + fecha
            + "'",
        )
        return fecha

    dia = partes[0]
    mes = partes[1]
    anio = partes[2]

    # Validar rangos basicos
    es_valida = True
    if not dia.isdigit() or not mes.isdigit() or not anio.isdigit():
        es_valida = False
    elif int(dia) < 1 or int(dia) > 31:
        es_valida = False
    elif int(mes) < 1 or int(mes) > 12:
        es_valida = False

    if not es_valida:
        logger.warn(
            MODULO,
            "Fecha con valores invalidos en registro " + id_sol + ": '" + fecha + "'",
        )
        return fecha

    resultado = dia + "/" + mes + "/" + anio

    # Loguear si la fecha fue convertida (estaba en otro formato)
    if resultado != fecha.strip():
        logger.warn(
            MODULO,
            "Fecha convertida en registro "
            + id_sol
            + ": '"
            + fecha.strip()
            + "' -> '"
            + resultado
            + "'",
        )

    return resultado


def calcular_categoria_riesgo(monto):
    # Deriva la categoria de riesgo segun el monto
    # BAJO: <= 50000, MEDIO: > 50000 y <= 500000, ALTO: > 500000
    cat = "BAJO"
    if monto > 500000:
        cat = "ALTO"
    elif monto > 50000:
        cat = "MEDIO"
    return cat


def normalizar_registros(registros):
    # Normaliza todos los campos de cada registro
    # Retorna la lista de registros normalizados
    resultado = []

    for reg in registros:
        d = {}

        # Copiar todos los campos con trimming
        for campo in reg.keys():
            valor = reg[campo]
            if valor != None:
                valor = valor.strip()
            d[campo] = valor

        # Obtener id para logs
        if "id_solicitud" in d.keys():
            id_sol = d["id_solicitud"]
        else:
            id_sol = "DESCONOCIDO"

        # Normalizar fecha
        if "fecha_solicitud" in d.keys() and d["fecha_solicitud"] != "":
            d["fecha_solicitud"] = normalizar_fecha(d["fecha_solicitud"], id_sol)

        # tipo_producto y moneda en MAYUSCULAS
        if "tipo_producto" in d.keys() and d["tipo_producto"] != "":
            d["tipo_producto"] = d["tipo_producto"].upper()

        if "moneda" in d.keys() and d["moneda"] != "":
            d["moneda"] = d["moneda"].upper()

        # pais con primera letra mayuscula (Title Case)
        if "pais" in d.keys() and d["pais"] != "":
            d["pais"] = d["pais"].strip()
            # Title case manual
            palabras = d["pais"].split(" ")
            ls_pal = []
            for p in palabras:
                if len(p) > 0:
                    pal = p[0].upper() + p[1:].lower()
                    ls_pal.append(pal)
            # Unir palabras con espacio usando concatenacion
            pais_final = ""
            idx = 0
            for p in ls_pal:
                if idx > 0:
                    pais_final = pais_final + " "
                pais_final = pais_final + p
                idx += 1
            d["pais"] = pais_final

        # Campo calculado: categoria_riesgo
        d["categoria_riesgo"] = ""
        if "monto_o_limite" in d.keys() and d["monto_o_limite"] != "":
            es_numero = True
            val = d["monto_o_limite"]
            # Verificar si es numero (puede ser negativo)
            if val == "":
                es_numero = False
            elif val[0] == "-":
                rest = val[1:]
                if rest == "" or not rest.isdigit():
                    es_numero = False
            else:
                rest = val
                if not rest.isdigit():
                    es_numero = False
            if es_numero:
                monto = int(val)
                d["categoria_riesgo"] = calcular_categoria_riesgo(monto)

        resultado.append(d)

    logger.info(
        MODULO,
        "Normalizacion completada - " + str(len(resultado)) + " registros normalizados",
    )
    return resultado
