# main.py - Menu unificado del proyecto (Root)
# Punto de entrada principal con menu interactivo y modo CLI
# Opciones: legacy, ai_first, comparar, generar, salir

import os
import sys

DIR_RAIZ = os.path.dirname(os.path.abspath(__file__))

# Agregar paths necesarios
sys.path.insert(0, DIR_RAIZ)
sys.path.insert(0, os.path.join(DIR_RAIZ, "legacy_system", "src"))
sys.path.insert(0, os.path.join(DIR_RAIZ, "ai_first_system", "src"))

MODULO = "ROOT_MAIN"


def listar_archivos_entrada():
    # Lista archivos disponibles en data/ con extension soportada
    dir_data = os.path.join(DIR_RAIZ, "data")
    extensiones = [".csv", ".json", ".txt"]
    archivos = []
    if not os.path.exists(dir_data):
        return archivos
    nombres = os.listdir(dir_data)
    i = 0
    while i < len(nombres):
        nombre = nombres[i]
        ext = os.path.splitext(nombre)[1].lower()
        if ext in extensiones:
            ruta = os.path.join(dir_data, nombre)
            archivos.append(ruta)
        i = i + 1
    archivos.sort()
    return archivos


def seleccionar_archivo():
    # Menu para seleccionar archivo de entrada
    archivos = listar_archivos_entrada()
    # Agregar datasets sinteticos si existen
    dir_datasets = os.path.join(DIR_RAIZ, "metrics", "datasets")
    if os.path.exists(dir_datasets):
        nombres = os.listdir(dir_datasets)
        for nombre in nombres:
            ext = os.path.splitext(nombre)[1].lower()
            if ext in [".csv", ".json", ".txt"]:
                ruta = os.path.join(dir_datasets, nombre)
                if ruta not in archivos:
                    archivos.append(ruta)

    if len(archivos) == 0:
        print("No se encontraron archivos de entrada")
        return None

    print("")
    print("Archivos disponibles:")
    i = 0
    while i < len(archivos):
        print("  " + str(i + 1) + ". " + archivos[i])
        i = i + 1
    print("")
    opcion = input("Seleccione archivo (1-" + str(len(archivos)) + "): ")
    opcion = opcion.strip()

    # Validar
    es_valido = False
    num = 0
    if len(opcion) > 0:
        es_numero = True
        j = 0
        while j < len(opcion):
            if opcion[j] < "0" or opcion[j] > "9":
                es_numero = False
            j = j + 1
        if es_numero:
            num = int(opcion)
            if num >= 1 and num <= len(archivos):
                es_valido = True

    if not es_valido:
        print("Opcion no valida")
        return None

    return archivos[num - 1]


def limpiar_modulos():
    # Limpia modulos cacheados para evitar conflictos entre legacy y ai_first
    modulos = ["main", "logger", "ingesta", "normalizador", "validador", "calidad"]
    for mod in modulos:
        if mod in sys.modules.keys():
            del sys.modules[mod]


def ejecutar_legacy(archivo_entrada):
    # Ejecuta el sistema legacy
    print("")
    print("=" * 50)
    print("SISTEMA LEGACY")
    print("=" * 50)
    print("Archivo: " + archivo_entrada)
    print("")

    limpiar_modulos()
    dir_legacy = os.path.join(DIR_RAIZ, "legacy_system", "src")
    sys.path.insert(0, dir_legacy)

    import main as main_legacy

    resultado = main_legacy.main(
        archivo_entrada_param=archivo_entrada,
        dir_data_param=os.path.join(DIR_RAIZ, "data"),
    )

    limpiar_modulos()

    if resultado["status"] == "ok":
        print("")
        print("Workflow legacy completado exitosamente")
        print("Carpeta ejecucion: " + resultado.get("carpeta_ejecucion", ""))
        resumen = resultado.get("resumen", {})
        print("Total: " + str(resumen.get("total_procesados", 0)) + " registros")
        print("Validos: " + str(resumen.get("total_validos", 0)))
        print("Invalidos: " + str(resumen.get("total_invalidos", 0)))
    elif resultado["status"] == "empty":
        print("Archivo vacio o sin registros")
    else:
        print("Error en el workflow legacy")

    return resultado


def ejecutar_ai_first(archivo_entrada, provider="gemini"):
    # Ejecuta el sistema AI-First
    print("")
    print("=" * 50)
    print("SISTEMA AI-FIRST")
    print("=" * 50)
    print("Archivo: " + archivo_entrada)
    print("Provider: " + provider)
    print("")

    limpiar_modulos()

    from ai_first_system.src.run_ai_first import run as run_ai_first

    resultado = run_ai_first(
        archivo_entrada,
        provider_nombre=provider,
        dir_data=os.path.join(DIR_RAIZ, "data"),
    )

    limpiar_modulos()

    if resultado["status"] == "ok":
        print("")
        print("Workflow AI-First completado exitosamente")
        print("Carpeta ejecucion: " + resultado.get("carpeta_ejecucion", ""))
        resumen = resultado.get("resumen", {})
        print("Total: " + str(resumen.get("total_procesados", 0)) + " registros")
        print("Validos: " + str(resumen.get("total_validos", 0)))
        print("Invalidos: " + str(resumen.get("total_invalidos", 0)))
        print("Duracion: " + str(resumen.get("duracion_segundos", 0)) + "s")
        enr = resultado.get("enrutamiento", {})
        print("Rule path: " + str(enr.get("regla_path", 0)))
        print("LLM path: " + str(enr.get("llm_path", 0)))
    elif resultado["status"] == "empty":
        print("Archivo vacio o sin registros")
    else:
        error = resultado.get("error", "Error desconocido")
        print("Error en el workflow AI-First: " + error)

    return resultado


def ejecutar_comparar(archivo_entrada, provider="gemini"):
    # Ejecuta benchmark comparativo
    print("")
    print("=" * 50)
    print("BENCHMARK COMPARATIVO")
    print("=" * 50)
    print("")

    from metrics.benchmark_runner import ejecutar_benchmark

    # Buscar ground truth si el archivo esta en datasets
    ruta_gt = None
    base = os.path.splitext(archivo_entrada)[0]
    posible_gt = base + "_ground_truth.json"
    if os.path.exists(posible_gt):
        ruta_gt = posible_gt
        print("Ground truth encontrado: " + ruta_gt)

    resultado = ejecutar_benchmark(archivo_entrada, ruta_gt, provider)
    return resultado


def ejecutar_generar(
    cantidad=100,
    seed=42,
    ratio_limpio=0.5,
    ratio_sucio=0.3,
    ratio_ambiguo=0.2,
    formato="csv",
):
    # Genera dataset sintetico
    print("")
    print("=" * 50)
    print("GENERADOR DE DATOS SINTETICOS")
    print("=" * 50)
    print("")

    from metrics.data_generator import generar

    resultado = generar(
        cantidad, seed, ratio_limpio, ratio_sucio, ratio_ambiguo, formato
    )

    if "error" in resultado.keys():
        print("ERROR: " + resultado["error"])
        return resultado

    print("Dataset generado exitosamente:")
    print("  Archivo: " + resultado["ruta_dataset"])
    print("  Ground truth: " + resultado["ruta_ground_truth"])
    print("  Total: " + str(resultado["cantidad_total"]) + " registros")
    print("  Limpios: " + str(resultado["cantidad_limpio"]))
    print("  Sucios: " + str(resultado["cantidad_sucio"]))
    print("  Ambiguos: " + str(resultado["cantidad_ambiguo"]))

    return resultado


def menu_interactivo():
    # Menu interactivo principal
    while True:
        print("")
        print("=" * 50)
        print("CHALLENGE TECNICO - MENU PRINCIPAL")
        print("=" * 50)
        print("")
        print("  1. Usar sistema Legacy")
        print("  2. Usar sistema AI-First")
        print("  3. Comparar performance (benchmark)")
        print("  4. Generar dataset sintetico")
        print("  5. Salir")
        print("")
        opcion = input("Seleccione una opcion (1-5): ")
        opcion = opcion.strip()

        if opcion == "1":
            archivo = seleccionar_archivo()
            if archivo != None:
                ejecutar_legacy(archivo)

        elif opcion == "2":
            archivo = seleccionar_archivo()
            if archivo != None:
                ejecutar_ai_first(archivo)

        elif opcion == "3":
            archivo = seleccionar_archivo()
            if archivo != None:
                ejecutar_comparar(archivo)

        elif opcion == "4":
            # Pedir parametros de generacion
            print("")
            cant_str = input("Cantidad de registros (default 100): ").strip()
            if cant_str == "":
                cant = 100
            else:
                cant = int(cant_str)

            seed_str = input("Seed (default 42): ").strip()
            if seed_str == "":
                seed = 42
            else:
                seed = int(seed_str)

            fmt = input("Formato (csv/json/txt, default csv): ").strip()
            if fmt == "":
                fmt = "csv"

            ejecutar_generar(cantidad=cant, seed=seed, formato=fmt)

        elif opcion == "5":
            print("Saliendo...")
            break

        else:
            print("Opcion no valida")


def parsear_args_cli():
    # Parsea argumentos CLI
    # Retorna diccionario con configuracion
    args = sys.argv[1:]
    config = {
        "modo": "",
        "input": "",
        "cantidad": 100,
        "seed": 42,
        "ratio_limpio": 0.5,
        "ratio_sucio": 0.3,
        "ratio_ambiguo": 0.2,
        "formato": "csv",
        "provider": "gemini",
    }

    i = 0
    while i < len(args):
        arg = args[i]
        if arg == "--modo" and i + 1 < len(args):
            config["modo"] = args[i + 1]
            i = i + 2
        elif arg == "--input" and i + 1 < len(args):
            config["input"] = args[i + 1]
            i = i + 2
        elif arg == "--cantidad" and i + 1 < len(args):
            config["cantidad"] = int(args[i + 1])
            i = i + 2
        elif arg == "--seed" and i + 1 < len(args):
            config["seed"] = int(args[i + 1])
            i = i + 2
        elif arg == "--ratio-limpio" and i + 1 < len(args):
            config["ratio_limpio"] = float(args[i + 1])
            i = i + 2
        elif arg == "--ratio-sucio" and i + 1 < len(args):
            config["ratio_sucio"] = float(args[i + 1])
            i = i + 2
        elif arg == "--ratio-ambiguo" and i + 1 < len(args):
            config["ratio_ambiguo"] = float(args[i + 1])
            i = i + 2
        elif arg == "--formato" and i + 1 < len(args):
            config["formato"] = args[i + 1]
            i = i + 2
        elif arg == "--provider" and i + 1 < len(args):
            config["provider"] = args[i + 1]
            i = i + 2
        elif arg == "--help" or arg == "-h":
            print("Uso: python main.py [--modo MODO] [opciones]")
            print("")
            print("Sin argumentos: menu interactivo")
            print("")
            print("Modos CLI:")
            print("  --modo legacy      Ejecutar sistema legacy")
            print("  --modo ai_first    Ejecutar sistema AI-First")
            print("  --modo comparar    Benchmark legacy vs AI-First")
            print("  --modo generar     Generar dataset sintetico")
            print("")
            print("Opciones generales:")
            print("  --input ARCHIVO    Archivo de entrada")
            print("  --provider PROV    Provider LLM (default: gemini)")
            print("")
            print("Opciones para generar:")
            print("  --cantidad N       Cantidad de registros (default: 100)")
            print("  --seed N           Seed (default: 42)")
            print("  --ratio-limpio F   (default: 0.5)")
            print("  --ratio-sucio F    (default: 0.3)")
            print("  --ratio-ambiguo F  (default: 0.2)")
            print("  --formato FMT      csv/json/txt (default: csv)")
            print("")
            print("Ejemplos:")
            print("  python main.py --modo legacy --input data/solicitudes.csv")
            print("  python main.py --modo ai_first --input data/solicitudes.csv")
            print("  python main.py --modo comparar --input data/solicitudes.csv")
            print("  python main.py --modo generar --cantidad 1000 --seed 42")
            config["modo"] = "help"
            return config
        else:
            print("Argumento no reconocido: " + arg)
            print("Usar --help para ver opciones")
            config["modo"] = "error"
            return config

    return config


def main():
    # Punto de entrada principal
    if len(sys.argv) <= 1:
        # Sin argumentos: menu interactivo
        menu_interactivo()
        return

    # Con argumentos: modo CLI
    config = parsear_args_cli()
    modo = config["modo"]

    if modo == "help" or modo == "error":
        return

    if modo == "":
        print("Debe especificar --modo. Usar --help para ver opciones")
        return

    if modo == "legacy":
        if config["input"] == "":
            print("Debe especificar --input para modo legacy")
            return
        ejecutar_legacy(config["input"])

    elif modo == "ai_first":
        if config["input"] == "":
            print("Debe especificar --input para modo ai_first")
            return
        ejecutar_ai_first(config["input"], config["provider"])

    elif modo == "comparar":
        if config["input"] == "":
            print("Debe especificar --input para modo comparar")
            return
        ejecutar_comparar(config["input"], config["provider"])

    elif modo == "generar":
        ejecutar_generar(
            cantidad=config["cantidad"],
            seed=config["seed"],
            ratio_limpio=config["ratio_limpio"],
            ratio_sucio=config["ratio_sucio"],
            ratio_ambiguo=config["ratio_ambiguo"],
            formato=config["formato"],
        )

    else:
        print("Modo no reconocido: " + modo)
        print("Modos validos: legacy, ai_first, comparar, generar")


if __name__ == "__main__":
    main()
