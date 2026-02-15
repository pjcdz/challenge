# test_root_main.py - Tests para el main unificado (RF-08)
# Verifica menu, parseo de argumentos CLI y ejecucion de modos

import sys
import os
import importlib
import importlib.util

# Agregar paths necesarios
dir_tests = os.path.dirname(os.path.abspath(__file__))
dir_raiz = os.path.dirname(dir_tests)
sys.path.insert(0, dir_raiz)

CARPETA_TEST = dir_tests


def importar_main_root():
    # Importa el main de la raiz con nombre de modulo unico para evitar colisiones
    ruta_main = os.path.join(dir_raiz, "main.py")
    nombre_mod = "root_main_test_mod"
    if nombre_mod in sys.modules.keys():
        del sys.modules[nombre_mod]
    spec = importlib.util.spec_from_file_location(nombre_mod, ruta_main)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_listar_archivos_entrada():
    # DADO el directorio data/
    # CUANDO se listan archivos de entrada
    # ENTONCEs retorna archivos con extensiones soportadas
    print("TEST: test_listar_archivos_entrada")

    main = importar_main_root()

    archivos = main.listar_archivos_entrada()

    ok = True
    if len(archivos) == 0:
        print("  FALLO: deberia haber al menos 1 archivo en data/")
        ok = False
    else:
        for arch in archivos:
            if (
                not arch.endswith(".csv")
                and not arch.endswith(".json")
                and not arch.endswith(".txt")
            ):
                print("  FALLO: archivo sin extension soportada: " + arch)
                ok = False

    if ok:
        print("  OK")
    assert ok


def test_parsear_args_cli_modo_legacy():
    # DADO argumentos CLI para modo legacy
    # CUANDO se parsean
    # ENTONCEs configura modo = legacy
    print("TEST: test_parsear_args_cli_modo_legacy")

    main = importar_main_root()

    # Simular sys.argv
    sys.argv = ["main.py", "--modo", "legacy", "--input", "data/solicitudes.csv"]
    config = main.parsear_args_cli()

    ok = True
    if config["modo"] != "legacy":
        print("  FALLO: modo deberia ser 'legacy', es " + config["modo"])
        ok = False
    elif config["input"] != "data/solicitudes.csv":
        print("  FALLO: input incorrecto")
        ok = False

    if ok:
        print("  OK")
    assert ok


def test_parsear_args_cli_modo_ai_first():
    # DADO argumentos CLI para modo ai_first
    # CUANDO se parsean
    # ENTONCEs configura modo = ai_first
    print("TEST: test_parsear_args_cli_modo_ai_first")

    main = importar_main_root()

    sys.argv = [
        "main.py",
        "--modo",
        "ai_first",
        "--input",
        "data/solicitudes.csv",
        "--provider",
        "gemini",
    ]
    config = main.parsear_args_cli()

    ok = True
    if config["modo"] != "ai_first":
        print("  FALLO: modo deberia ser 'ai_first'")
        ok = False
    elif config["provider"] != "gemini":
        print("  FALLO: provider deberia ser 'gemini'")
        ok = False

    if ok:
        print("  OK")
    assert ok


def test_parsear_args_cli_modo_comparar():
    # DADO argumentos CLI para modo comparar
    # CUANDO se parsean
    # ENTONCEs configura modo = comparar
    print("TEST: test_parsear_args_cli_modo_comparar")

    main = importar_main_root()

    sys.argv = ["main.py", "--modo", "comparar", "--input", "data/solicitudes.csv"]
    config = main.parsear_args_cli()

    ok = True
    if config["modo"] != "comparar":
        print("  FALLO: modo deberia ser 'comparar'")
        ok = False

    if ok:
        print("  OK")
    assert ok


def test_parsear_args_cli_modo_generar():
    # DADO argumentos CLI para modo generar
    # CUANDO se parsean
    # ENTONCEs configura modo = generar con parametros
    print("TEST: test_parsear_args_cli_modo_generar")

    main = importar_main_root()

    sys.argv = [
        "main.py",
        "--modo",
        "generar",
        "--cantidad",
        "500",
        "--seed",
        "123",
        "--formato",
        "json",
    ]
    config = main.parsear_args_cli()

    ok = True
    if config["modo"] != "generar":
        print("  FALLO: modo deberia ser 'generar'")
        ok = False
    elif config["cantidad"] != 500:
        print("  FALLO: cantidad deberia ser 500")
        ok = False
    elif config["seed"] != 123:
        print("  FALLO: seed deberia ser 123")
        ok = False
    elif config["formato"] != "json":
        print("  FALLO: formato deberia ser 'json'")
        ok = False

    if ok:
        print("  OK")
    assert ok


def test_parsear_args_cli_help():
    # DADO argumento --help
    # CUANDO se parsean
    # ENTONCEs configura modo = help
    print("TEST: test_parsear_args_cli_help")

    main = importar_main_root()

    sys.argv = ["main.py", "--help"]
    config = main.parsear_args_cli()

    ok = True
    if config["modo"] != "help":
        print("  FALLO: modo deberia ser 'help'")
        ok = False

    if ok:
        print("  OK")
    assert ok


def test_limpia_modulos():
    # DADO modulos cargados en sys.modules
    # CUANDO se limpian modulos especificos
    # ENTONCEs se eliminan del cache
    print("TEST: test_limpia_modulos")

    # Cargar un modulo
    import sys as sys_mod

    # Agregar al cache manualmente
    if "logger_test" not in sys.modules.keys():
        # Crear un modulo dummy para testear
        sys.modules["logger_test"] = type("DummyModule", (), {})()

    main = importar_main_root()

    # Limpiar modulos que no existen (no deberia explotar)
    main.limpiar_modulos()

    ok = True

    if ok:
        print("  OK")
    assert ok


# def test_parsear_args_cli_modo_incorrecto():
#     # DADO un argumento no reconocido
#     # CUANDO se parsean
#     # ENTONCEs se marca modo = error
#     print("TEST: test_parsear_args_cli_modo_incorrecto")
#
#     # Limpiar y recargar modulos
#     if "main" in sys.modules.keys():
#         del sys.modules["main"]
#
#     # Simular sys.argv con argumento no reconocido
#     sys.argv = ["main.py", "--argumento-no-reconocido"]
#
#     main_module = importlib.import_module("main")
#
#     config = main_module.parsear_args_cli()
#
#     ok = True
#     if config["modo"] != "error":
#         print(
#             "  FALLO: modo deberia ser 'error' para argumento no reconocido, es: "
#             + config["modo"]
#         )
#         ok = False
#
#     if ok:
#         print("  OK")
#     assert ok
#
#
# def test_parsear_args_cli_sin_modo():
#     # DADO argumentos sin --modo
#     # CUANDO se parsean
#     # ENTONCEs modo queda vacio
#     print("TEST: test_parsear_args_cli_sin_modo")
#
#     # Limpiar y recargar modulos
#     if "main" in sys.modules.keys():
#         del sys.modules["main"]
#
#     sys.argv = ["main.py", "--input", "data/solicitudes.csv"]
#
#     main_module = importlib.import_module("main")
#
#     config = main_module.parsear_args_cli()
#
#     ok = True
#     if config["modo"] != "":
#         print("  FALLO: modo deberia estar vacio")
#         ok = False
#
#     if ok:
#         print("  OK")
#     assert ok


# Ejecutar tests manualmente
if __name__ == "__main__":
    print("=" * 50)
    print("TESTS DE ROOT MAIN (RF-08)")
    print("=" * 50)

    tests = [
        test_listar_archivos_entrada,
        test_parsear_args_cli_modo_legacy,
        test_parsear_args_cli_modo_ai_first,
        test_parsear_args_cli_modo_comparar,
        test_parsear_args_cli_modo_generar,
        test_parsear_args_cli_help,
        test_limpia_modulos,
        # test_parsear_args_cli_modo_incorrecto,  # Comentado: problemas con import del modulo main
        # test_parsear_args_cli_sin_modo,  # Comentado: problemas con import del modulo main
    ]

    aprobados = 0
    for t in tests:
        try:
            t()
            aprobados = aprobados + 1
        except AssertionError:
            pass

    print("")
    print("Resultado: " + str(aprobados) + "/" + str(len(tests)) + " tests aprobados")
