# data_generator.py - Generador de datos sinteticos para benchmark (RF-06 AI-First)
# Genera datasets con registros limpios, sucios y ambiguos + ground truth
# Parametros: --cantidad, --seed, --ratio-limpio, --ratio-sucio, --ratio-ambiguo, --formato, --perfil

import os
import sys
import json
import random

MODULO = "DATA_GENERATOR"

# Ruta base
DIR_RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIR_DATASETS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "datasets")

# Agregar root al path para imports de ai_first_system
if DIR_RAIZ not in sys.path:
    sys.path.insert(0, DIR_RAIZ)

# Valores canonicos para generacion
TIPOS_PRODUCTO = ["CUENTA", "TARJETA", "SERVICIO", "PRESTAMO", "SEGURO"]
MONEDAS = ["ARS", "USD", "EUR"]
PAISES = [
    "Argentina",
    "Brasil",
    "Chile",
    "Colombia",
    "Mexico",
    "Uruguay",
    "Paraguay",
    "Peru",
]

# Variantes sucias (spacing, casing, formatos distintos)
TIPOS_SUCIOS = ["  CUENTA ", "tarjeta", " Servicio", "PRESTAMO  ", "seguro"]
MONEDAS_SUCIAS = [" ARS", "usd ", "Eur", " USD ", "ars"]
PAISES_SUCIOS = [
    "  Argentina",
    "brasil",
    " CHILE ",
    "colombia  ",
    "MEXICO",
    "  uruguay",
]

# Variantes ambiguas (sinonimos, texto libre)
TIPOS_AMBIGUOS = [
    "cta",
    "cta ahorro",
    "tarj",
    "plastico",
    "serv",
    "cuenta corriente",
    "tarjeta credito",
    "prestamo personal",
]
MONEDAS_AMBIGUAS = [
    "pesos",
    "dolares",
    "euros",
    "pesos argentinos",
    "dolar",
    "moneda local",
    "divisa extranjera",
]
PAISES_AMBIGUOS = [
    "arg",
    "bra",
    "cl",
    "col",
    "mx",
    "uy",
    "republica argentina",
    "estados unidos mexicanos",
]

# Fechas limpias (DD/MM/YYYY)
FECHAS_LIMPIAS = [
    "01/01/2025",
    "15/03/2025",
    "28/06/2025",
    "10/09/2025",
    "22/11/2025",
    "05/04/2025",
    "18/07/2025",
    "30/12/2025",
]

# Fechas en otros formatos validos (YYYY-MM-DD, DD-MM-YYYY)
FECHAS_SUCIAS = [
    "2025-01-15",
    "2025-03-20",
    "2025-06-10",
    "2025-09-05",
    "15-03-2025",
    "20-06-2025",
    "10-09-2025",
    "05-12-2025",
]

# Fechas ambiguas (texto libre, formatos raros)
FECHAS_AMBIGUAS = [
    "marzo 2025",
    "15 de marzo del 2025",
    "Mar 15, 2025",
    "2025/03/15",
    "15.03.2025",
    "Q1 2025",
    "primer trimestre",
]

# Montos invalidos para registros que deben fallar R3
MONTOS_INVALIDOS = ["-500", "0", "1000000000", "-1", "99999999999"]

# Variantes ambiguas realistas (deberian requerir IA semantica)
TIPOS_AMBIGUOS_REALISTAS = [
    "cuenta sueldo",
    "tarjeta gold",
    "servicio hogar",
    "prestamo nomina",
    "seguro vida",
    "producto premium",
]

MONEDAS_AMBIGUAS_REALISTAS = [
    "u$s",
    "usd oficial",
    "dolar blue",
    "euros billete",
    "pesos arg",
]

PAISES_AMBIGUOS_REALISTAS = [
    "rep argentina",
    "mexico df",
    "brasilia brasil",
    "republica del paraguay",
    "santiago chile",
]

FECHAS_AMBIGUAS_REALISTAS = [
    "5 marzo 2026",
    "11 abril 2025",
    "2 julio 2025",
    "8 octubre 2025",
    "17 diciembre 2025",
]

MONTOS_AMBIGUOS_REALISTAS = [
    "50 mil",
    "$25000",
    "1.2 millones",
    "usd 1200",
    "20k",
]


def obtener_catalogos_ambiguos(perfil):
    # Retorna catalogos de datos ambiguos segun perfil de benchmark
    # perfil soportado: base, realista
    p = "base"
    if perfil != None:
        p = str(perfil).strip().lower()

    d = {}
    if p == "realista":
        d["tipos"] = TIPOS_AMBIGUOS_REALISTAS
        d["monedas"] = MONEDAS_AMBIGUAS_REALISTAS
        d["paises"] = PAISES_AMBIGUOS_REALISTAS
        d["fechas"] = FECHAS_AMBIGUAS_REALISTAS
        d["montos"] = MONTOS_AMBIGUOS_REALISTAS
        d["usar_monto_semantico"] = True
        d["perfil"] = "realista"
    else:
        d["tipos"] = TIPOS_AMBIGUOS
        d["monedas"] = MONEDAS_AMBIGUAS
        d["paises"] = PAISES_AMBIGUOS
        d["fechas"] = FECHAS_AMBIGUAS
        d["montos"] = []
        d["usar_monto_semantico"] = False
        d["perfil"] = "base"

    return d


def generar_id_solicitud(numero):
    # Genera un ID de solicitud con formato SOL-XXXX
    num_str = str(numero)
    # Pad manual a 4 digitos
    while len(num_str) < 4:
        num_str = "0" + num_str
    return "SYNTH-" + num_str


def generar_id_cliente(numero):
    # Genera un ID de cliente con formato CLI-XXX
    num_str = str(numero)
    while len(num_str) < 3:
        num_str = "0" + num_str
    return "CLI-" + num_str


def generar_monto_valido():
    # Genera un monto aleatorio valido (> 0 y <= 999999999)
    opciones = [
        random.randint(1000, 50000),
        random.randint(50001, 500000),
        random.randint(500001, 999999999),
    ]
    return str(opciones[random.randint(0, 2)])


def generar_registro_limpio(num_sol, num_cli):
    # Genera un registro completamente limpio y valido
    reg = {}
    reg["id_solicitud"] = generar_id_solicitud(num_sol)
    reg["fecha_solicitud"] = FECHAS_LIMPIAS[random.randint(0, len(FECHAS_LIMPIAS) - 1)]
    reg["tipo_producto"] = TIPOS_PRODUCTO[random.randint(0, len(TIPOS_PRODUCTO) - 1)]
    reg["id_cliente"] = generar_id_cliente(num_cli)
    reg["monto_o_limite"] = generar_monto_valido()
    reg["moneda"] = MONEDAS[random.randint(0, len(MONEDAS) - 1)]
    reg["pais"] = PAISES[random.randint(0, len(PAISES) - 1)]
    reg["flag_prioritario"] = ["S", "N"][random.randint(0, 1)]
    reg["flag_digital"] = ["S", "N"][random.randint(0, 1)]

    # Ground truth: todos los campos ya estan normalizados, estado VALIDO
    gt = {}
    gt["id_solicitud"] = reg["id_solicitud"]
    gt["estado_esperado"] = "VALIDO"
    gt["tipo"] = "limpio"
    gt["origen_esperado"] = "rule_path"
    gt["motivos_falla_esperados"] = ""
    gt["tipo_producto_normalizado"] = reg["tipo_producto"]
    gt["moneda_normalizada"] = reg["moneda"]
    gt["pais_normalizado"] = reg["pais"]

    return reg, gt


def generar_registro_sucio(num_sol, num_cli):
    # Genera un registro con problemas de formato (spacing, casing, fecha otro formato)
    # Pero que DEBERIA ser resuelto por normalizacion deterministica
    reg = {}
    reg["id_solicitud"] = generar_id_solicitud(num_sol)
    reg["fecha_solicitud"] = FECHAS_SUCIAS[random.randint(0, len(FECHAS_SUCIAS) - 1)]
    tipo_sucio = TIPOS_SUCIOS[random.randint(0, len(TIPOS_SUCIOS) - 1)]
    reg["tipo_producto"] = tipo_sucio
    reg["id_cliente"] = generar_id_cliente(num_cli)
    reg["monto_o_limite"] = generar_monto_valido()
    moneda_sucia = MONEDAS_SUCIAS[random.randint(0, len(MONEDAS_SUCIAS) - 1)]
    reg["moneda"] = moneda_sucia
    pais_sucio = PAISES_SUCIOS[random.randint(0, len(PAISES_SUCIOS) - 1)]
    reg["pais"] = pais_sucio
    reg["flag_prioritario"] = ["S", "N"][random.randint(0, 1)]
    reg["flag_digital"] = ["S", "N"][random.randint(0, 1)]

    # Decidir si ademas tiene un error de validacion (50% de probabilidad)
    tiene_error = random.randint(0, 1) == 1
    motivos_esperados = ""
    estado_esperado = "VALIDO"

    if tiene_error:
        tipo_error = random.randint(1, 4)
        if tipo_error == 1:
            # Campo obligatorio vacio
            campo_vacio = ["tipo_producto", "moneda", "pais", "id_cliente"][
                random.randint(0, 3)
            ]
            reg[campo_vacio] = ""
            estado_esperado = "INVALIDO"
            motivos_esperados = "R1: campo " + campo_vacio + " vacio"
        elif tipo_error == 2:
            # Moneda invalida
            reg["moneda"] = "GBP"
            moneda_sucia = "GBP"
            estado_esperado = "INVALIDO"
            motivos_esperados = "R2: moneda no soportada: GBP"
        elif tipo_error == 3:
            # Monto invalido
            reg["monto_o_limite"] = MONTOS_INVALIDOS[
                random.randint(0, len(MONTOS_INVALIDOS) - 1)
            ]
            estado_esperado = "INVALIDO"
            motivos_esperados = "R3: monto fuera de rango"
        elif tipo_error == 4:
            # Fecha invalida
            reg["fecha_solicitud"] = "32/13/2025"
            estado_esperado = "INVALIDO"
            motivos_esperados = "R2: formato de fecha invalido"

    # Ground truth
    gt = {}
    gt["id_solicitud"] = reg["id_solicitud"]
    gt["estado_esperado"] = estado_esperado
    gt["tipo"] = "sucio"
    gt["origen_esperado"] = "rule_path"
    gt["motivos_falla_esperados"] = motivos_esperados
    # Normalizar para ground truth
    gt["tipo_producto_normalizado"] = tipo_sucio.strip().upper()
    gt["moneda_normalizada"] = moneda_sucia.strip().upper()
    # Pais en Title Case
    pais_stripped = pais_sucio.strip()
    palabras = pais_stripped.split(" ")
    ls_pal = []
    for p in palabras:
        if len(p) > 0:
            pal = p[0].upper() + p[1:].lower()
            ls_pal.append(pal)
    pais_final = ""
    idx = 0
    for p in ls_pal:
        if idx > 0:
            pais_final = pais_final + " "
        pais_final = pais_final + p
        idx = idx + 1
    gt["pais_normalizado"] = pais_final

    return reg, gt


def generar_registro_ambiguo(num_sol, num_cli, perfil="base"):
    # Genera un registro con datos ambiguos semanticamente
    # Que NECESITA LLM para resolver (sinonimos, texto libre, etc.)
    catalogos = obtener_catalogos_ambiguos(perfil)
    tipos_amb = catalogos["tipos"]
    monedas_amb = catalogos["monedas"]
    paises_amb = catalogos["paises"]
    fechas_amb = catalogos["fechas"]
    montos_amb = catalogos["montos"]
    usar_monto_semantico = catalogos["usar_monto_semantico"]

    reg = {}
    reg["id_solicitud"] = generar_id_solicitud(num_sol)

    # Elegir que campos son ambiguos (al menos 1)
    campos_para_ambiguar = []
    # Siempre al menos uno ambiguo
    opcion = random.randint(0, 3)
    if opcion == 0:
        campos_para_ambiguar.append("tipo_producto")
    elif opcion == 1:
        campos_para_ambiguar.append("moneda")
    elif opcion == 2:
        campos_para_ambiguar.append("pais")
    elif opcion == 3:
        campos_para_ambiguar.append("fecha_solicitud")

    # Posibilidad de agregar mas campos ambiguos (40%)
    if random.randint(1, 10) <= 4:
        extras = ["tipo_producto", "moneda", "pais", "fecha_solicitud"]
        if usar_monto_semantico:
            extras.append("monto_o_limite")
        extra = extras[random.randint(0, 3)]
        if len(extras) == 5:
            extra = extras[random.randint(0, 4)]
        if extra not in campos_para_ambiguar:
            campos_para_ambiguar.append(extra)

    # Segunda ambiguedad adicional para perfil realista (25%)
    if usar_monto_semantico and random.randint(1, 100) <= 25:
        extras2 = ["tipo_producto", "moneda", "pais", "fecha_solicitud", "monto_o_limite"]
        extra2 = extras2[random.randint(0, 4)]
        if extra2 not in campos_para_ambiguar:
            campos_para_ambiguar.append(extra2)

    # Fecha
    if "fecha_solicitud" in campos_para_ambiguar:
        reg["fecha_solicitud"] = fechas_amb[random.randint(0, len(fechas_amb) - 1)]
    else:
        reg["fecha_solicitud"] = FECHAS_LIMPIAS[
            random.randint(0, len(FECHAS_LIMPIAS) - 1)
        ]

    # Tipo producto
    tipo_ambiguo = ""
    if "tipo_producto" in campos_para_ambiguar:
        tipo_ambiguo = tipos_amb[random.randint(0, len(tipos_amb) - 1)]
        reg["tipo_producto"] = tipo_ambiguo
    else:
        reg["tipo_producto"] = TIPOS_PRODUCTO[
            random.randint(0, len(TIPOS_PRODUCTO) - 1)
        ]

    reg["id_cliente"] = generar_id_cliente(num_cli)

    monto_ambiguo = ""
    if usar_monto_semantico and "monto_o_limite" in campos_para_ambiguar:
        monto_ambiguo = montos_amb[random.randint(0, len(montos_amb) - 1)]
        reg["monto_o_limite"] = monto_ambiguo
    else:
        reg["monto_o_limite"] = generar_monto_valido()

    # Moneda
    moneda_ambigua = ""
    if "moneda" in campos_para_ambiguar:
        moneda_ambigua = monedas_amb[random.randint(0, len(monedas_amb) - 1)]
        reg["moneda"] = moneda_ambigua
    else:
        reg["moneda"] = MONEDAS[random.randint(0, len(MONEDAS) - 1)]

    # Pais
    pais_ambiguo = ""
    if "pais" in campos_para_ambiguar:
        pais_ambiguo = paises_amb[random.randint(0, len(paises_amb) - 1)]
        reg["pais"] = pais_ambiguo
    else:
        reg["pais"] = PAISES[random.randint(0, len(PAISES) - 1)]

    reg["flag_prioritario"] = ["S", "N"][random.randint(0, 1)]
    reg["flag_digital"] = ["S", "N"][random.randint(0, 1)]

    # Ground truth para ambiguos (el resultado esperado depende de la resolucion LLM)
    gt = {}
    gt["id_solicitud"] = reg["id_solicitud"]
    gt["tipo"] = "ambiguo"
    gt["campos_ambiguos"] = campos_para_ambiguar
    gt["origen_esperado"] = "llm_path"

    # Para sinonimos conocidos podemos dar el valor esperado
    # Para texto libre dejamos "requiere_llm"
    from ai_first_system.src.config import (
        SINONIMOS_TIPO_PRODUCTO,
        SINONIMOS_MONEDA,
        SINONIMOS_PAIS,
    )

    if tipo_ambiguo != "":
        tipo_lower = tipo_ambiguo.strip().lower()
        if tipo_lower in SINONIMOS_TIPO_PRODUCTO.keys():
            gt["tipo_producto_normalizado"] = SINONIMOS_TIPO_PRODUCTO[tipo_lower]
        else:
            gt["tipo_producto_normalizado"] = "requiere_llm"
    else:
        gt["tipo_producto_normalizado"] = reg["tipo_producto"]

    if moneda_ambigua != "":
        moneda_lower = moneda_ambigua.strip().lower()
        if moneda_lower in SINONIMOS_MONEDA.keys():
            gt["moneda_normalizada"] = SINONIMOS_MONEDA[moneda_lower]
            # Si solo la moneda era ambigua y se resolvio, puede ser rule_path
        else:
            gt["moneda_normalizada"] = "requiere_llm"
    else:
        gt["moneda_normalizada"] = reg["moneda"]

    if pais_ambiguo != "":
        pais_lower = pais_ambiguo.strip().lower()
        if pais_lower in SINONIMOS_PAIS.keys():
            gt["pais_normalizado"] = SINONIMOS_PAIS[pais_lower]
        else:
            gt["pais_normalizado"] = "requiere_llm"
    else:
        gt["pais_normalizado"] = reg["pais"]

    if "fecha_solicitud" in campos_para_ambiguar:
        gt["fecha_normalizada"] = "requiere_llm"
    else:
        gt["fecha_normalizada"] = reg["fecha_solicitud"]

    if monto_ambiguo != "":
        gt["monto_normalizado"] = "requiere_llm"
    else:
        gt["monto_normalizado"] = reg["monto_o_limite"]

    # Estado esperado: si todos los campos ambiguos se resuelven bien, VALIDO
    # Pero como depende del LLM, marcamos como "depende_resolucion"
    hay_requiere_llm = False
    if gt.get("tipo_producto_normalizado") == "requiere_llm":
        hay_requiere_llm = True
    if gt.get("moneda_normalizada") == "requiere_llm":
        hay_requiere_llm = True
    if gt.get("pais_normalizado") == "requiere_llm":
        hay_requiere_llm = True
    if gt.get("fecha_normalizada") == "requiere_llm":
        hay_requiere_llm = True
    if gt.get("monto_normalizado") == "requiere_llm":
        hay_requiere_llm = True

    if hay_requiere_llm:
        gt["estado_esperado"] = "depende_resolucion"
    else:
        gt["estado_esperado"] = "VALIDO"

    gt["motivos_falla_esperados"] = ""

    return reg, gt


def generar_dataset(cantidad, seed, ratio_limpio, ratio_sucio, ratio_ambiguo, perfil="base"):
    # Genera un dataset sintetico con la distribucion indicada
    # Retorna (registros, ground_truth)

    random.seed(seed)

    # Calcular cantidades por tipo
    cant_limpio = int(cantidad * ratio_limpio)
    cant_sucio = int(cantidad * ratio_sucio)
    cant_ambiguo = cantidad - cant_limpio - cant_sucio  # el resto va a ambiguo

    registros = []
    ground_truth = []

    num_sol = 1
    num_cli = 100

    # Generar limpios
    i = 0
    while i < cant_limpio:
        reg, gt = generar_registro_limpio(num_sol, num_cli)
        registros.append(reg)
        ground_truth.append(gt)
        num_sol = num_sol + 1
        num_cli = num_cli + 1
        i = i + 1

    # Generar sucios
    i = 0
    while i < cant_sucio:
        reg, gt = generar_registro_sucio(num_sol, num_cli)
        registros.append(reg)
        ground_truth.append(gt)
        num_sol = num_sol + 1
        num_cli = num_cli + 1
        i = i + 1

    # Generar ambiguos
    i = 0
    while i < cant_ambiguo:
        reg, gt = generar_registro_ambiguo(num_sol, num_cli, perfil)
        registros.append(reg)
        ground_truth.append(gt)
        num_sol = num_sol + 1
        num_cli = num_cli + 1
        i = i + 1

    # Mezclar registros manteniendo la relacion con ground truth
    indices = []
    j = 0
    while j < len(registros):
        indices.append(j)
        j = j + 1
    random.shuffle(indices)

    registros_mezclados = []
    gt_mezclados = []
    for idx in indices:
        registros_mezclados.append(registros[idx])
        gt_mezclados.append(ground_truth[idx])

    return registros_mezclados, gt_mezclados


def exportar_csv(registros, ruta):
    # Exporta registros a CSV
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

    arch = open(ruta, "w", encoding="utf-8")

    # Header
    linea_header = ""
    i = 0
    for campo in campos:
        if i > 0:
            linea_header = linea_header + ","
        linea_header = linea_header + campo
        i = i + 1
    arch.write(linea_header + "\n")

    # Datos
    for reg in registros:
        linea = ""
        idx = 0
        for campo in campos:
            if campo in reg.keys():
                val = reg[campo]
            else:
                val = ""
            if val == None:
                val = ""
            val_str = str(val)
            # Escapar comas
            necesita_comillas = False
            j = 0
            while j < len(val_str):
                if val_str[j] == "," or val_str[j] == '"' or val_str[j] == "\n":
                    necesita_comillas = True
                j = j + 1
            if necesita_comillas:
                val_escapado = ""
                j = 0
                while j < len(val_str):
                    if val_str[j] == '"':
                        val_escapado = val_escapado + '""'
                    else:
                        val_escapado = val_escapado + val_str[j]
                    j = j + 1
                val_str = '"' + val_escapado + '"'
            if idx > 0:
                linea = linea + ","
            linea = linea + val_str
            idx = idx + 1
        arch.write(linea + "\n")

    arch.close()


def exportar_json(registros, ruta):
    # Exporta registros como JSON array
    arch = open(ruta, "w", encoding="utf-8")
    arch.write(json.dumps(registros, indent=2, ensure_ascii=False))
    arch.close()


def exportar_txt(registros, ruta):
    # Exporta registros como TXT delimitado por pipe
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

    arch = open(ruta, "w", encoding="utf-8")

    # Header
    linea_header = ""
    i = 0
    for campo in campos:
        if i > 0:
            linea_header = linea_header + "|"
        linea_header = linea_header + campo
        i = i + 1
    arch.write(linea_header + "\n")

    # Datos
    for reg in registros:
        linea = ""
        idx = 0
        for campo in campos:
            if campo in reg.keys():
                val = reg[campo]
            else:
                val = ""
            if val == None:
                val = ""
            if idx > 0:
                linea = linea + "|"
            linea = linea + str(val)
            idx = idx + 1
        arch.write(linea + "\n")

    arch.close()


def generar(
    cantidad=100,
    seed=42,
    ratio_limpio=0.5,
    ratio_sucio=0.3,
    ratio_ambiguo=0.2,
    formato="csv",
    perfil="base",
):
    # Funcion principal del generador
    # Retorna diccionario con rutas de archivos generados

    # Validar ratios
    total_ratio = ratio_limpio + ratio_sucio + ratio_ambiguo
    if total_ratio < 0.99 or total_ratio > 1.01:
        return {"error": "Los ratios deben sumar 1.0, suman: " + str(total_ratio)}

    # Validar formato
    if formato not in ["csv", "json", "txt"]:
        return {"error": "Formato no soportado: " + formato + ". Usar csv, json o txt"}

    # Validar perfil
    perfil_txt = str(perfil).strip().lower()
    if perfil_txt == "":
        perfil_txt = "base"
    if perfil_txt not in ["base", "realista"]:
        return {
            "error": "Perfil no soportado: "
            + str(perfil)
            + ". Usar base o realista"
        }

    # Crear directorio de datasets si no existe
    if not os.path.exists(DIR_DATASETS):
        os.makedirs(DIR_DATASETS)

    # Generar dataset
    registros, ground_truth = generar_dataset(
        cantidad, seed, ratio_limpio, ratio_sucio, ratio_ambiguo, perfil_txt
    )

    # Nombre del archivo
    nombre_base = "synth_" + str(cantidad) + "_s" + str(seed)
    if perfil_txt == "realista":
        nombre_base = nombre_base + "_realista"

    # Exportar dataset
    ruta_dataset = os.path.join(DIR_DATASETS, nombre_base + "." + formato)
    if formato == "csv":
        exportar_csv(registros, ruta_dataset)
    elif formato == "json":
        exportar_json(registros, ruta_dataset)
    elif formato == "txt":
        exportar_txt(registros, ruta_dataset)

    # Exportar ground truth siempre como JSON
    ruta_gt = os.path.join(DIR_DATASETS, nombre_base + "_ground_truth.json")
    arch_gt = open(ruta_gt, "w", encoding="utf-8")
    arch_gt.write(json.dumps(ground_truth, indent=2, ensure_ascii=False))
    arch_gt.close()

    # Resumen
    cant_limpio = 0
    cant_sucio = 0
    cant_ambiguo = 0
    for gt in ground_truth:
        if gt["tipo"] == "limpio":
            cant_limpio = cant_limpio + 1
        elif gt["tipo"] == "sucio":
            cant_sucio = cant_sucio + 1
        elif gt["tipo"] == "ambiguo":
            cant_ambiguo = cant_ambiguo + 1

    resultado = {
        "ruta_dataset": ruta_dataset,
        "ruta_ground_truth": ruta_gt,
        "cantidad_total": len(registros),
        "cantidad_limpio": cant_limpio,
        "cantidad_sucio": cant_sucio,
        "cantidad_ambiguo": cant_ambiguo,
        "seed": seed,
        "formato": formato,
        "perfil": perfil_txt,
    }

    return resultado


def main():
    # Parseo manual de argumentos CLI
    args = sys.argv[1:]

    cantidad = 100
    seed = 42
    ratio_limpio = 0.5
    ratio_sucio = 0.3
    ratio_ambiguo = 0.2
    formato = "csv"
    perfil = "base"

    i = 0
    while i < len(args):
        arg = args[i]
        if arg == "--cantidad" and i + 1 < len(args):
            cantidad = int(args[i + 1])
            i = i + 2
        elif arg == "--seed" and i + 1 < len(args):
            seed = int(args[i + 1])
            i = i + 2
        elif arg == "--ratio-limpio" and i + 1 < len(args):
            ratio_limpio = float(args[i + 1])
            i = i + 2
        elif arg == "--ratio-sucio" and i + 1 < len(args):
            ratio_sucio = float(args[i + 1])
            i = i + 2
        elif arg == "--ratio-ambiguo" and i + 1 < len(args):
            ratio_ambiguo = float(args[i + 1])
            i = i + 2
        elif arg == "--formato" and i + 1 < len(args):
            formato = args[i + 1]
            i = i + 2
        elif arg == "--perfil" and i + 1 < len(args):
            perfil = args[i + 1]
            i = i + 2
        elif arg == "--help" or arg == "-h":
            print("Uso: python data_generator.py [opciones]")
            print("")
            print("Opciones:")
            print("  --cantidad N       Cantidad de registros (default: 100)")
            print("  --seed N           Seed para reproducibilidad (default: 42)")
            print("  --ratio-limpio F   Ratio de registros limpios (default: 0.5)")
            print("  --ratio-sucio F    Ratio de registros sucios (default: 0.3)")
            print("  --ratio-ambiguo F  Ratio de registros ambiguos (default: 0.2)")
            print(
                "  --formato FMT      Formato de salida: csv, json, txt (default: csv)"
            )
            print("  --perfil PERF      Perfil: base o realista (default: base)")
            print("")
            print("Ejemplo:")
            print(
                "  python data_generator.py --cantidad 1000 --seed 2026 --ratio-limpio 0.65 --ratio-sucio 0.3 --ratio-ambiguo 0.05 --perfil realista --formato csv"
            )
            return
        else:
            print("Argumento no reconocido: " + arg)
            print("Usar --help para ver opciones")
            return

    print("Generando dataset sintetico...")
    print("  Cantidad: " + str(cantidad))
    print("  Seed: " + str(seed))
    print("  Ratio limpio: " + str(ratio_limpio))
    print("  Ratio sucio: " + str(ratio_sucio))
    print("  Ratio ambiguo: " + str(ratio_ambiguo))
    print("  Formato: " + formato)
    print("  Perfil: " + perfil)
    print("")

    resultado = generar(
        cantidad, seed, ratio_limpio, ratio_sucio, ratio_ambiguo, formato, perfil
    )

    if "error" in resultado.keys():
        print("ERROR: " + resultado["error"])
        return

    print("Dataset generado exitosamente:")
    print("  Archivo: " + resultado["ruta_dataset"])
    print("  Ground truth: " + resultado["ruta_ground_truth"])
    print("  Total: " + str(resultado["cantidad_total"]) + " registros")
    print("  Limpios: " + str(resultado["cantidad_limpio"]))
    print("  Sucios: " + str(resultado["cantidad_sucio"]))
    print("  Ambiguos: " + str(resultado["cantidad_ambiguo"]))
    print("  Perfil: " + str(resultado.get("perfil", "base")))


if __name__ == "__main__":
    main()
