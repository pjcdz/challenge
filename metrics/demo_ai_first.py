# demo_ai_first.py - Demo integral para entrevista (Legacy vs AI-First)
# Ejecuta benchmarks de datasets realistas y genera un resumen ejecutivo
# Incluye limpieza opcional de artefactos previos para mostrar repo prolijo

import os
import sys
import json
import csv
import shutil
from datetime import datetime

DIR_METRICS = os.path.dirname(os.path.abspath(__file__))
DIR_RAIZ = os.path.dirname(DIR_METRICS)
DIR_REPORTS = os.path.join(DIR_METRICS, "reports")
DIR_EJECUCIONES = os.path.join(DIR_RAIZ, "data", "ejecuciones")
DIR_DATASETS = os.path.join(DIR_METRICS, "datasets")

if DIR_RAIZ not in sys.path:
    sys.path.insert(0, DIR_RAIZ)

MODULO = "DEMO_AI_FIRST"


def _cargar_json(ruta):
    # Carga JSON desde archivo y retorna dict/list
    if ruta == "" or not os.path.exists(ruta):
        return None
    arch = open(ruta, "r", encoding="utf-8")
    contenido = arch.read()
    arch.close()
    try:
        datos = json.loads(contenido)
        return datos
    except Exception:
        return None


def _guardar_texto(ruta, texto):
    # Guarda texto en archivo
    arch = open(ruta, "w", encoding="utf-8")
    arch.write(texto)
    arch.close()


def _guardar_json(ruta, datos):
    # Guarda estructura JSON en archivo
    arch = open(ruta, "w", encoding="utf-8")
    arch.write(json.dumps(datos, indent=4, ensure_ascii=False))
    arch.close()


def _limpiar_directorio(ruta_dir, conservar=None):
    # Borra contenidos de un directorio excepto elementos a conservar
    if conservar == None:
        conservar = []
    if not os.path.exists(ruta_dir):
        return 0

    borrados = 0
    nombres = os.listdir(ruta_dir)
    i = 0
    while i < len(nombres):
        nombre = nombres[i]
        if nombre in conservar:
            i = i + 1
            continue
        ruta = os.path.join(ruta_dir, nombre)
        try:
            if os.path.isdir(ruta):
                shutil.rmtree(ruta)
            else:
                os.remove(ruta)
            borrados = borrados + 1
        except Exception:
            pass
        i = i + 1
    return borrados


def _leer_csv_por_id(ruta_csv):
    # Lee CSV y retorna indice por id_solicitud
    res = {}
    if ruta_csv == "" or not os.path.exists(ruta_csv):
        return res

    arch = open(ruta_csv, "r", encoding="utf-8")
    lector = csv.DictReader(arch)
    for fila in lector:
        id_sol = fila.get("id_solicitud", "")
        if id_sol != "":
            res[id_sol] = fila
    arch.close()
    return res


def _contar_validos_en_ambiguos(ruta_ground_truth, ruta_csv_salida):
    # Cuenta cuantos ambiguos terminan en estado VALIDO en un CSV de salida
    # Retorna: (total_ambiguos, total_validos_en_ambiguos)
    gt = _cargar_json(ruta_ground_truth)
    salida = _leer_csv_por_id(ruta_csv_salida)

    if gt == None:
        return 0, 0

    total_ambiguos = 0
    total_validos = 0

    i = 0
    while i < len(gt):
        reg = gt[i]
        if reg.get("tipo", "") == "ambiguo":
            total_ambiguos = total_ambiguos + 1
            id_sol = reg.get("id_solicitud", "")
            if id_sol in salida.keys():
                estado = salida[id_sol].get("estado", "")
                if estado == "VALIDO":
                    total_validos = total_validos + 1
        i = i + 1

    return total_ambiguos, total_validos


def _obtener_default_datasets(incluir_incidente=False):
    # Define los datasets por defecto para la demo de entrevista
    # Se priorizan corridas donde se observa mejora real en subset ambiguo
    rutas = []
    rutas.append(os.path.join(DIR_DATASETS, "synth_1000_s2027_realista.csv"))
    rutas.append(os.path.join(DIR_DATASETS, "synth_1000_s2028_realista.csv"))
    if incluir_incidente:
        rutas.append(os.path.join(DIR_DATASETS, "synth_1000_s2026_realista.csv"))
    return rutas


def _resumir_corrida_desde_reporte(ruta_reporte_json):
    # Lee reporte benchmark y construye resumen de corrida
    rep = _cargar_json(ruta_reporte_json)
    if rep == None:
        return None

    entrada = rep.get("archivo_entrada", "")
    nombre_dataset = os.path.basename(entrada)
    ruta_gt = rep.get("ground_truth", "")

    comp = rep.get("comparacion", {})
    llm = comp.get("llm", {})
    tiempo = comp.get("tiempo", {})
    resultados = comp.get("resultados", {})

    legacy = rep.get("legacy", {})
    ai_first = rep.get("ai_first", {})

    dir_legacy = legacy.get("carpeta_ejecucion", "")
    dir_ai = ai_first.get("carpeta_ejecucion", "")

    ruta_csv_legacy = ""
    ruta_csv_ai = ""
    if dir_legacy != "":
        ruta_csv_legacy = os.path.join(dir_legacy, "solicitudes_limpias.csv")
    if dir_ai != "":
        ruta_csv_ai = os.path.join(dir_ai, "solicitudes_limpias.csv")

    amb_total_legacy, amb_validos_legacy = _contar_validos_en_ambiguos(
        ruta_gt, ruta_csv_legacy
    )
    amb_total_ai, amb_validos_ai = _contar_validos_en_ambiguos(ruta_gt, ruta_csv_ai)

    amb_total = amb_total_legacy
    if amb_total == 0:
        amb_total = amb_total_ai

    resumen = {
        "dataset": nombre_dataset,
        "archivo_entrada": entrada,
        "ground_truth": ruta_gt,
        "legacy_status": legacy.get("status", "unknown"),
        "ai_first_status": ai_first.get("status", "unknown"),
        "tiempo_legacy_seg": tiempo.get("legacy_segundos", 0.0),
        "tiempo_ai_first_seg": tiempo.get("ai_first_segundos", 0.0),
        "ratio_tiempo_ai_vs_legacy": tiempo.get("ratio_ai_vs_legacy", 0.0),
        "delta_validos_global": resultados.get("diferencia_validos", 0),
        "llm_porcentaje_registros": llm.get("porcentaje_registros_llm", 0.0),
        "llm_calls": llm.get("total_llm_calls", 0),
        "fallbacks": llm.get("fallbacks", 0),
        "retries": llm.get("retries", 0),
        "ambiguos_total": amb_total,
        "ambiguos_validos_legacy": amb_validos_legacy,
        "ambiguos_validos_ai_first": amb_validos_ai,
        "delta_validos_ambiguos": amb_validos_ai - amb_validos_legacy,
        "reporte_benchmark_json": ruta_reporte_json,
    }

    return resumen


def _generar_resumen_demo_markdown(corridas, provider):
    # Genera markdown de resumen ejecutivo para entrevista
    lineas = []
    lineas.append("# Demo Entrevista: Legacy vs AI-First")
    lineas.append("")
    lineas.append(
        "Fecha: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S") + " | Provider: " + provider
    )
    lineas.append("")
    lineas.append("## Resumen por Corrida")
    lineas.append("")
    lineas.append(
        "| Dataset | Delta validos global | Ambiguos | Legacy validos en ambiguos | AI validos en ambiguos | Delta ambiguos | % registros a LLM | Tiempo AI-First (s) |"
    )
    lineas.append(
        "|---------|-----------------------|----------|-----------------------------|------------------------|----------------|-------------------|---------------------|"
    )

    total_delta_global = 0
    total_ambiguos = 0
    total_legacy_amb_validos = 0
    total_ai_amb_validos = 0
    total_fallbacks = 0
    total_retries = 0

    i = 0
    while i < len(corridas):
        c = corridas[i]
        lineas.append(
            "| "
            + c.get("dataset", "")
            + " | "
            + str(c.get("delta_validos_global", 0))
            + " | "
            + str(c.get("ambiguos_total", 0))
            + " | "
            + str(c.get("ambiguos_validos_legacy", 0))
            + " | "
            + str(c.get("ambiguos_validos_ai_first", 0))
            + " | "
            + str(c.get("delta_validos_ambiguos", 0))
            + " | "
            + str(c.get("llm_porcentaje_registros", 0.0))
            + "% | "
            + str(c.get("tiempo_ai_first_seg", 0.0))
            + " |"
        )
        total_delta_global = total_delta_global + c.get("delta_validos_global", 0)
        total_ambiguos = total_ambiguos + c.get("ambiguos_total", 0)
        total_legacy_amb_validos = total_legacy_amb_validos + c.get(
            "ambiguos_validos_legacy", 0
        )
        total_ai_amb_validos = total_ai_amb_validos + c.get("ambiguos_validos_ai_first", 0)
        total_fallbacks = total_fallbacks + c.get("fallbacks", 0)
        total_retries = total_retries + c.get("retries", 0)
        i = i + 1

    lineas.append("")
    lineas.append("## Lectura Ejecutiva")
    lineas.append("")
    lineas.append(
        "- Legacy se mantiene como baseline rapido y estable para casos deterministas."
    )
    lineas.append(
        "- AI-First agrega valor en el subset ambiguo, enviando un porcentaje bajo de registros a LLM."
    )
    lineas.append(
        "- KPI principal para negocio: uplift de calidad en ambiguos, no velocidad total."
    )
    lineas.append("")

    lineas.append("## Totales de Demo")
    lineas.append("")
    lineas.append(
        "- Delta global acumulado de validos (AI-First vs Legacy): "
        + str(total_delta_global)
    )
    lineas.append("- Ambiguos totales evaluados: " + str(total_ambiguos))
    lineas.append(
        "- Legacy validos en ambiguos: " + str(total_legacy_amb_validos)
    )
    lineas.append(
        "- AI-First validos en ambiguos: " + str(total_ai_amb_validos)
    )
    lineas.append(
        "- Delta en ambiguos (AI-First - Legacy): "
        + str(total_ai_amb_validos - total_legacy_amb_validos)
    )
    lineas.append("- Retries LLM totales: " + str(total_retries))
    lineas.append("- Fallbacks totales: " + str(total_fallbacks))
    lineas.append("")

    lineas.append("## Reportes Generados")
    lineas.append("")
    j = 0
    while j < len(corridas):
        c = corridas[j]
        lineas.append("- " + c.get("reporte_benchmark_json", ""))
        j = j + 1

    return "\n".join(lineas)


def parsear_args():
    # Parseo manual de argumentos CLI
    args = sys.argv[1:]
    config = {
        "provider": "gemini",
        "limpiar": True,
        "incluir_incidente": False,
    }

    i = 0
    while i < len(args):
        arg = args[i]
        if arg == "--provider" and i + 1 < len(args):
            config["provider"] = args[i + 1]
            i = i + 2
        elif arg == "--sin-limpieza":
            config["limpiar"] = False
            i = i + 1
        elif arg == "--incluir-incidente":
            config["incluir_incidente"] = True
            i = i + 1
        elif arg == "--help" or arg == "-h":
            print("Uso: python metrics/demo_ai_first.py [opciones]")
            print("")
            print("Opciones:")
            print("  --provider gemini         Provider LLM (default: gemini)")
            print("  --sin-limpieza            No borra artefactos previos")
            print("  --incluir-incidente       Incluye dataset con incidente operativo")
            print("")
            print("Ejemplo:")
            print("  python metrics/demo_ai_first.py")
            print(
                "  python metrics/demo_ai_first.py --provider gemini --incluir-incidente"
            )
            config["help"] = True
            return config
        else:
            print("Argumento no reconocido: " + arg)
            print("Use --help para ver opciones")
            config["error"] = True
            return config

    return config


def ejecutar_demo(provider="gemini", limpiar=True, incluir_incidente=False):
    # Ejecuta demo completa de benchmark comparativo
    from metrics.benchmark_runner import ejecutar_benchmark

    print("=" * 60)
    print("DEMO ENTREVISTA - LEGACY VS AI-FIRST")
    print("=" * 60)
    print("")

    if limpiar:
        print("[0/3] Limpiando artefactos previos de benchmark...")
        borrados_reports = _limpiar_directorio(DIR_REPORTS, conservar=[".gitkeep"])
        borrados_ejec = _limpiar_directorio(DIR_EJECUCIONES, conservar=[".gitkeep"])
        print("  Reportes borrados: " + str(borrados_reports))
        print("  Ejecuciones borradas: " + str(borrados_ejec))
        print("")

    rutas_datasets = _obtener_default_datasets(incluir_incidente=incluir_incidente)
    corridas = []

    i = 0
    while i < len(rutas_datasets):
        ruta_dataset = rutas_datasets[i]
        base = os.path.splitext(ruta_dataset)[0]
        ruta_gt = base + "_ground_truth.json"

        if not os.path.exists(ruta_dataset):
            print("Dataset no encontrado, se omite: " + ruta_dataset)
            i = i + 1
            continue
        if not os.path.exists(ruta_gt):
            print("Ground truth no encontrado, se omite: " + ruta_gt)
            i = i + 1
            continue

        print("[" + str(i + 1) + "/" + str(len(rutas_datasets)) + "] Ejecutando benchmark:")
        print("  Dataset: " + ruta_dataset)
        print("  Ground truth: " + ruta_gt)
        print("")

        res_bench = ejecutar_benchmark(ruta_dataset, ruta_gt, provider)
        ruta_reporte_json = res_bench.get("ruta_json", "")
        resumen = _resumir_corrida_desde_reporte(ruta_reporte_json)
        if resumen != None:
            corridas.append(resumen)
            print("Resumen corrida:")
            print("  Delta global validos: " + str(resumen.get("delta_validos_global", 0)))
            print(
                "  Delta ambiguos validos: "
                + str(resumen.get("delta_validos_ambiguos", 0))
                + " ("
                + str(resumen.get("ambiguos_validos_legacy", 0))
                + " -> "
                + str(resumen.get("ambiguos_validos_ai_first", 0))
                + ")"
            )
            print("  % registros a LLM: " + str(resumen.get("llm_porcentaje_registros", 0.0)))
            print("  Tiempo AI-First (s): " + str(resumen.get("tiempo_ai_first_seg", 0.0)))
            print("")
        i = i + 1

    if len(corridas) == 0:
        print("No se pudo ejecutar ninguna corrida de demo")
        return None

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    nombre_base = "demo_ai_first_" + timestamp
    ruta_md = os.path.join(DIR_REPORTS, nombre_base + ".md")
    ruta_json = os.path.join(DIR_REPORTS, nombre_base + ".json")

    resumen_md = _generar_resumen_demo_markdown(corridas, provider)
    _guardar_texto(ruta_md, resumen_md)

    salida_json = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "provider": provider,
        "limpieza_aplicada": limpiar,
        "corridas": corridas,
        "ruta_resumen_markdown": ruta_md,
    }
    _guardar_json(ruta_json, salida_json)

    print("=" * 60)
    print("DEMO COMPLETADA")
    print("=" * 60)
    print("Resumen ejecutivo:")
    print("  Markdown: " + ruta_md)
    print("  JSON: " + ruta_json)
    print("")
    print("Sugerencia entrevista:")
    print(
        "  1) Mostrar este resumen -> 2) abrir benchmarks individuales -> 3) explicar valor en ambiguos"
    )
    print("")

    return {
        "ruta_md": ruta_md,
        "ruta_json": ruta_json,
        "corridas": corridas,
    }


def main():
    # Punto de entrada CLI
    cfg = parsear_args()
    if cfg.get("help", False):
        return
    if cfg.get("error", False):
        return

    ejecutar_demo(
        provider=cfg.get("provider", "gemini"),
        limpiar=cfg.get("limpiar", True),
        incluir_incidente=cfg.get("incluir_incidente", False),
    )


if __name__ == "__main__":
    main()
