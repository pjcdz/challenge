# AGENTS.md - Knowledge Base Personal para Challenge Tecnico

## Objetivo

Este archivo contiene el conocimiento personal del usuario para que la IA:
1. **Genere codigo Python que el usuario entienda y pueda defender**
2. **Aplique metodologia de Ingenieria de Requerimientos correctamente**

---

# PARTE 1: ESTILO DE CODIGO PYTHON

## 1.1 Fingerprint de Codigo

### Nomenclatura
| Elemento | Patron | Ejemplos |
|----------|--------|----------|
| Variables | Cortas, espanol, snake_case | `ls`, `d`, `i`, `x`, `arch`, `linea`, `prom` |
| Funciones | snake_case descriptivo | `calcular_promedio()`, `ordenar_lista()` |
| Archivos | Numeros o nombres descriptivos | `01.py`, `final.py` |

### Estructura Tipica

```python
# 1. Imports al inicio (minimos)
from math import pi
from random import randint

# 2. Funciones auxiliares primero
def esletra(x):
    res = False
    if (x>="a" and x<="z") or (x>="A" and x<="Z") or x in "aeiouAEIOU":
        res = True
    return res

# 3. Funcion principal al final
def main():
    arch = open("archivo.txt", "r")
    for linea in arch:
        # procesamiento
        pass
    arch.close()

# 4. Llamada a main
main()
```

## 1.2 Patrones de Codigo OBLIGATORIOS

### While Loop (PREFERIDO sobre for cuando hay control de indice)

```python
# CORRECTO - Estilo del usuario
def algoritmo(t):
    i = 0
    largotexto = len(t)
    while i < largotexto:
        pal = ""
        while i < largotexto and esletra(t[i]):
            pal = pal + t[i]
            i += 1
        # procesar pal
        i += 1
    return res

# INCORRECTO - No usar
# for i, char in enumerate(t):  # NO
```

### Diccionarios como Acumuladores

```python
# CORRECTO - Estilo del usuario
def media_01(n, lstCiudad, lstResiduos):
    d = {}
    for linea in lstResiduos:
        if linea[-1] == "\n":
            linea = linea[:-1]
        ls = linea.split(",")
        if ls[1] not in d.keys():
            d[ls[1]] = [int(ls[0]), 1]
        elif ls[1] in d.keys():
            c = d[ls[1]][1] + 1
            v = d[ls[1]][0] + int(ls[0])
            d[ls[1]] = [v, c]
    return d

# INCORRECTO - No usar
# from collections import defaultdict  # NO
# d = defaultdict(list)  # NO
```

### Lectura de Archivos

```python
# CORRECTO - Estilo del usuario
arch = open("archivo.txt", "r")
for linea in arch:
    if linea[-1] == "\n":
        linea = linea[:-1]
    ls = linea.split(",")
    # procesar
arch.close()

# INCORRECTO - No usar
# with open("archivo.txt", "r") as f:  # NO - context manager
#     lines = f.readlines()  # NO
```

### Concatenacion de Strings

```python
# CORRECTO - Estilo del usuario
res = "Nombre: " + nombre + " - Valor: " + str(valor)

# INCORRECTO - No usar
# res = f"Nombre: {nombre} - Valor: {valor}"  # NO - f-string
```

### Validaciones con if/elif

```python
# CORRECTO - Estilo del usuario
def validar(x):
    res = False
    if x > 0 and x < 100:
        res = True
    elif x == 100:
        res = True
    return res

# INCORRECTO - No usar
# return 0 < x <= 100  # NO - chained comparison
```

## 1.3 Features PROHIBIDOS

| Feature | Ejemplo | Por que NO |
|---------|---------|------------|
| List comprehensions | `[x*2 for x in lista]` | Usuario no los usa |
| f-strings | `f"valor: {x}"` | Usuario usa concatenacion |
| Lambda | `lambda x: x*2` | Usuario define funciones |
| Type hints | `def f(x: int) -> str:` | Usuario no tipea |
| Context managers | `with open() as f:` | Usuario usa open/close |
| Decorators | `@decorator` | Usuario no los usa |
| enumerate/zip | `for i, x in enumerate()` | Usuario usa indices manuales |
| Walrus operator | `if (n := len(x)) > 10:` | Usuario no lo conoce |

---

# PARTE 2: INGENIERIA DE REQUERIMIENTOS

## 2.1 Proceso de Ingenieria de Requerimientos

```
ELICITACION --> ANALISIS --> ESPECIFICACION --> VALIDACION
     |              |              |                |
     v              v              v                v
 Entrevistas   Casos de uso    Doc SRS         Revisiones
 Encuestas     Diagramas       Historias       Pruebas
 Observacion   Modelos         Criterios       Inspecciones
```

## 2.2 Clasificacion de Requerimientos

### Por Origen
- **Negocio**: De la empresa o usuario
- **Sistema**: Tecnicos del sistema

### Por Implementacion
- **Funcionales (RF)**: Que hace el sistema
- **No Funcionales (RNF)**: Como lo hace
  - Producto: Rendimiento, usabilidad
  - Organizacion: Estandares, procesos
  - Externos: Legales, interoperabilidad

## 2.3 Objetivos SMART

| Letra | Significado | Aplicacion |
|-------|-------------|------------|
| S | Especifico | "Procesar archivos CSV" no "Procesar datos" |
| M | Medible | "En menos de 5 segundos" |
| A | Alcanzable | Realista con los recursos |
| R | Relevante | Alineado al negocio |
| T | Tiempo | "Entrega en 2 semanas" |

## 2.4 Artefactos Clave

### Documento SRS (Software Requirements Specification)
```
1. Introduccion
   1.1 Proposito
   1.2 Alcance
   1.3 Definiciones y acronimos
2. Descripcion General
   2.1 Perspectiva del producto
   2.2 Funciones del producto
   2.3 Caracteristicas de usuarios
3. Requerimientos Especificos
   3.1 Requerimientos funcionales
   3.2 Requerimientos no funcionales
4. Apendices
```

### Matriz de Trazabilidad
| ID Req | Descripcion | Componente | Test | Estado |
|--------|-------------|------------|------|--------|
| RF-01 | Leer CSV/JSON/TXT | ingesta.py | test_ingesta | OK |
| RF-02 | Validar datos | validador.py | test_validador | OK |

### Historia de Usuario
```
COMO [rol de usuario]
QUIERO [funcionalidad]
PARA [beneficio/valor]

Criterios de Aceptacion:
- DADO [contexto] CUANDO [accion] ENTONCES [resultado]
```

## 2.5 Tecnicas de Elicitacion

| Tecnica | Cuando Usar | Output |
|---------|-------------|--------|
| Entrevista | Reqs detallados | Notas, grabacion |
| Focus Group | Vision grupal | Consenso |
| Observacion | Proceso actual | Workflow |
| Analisis docs | Sistema existente | Gaps |

## 2.6 Validacion de Requerimientos

### Checklist
- [ ] Completos: No falta informacion
- [ ] Consistentes: No hay contradicciones
- [ ] Correctos: Reflejan necesidad real
- [ ] No ambiguos: Una sola interpretacion
- [ ] Verificables: Se pueden probar
- [ ] Trazables: Origen conocido

---

# PARTE 3: APLICACION AL CHALLENGE

## 3.1 Challenge Tecnico - Contexto

Una unidad de Back-Office recibe solicitudes de alta de productos (cuentas, tarjetas, servicios).
Cada solicitud llega en CSV, JSON o TXT con campos: id_solicitud, fecha_solicitud, tipo_producto, id_cliente,
monto_o_limite, moneda, pais, y 1-2 flags.

### Mini-Workflow requerido:
1. **Ingesta**: Leer archivo de solicitudes
2. **Normalizacion**: Fechas al mismo formato, trimming, upper/lower
3. **Validacion**: 3 reglas de elegibilidad
4. **Control de calidad**: Reporte JSON con totales y detalle por regla
5. **Logs**: Timestamps, niveles info/warn/error, trazabilidad

## 3.2 Criterios de Evaluacion (CUMPLIR OBLIGATORIAMENTE)

| Criterio | Que evaluan | Como cumplirlo |
|----------|-------------|----------------|
| Claridad de diseno | Diagrama de flujo, componentes, trazabilidad | Diagrama mermaid, SRS con estructura IEEE |
| Estandares | Nombres, estructura, logs, errores | snake_case, modulos separados, logging con niveles |
| Validaciones | Calidad de reglas y reporte | 3 reglas minimo, reporte JSON con % cumplimiento |
| Simplicidad | Sin complejidad innecesaria | Sin frameworks, codigo defendible |
| Comunicacion | Presentacion tecnica 20-30 min | Documentacion clara, decisiones justificadas |

## 3.3 Estructura de Modulos (Trazabilidad)

| Modulo | Requerimiento | Responsabilidad |
|--------|---------------|-----------------|
| `main.py` (root) | RF-08 | Orquestar menu/CLI para legacy, ai_first, comparar y generar |
| `legacy_system/src/ingesta.py` | RF-01 | Leer CSV/JSON/TXT, retornar lista de registros |
| `legacy_system/src/normalizador.py` | RF-02 | Normalizar fechas, trimming, mayusculas |
| `legacy_system/src/validador.py` | RF-03 | Aplicar reglas R1, R2, R3 |
| `legacy_system/src/calidad.py` | RF-04 | Generar reporte JSON de calidad |
| `legacy_system/src/logger.py` | RNF-01 | Logging con timestamps y niveles |
| `ai_first_system/src/router_ambiguedad.py` | RF-03 | Enrutar `rule_path` vs `llm_path` |
| `ai_first_system/src/graph/workflow_graph.py` | RF-04 | Resolver casos ambiguos con retry/fallback |
| `ai_first_system/src/guardrails/` | RF-05 | Validar schema y aplicar fallback seguro |
| `ai_first_system/src/adapters/gemini_adapter.py` | RF-05 | Integrar Gemini real y telemetria de usage |
| `metrics/benchmark_runner.py` | RF-06 | Comparar legacy vs ai_first y generar reportes |
| `metrics/metricas.py` | RF-06 | Consolidar metricas de calidad, costo y disponibilidad |
| `metrics/data_generator.py` | RF-07 | Generar datasets sinteticos reproducibles |

## 3.4 Reglas de Validacion

| Regla | Descripcion | Criterio |
|-------|-------------|----------|
| R1 | Campos obligatorios presentes | Todos los campos no vacios |
| R2 | Formato fecha y moneda validos | Fecha DD/MM/YYYY, moneda en ["ARS","USD","EUR"] |
| R3 | Rango de monto valido | monto_o_limite > 0 y <= 999999999 |

## 3.5 Flujo de Trabajo para IA

```
1. ANTES de disenar:
   --> Consultar MCP: search_requirements("concepto")
   --> Aplicar metodologia del usuario (SRS, SMART, trazabilidad)
   
2. ANTES de codificar:
   --> Consultar MCP: search_python_style("patron")
   --> Escribir codigo en estilo del usuario
   
3. SIEMPRE verificar:
   --> El usuario PODRIA haber escrito este codigo?
   --> Aplica el conocimiento de requerimientos?
   --> Cumple los criterios de evaluacion del challenge?
```

## 3.6 Checklist Pre-Commit

### Codigo:
- [ ] Usa patrones del usuario (while, dict acumulador, open/close, etc.)
- [ ] No usa features prohibidos (f-strings, comprehensions, lambda, etc.)
- [ ] Comentarios en espanol
- [ ] Variables con nombres cortos en espanol
- [ ] Funciones snake_case descriptivas

### Diseno:
- [ ] Documentacion sigue estructura SRS (IEEE)
- [ ] Hay diagrama de flujo del workflow
- [ ] Hay matriz de trazabilidad (RF -> Componente -> Test)
- [ ] Requerimientos son SMART
- [ ] Criterios de aceptacion DADO/CUANDO/ENTONCES

### Challenge:
- [ ] 3 reglas de validacion implementadas
- [ ] Reporte JSON de calidad con totales y % cumplimiento
- [ ] Logs con timestamps y niveles (info/warn/error)
- [ ] Datos de entrada de ejemplo (CSV, JSON, TXT)
- [ ] Datos de salida normalizados
- [ ] README con instrucciones de ejecucion

## 3.7 Estructura Canonica y Rutas de Salida

Para mantener concordancia con `README.md`, `CLAUDE.md` y `docs/diseno_srs.md`:

- Documentacion oficial en `docs/`:
  - `challenge_tecnico.md`
  - `diseno_resumido.md`
  - `diseno_srs.md`
  - `diseno_srs_ai_first.md`
  - `registro_decisiones.md`
- Salidas del workflow por corrida (no en la raiz de `data/`):
  - `data/ejecuciones/ejecucion_YYYYMMDD_HHMMSS_<archivo>/solicitudes_limpias.csv`
  - `data/ejecuciones/ejecucion_YYYYMMDD_HHMMSS_<archivo>/reporte_calidad.json`
  - `data/ejecuciones/ejecucion_YYYYMMDD_HHMMSS_<archivo>/workflow.log`

## 3.8 Politica AI-First Obligatoria (Estado Actual)

- Provider por defecto: `gemini`.
- Prohibido usar mocks/stubs/fakes de LLM en runtime y en pruebas de contrato/integracion.
- Configuracion obligatoria en `.env.local`:
  - `GEMINI_API_KEY`
  - `GEMINI_GEMMA_MODEL`
  - `GEMINI_EMBEDDING_MODEL`
- Si falta configuracion, AI-First debe fallar con mensaje claro (sin fallback mock).

## 3.9 Validacion y Metricas (Estado Actual)

- Tests de contrato (`tests/contract/test_contract.py`) deben forzar casos ambiguos reales y verificar:
  - `stats["llm_path"] > 0`
  - incremento de llamadas del provider (`total_llamadas` o equivalente)
- Benchmark y metricas deben evitar subreporte:
  - si hay llamadas LLM reales sin usage metadata, tokens/costo se reportan como `NO_DISPONIBLE` (`null` en JSON)
  - usar estados explicitos: `sin_llamadas`, `completo`, `parcial`, `sin_datos`, `no_disponible`

## 3.10 Refactor AI-First de Performance (Estado Actual)

### Clasificacion obligatoria previa al LLM

- Todo registro debe clasificarse en:
  - `VALIDO_DIRECTO`
  - `INVALIDO_DIRECTO`
  - `AMBIGUO_REQUIERE_IA`
- Solo `AMBIGUO_REQUIERE_IA` se envia al LLM.
- Trazabilidad por registro obligatoria:
  - motivo de clasificacion
  - regla afectada
  - ronda/batch si paso por IA

### Criterios de ambiguo

- Fecha en lenguaje natural no deterministica (ej: `15 marzo 2025`)
- Campo parcialmente interpretable fuera de regex estricto
- Valor que requiere inferencia semantica real

### Criterios deterministas (sin LLM)

- Fechas no canonicas resolubles por reglas:
  - `15 de marzo del 2025`
  - `Mar 15, 2025`
  - `2025/03/15`
  - `15.03.2025`
- Fechas incompletas (`marzo 2025`, `Q1 2025`, `primer trimestre`) -> invalido directo R2
- Monedas directas no soportadas (`GBP`, `MONEDA LOCAL`, `DIVISA EXTRANJERA`) -> invalido directo R2

### Batching paralelo por rondas

- Payload minimo por ambiguo (`id_solicitud` + campos necesarios + reglas)
- Lotes por `batch_size` + tope de tokens estimados
- Ejecucion concurrente con `max_workers`
- Rondas de pendientes con timeout/retry/backoff
- Al agotar rondas: fallback tecnico explicito

### Parametros tunables en `.env.local` (opcionales)

- `AI_FIRST_TIMEOUT_LLM_SEGUNDOS`
- `AI_FIRST_BATCH_SIZE`
- `AI_FIRST_BATCH_MAX_TOKENS`
- `AI_FIRST_BATCH_MAX_WORKERS`
- `AI_FIRST_BATCH_TIMEOUT_SEGUNDOS`
- `AI_FIRST_BATCH_MAX_RONDAS`
- `AI_FIRST_BATCH_RETRIES`
- `AI_FIRST_BATCH_BACKOFF_SEGUNDOS`

---

# REFERENCIA RAPIDA: MCP Tools

```python
# Antes de escribir codigo de loops
digital-twin_get_python_pattern("while_loop")

# Antes de manejar archivos
digital-twin_search_python_style("file reading open close")

# Antes de disenar validaciones
digital-twin_search_requirements("validacion requerimientos")

# Para contexto combinado
digital-twin_get_combined_context("procesamiento datos workflow")
```
