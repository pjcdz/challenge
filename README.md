# Challenge Tecnico - Mini-Workflow Supervisado Back-Office

Plataforma dual para procesar solicitudes de alta de productos (cuentas, tarjetas y servicios).  
Lee archivos CSV, JSON o TXT, normaliza, valida con 3 reglas de elegibilidad, genera un reporte de calidad JSON y registra logs con trazabilidad completa.

La solucion incluye dos caminos de ejecucion:
- **Modo Legacy**: Sistema deterministico puramente basado en reglas (baseline original)
- **Modo AI-First**: Sistema hibrido con enrutamiento inteligente (reglas + LLM para casos ambiguos)
- **Modo Comparar**: Benchmark para comparar rendimiento y calidad entre ambos modos

## Estructura del Proyecto

```text
challenge/
|- CLAUDE.md
|- AGENTS.md
|- README.md
|- main.py
|- requirements.txt
|- pytest.ini
|- .env.local                     # Configuracion local LLM (no versionar)
|- legacy_system/
|  |- src/                        # Baseline deterministico
|  |  |- main.py
|  |  |- ingesta.py
|  |  |- normalizador.py
|  |  |- validador.py
|  |  |- calidad.py
|  |  `- logger.py
|  |- data/
|  |  `- ejecuciones/             # Salidas legacy por corrida
|  `- tests/
|     |- test_ingesta.py
|     |- test_normalizador.py
|     |- test_validador.py
|     |- test_calidad.py
|     |- test_main.py
|     `- ejecuciones/             # Solo .gitkeep en repo
|- ai_first_system/
|  |- src/
|  |  |- config.py
|  |  |- router_ambiguedad.py
|  |  |- run_ai_first.py
|  |  |- adapters/
|  |  |- agents/
|  |  |- graph/
|  |  |- guardrails/
|  |  `- prompts/
|  `- tests/
|- data/
|  |- solicitudes.csv
|  |- solicitudes.json
|  |- solicitudes.txt
|  `- ejecuciones/                # Salidas workflow (legacy y AI-First)
|- metrics/
|  |- benchmark_runner.py
|  |- data_generator.py
|  |- metricas.py
|  |- datasets/
|  `- reports/                    # Reportes benchmark JSON/MD
|- tests/
|  |- test_root_main.py
|  |- legacy/
|  |- ai_first/
|  |- contract/
|  |- integration/
|  |- metrics/
|  `- ejecuciones/                # Solo .gitkeep en repo
`- docs/
   |- challenge_tecnico.md
   |- diseno_resumido.md
   |- diseno_srs.md
   |- diseno_srs_ai_first.md
   `- registro_decisiones.md
```

## Requisitos

- Python 3.10+ (Python 3.13.7 probado)
- **Modo Legacy**: Sin dependencias externas (stdlib unicamente)
- **Modo AI-First**: `requirements.txt` (google-genai, google-generativeai, Pydantic, python-dotenv, LangGraph)
- `pytest` (solo para ejecutar tests)

### Configuracion Obligatoria de AI-First

AI-First solo funciona con LLM real Gemini y configuracion explicita en `.env.local`.

Variables obligatorias:
- `GEMINI_API_KEY`
- `GEMINI_GEMMA_MODEL`
- `GEMINI_EMBEDDING_MODEL`

Ejemplo de `.env.local`:

```env
GEMINI_API_KEY=tu_api_key
GEMINI_GEMMA_MODEL=gemini-2.0-flash
GEMINI_EMBEDDING_MODEL=text-embedding-004
```

Si falta alguna variable obligatoria, AI-First falla con mensaje claro y no usa fallback mock.

## Ejecucion

### 1. Menu Principal Interactivo

```bash
cd challenge

# Menu unificado con 5 opciones:
python main.py
```

El menu ofrece las siguientes opciones:

**1. Usar sistema Legacy**
   - Ejecuta el baseline deterministico
   - Procesa reglas puras (R1, R2, R3)
   - Alta velocidad y bajo costo

**2. Usar sistema AI-First**
   - Ejecuta el pipeline hibrido
   - Enrutamiento inteligente: reglas primero, LLM solo para casos ambiguos
   - Mayor robustez semantica en datos sucios o ambiguos

**3. Comparar performance (Benchmark)**
   - Ejecuta ambos modos sobre el mismo dataset
   - Genera reporte comparativo en `metrics/reports/`
   - Metricas: tiempo, throughput, calidad, costo LLM

**4. Generar dataset sintetico**
   - Genera datasets de prueba con distribucion controlada
   - Parametros: cantidad, seed, ratios (limpio/sucio/ambiguo), formato
   - Crea ground truth para evaluacion de calidad

**5. Salir**
   - Termina el programa

### 2. Modo CLI (No Interactivo)

```bash
cd challenge

# Ejecutar sistema legacy
python main.py --modo legacy --input data/solicitudes.csv

# Ejecutar sistema AI-First
python main.py --modo ai_first --input data/solicitudes.csv --provider gemini

# Comparar ambos modos
python main.py --modo comparar --input metrics/datasets/synth_1k.csv

# Generar dataset sintetico
python main.py --modo generar --cantidad 10000 --seed 42 --formato csv

# Ver todas las opciones
python main.py --help
```

**Opciones CLI disponibles:**

| Opcion | Descripcion | Default |
|---------|-------------|----------|
| `--modo` | Modo de ejecucion: legacy, ai_first, comparar, generar | (requerido) |
| `--input` | Archivo de entrada (CSV/JSON/TXT) | - |
| `--provider` | Provider LLM para AI-First: gemini | gemini |
| `--cantidad` | Cantidad de registros para generar (modo generar) | 100 |
| `--seed` | Seed para reproducibilidad | 42 |
| `--ratio-limpio` | Ratio de registros limpios | 0.5 |
| `--ratio-sucio` | Ratio de registros sucios | 0.3 |
| `--ratio-ambiguo` | Ratio de registros ambiguos | 0.2 |
| `--formato` | Formato de salida: csv, json, txt | csv |

### 3. Salidas de Ejecucion

**Legacy Mode:**
Cada ejecucion crea una carpeta en `data/ejecuciones/`:
```
data/ejecuciones/ejecucion_YYYYMMDD_HHMMSS_<archivo>/
|- solicitudes_limpias.csv
|- reporte_calidad.json
`- workflow.log
```

**AI-First Mode:**
Cada ejecucion crea una carpeta en `data/ejecuciones/`:
```
data/ejecuciones/ejecucion_YYYYMMDD_HHMMSS_<archivo>/
|- solicitudes_limpias.csv    # Incluye origen_procesamiento, retries_llm
|- reporte_calidad.json       # Incluye metricas de enrutamiento y LLM
`- workflow.log               # Logs con trazabilidad LLMOps
```

**Benchmark Reports:**
Los resultados de comparacion se guardan en `metrics/reports/`:
```
metrics/reports/benchmark_YYYYMMDD_HHMMSS.json
metrics/reports/benchmark_YYYYMMDD_HHMMSS.md
```

### 4. Correr los Tests

```bash
cd challenge

# Ejecutar todos los tests
python -m pytest tests/ -v

# Ejecutar tests especificos
python -m pytest tests/legacy/ -v           # Tests de no-regresion legacy
python -m pytest tests/ai_first/ -v          # Tests de AI-First (incluyen provider real)
python -m pytest tests/contract/ -v          # Tests de contrato (fuerzan llm_path real)
python -m pytest tests/metrics/ -v           # Tests de metrics
python -m pytest tests/test_root_main.py -v   # Tests de menu root
python -m pytest tests/integration/ -v        # Integracion real Gemini (.env.local, sin mocks)
```

La suite completa `python -m pytest -q` asume `.env.local` valido para Gemini.

**Politica obligatoria de LLM real (AI-First):**
- No se permiten mocks/stubs/fakes del provider Gemini ni de llamadas LLM.
- Provider por defecto: `gemini`.
- `.env.local` es obligatorio y debe definir `GEMINI_API_KEY`, `GEMINI_GEMMA_MODEL` y `GEMINI_EMBEDDING_MODEL`.
- Si falta alguna variable obligatoria, AI-First falla con mensaje claro de configuracion (sin fallback mock).

## Flujo del Workflow

### Modo Legacy (Deterministico)

```text
solicitudes.csv / .json / .txt
    |
    v
[1] INGESTA -> detecta formato por extension, lee y arma registros
    |
    v
[2] NORMALIZACION -> trimming, upper/lower, fecha DD/MM/YYYY, categoria_riesgo
    |
    v
[3] VALIDACION -> R1 obligatorios, R2 fecha/moneda, R3 rango de monto
    |
    v
[4] CALIDAD -> totales, porcentaje global y detalle por regla
    |
    v
[5] EXPORTACION -> CSV limpio + reporte JSON + log en carpeta de ejecucion
```

### Modo AI-First (Hibrido)

```text
solicitudes.csv / .json / .txt
    |
    v
[1] INGESTA BASE -> lee registros, agrega campos de tracking
    |
    v
[2] ENRUTAMIENTO HIBRIDO
    |
    +--> [REGLA PATH] ~80-95% de registros
    |     |
    |     v
    |  [2a] NORMALIZACION DETERMINISTICA
    |     |
    |     v
    |  [3a] VALIDACION (R1/R2/R3)
    |     |
    |     v
    |  [4a] CONTROL DE CALIDAD
    |
    +--> [LLM PATH] ~5-20% de registros (ambiguos)
          |
          v
       [2b] DETECTOR DE AMBIGUEDAD
          |
          v
       [3b] NORMALIZACION SEMANTICA (LLM)
          |  - Resuelve sinonimos desconocidos
          |  - Normaliza fechas textuales
          |  - Inferencia de categorias
          |
          v
       [4b] GUARDRAILS + RETRY
          |  - Schema estricto Pydantic
          |  - Validacion post-LLM
          |  - Prompt correctivo (max 2 retries)
          |  - Fallback a INVALIDO si falla
          |
          v
       [5b] VALIDACION DURA (R1/R2/R3)
          |
          v
       [6b] CALIDAD EXPANSIVA
          |  - Metricas legacy
          |  - Metricas de enrutamiento
          |  - Metricas LLM (tokens, costo, retries)
          |
    |---------------------|
    v
[7] EXPORTACION COMUN
    |  - CSV con origen_procesamiento (rule_path/llm_path)
    |  - Reporte JSON extendido
    |  - Logs con trazabilidad completa
```

### Comparador (Benchmark)

```text
Dataset de entrada
    |
    v
+--> [Ejecutar Legacy] --> Registros limpios + metricas
|   - Tiempo total
|   - Throughput
|   - Validos/Invalidos
|
|   v
+--> [Ejecutar AI-First] --> Registros + metricas extendidas
|   - Tiempo total
|   - Throughput
|   - Validos/Invalidos
|   - Porcentaje LLM
|   - Tokens, costo y estado de disponibilidad
|
v
[GENERAR REPORTE]
  - Ratio tiempo (AI/Legacy)
  - Diferencia de validos
  - Precision en subset ambiguo
  - Costo estimado
  - Analisis cualitativo
```

## Diferencias entre Modos

| Aspecto | Legacy | AI-First |
|---------|--------|----------|
| **Algoritmo** | Reglas deterministicas puras | Reglas + LLM para ambiguos |
| **Velocidad** | Muy rapida (solo local) | Rapida (80-95% por reglas, 5-20% LLM) |
| **Costo** | Cero (sin LLM) | Bajo (solo para casos ambiguos) |
| **Robustez** | Datos limpios y sucios resueltos por reglas | Tambien resuelve datos semanticamente ambiguos |
| **Trazabilidad** | Logs basicos | Logs extendidos + metricas LLM |
| **Output** | CSV basico | CSV + origen_procesamiento + retries_llm |

**Cuando usar cada modo:**

- **Legacy**: Produccion con datos limpios o bien estructurados; prioridad velocidad
- **AI-First**: Datos ambiguos, texto libre, sinonimos desconocidos; prioridad calidad
- **Comparar**: Analisis decision sobre migracion; benchmarking

## Caracteristicas del Modo AI-First

### Enrutamiento Hibrido
El router clasifica cada registro y decide la ruta:

- **Rule Path** (80-95% de casos):
  - Fechas en formato estandar (DD/MM/YYYY, YYYY-MM-DD, DD-MM-YYYY)
  - Monedas canonicas o sinonimos conocidos (ARS, USD, EUR, pesos, dolares, euros)
  - Tipos de producto canonicos o sinonimos (CUENTA, TARJETA, SERVICIO, PRESTAMO, SEGURO)
  - Paises canonicos o sinonimos (Argentina, Brasil, Chile, etc.)

- **LLM Path** (5-20% de casos):
  - Fechas textuales ("15 de marzo", "Q1 2025")
  - Monedas o productos desconocidos
  - Paises en idiomas extranjeros
  - Campos que requieren inferencia semantica

### Guardrails de Salida

Toda respuesta del LLM pasa por validaciones:

1. **Schema Estricto**: Pydantic model para estructura y tipos
2. **Validacion de Campo**:
   - Fecha: DD/MM/YYYY, rango valido
   - Moneda: ARS, USD, EUR
   - Tipo Producto: CUENTA, TARJETA, SERVICIO, PRESTAMO, SEGURO
   - Monto: entero positivo y dentro de rango
3. **Retry Acotado**: Maximo 2 reintentos con prompt correctivo
4. **Fallback**: Marca como INVALIDO si falla despues de reintentos

### Metricas de Salida

El reporte de calidad AI-First incluye:

```json
{
  "resumen": { /* metricas legacy */ },
  "ai_first": {
    "enrutamiento": {
      "total_registros": 1000,
      "rule_path": 850,
      "llm_path": 150,
      "porcentaje_llm": 15.0,
      "total_fallbacks": 3,
      "total_retries_llm": 12,
      "sinonimos_resueltos": 42
    },
    "llm_provider": {
      "total_llamadas": 150,
      "total_llamadas_exitosas": 148,
      "total_llamadas_con_tokens": 145,
      "total_llamadas_sin_tokens": 5,
      "token_usage_disponible": true,
      "token_usage_estado": "parcial",
      "total_tokens_prompt": 30000,
      "total_tokens_completion": 15000,
      "costo_estimado_usd": 0.00675,
      "costo_estimado_estado": "parcial",
      "total_llamadas_fallidas": 2
    }
  }
}
```

Si el SDK no devuelve usage metadata en llamadas reales, el benchmark reporta
`llm_tokens_prompt`, `llm_tokens_completion` y `llm_costo_estimado_usd` como
`NO_DISPONIBLE` (`null` en JSON) para evitar subreporte silencioso en `0`.

## Reglas de Validacion

| Regla | Que valida | Criterio de falla |
|---|---|---|
| R1 | Campos obligatorios | Algun campo obligatorio vacio |
| R2 | Fecha y moneda | Fecha no valida para DD/MM/YYYY o moneda fuera de [ARS, USD, EUR] |
| R3 | Rango de monto | monto <= 0 o monto > 999999999 |

## Campos de Entrada

`id_solicitud, fecha_solicitud, tipo_producto, id_cliente, monto_o_limite, moneda, pais, flag_prioritario, flag_digital`

## Formatos de Entrada Soportados

| Formato | Extension | Separador | Ejemplo |
|---|---|---|---|
| CSV | `.csv` | Coma (`,`) | `data/solicitudes.csv` |
| JSON | `.json` | Array de objetos | `data/solicitudes.json` |
| TXT | `.txt` | Pipe (`\|`) | `data/solicitudes.txt` |

El formato se detecta automaticamente por la extension del archivo. La salida siempre es CSV.

## Documentacion

- `docs/diseno_resumido.md`: version corta para entrega (1-2 paginas).
- `docs/diseno_srs.md`: especificacion completa (SRS extendido) del sistema legacy.
- `docs/diseno_srs_ai_first.md`: especificacion completa del sistema AI-First con arquitectura hibrida.
- `docs/registro_decisiones.md`: decisiones tecnicas del proyecto.
- `docs/challenge_tecnico.md`: enunciado original.

## Ejemplos de Uso

### Ejemplo 1: Procesar con Legacy (rapido)

```bash
# Menu interactivo
python main.py
# Seleccionar: 1. Usar sistema Legacy

# CLI directo
python main.py --modo legacy --input data/solicitudes.csv
```

### Ejemplo 2: Procesar con AI-First (robusto)

```bash
# Menu interactivo
python main.py
# Seleccionar: 2. Usar sistema AI-First

# CLI directo
python main.py --modo ai_first --input data/solicitudes.csv --provider gemini
```

### Ejemplo 3: Comparar rendimientos

```bash
# Generar dataset sintetico primero
python main.py --modo generar --cantidad 500 --seed 123

# Comparar ambos modos sobre el dataset
python main.py --modo comparar --input metrics/datasets/synth_500_s123.csv

# Revisar reporte en:
# metrics/reports/benchmark_YYYYMMDD_HHMMSS.md
```

### Ejemplo 4: Test de escala

```bash
# Generar dataset grande
python main.py --modo generar --cantidad 10000 --seed 42 --formato csv

# Procesar con legacy (rapido)
python main.py --modo legacy --input metrics/datasets/synth_10000_s42.csv

# Procesar con AI-First (robusto)
python main.py --modo ai_first --input metrics/datasets/synth_10000_s42.csv

# Comparar resultados
python main.py --modo comparar --input metrics/datasets/synth_10000_s42.csv
```



