# Registro de Decisiones Tecnicas

**Proyecto**: Mini-Workflow Supervisado Back-Office
**Fecha**: Febrero 2026

---

## Proposito

Este documento registra las decisiones tecnicas tomadas durante el diseno e implementacion
del mini-workflow, justificando el "por que" de cada eleccion para facilitar la comunicacion
en la presentacion tecnica y la mantenibilidad futura del sistema.

---

## DEC-01: Parsing de CSV sin libreria externa

**Fecha**: Febrero 2026
**Estado**: Aprobada
**Contexto**: El challenge requiere procesar archivos CSV. Python ofrece el modulo `csv` en
la libreria estandar, pero tambien es posible hacerlo con `split(",")` o parsing manual.

**Decision**: Implementar un parser manual con la funcion `separar_campos()` que recorre
caracter por caracter, respetando campos entre comillas.

**Justificacion**:
- El enunciado pide "sin dependencias externas" y simplicidad
- Un `split(",")` simple falla si un campo contiene comas entre comillas
- El parser manual es defendible, transparente y cubre el caso de comillas
- Se mantiene el control total sobre el comportamiento del parsing

**Alternativas descartadas**:
- `csv.reader()`: Aunque es stdlib, agrega una capa de abstraccion innecesaria para este caso
- `split(",")` sin proteccion: No maneja campos con comas internas

---

## DEC-02: Validacion de formato, no de calendario

**Fecha**: Febrero 2026
**Estado**: Aprobada
**Contexto**: La regla R2 valida que la fecha tenga formato DD/MM/YYYY. Surge la pregunta
de si tambien se debe validar que la fecha sea una fecha real (por ejemplo, rechazar 31/02/2025).

**Decision**: Solo validar el formato (patron DD/MM/YYYY con digitos correctos), no la
validez del calendario.

**Justificacion**:
- El enunciado del challenge especifica "formato fecha" como criterio, no "fecha valida"
- Agregar validacion de calendario introduce complejidad (dias por mes, bisiestos)
- El alcance del SRS define la regla R2 como validacion de formato y moneda
- Si se necesitara en el futuro, se puede agregar como regla R4 sin modificar R2

**Riesgo aceptado**: Fechas como "31/02/2025" o "99/99/9999" pasan la validacion de formato
si tienen el patron correcto. Esto esta documentado en los tests como comportamiento esperado.

---

## DEC-03: Deteccion dinamica de reglas en calidad.py

**Fecha**: Febrero 2026
**Estado**: Aprobada
**Contexto**: El modulo `calidad.py` genera un reporte JSON con detalle por regla de validacion.
La implementacion original tenia contadores hardcodeados para R1, R2 y R3.

**Decision**: Implementar deteccion dinamica de reglas. El modulo recorre los registros,
descubre las claves de `_detalle_reglas` y genera el reporte sin conocer las reglas de antemano.

**Justificacion**:
- RNF-03 (Mantenibilidad) exige que "agregar una regla nueva no requiera modificar modulos existentes"
- Con deteccion dinamica, agregar R4 en `validador.py` automaticamente aparece en el reporte
- Se mantiene un diccionario `nombres_reglas` para mapear claves cortas (R1) a nombres descriptivos
- Si aparece una regla desconocida (por ejemplo R4), se usa la clave tal cual

**Alternativa descartada**:
- Contadores hardcodeados `fallas_r1`, `fallas_r2`, `fallas_r3`: Requerian modificar `calidad.py`
  cada vez que se agregara una regla nueva, violando RNF-03

---

## DEC-04: Guard contra strings vacios en parsing numerico

**Fecha**: Febrero 2026
**Estado**: Aprobada
**Contexto**: En `validador.py` y `normalizador.py`, el campo `monto_o_limite` se analiza
como string. El codigo accedia a `val[0]` para detectar signos negativos, pero si el valor
quedaba vacio despues de `.strip()`, se producia un `IndexError`.

**Decision**: Agregar una guarda `if val == ""` antes de acceder a `val[0]` en ambos modulos.
Tambien se agrego guarda para el caso de un signo `-` solitario.

**Justificacion**:
- Un campo vacio o solo con espacios es un caso real (datos sucios de Back-Office)
- El crash por `IndexError` es un defecto critico que aborta todo el workflow
- La guarda es minima (2 lineas) y no cambia la logica existente para valores normales
- Se agregaron tests especificos para verificar que estos casos no producen crash

---

## DEC-05: Estructura de tests con assert y flag ok

**Fecha**: Febrero 2026
**Estado**: Aprobada
**Contexto**: Se necesita elegir un patron para escribir los tests del proyecto.

**Decision**: Cada test usa un flag `ok` inicializado en `True`, realiza verificaciones
manuales con `if ... != ...` que setean `ok = False`, y al final usa `assert ok`.

**Justificacion**:
- Es el patron que el autor del proyecto usa consistentemente
- Compatible con pytest (que captura `AssertionError`)
- Cada test es tambien ejecutable como script individual con `if __name__ == "__main__"`
- No depende de metodos especiales de frameworks de testing

**Alternativa descartada**:
- `assertEqual()`, `assertTrue()` de `unittest`: Introduce dependencia de clases y herencia
  que no se usan en el resto del proyecto

---

## DEC-06: Archivos temporales en tests con rutas relativas

**Fecha**: Febrero 2026
**Estado**: Aprobada
**Contexto**: Los tests necesitan crear archivos CSV temporales para probar la ingesta
y el workflow completo.

**Decision**: Crear archivos temporales con `open()` / `.close()` en rutas relativas
(por ejemplo `"test_temp.csv"`), ejecutar el test, y borrar con `os.remove()` al final.

**Justificacion**:
- Consistente con el estilo del proyecto (no usa context managers `with`)
- `os.remove()` al final asegura limpieza
- Las rutas relativas funcionan porque los tests se ejecutan desde `challenge/`
- No se usa `tempfile` para mantener simplicidad

---

## DEC-07: Python 3.10+ como version minima

**Fecha**: Febrero 2026
**Estado**: Aprobada
**Contexto**: El README indicaba Python 3.10+ pero el SRS indicaba Python 3.8+,
generando una inconsistencia.

**Decision**: Unificar en Python 3.10+ en ambos documentos.

**Justificacion**:
- 3.10 es la version relevante y actual para el contexto del challenge
- No se usan features exclusivas de 3.10 (match/case), pero se alinea con
  lo que el entorno de desarrollo realmente usa
- Mantener una sola version documentada evita confusion

---

## DEC-08: Logger sin libreria logging de Python

**Fecha**: Febrero 2026
**Estado**: Aprobada
**Contexto**: Python tiene un modulo `logging` en la stdlib. El proyecto implementa
su propio logger con funciones `info()`, `warn()`, `error()`.

**Decision**: Usar logger propio (`legacy_system/src/logger.py`) con funciones simples que escriben
a archivo y a consola.

**Justificacion**:
- Simplicidad: el modulo tiene ~50 lineas y es completamente transparente
- El formato de log es exactamente el requerido por RNF-01
- No requiere configuracion de handlers, formatters o niveles del modulo `logging`
- El codigo es defendible en una presentacion tecnica

---

## DEC-09: Artefactos versionados por ejecucion (sin sobreescritura)

**Fecha**: Febrero 2026
**Estado**: Aprobada
**Contexto**: La salida original escribia siempre en rutas fijas (`data/solicitudes_limpias.csv`,
`data/reporte_calidad.json`, `data/logs/workflow_YYYYMMDD.log`). Si se ejecutaba mas de una
vez el mismo dia, los artefactos se sobreescribian y se perdia trazabilidad fina por corrida.

**Decision**: Cada ejecucion crea una carpeta unica:
`data/ejecuciones/ejecucion_YYYYMMDD_HHMMSS_<archivo>/`
y dentro guarda:
- `solicitudes_limpias.csv`
- `reporte_calidad.json`
- `workflow.log`

**Justificacion**:
- Mejora auditabilidad: todos los artefactos de una corrida quedan juntos.
- Evita perdida de evidencia por sobreescritura.
- Facilita comparacion entre corridas del mismo dia.
- Hace trazable el origen (nombre de archivo) y momento exacto (timestamp).

**Alternativa descartada**:
- Mantener rutas fijas y agregar solo timestamp al log diario: no evita sobreescritura de
  `solicitudes_limpias.csv` y `reporte_calidad.json`.

---

## DEC-10: Soporte multi-formato (CSV, JSON, TXT)

**Fecha**: Febrero 2026
**Estado**: Aprobada
**Contexto**: El enunciado del challenge tecnico indica que las solicitudes pueden llegar
en formato CSV, JSON o TXT. La implementacion inicial solo soportaba CSV.

**Decision**: Agregar soporte para JSON (array de objetos) y TXT (delimitado por pipe `|`),
detectando el formato automaticamente por la extension del archivo.

**Justificacion**:
- El enunciado explicitamente dice "CSV/JSON/TXT" (docs/challenge_tecnico.md, linea 10)
- La deteccion por extension es simple, predecible y no requiere heuristicas de contenido
- Cada formato tiene su funcion dedicada (`leer_json()`, `leer_txt()`) manteniendo modularidad
- Si la extension no es soportada, se retorna None y se loguea ERROR
- La salida siempre es CSV independientemente del formato de entrada

**Formatos**:
- **CSV**: separado por comas, primera linea es header (comportamiento existente)
- **JSON**: array de objetos `[{"campo": "valor", ...}, ...]`
- **TXT**: delimitado por pipe (`|`), primera linea es header

**Alternativas descartadas**:
- Deteccion por contenido (sniffing): fragil, ambigua y mas compleja de implementar
- Parametro de formato obligatorio: agrega friccion al operador sin beneficio real

---

## DEC-11: Seleccion de archivo por argumento CLI o menu interactivo

**Fecha**: Febrero 2026
**Estado**: Aprobada
**Contexto**: La implementacion original hardcodeaba `solicitudes.csv` como archivo de entrada.
Con el soporte multi-formato (DEC-10), el operador necesita poder elegir que archivo procesar.

**Decision**: Implementar doble mecanismo de seleccion:
1. **Argumento CLI**: `python legacy_system/src/main.py data/solicitudes.json` - el archivo se pasa como `sys.argv[1]`
2. **Menu interactivo**: si no se pasa argumento, se listan los archivos `.csv`, `.json`, `.txt`
   disponibles en `data/` y el operador elige por numero

**Justificacion**:
- El argumento CLI permite automatizacion (scripts, cron, pipelines)
- El menu interactivo es amigable para uso manual y evita errores de tipeo en rutas
- Si no hay archivos disponibles o la opcion es invalida, se retorna error controlado
- Los tests existentes no se ven afectados porque usan `archivo_entrada_param` (parametro directo)

**Alternativas descartadas**:
- Solo argumento CLI sin menu: poco amigable para operadores que no conocen las rutas
- Argparse: agrega complejidad innecesaria para un solo parametro opcional

---

## DEC-12: Arquitectura dual `legacy_system` + `ai_first_system`

**Fecha**: Febrero 2026  
**Estado**: Aprobada  
**Contexto**: El challenge evoluciono de un flujo unico a una plataforma comparativa con baseline estable y pista AI.

**Decision**: Separar implementacion en dos sistemas explicitos:
- `legacy_system/src/` para baseline deterministico
- `ai_first_system/src/` para flujo hibrido con LLM real

**Justificacion**:
- Facilita comparacion tecnica y de negocio (tiempo, calidad, costo)
- Aisla regresiones: cambios en AI-First no rompen baseline legacy
- Mejora trazabilidad de requerimientos por modulo y por suite de tests

---

## DEC-13: Politica de LLM real obligatoria (sin mocks)

**Fecha**: Febrero 2026  
**Estado**: Aprobada  
**Contexto**: Habia riesgo de validar AI-First con dobles de prueba en lugar de llamadas reales al provider.

**Decision**:
- Prohibir mocks/stubs/fakes de LLM en capas de runtime y pruebas de contrato/integracion.
- Mantener `gemini` como provider por defecto.
- Bloquear `MODO_MOCK` en ejecucion real.

**Justificacion**:
- Evita falsos positivos en calidad y enrutamiento
- Garantiza que benchmark y contrato midan comportamiento real
- Alinea evaluacion tecnica con el objetivo del challenge (AI aplicada en condiciones reales)

---

## DEC-14: `.env.local` como fuente obligatoria de configuracion Gemini

**Fecha**: Febrero 2026  
**Estado**: Aprobada  
**Contexto**: La configuracion de LLM podia quedar incompleta o dispersa, generando fallas silenciosas.

**Decision**:
- Validar obligatoriamente en AI-First la presencia de:
  - `GEMINI_API_KEY`
  - `GEMINI_GEMMA_MODEL`
  - `GEMINI_EMBEDDING_MODEL`
- Si falta algo, abortar con mensaje claro sin fallback.

**Justificacion**:
- Reduce errores operativos y estados ambiguos
- Hace reproducible la ejecucion AI-First
- Mantiene una sola fuente de verdad de configuracion

---

## DEC-15: Contrato AI-First con casos ambiguos forzando `llm_path`

**Fecha**: Febrero 2026  
**Estado**: Aprobada  
**Contexto**: Un test de contrato podia pasar sin validar realmente el camino LLM ni las llamadas al provider.

**Decision**:
- Incorporar casos ambiguos controlados en contrato.
- Exigir asserts explicitos:
  - `stats["llm_path"] > 0`
  - incremento de metricas reales del provider (`total_llamadas` o equivalente)

**Justificacion**:
- Garantiza cobertura del camino hibrido completo
- Evita contratos que validan solo forma de salida sin ejecutar LLM real

---

## DEC-16: Metricas LLM sin subreporte silencioso

**Fecha**: Febrero 2026  
**Estado**: Aprobada  
**Contexto**: Se observaron corridas con `llm_calls_totales > 0` y tokens/costo en `0`, lo que subreportaba uso real.

**Decision**:
- Introducir estados explicitos de disponibilidad:
  - `token_usage_estado`: `sin_llamadas`, `completo`, `parcial`, `sin_datos`
  - `costo_estimado_estado`: `sin_llamadas`, `completo`, `parcial`, `no_disponible`
- Publicar `llm_tokens_prompt`, `llm_tokens_completion`, `llm_costo_estimado_usd` como `None`
  cuando no hay usage metadata confiable.

**Justificacion**:
- Evita confundir "dato no disponible" con "valor real cero"
- Mejora lectura de benchmarks para toma de decision

---

## DEC-17: Compatibilidad de usage metadata entre SDK Gemini nuevo y legacy

**Fecha**: Febrero 2026  
**Estado**: Aprobada  
**Contexto**: Distintas versiones/SDKs de Gemini exponen usage con estructuras y nombres de campos diferentes.

**Decision**:
- Implementar extraccion robusta de tokens en `gemini_adapter.py` para:
  - `google.genai` (SDK nuevo)
  - `google-generativeai` (SDK legacy)
- Incluir fallback controlado de SDK nuevo a legacy en runtime.

**Justificacion**:
- Mantiene continuidad operativa ante diferencias de SDK
- Reduce perdidas de telemetria de tokens/costo

---

## DEC-18: Higiene estructural del repo y artefactos efimeros

**Fecha**: Febrero 2026  
**Estado**: Aprobada  
**Contexto**: El repositorio acumulaba artefactos efimeros (ejecuciones, caches, carpetas temporales) que degradaban legibilidad.

**Decision**:
- Consolidar estructura canonicamente en:
  - `legacy_system/`
  - `ai_first_system/`
  - `metrics/`
  - `docs/`
  - `tests/`
- Ignorar artefactos de ejecucion/caches en `.gitignore` y conservar carpetas con `.gitkeep`.

**Justificacion**:
- Reduce ruido de versionado
- Facilita auditoria de codigo y documentacion
- Alinea estructura real con README/SRS

---

## Resumen de Decisiones

| ID | Titulo | Prioridad | Modulos afectados |
|----|--------|-----------|-------------------|
| DEC-01 | Parsing CSV manual | Media | ingesta.py |
| DEC-02 | Validacion formato, no calendario | Media | validador.py |
| DEC-03 | Deteccion dinamica de reglas | Alta | calidad.py |
| DEC-04 | Guard strings vacios | Alta | validador.py, normalizador.py |
| DEC-05 | Tests con flag ok | Baja | tests/ |
| DEC-06 | Archivos temporales en tests | Baja | tests/ |
| DEC-07 | Python 3.10+ unificado | Baja | docs/ |
| DEC-08 | Logger propio | Media | logger.py |
| DEC-09 | Artefactos por ejecucion | Alta | main.py, logger.py, docs/, tests/ |
| DEC-10 | Soporte multi-formato CSV/JSON/TXT | Alta | ingesta.py, docs/, tests/ |
| DEC-11 | Seleccion archivo CLI o menu interactivo | Media | main.py, docs/ |
| DEC-12 | Arquitectura dual legacy + ai_first | Alta | legacy_system/, ai_first_system/, main.py |
| DEC-13 | Politica LLM real sin mocks | Alta | ai_first_system/, tests/contract/, tests/integration/ |
| DEC-14 | `.env.local` obligatorio para Gemini | Alta | ai_first_system/src/config.py, run_ai_first.py |
| DEC-15 | Contrato con `llm_path` y llamadas reales | Alta | tests/contract/test_contract.py |
| DEC-16 | Metricas LLM sin subreporte silencioso | Alta | ai_first_system/src/adapters/llm_provider.py, metrics/metricas.py |
| DEC-17 | Compatibilidad usage SDK nuevo/legacy | Media | ai_first_system/src/adapters/gemini_adapter.py |
| DEC-18 | Higiene estructural y artefactos efimeros | Media | .gitignore, data/, metrics/reports/, tests/ejecuciones/ |
