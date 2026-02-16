# Challenge Tecnico - Instrucciones para IA

## REGLA FUNDAMENTAL

**NUNCA generes codigo o hagas decisiones de diseno sin consultar primero el Knowledge Graph.**

Este proyecto usa GraphRAG con Neo4j para almacenar:
1. **Estilo de codigo Python del usuario** - Como escribe codigo
2. **Conocimiento de Ingenieria de Requerimientos** - Metodologia y artefactos

## MCP Tools Disponibles (OBLIGATORIOS)

### 1. `digital-twin_search_python_style`
**USAR ANTES de escribir CUALQUIER codigo Python.**

```
Busca: "if else", "while loop", "file reading", "string manipulation"
Retorna: Codigo REAL del usuario mostrando su estilo
```

### 2. `digital-twin_search_requirements`
**USAR ANTES de tomar decisiones de diseno o arquitectura.**

```
Busca: "validacion", "SRS", "trazabilidad", "stakeholder", "casos de uso"
Retorna: Conocimiento de ingenieria de requerimientos del usuario
```

### 3. `digital-twin_get_python_pattern`
**USAR cuando necesites ver TODOS los ejemplos de un patron especifico.**

```
Patrones: "while_loop", "if_statement", "file_reading", "dictionary_operations"
Retorna: Descripcion + codigo completo de todas las funciones con ese patron
```

### 4. `digital-twin_get_combined_context`
**USAR para queries que necesitan ambos dominios.**

```
Busca: "workflow procesamiento", "validacion datos"
Retorna: Contexto combinado de Python style + Requirements Engineering
```

## Workflow OBLIGATORIO

### Antes de escribir codigo:

```
1. digital-twin_search_python_style("lo que vas a implementar")
2. Analizar el estilo del usuario
3. Escribir codigo que COINCIDA con ese estilo
4. Verificar que no usas features que el usuario NO usa
```

### Antes de disenar:

```
1. digital-twin_search_requirements("concepto de diseno")
2. Aplicar la metodologia del usuario
3. Crear artefactos segun su conocimiento
```

## Estilo de Codigo del Usuario (RESUMEN)

### LO QUE USA:
- Variables cortas en espanol: `ls`, `d`, `arch`, `linea`
- Funciones snake_case: `calcular_promedio()`
- `while` loops con control manual de indice
- Diccionarios para acumulacion: `d[key] = valor`
- String concatenation con `+`
- Comentarios en espanol
- `open()/close()` explicito (no `with`)

### LO QUE NO USA (EVITAR):
- List comprehensions: `[x for x in lista]`
- f-strings: `f"valor: {x}"`
- Lambda functions
- Type hints: `def func(x: int) -> str:`
- Context managers: `with open(...) as f:`
- Decorators: `@decorator`

## Estructura del Challenge

```text
challenge/
|- CLAUDE.md
|- AGENTS.md
|- main.py
|- requirements.txt
|- pytest.ini
|- legacy_system/
|  `- src/           # Baseline deterministico (RF-01..RF-05)
|- ai_first_system/
|  `- src/           # Flujo hibrido con Gemini real
|- metrics/
|  |- benchmark_runner.py
|  |- data_generator.py
|  |- metricas.py
|  |- datasets/
|  `- reports/
|- docs/             # Documentacion (SRS, resumen y decisiones)
|  |- challenge_tecnico.md
|  |- diseno_resumido.md
|  |- diseno_srs.md
|  |- diseno_srs_ai_first.md
|  `- registro_decisiones.md
|- tests/            # legacy, ai_first, contract, integration, metrics
|- data/
|  |- solicitudes.csv
|  `- ejecuciones/
|     `- ejecucion_YYYYMMDD_HHMMSS_<archivo>/
|        |- solicitudes_limpias.csv
|        |- reporte_calidad.json
|        `- workflow.log
`- README.md
```

## Politica AI-First (Obligatoria)

- Provider por defecto y unico soportado en runtime: `gemini`.
- No usar mocks/stubs/fakes de LLM en ejecucion real.
- Configuracion obligatoria desde `.env.local`:
  - `GEMINI_API_KEY`
  - `GEMINI_GEMMA_MODEL`
  - `GEMINI_EMBEDDING_MODEL`
- Si falta configuracion, AI-First debe fallar con mensaje claro (sin fallback mock).

## Tests y Metricas Reales

- `tests/contract/test_contract.py` debe validar casos ambiguos reales:
  - `stats["llm_path"] > 0`
  - incremento de llamadas reales del provider (`total_llamadas` o equivalente)
- `tests/integration/test_real_llm.py` valida provider Gemini real desde `.env.local`.
- Benchmark (`metrics/benchmark_runner.py` + `metrics/metricas.py`) debe evitar subreporte:
  - cuando no hay usage metadata, publicar tokens/costo como `NO_DISPONIBLE` (`null` en JSON)
  - reportar estados de disponibilidad (`completo`, `parcial`, `sin_datos`, `no_disponible`)

## Refactor AI-First de Performance (Obligatorio)

### Clasificacion previa

- Clasificar cada registro en:
  - `VALIDO_DIRECTO`
  - `INVALIDO_DIRECTO`
  - `AMBIGUO_REQUIERE_IA`
- Solo `AMBIGUO_REQUIERE_IA` puede ir a LLM.
- Registrar trazabilidad por registro (motivo, regla, ronda/batch, estado final).

### Criterios de ambiguo

- Fecha semantica no deterministica (ej: `15 marzo 2025`)
- Campo parcialmente interpretable fuera de regex estricta
- Valor que requiere inferencia contextual real

### Motor de ambiguos

- Payload minimo por registro ambiguo
- Batching por tamano y tope de tokens estimados
- Ejecucion paralela con concurrencia acotada
- Rondas de pendientes con timeout/retry/backoff
- Fallback tecnico explicito al agotar rondas

### Tunables via `.env.local` (opcionales)

- `AI_FIRST_TIMEOUT_LLM_SEGUNDOS`
- `AI_FIRST_BATCH_SIZE`
- `AI_FIRST_BATCH_MAX_TOKENS`
- `AI_FIRST_BATCH_MAX_WORKERS`
- `AI_FIRST_BATCH_TIMEOUT_SEGUNDOS`
- `AI_FIRST_BATCH_MAX_RONDAS`
- `AI_FIRST_BATCH_RETRIES`
- `AI_FIRST_BATCH_BACKOFF_SEGUNDOS`

## Criterios de Evaluacion del Challenge (CUMPLIR TODOS)

> "Claridad de diseno, estandares, diagramas, calidad de validaciones
> y del reporte, simplicidad, sin complejidad innecesaria, comunicacion tecnica."

### 1. Claridad de diseno y calidad del diagrama
- Diagrama de flujo: Entrada -> Procesamiento -> Validacion -> Salida
- Componentes claros del workflow
- Donde y como se generan logs
- Puntos de validacion y controles de calidad

### 2. Estandares aplicados
- Convenciones de nombres (snake_case, espanol)
- Estructura de carpetas/modulos (separacion por responsabilidad)
- Criterios de logging (que, cuando, nivel info/warn/error)
- Manejo de errores (categorias, mensajes, propagacion)
- Supuestos tecnicos documentados

### 3. Calidad de validaciones y reporte de control
- Al menos 3 reglas de validacion:
  - R1: Campos obligatorios presentes
  - R2: Formato de fecha valido y moneda en lista soportada
  - R3: Rango de monto_o_limite valido (> 0)
- Reporte JSON con totales, detalle por regla, % cumplimiento

### 4. Simplicidad efectiva
- Hace lo necesario sin complejidad innecesaria
- Sin frameworks pesados
- Codigo que el usuario pueda defender en presentacion

### 5. Trazabilidad
- Que se hizo, cuando y por que
- Logs con timestamps y niveles
- Matriz de trazabilidad: Requerimiento -> Componente -> Test

### 6. Supervision tecnica
- Mantenibilidad: modulos independientes, responsabilidad unica
- Code review: que revisarias
- Riesgos: errores de formato, datos faltantes, inconsistencias

## Aplicar TODA la Ingenieria de Requerimientos

El diseno DEBE seguir:
- Proceso: Elicitacion -> Analisis -> Especificacion -> Validacion
- Objetivos SMART
- Documento SRS (IEEE)
- Matriz de trazabilidad
- Criterios de aceptacion (DADO/CUANDO/ENTONCES)
- Checklist de validacion de requerimientos

**Aplicar TODO el conocimiento de ingenieria de requerimientos del usuario.**


