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

**Decision**: Usar logger propio (`src/logger.py`) con funciones simples que escriben
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
