# benchmark_runner.py - Ejecutor de benchmarks comparativos (RF-08 AI-First)
# Corre ambos modos (legacy y ai_first) sobre el mismo dataset
# Genera reportes JSON y Markdown en metrics/reports/

import os
import sys
import json
import time
from datetime import datetime

DIR_RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIR_REPORTS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "reports")
DIR_DATASETS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "datasets")

# Agregar paths necesarios
if DIR_RAIZ not in sys.path:
    sys.path.insert(0, DIR_RAIZ)
sys.path.insert(0, os.path.join(DIR_RAIZ, "legacy_system", "src"))
sys.path.insert(0, os.path.join(DIR_RAIZ, "ai_first_system", "src"))

MODULO = "BENCHMARK"


def construir_resultado_error(mensaje):
    # Construye una estructura de resultado compatible con metricas
    return {
        "status": "error",
        "error": mensaje,
        "resumen": {
            "duracion_segundos": 0.0,
            "total_procesados": 0,
            "total_validos": 0,
            "total_invalidos": 0,
        },
        "enrutamiento": {
            "porcentaje_llm": 0.0,
            "llm_path": 0,
            "regla_path": 0,
            "sinonimos_resueltos": 0,
        },
        "metricas_llm": {
            "total_llamadas": 0,
            "total_llamadas_con_tokens": 0,
            "total_llamadas_sin_tokens": 0,
            "token_usage_disponible": False,
            "token_usage_estado": "sin_llamadas",
            "total_tokens_prompt": 0,
            "total_tokens_completion": 0,
            "costo_estimado_usd": 0.0,
            "costo_estimado_estado": "sin_llamadas",
            "total_embedding_calls": 0,
            "latencia_promedio_embedding": 0.0,
        },
    }


def ejecutar_legacy(archivo_entrada):
    # Ejecuta el modo legacy y retorna resultado con duracion
    # Usa legacy_system/src/main.py
    dir_legacy_src = os.path.join(DIR_RAIZ, "legacy_system", "src")
    if dir_legacy_src not in sys.path:
        sys.path.insert(0, dir_legacy_src)

    # Importar main legacy
    import importlib

    # Limpiar imports previos para evitar conflictos
    modulos_a_limpiar = [
        "main",
        "ingesta",
        "normalizador",
        "validador",
        "calidad",
        "logger",
    ]
    for mod in modulos_a_limpiar:
        if mod in sys.modules.keys():
            del sys.modules[mod]

    # Recargar con path legacy
    sys.path.insert(0, dir_legacy_src)

    import main as main_legacy

    inicio = time.time()

    # Crear directorio temporal para la ejecucion
    dir_data = os.path.join(DIR_RAIZ, "data")

    try:
        resultado = main_legacy.main(
            archivo_entrada_param=archivo_entrada,
            dir_data_param=dir_data,
        )
    except Exception as e:
        resultado = construir_resultado_error(
            "Fallo en modo legacy durante benchmark: " + str(e)
        )

    fin = time.time()
    duracion = round(fin - inicio, 2)

    # Agregar duracion al resumen si no esta
    if "resumen" in resultado.keys():
        if "duracion_segundos" not in resultado["resumen"].keys():
            resultado["resumen"]["duracion_segundos"] = duracion
    else:
        resultado["resumen"] = {"duracion_segundos": duracion}

    # Limpiar modulos legacy del cache
    for mod in modulos_a_limpiar:
        if mod in sys.modules.keys():
            del sys.modules[mod]

    return resultado


def ejecutar_ai_first(archivo_entrada, provider="gemini"):
    # Ejecuta el modo AI-First y retorna resultado
    dir_ai_src = os.path.join(DIR_RAIZ, "ai_first_system", "src")
    if dir_ai_src not in sys.path:
        sys.path.insert(0, dir_ai_src)

    # Limpiar modulos que puedan conflictar
    modulos_a_limpiar = ["logger", "ingesta", "normalizador", "validador", "calidad"]
    for mod in modulos_a_limpiar:
        if mod in sys.modules.keys():
            del sys.modules[mod]

    from ai_first_system.src.run_ai_first import run as run_ai_first

    dir_data = os.path.join(DIR_RAIZ, "data")
    try:
        resultado = run_ai_first(
            archivo_entrada, provider_nombre=provider, dir_data=dir_data
        )
    except Exception as e:
        resultado = construir_resultado_error(
            "Fallo en modo ai_first durante benchmark: " + str(e)
        )

    # Limpiar modulos
    for mod in modulos_a_limpiar:
        if mod in sys.modules.keys():
            del sys.modules[mod]

    return resultado


def cargar_ground_truth(ruta_gt):
    # Carga ground truth desde archivo JSON
    if not os.path.exists(ruta_gt):
        return None
    arch = open(ruta_gt, "r", encoding="utf-8")
    contenido = arch.read()
    arch.close()
    datos = json.loads(contenido)
    return datos


def ejecutar_benchmark(archivo_entrada, ruta_ground_truth=None, provider="gemini"):
    # Ejecuta benchmark completo: legacy + ai_first sobre el mismo dataset
    # Retorna diccionario con todos los resultados y metricas

    from metrics.metricas import (
        calcular_metricas_modo,
        comparar_modos,
        generar_resumen_markdown,
    )

    print("=" * 60)
    print("BENCHMARK: Legacy vs AI-First")
    print("=" * 60)
    print("")
    print("Archivo de entrada: " + archivo_entrada)
    print("")

    # Cargar ground truth si existe
    ground_truth = None
    if ruta_ground_truth != None:
        ground_truth = cargar_ground_truth(ruta_ground_truth)
        if ground_truth != None:
            print("Ground truth cargado: " + str(len(ground_truth)) + " registros")
        else:
            print("No se pudo cargar ground truth: " + ruta_ground_truth)
    print("")

    # Paso 1: Ejecutar legacy
    print("[1/2] Ejecutando modo Legacy...")
    resultado_legacy = ejecutar_legacy(archivo_entrada)
    print("  Status: " + resultado_legacy.get("status", "unknown"))
    if "resumen" in resultado_legacy.keys():
        res_leg = resultado_legacy["resumen"]
        print("  Total: " + str(res_leg.get("total_procesados", 0)) + " registros")
        print("  Validos: " + str(res_leg.get("total_validos", 0)))
        print("  Invalidos: " + str(res_leg.get("total_invalidos", 0)))
        print("  Duracion: " + str(res_leg.get("duracion_segundos", 0)) + "s")
    print("")

    # Paso 2: Ejecutar AI-First
    print("[2/2] Ejecutando modo AI-First...")
    resultado_ai_first = ejecutar_ai_first(archivo_entrada, provider)
    print("  Status: " + resultado_ai_first.get("status", "unknown"))
    if "resumen" in resultado_ai_first.keys():
        res_ai = resultado_ai_first["resumen"]
        print("  Total: " + str(res_ai.get("total_procesados", 0)) + " registros")
        print("  Validos: " + str(res_ai.get("total_validos", 0)))
        print("  Invalidos: " + str(res_ai.get("total_invalidos", 0)))
        print("  Duracion: " + str(res_ai.get("duracion_segundos", 0)) + "s")
    print("")

    # Paso 3: Calcular metricas
    print("Calculando metricas...")
    metricas_legacy = calcular_metricas_modo(resultado_legacy, ground_truth)
    metricas_ai_first = calcular_metricas_modo(resultado_ai_first, ground_truth)
    comparacion = comparar_modos(metricas_legacy, metricas_ai_first)

    # Paso 4: Generar reportes
    if not os.path.exists(DIR_REPORTS):
        os.makedirs(DIR_REPORTS)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    nombre_base = "benchmark_" + timestamp

    # Reporte JSON
    reporte_json = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "archivo_entrada": archivo_entrada,
        "ground_truth": ruta_ground_truth,
        "provider": provider,
        "legacy": {
            "status": resultado_legacy.get("status", "unknown"),
            "carpeta_ejecucion": resultado_legacy.get("carpeta_ejecucion", ""),
            "metricas": metricas_legacy,
        },
        "ai_first": {
            "status": resultado_ai_first.get("status", "unknown"),
            "carpeta_ejecucion": resultado_ai_first.get("carpeta_ejecucion", ""),
            "metricas": metricas_ai_first,
        },
        "comparacion": comparacion,
    }

    ruta_json = os.path.join(DIR_REPORTS, nombre_base + ".json")
    arch_json = open(ruta_json, "w", encoding="utf-8")
    arch_json.write(json.dumps(reporte_json, indent=4, ensure_ascii=False))
    arch_json.close()

    # Reporte Markdown
    markdown = generar_resumen_markdown(metricas_legacy, metricas_ai_first, comparacion)
    ruta_md = os.path.join(DIR_REPORTS, nombre_base + ".md")
    arch_md = open(ruta_md, "w", encoding="utf-8")
    arch_md.write(markdown)
    arch_md.close()

    print("")
    print("Reportes generados:")
    print("  JSON: " + ruta_json)
    print("  Markdown: " + ruta_md)
    print("")

    # Mostrar resumen comparativo
    print("=" * 60)
    print("RESUMEN COMPARATIVO")
    print("=" * 60)
    t_leg = metricas_legacy.get("tiempo_total_segundos", 0)
    t_ai = metricas_ai_first.get("tiempo_total_segundos", 0)
    print("Tiempo: Legacy=" + str(t_leg) + "s, AI-First=" + str(t_ai) + "s")
    print(
        "Validos: Legacy="
        + str(metricas_legacy.get("total_validos", 0))
        + ", AI-First="
        + str(metricas_ai_first.get("total_validos", 0))
    )
    print(
        "Invalidos: Legacy="
        + str(metricas_legacy.get("total_invalidos", 0))
        + ", AI-First="
        + str(metricas_ai_first.get("total_invalidos", 0))
    )
    pct_llm = metricas_ai_first.get("porcentaje_llm", 0)
    print("% registros LLM: " + str(pct_llm) + "%")
    costo = metricas_ai_first.get("llm_costo_estimado_usd", 0)
    print("Costo LLM estimado: $" + str(costo))
    print("")

    resultado = {
        "ruta_json": ruta_json,
        "ruta_md": ruta_md,
        "metricas_legacy": metricas_legacy,
        "metricas_ai_first": metricas_ai_first,
        "comparacion": comparacion,
    }

    return resultado


def main():
    # Parseo manual de argumentos CLI
    args = sys.argv[1:]

    archivo_entrada = ""
    ruta_ground_truth = None
    provider = "gemini"

    i = 0
    while i < len(args):
        arg = args[i]
        if arg == "--input" and i + 1 < len(args):
            archivo_entrada = args[i + 1]
            i = i + 2
        elif arg == "--ground-truth" and i + 1 < len(args):
            ruta_ground_truth = args[i + 1]
            i = i + 2
        elif arg == "--provider" and i + 1 < len(args):
            provider = args[i + 1]
            i = i + 2
        elif arg == "--help" or arg == "-h":
            print("Uso: python benchmark_runner.py [opciones]")
            print("")
            print("Opciones:")
            print("  --input ARCHIVO          Archivo de entrada para benchmark")
            print("  --ground-truth ARCHIVO   Archivo de ground truth JSON (opcional)")
            print("  --provider PROVIDER      Provider LLM: gemini (default: gemini)")
            print("")
            print("Ejemplo:")
            print(
                "  python benchmark_runner.py --input metrics/datasets/synth_100_s42.csv --ground-truth metrics/datasets/synth_100_s42_ground_truth.json"
            )
            return
        else:
            print("Argumento no reconocido: " + arg)
            print("Usar --help para ver opciones")
            return

    if archivo_entrada == "":
        # Buscar dataset sintetico por defecto
        archivos_synth = []
        if os.path.exists(DIR_DATASETS):
            for nombre in os.listdir(DIR_DATASETS):
                if nombre.startswith("synth_") and nombre.endswith(".csv"):
                    archivos_synth.append(nombre)

        if len(archivos_synth) > 0:
            archivos_synth.sort()
            archivo_entrada = os.path.join(DIR_DATASETS, archivos_synth[0])
            # Buscar ground truth correspondiente
            base = os.path.splitext(archivos_synth[0])[0]
            gt_path = os.path.join(DIR_DATASETS, base + "_ground_truth.json")
            if os.path.exists(gt_path):
                ruta_ground_truth = gt_path
            print("Usando dataset sintetico: " + archivo_entrada)
        else:
            # Usar dataset original
            archivo_entrada = os.path.join(DIR_RAIZ, "data", "solicitudes.csv")
            print("Usando dataset original: " + archivo_entrada)

    ejecutar_benchmark(archivo_entrada, ruta_ground_truth, provider)


if __name__ == "__main__":
    main()
