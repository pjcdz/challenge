# validador.py - Validacion de reglas de elegibilidad (RF-03)
# Aplica 3 reglas de validacion a cada registro

import logger

MODULO = "VALIDADOR"

# Monedas soportadas
MONEDAS_SOPORTADAS = ["ARS", "USD", "EUR"]

# Campos obligatorios para R1
CAMPOS_OBLIGATORIOS = [
    "id_solicitud",
    "fecha_solicitud",
    "tipo_producto",
    "id_cliente",
    "monto_o_limite",
    "moneda",
    "pais",
]


def validar_r1(reg):
    # R1: Campos obligatorios presentes y no vacios
    # Retorna lista de motivos de falla (vacia si pasa)
    motivos = []
    for campo in CAMPOS_OBLIGATORIOS:
        if campo not in reg.keys():
            motivos.append("campo " + campo + " no existe")
        elif reg[campo] == None or reg[campo].strip() == "":
            motivos.append("campo " + campo + " vacio")
    return motivos


def validar_r2(reg):
    # R2: Formato de fecha valido y moneda en lista soportada
    # Retorna lista de motivos de falla (vacia si pasa)
    motivos = []

    # Validar fecha
    if "fecha_solicitud" in reg.keys():
        fecha = reg["fecha_solicitud"]
    else:
        fecha = ""
    if fecha != "":
        # Despues de normalizacion deberia estar en DD/MM/YYYY
        es_valida = True
        if len(fecha) != 10:
            es_valida = False
        elif fecha[2] != "/" or fecha[5] != "/":
            es_valida = False
        else:
            dia = fecha[0:2]
            mes = fecha[3:5]
            anio = fecha[6:10]
            if not dia.isdigit() or not mes.isdigit() or not anio.isdigit():
                es_valida = False
            elif int(dia) < 1 or int(dia) > 31:
                es_valida = False
            elif int(mes) < 1 or int(mes) > 12:
                es_valida = False
        if not es_valida:
            motivos.append("formato de fecha invalido: '" + fecha + "'")

    # Validar moneda
    if "moneda" in reg.keys():
        moneda = reg["moneda"]
    else:
        moneda = ""
    if moneda != "" and moneda not in MONEDAS_SOPORTADAS:
        motivos.append("moneda no soportada: " + moneda)

    return motivos


def validar_r3(reg):
    # R3: Rango de monto valido (> 0 y <= 999999999)
    # Retorna lista de motivos de falla (vacia si pasa)
    motivos = []

    if "monto_o_limite" in reg.keys():
        monto_str = reg["monto_o_limite"]
    else:
        monto_str = ""
    if monto_str != "":
        # Intentar convertir a numero
        es_numero = True
        val = monto_str.strip()
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

        if not es_numero:
            motivos.append("monto no es numerico: " + monto_str)
        else:
            monto = int(val)
            if monto <= 0:
                motivos.append(
                    "monto fuera de rango: " + str(monto) + " (debe ser > 0)"
                )
            elif monto > 999999999:
                motivos.append(
                    "monto fuera de rango: " + str(monto) + " (debe ser <= 999999999)"
                )

    return motivos


def validar_registros(registros):
    # Aplica las 3 reglas de validacion a cada registro
    # Agrega campos: estado (VALIDO/INVALIDO), motivos_falla, detalle_reglas
    # Retorna la lista de registros con los campos agregados

    total_validos = 0
    total_invalidos = 0

    for reg in registros:
        if "id_solicitud" in reg.keys():
            id_sol = reg["id_solicitud"]
        else:
            id_sol = "DESCONOCIDO"
        motivos_todos = []
        detalle = {}

        # Aplicar R1
        fallas_r1 = validar_r1(reg)
        detalle["R1"] = fallas_r1
        for m in fallas_r1:
            motivos_todos.append("R1: " + m)

        # Aplicar R2
        fallas_r2 = validar_r2(reg)
        detalle["R2"] = fallas_r2
        for m in fallas_r2:
            motivos_todos.append("R2: " + m)

        # Aplicar R3
        fallas_r3 = validar_r3(reg)
        detalle["R3"] = fallas_r3
        for m in fallas_r3:
            motivos_todos.append("R3: " + m)

        # Determinar estado
        if len(motivos_todos) == 0:
            reg["estado"] = "VALIDO"
            reg["motivos_falla"] = ""
            total_validos += 1
        else:
            reg["estado"] = "INVALIDO"
            # Unir motivos con "; " usando concatenacion
            motivos_str = ""
            idx = 0
            for m in motivos_todos:
                if idx > 0:
                    motivos_str = motivos_str + "; "
                motivos_str = motivos_str + m
                idx += 1
            reg["motivos_falla"] = motivos_str
            total_invalidos += 1
            logger.warn(
                MODULO, "Registro " + id_sol + " invalido: " + reg["motivos_falla"]
            )

        # Guardar detalle para el reporte de calidad
        reg["_detalle_reglas"] = detalle

    logger.info(
        MODULO,
        "Validacion completada - "
        + str(total_validos)
        + " validos, "
        + str(total_invalidos)
        + " invalidos",
    )
    return registros
