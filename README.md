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

# Generar dataset realista para benchmark (ambiguos reales controlados)
python metrics/data_generator.py --cantidad 1000 --seed 2028 --ratio-limpio 0.7 --ratio-sucio 0.295 --ratio-ambiguo 0.005 --perfil realista --formato csv

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

Para usar el perfil realista del generador (`base` / `realista`), ejecutar `metrics/data_generator.py` de forma directa con `--perfil`.

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
[2] PRECLASIFICACION DETERMINISTICA (sin LLM)
    |
    +--> [VALIDO_DIRECTO] -> rule_path
    |     |
    +--> [INVALIDO_DIRECTO] -> rule_path
    |
    +--> [AMBIGUO_REQUIERE_IA] -> llm_path
          |
          v
       [3] BATCHING PARALELO POR RONDAS
          - payload minimo por ambiguo
          - lotes por batch_size + tokens estimados
          - concurrencia con max_workers
          - timeout/retry/backoff
          - fallback tecnico si agota rondas
    |---------------------|
    v
[4] NORMALIZACION + VALIDACION + CALIDAD
    |
    v
[5] EXPORTACION COMUN
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
| **Algoritmo** | Reglas deterministicas puras | Preclasificacion deterministica + LLM solo para ambiguos reales |
| **Velocidad** | Muy rapida (solo local) | Objetivo 10-20s/1000 (o menos) con lotes paralelos |
| **Costo** | Cero (sin LLM) | Variable segun ambiguos enviados |
| **Robustez** | Datos limpios y sucios resueltos por reglas | Tambien resuelve datos semanticamente ambiguos |
| **Trazabilidad** | Logs basicos | Logs extendidos + metricas LLM |
| **Output** | CSV basico | CSV + origen_procesamiento + retries_llm + trazabilidad AI |

**Cuando usar cada modo:**

- **Legacy**: Produccion con datos limpios o bien estructurados; prioridad velocidad
- **AI-First**: Datos ambiguos, texto libre, sinonimos desconocidos; prioridad calidad
- **Comparar**: Analisis decision sobre migracion; benchmarking

## Caracteristicas del Modo AI-First

### Flujo Optimizado (Deterministico + IA Solo Ambiguos Reales)

El router ahora clasifica cada registro en tres estados:

- `VALIDO_DIRECTO`: caso deterministico resoluble por reglas (`rule_path`)
- `INVALIDO_DIRECTO`: falla deterministica de R1/R2/R3 sin necesidad de LLM (`rule_path`)
- `AMBIGUO_REQUIERE_IA`: ambiguedad real semantica (`llm_path`)

Criterios de ambiguo:

- Fecha con lenguaje natural no deterministico (por ejemplo `15 marzo 2025`)
- Campo parcialmente interpretable fuera de formato estricto
- Valor con posible inferencia semantica contextual

Criterios deterministas agregados (sin LLM):

- Fechas no canonicas resolubles: `15 de marzo del 2025`, `Mar 15, 2025`, `2025/03/15`, `15.03.2025`
- Fechas incompletas (`marzo 2025`, `Q1 2025`, `primer trimestre`) pasan a invalido directo R2
- Monedas directas invalidas (`GBP`, `MONEDA LOCAL`, `DIVISA EXTRANJERA`) pasan a invalido directo R2
- Sinonimos de pais extendidos (`republica argentina`, `estados unidos mexicanos`)

### Batching Paralelo por Rondas

Solo registros `AMBIGUO_REQUIERE_IA` entran al motor de lotes:

1. Se arma payload minimo por registro (`id_solicitud` + campos necesarios + reglas a validar)
2. Se empaqueta en lotes por `batch_size` y `batch_max_tokens`
3. Se ejecutan lotes en paralelo (`max_workers`)
4. Se guardan resueltos y se reintenta por rondas solo pendientes
5. Si agotan rondas, se marca fallback tecnico explicito

### Parametros Tunables de Performance

Se configuran en `.env.local` (opcionales, con defaults):

| Variable | Default | Uso |
|---------|---------|-----|
| `AI_FIRST_BATCH_SIZE` | `25` | Tamano maximo de lote ambiguo |
| `AI_FIRST_BATCH_MAX_TOKENS` | `12000` | Presupuesto estimado de tokens por lote |
| `AI_FIRST_BATCH_MAX_WORKERS` | `4` | Concurrencia de lotes |
| `AI_FIRST_BATCH_TIMEOUT_SEGUNDOS` | `45` | Timeout maximo de espera por ronda de lotes |
| `AI_FIRST_BATCH_MAX_RONDAS` | `3` | Reintentos por rondas de pendientes |
| `AI_FIRST_BATCH_RETRIES` | `1` | Reintentos internos por llamada batch |
| `AI_FIRST_BATCH_BACKOFF_SEGUNDOS` | `0.6` | Espera entre rondas |
| `AI_FIRST_TIMEOUT_LLM_SEGUNDOS` | `30` | Timeout de llamada LLM individual |

### SLA y Medicion

SLA objetivo AI-First para benchmark de 1000 registros: **10-20s (o menos)**.

Corrida de evidencia local (domingo 15/02/2026):

- Dataset: `metrics/datasets/synth_1000_s42.csv`
- Reporte: `metrics/reports/benchmark_20260215_013307.json`
- Latencia AI-First: **0.26s**
- `ambiguous_detected`: `0`
- `ambiguous_sent_llm`: `0`

### Metricas de Salida

El reporte AI-First ahora incluye:

```json
{
  "resumen": { /* metricas legacy */ },
    "ai_first": {
        "enrutamiento": {
            "total_registros": 1000,
            "rule_path": 1000,
            "llm_path": 0,
            "porcentaje_llm": 0.0,
            "validos_directos": 781,
            "invalidos_directos": 219,
            "ambiguous_detected": 0,
            "ambiguous_sent_llm": 0,
            "batches_total": 0,
            "batch_size_promedio": 0.0,
            "rounds_total": 0,
            "total_fallbacks": 0,
            "total_retries_llm": 0,
            "sinonimos_resueltos": 390
        },
        "performance": {
            "tiempo_total": 0.26,
            "tiempo_preclasificacion": 0.0117,
            "tiempo_llm": 0.0,
            "tiempo_postproceso": 0.0009
        },
        "llm_provider": {
            "total_llamadas": 0,
            "total_llamadas_exitosas": 0,
            "token_usage_estado": "sin_llamadas",
            "total_tokens_prompt": 0,
            "total_tokens_completion": 0,
            "costo_estimado_usd": 0.0,
            "costo_estimado_estado": "sin_llamadas"
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



