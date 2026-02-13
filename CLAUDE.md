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

```
challenge/
├── CLAUDE.md          # Este archivo - instrucciones IA
├── AGENTS.md          # Knowledge base expandida
├── src/               # Codigo fuente
│   ├── ingesta.py     # RF-01: Lectura de archivos de solicitudes
│   ├── normalizador.py # RF-02: Normalizacion de campos
│   ├── validador.py   # RF-03: Validacion de reglas de elegibilidad
│   ├── calidad.py     # RF-04: Control de calidad y reporte
│   ├── logger.py      # RNF-01: Sistema de logging
│   └── main.py        # Orquestador del workflow
├── docs/              # Documentacion (SRS, diagramas)
│   ├── challenge_tecnico.md  # Enunciado original del challenge
│   └── diseno_srs.md         # Documento de diseno SRS
├── tests/             # Tests
└── data/              # Datos de entrada/salida
    ├── solicitudes.csv       # Entrada
    ├── solicitudes_limpias.csv # Salida normalizada
    ├── reporte_calidad.json  # Reporte de calidad
    └── logs/                 # Archivos de log
```

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
