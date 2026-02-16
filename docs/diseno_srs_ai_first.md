# Documento de Diseno - SRS
# Plataforma Hibrida Legacy + AI-First: Alta de Productos Back-Office

**Version**: 1.0
**Fecha**: Febrero 2026
**Autor**: Candidato

---

## 1. Introduccion

### 1.1 Proposito

Este documento especifica los requerimientos funcionales y no funcionales de una
plataforma hibrida con dos caminos de ejecucion:
- Sistema `legacy` deterministico (reglas puras)
- Sistema `ai_first` con enrutamiento hibrido (reglas primero, LLM solo casos ambiguos)

El objetivo es mantener auditabilidad y simplicidad en el core, y agregar una pista
LLMOps medible para robustez semantica, adaptabilidad y comparacion cuantitativa.

### 1.2 Alcance

El sistema procesa solicitudes de alta en batch y permite:
- Ejecutar pipeline `legacy`
- Ejecutar pipeline `ai_first` con LangChain/LangGraph
- Comparar desempeno entre ambos modos sobre el mismo dataset
- Generar datasets sinteticos para pruebas de escala y robustez
- Persistir metricas tecnicas y de calidad por corrida

**Fuera de alcance**: despliegue productivo en Kubernetes, entrenamiento de modelos,
integracion con sistemas externos reales, procesamiento en tiempo real.

### 1.3 Definiciones y Acronimos

| Termino | Definicion |
|---------|------------|
| SRS | Software Requirements Specification |
| RF | Requerimiento Funcional |
| RNF | Requerimiento No Funcional |
| LLM | Large Language Model |
| LLMOps | Practicas de operacion, evaluacion y gobierno de sistemas LLM |
| RAG | Retrieval Augmented Generation |
| SLA | Service Level Agreement |
| Guardrail | Validacion dura para limitar salidas de un LLM |
| Caso ambiguo | Registro con campos no deterministas o semanticos |

### 1.4 Referencias

- IEEE 830-1998: Recommended Practice for SRS
- Challenge Tecnico: Lider Tecnico / Arquitecto de Solucion
- Documentacion LangChain y LangGraph
- SRS base existente en `docs/diseno_srs.md`

---

## 2. Descripcion General

### 2.1 Perspectiva del Producto

La solucion evoluciona de un workflow unico a una plataforma dual:
- Camino A: `legacy` (deterministico, bajo costo, alta velocidad, alta trazabilidad)
- Camino B: `ai_first` (hibrido, mayor robustez en datos ambiguos/sucios)

Un orquestador en root permite elegir modo de ejecucion o correr comparativas.

### 2.2 Funciones del Producto

```
ENTRADA (solicitudes.csv / .json / .txt / sintetico)
  -> MODO 1: LEGACY
     1) ingesta
     2) normalizacion
     3) validacion
     4) calidad
     5) export + logs

  -> MODO 2: AI-FIRST HIBRIDO
     1) ingesta base
     2) detector de ambiguedad
     3) reglas deterministicas primero
     4) LLM solo para casos ambiguos
     5) guardrails + retries acotados + fallback
     6) validacion final, calidad y export

  -> MODO 3: COMPARAR
     - ejecuta legacy y ai_first sobre mismo input
     - guarda metricas de tiempo, costo, calidad y robustez en metrics/
```

### 2.3 Caracteristicas de Usuarios

| Rol | Descripcion | Interaccion |
|-----|-------------|-------------|
| Operador Back-Office | Ejecuta el workflow | Elige modo y archivo de entrada |
| Auditor | Evalua resultados | Revisa reportes, logs y metricas |
| Ingeniero LLMOps | Mantiene pista AI | Ajusta prompts, enrutador y guardrails |
| Tech Lead | Decide evolucion | Compara baseline legacy vs ai_first |

### 2.4 Restricciones

- Python 3.10+
- Modo `legacy` sin dependencias externas
- Modo `ai_first` con dependencias controladas (LangChain, LangGraph, proveedor LLM)
- Provider por defecto en AI-First: `gemini`
- `.env.local` obligatorio con `GEMINI_API_KEY`, `GEMINI_GEMMA_MODEL`, `GEMINI_EMBEDDING_MODEL`
- Prohibido usar mocks/stubs/fakes de LLM en runtime o pruebas de contrato/integracion
- Codificacion UTF-8
- Ejecucion batch local
- Salidas siempre auditables en archivos (CSV/JSON/LOG/metrics)

### 2.5 Supuestos Tecnicos

1. Se mantiene el pipeline legacy como baseline oficial
2. El LLM no reemplaza reglas deterministicas de negocio
3. Todo output LLM pasa por validadores duros antes de persistir
4. Hay mecanismo de fallback si LLM falla o excede retries
5. Las comparaciones se ejecutan con la misma entrada y semilla fija
6. Existe configuracion de proveedor/modelo via `.env.local` y se valida antes de ejecutar AI-First

---

## 3. Requerimientos Especificos

### 3.1 Requerimientos Funcionales

#### RF-01: Estructura Dual de Sistemas

**Objetivo SMART**: separar la solucion en dos carpetas (`legacy_system` y `ai_first_system`)
con contrato de entrada/salida comun y orquestacion unificada en root en 1 iteracion.

**Descripcion**:
- `legacy_system/`: replica el flujo deterministico actual
- `ai_first_system/`: implementa enrutamiento hibrido + agentes LangGraph
- Ambos modos deben producir mismo esquema de salida funcional

**Historia de Usuario**:
```
COMO tech lead
QUIERO dos implementaciones paralelas con contrato comun
PARA comparar objetivamente costo, rendimiento y calidad
```

**Criterios de Aceptacion**:
- DADO el mismo archivo de entrada CUANDO se ejecuta legacy y ai_first ENTONCES ambos generan CSV limpio, reporte JSON y log
- DADO un cambio en reglas CUANDO se aplica ENTONCES no rompe el contrato comun de salida

**Componente**: `legacy_system/`, `ai_first_system/`, `main.py` (root)
**Test**: `tests/contract/`

---

#### RF-02: Ejecucion Legacy Baseline

**Objetivo SMART**: preservar comportamiento legacy con cero regresiones funcionales
en reglas R1/R2/R3 y reporte de calidad.

**Descripcion**:
- Mantener el procesamiento deterministico existente
- Reusar reglas y formato de reportes actuales
- Exponer runner legacy independiente

**Historia de Usuario**:
```
COMO auditor
QUIERO conservar un baseline deterministico
PARA tener referencia estable y trazable
```

**Criterios de Aceptacion**:
- DADO dataset historico CUANDO corre legacy ENTONCES resultados coinciden con baseline esperado
- DADO input invalido CUANDO corre legacy ENTONCES registra ERROR/WARN y no crashea

**Componente**: `legacy_system/src/`
**Test**: `tests/legacy/`

---

#### RF-03: Preclasificacion Deterministica de Ambiguedad

**Objetivo SMART**: clasificar 100% de registros en `VALIDO_DIRECTO`, `INVALIDO_DIRECTO`
o `AMBIGUO_REQUIERE_IA` en menos de 0.1s por 1000 registros y enviar a LLM solo ambiguos reales.

**Descripcion**:
- Ejecutar reglas duras de preclasificacion sin LLM:
  - `VALIDO_DIRECTO`: resoluble por reglas
  - `INVALIDO_DIRECTO`: invalido deterministico por R1/R2/R3
  - `AMBIGUO_REQUIERE_IA`: requiere inferencia semantica real
- Aplicar resolucion deterministica extendida para fechas no canonicas y sinonimos
- Derivar a LLM solo `AMBIGUO_REQUIERE_IA`

**Historia de Usuario**:
```
COMO ingeniero LLMOps
QUIERO aplicar LLM solo donde agrega valor
PARA reducir costo, latencia y riesgo de alucinacion
```

**Criterios de Aceptacion**:
- DADO un registro CUANDO se preclasifica ENTONCES queda trazado con motivo y regla afectada
- DADO un caso invalido directo CUANDO se procesa ENTONCES no consume llamadas LLM
- DADO un caso ambiguo real CUANDO se procesa ENTONCES se enruta a `llm_path`

**Componente**: `ai_first_system/src/router_ambiguedad.py`
**Test**: `tests/ai_first/test_router.py`

---

#### RF-04: Batching Paralelo por Rondas para Ambiguos

**Objetivo SMART**: procesar ambiguos en lotes paralelos por rondas con timeout/retry acotado,
con trazabilidad por registro y fallback tecnico explicito.

**Descripcion**:
El motor de ambiguos debe:
- construir payload minimo por registro (id + campos necesarios + reglas)
- empaquetar por `batch_size` y limite de tokens estimados
- ejecutar lotes en paralelo (`max_workers`)
- iterar por rondas (resolver -> conservar utiles -> reprocesar pendientes)
- aplicar fallback tecnico al agotar rondas

**Historia de Usuario**:
```
COMO tech lead
QUIERO agentes especializados y desacoplados
PARA escalar capacidades sin reescribir todo el flujo
```

**Criterios de Aceptacion**:
- DADO un caso ambiguo CUANDO corre el grafo ENTONCES se registra el camino de nodos ejecutados
- DADO error en un nodo CUANDO ocurre ENTONCES aplica fallback sin romper corrida completa

**Componente**: `ai_first_system/src/agents/agente_normalizador.py`
**Test**: `tests/ai_first/test_graph.py`

---

#### RF-05: Guardrails, Verificacion y Retry

**Objetivo SMART**: garantizar 100% de salidas LLM en esquema valido con maximo 2 retries
por registro ambiguo.

**Descripcion**:
- Definir schema estricto de salida
- Validar parseo y reglas duras despues del LLM
- Reintentar con prompt correctivo si falla
- Fallback a estado `INVALIDO` si no se corrige

**Historia de Usuario**:
```
COMO auditor
QUIERO salidas LLM verificables y controladas
PARA mantener trazabilidad y reducir riesgo operativo
```

**Criterios de Aceptacion**:
- DADO output invalido del LLM CUANDO se detecta ENTONCES se reintenta hasta maximo configurado
- DADO agotamiento de retries CUANDO ocurre ENTONCES se aplica fallback documentado

**Componente**: `ai_first_system/src/guardrails/`
**Test**: `tests/ai_first/test_guardrails.py`

---

#### RF-06: Comparador de Performance, Costo y Calidad

**Objetivo SMART**: generar un reporte comparativo reproducible legacy vs ai_first para
lotes de 1k, 5k y 10k registros.

**Descripcion**:
Metricas minimas:
- tiempo total y registros/seg
- precision/cobertura por regla
- tasa de fallback
- llamadas LLM, tokens y costo estimado
- diferencia de calidad en casos ambiguos

**Historia de Usuario**:
```
COMO tech lead
QUIERO comparar ambos enfoques con datos
PARA decidir cuando usar cada modo
```

**Criterios de Aceptacion**:
- DADO una corrida comparativa CUANDO finaliza ENTONCES se guarda JSON y resumen markdown en `metrics/`
- DADO la misma semilla y input CUANDO se reejecuta ENTONCES los resultados son comparables

**Componente**: `metrics/benchmark_runner.py`
**Test**: `tests/metrics/test_benchmark_runner.py`

---

#### RF-07: Generador de Solicitudes Sinteticas

**Objetivo SMART**: generar datasets sinteticos de tamano configurable (hasta 10k+)
con mezcla de casos limpios, sucios y ambiguos.

**Descripcion**:
- Parametros: `cantidad`, `seed`, `ratio_limpio`, `ratio_sucio`, `ratio_ambiguo`
- Genera dataset + ground truth esperado para evaluacion de calidad

**Historia de Usuario**:
```
COMO ingeniero LLMOps
QUIERO generar datos de prueba controlados
PARA medir robustez y performance en escala
```

**Criterios de Aceptacion**:
- DADO seed fija CUANDO se genera dataset ENTONCES el resultado es reproducible
- DADO 10000 registros CUANDO se genera ENTONCES se obtiene dataset valido y util para benchmark

**Componente**: `metrics/data_generator.py`
**Test**: `tests/metrics/test_data_generator.py`

---

#### RF-08: Menu Unificado en Root

**Objetivo SMART**: exponer un `main.py` en root con menu interactivo y modo no interactivo
para CI/automatizacion.

**Descripcion**:
Opciones minimas:
1. Ejecutar sistema legacy
2. Ejecutar sistema ai_first
3. Comparar performance y calidad
4. Generar dataset sintetico

**Historia de Usuario**:
```
COMO operador
QUIERO lanzar cualquier modo desde un unico punto
PARA simplificar ejecucion y demo tecnica
```

**Criterios de Aceptacion**:
- DADO ejecucion interactiva CUANDO elijo opcion ENTONCES corre el flujo seleccionado
- DADO ejecucion por argumentos CLI CUANDO invoco comando ENTONCES corre sin menu

**Componente**: `main.py` (root)
**Test**: `tests/test_root_main.py`

---

### 3.2 Requerimientos No Funcionales

#### RNF-01: Logging y Trazabilidad End-to-End

**Descripcion**: ambos modos deben loguear:
- timestamp, nivel, modulo, id_solicitud cuando aplique
- modo de ejecucion (`legacy` o `ai_first`)
- ruta tomada (`rule_path` o `llm_path`)
- retries, fallback y motivo

#### RNF-02: Rendimiento y Costo Operativo

- Legacy: procesar 10k registros en tiempo acotado local
- AI-first: SLA objetivo de 1000 registros en 10-20 segundos (o menos)
- AI-first: controlar latencia y costo con preclasificacion deterministica + lotes paralelos
- Reportar siempre tiempo, throughput y costo estimado por corrida

#### RNF-03: Mantenibilidad

- Contratos comunes de entrada/salida entre modos
- Modulos desacoplados por responsabilidad
- Agregar regla nueva sin romper comparador

#### RNF-04: Reproducibilidad

- Seeds fijas para generacion sintetica y benchmark
- Configuraciones versionadas por corrida
- Reportes comparables entre ejecuciones

#### RNF-05: Calidad y Gobernanza de Salida LLM

- Esquema estricto de salida
- Validacion post-LLM obligatoria
- Reintentos acotados y fallback definido

---

## 4. Arquitectura - Diagrama de Flujo

```
ORQUESTADOR ROOT (main.py)
  |
  +--> [Modo 1] LEGACY
  |      +--> ingesta -> normalizacion -> validacion -> calidad -> export
  |      +--> logs workflow legacy
  |
  +--> [Modo 2] AI-FIRST HIBRIDO
  |      +--> ingesta base
  |      +--> preclasificacion deterministica (3 estados)
  |      +--> rule_path: VALIDO_DIRECTO + INVALIDO_DIRECTO
  |      +--> llm_path: AMBIGUO_REQUIERE_IA
  |      +--> lotes paralelos por rondas (timeout/retry/backoff)
  |      +--> guardrails + fallback tecnico
  |      +--> validacion final -> calidad -> export
  |      +--> logs workflow ai_first + telemetria LLM
  |
  +--> [Modo 3] COMPARAR
         +--> corre modo 1 y modo 2 sobre mismo input
         +--> genera metricas comparativas en metrics/
```

---

## 5. Estandares y Convenciones

### 5.1 Convenciones de Nombres

| Elemento | Convencion | Ejemplo |
|----------|-----------|---------|
| Archivos Python | snake_case.py | `router_ambiguedad.py` |
| Funciones | snake_case descriptivo | `detectar_ambiguedad()` |
| Variables | Cortas, espanol | `reg`, `mot`, `ruta`, `res` |
| Constantes | UPPER_SNAKE_CASE | `MAX_RETRIES_LLM` |
| Reglas | ID corto | `R1`, `R2`, `R3`, `R4` |

### 5.2 Estructura de Carpetas

```
challenge/
|- main.py                           # Menu unificado (RF-08)
|- legacy_system/
|  |- src/                           # Baseline deterministico
|  `- tests/
|- ai_first_system/
|  |- src/
|  |  |- graph/                      # Orquestacion LangGraph (RF-04)
|  |  |- agents/                     # Agentes especializados (RF-04)
|  |  |- guardrails/                 # Schema + verificadores (RF-05)
|  |  |- router_ambiguedad.py        # Enrutamiento hibrido (RF-03)
|  |  `- run_ai_first.py
|  `- tests/
|- metrics/
|  |- data_generator.py              # Dataset sintetico (RF-07)
|  |- benchmark_runner.py            # Comparador (RF-06)
|  |- reports/
|  `- datasets/
|- docs/
|  |- diseno_srs.md                  # SRS original legacy
|  `- diseno_srs_ai_first.md         # Este documento
`- README.md
```

### 5.3 Criterios de Logging

| Nivel | Cuando usar | Ejemplo |
|-------|------------|---------|
| INFO | Inicio/fin de flujo, paso exitoso | "Router envio registro SOL-001 por rule_path" |
| WARN | Dato ambiguo, fallback, retry | "Retry 2 por schema invalido en SOL-009" |
| ERROR | Falla critica de ejecucion | "Proveedor LLM no disponible" |

**Formato de log**: `[YYYY-MM-DD HH:MM:SS] [NIVEL] [MODO] [MODULO] Mensaje`

### 5.4 Manejo de Errores

| Categoria | Ejemplo | Accion |
|-----------|---------|--------|
| Error critico | input no existe, config invalida | ERROR + detener corrida |
| Error de datos | fecha invalida, campo vacio | WARN + marcar INVALIDO |
| Error LLM recuperable | schema invalido | WARN + retry acotado |
| Error LLM no recuperable | timeout repetido | ERROR + fallback + continuar lote |

**Propagacion**: errores criticos abortan; errores por registro no abortan corrida completa.

### 5.5 Parametros Tunables de Performance

| Parametro | Variable `.env.local` | Default |
|-----------|-------------------------|---------|
| Timeout llamada LLM | `AI_FIRST_TIMEOUT_LLM_SEGUNDOS` | `30` |
| Tamano de batch | `AI_FIRST_BATCH_SIZE` | `25` |
| Tokens max estimados por batch | `AI_FIRST_BATCH_MAX_TOKENS` | `12000` |
| Concurrencia de batches | `AI_FIRST_BATCH_MAX_WORKERS` | `4` |
| Timeout de ronda batch | `AI_FIRST_BATCH_TIMEOUT_SEGUNDOS` | `45` |
| Rondas maximas | `AI_FIRST_BATCH_MAX_RONDAS` | `3` |
| Reintentos por batch | `AI_FIRST_BATCH_RETRIES` | `1` |
| Backoff entre rondas | `AI_FIRST_BATCH_BACKOFF_SEGUNDOS` | `0.6` |

---

## 6. Supervision Tecnica

### 6.1 Mantenibilidad

- Separacion de concerns entre legacy y ai_first
- Contrato comun de IO para comparar sin friccion
- Guardrails reutilizables en cualquier agente
- Benchmarking continuo para evitar regresiones ocultas

### 6.2 Code Review Checklist

En una code review se revisaria:
- [ ] Compatibilidad de contrato entre modos
- [ ] Router envia LLM solo casos ambiguos justificados
- [ ] Salida LLM siempre validada por schema + reglas duras
- [ ] Retry/fallback no rompe trazabilidad
- [ ] Metricas incluyen tiempo, costo y calidad
- [ ] Datasets sinteticos son reproducibles por seed
- [ ] Logs permiten auditar decision por registro

### 6.3 Riesgos Tecnicos y Mitigaciones

| Riesgo | Probabilidad | Impacto | Mitigacion |
|--------|-------------|---------|------------|
| Aumento de costo LLM | Media | Alto | Router hibrido, cache, limite de retries |
| Alucinacion o formato invalido | Media | Alto | Schema estricto, verificador, fallback |
| Latencia alta | Alta | Medio | Batch, paralelismo controlado, modelo adecuado |
| Drift semantico de prompts | Media | Medio | Versionado de prompts y tests de regresion |
| Incomparabilidad de benchmarks | Baja | Alto | Seed fija, mismo input, reporte estandar |
| Regresion legacy | Baja | Alto | Suite de tests legacy obligatoria |

---

## 7. Matriz de Trazabilidad

| ID | Requerimiento | Componente | Funcion Principal | Test | Estado |
|----|---------------|------------|-------------------|------|--------|
| RF-01 | Estructura dual | main.py / carpetas raiz | main(), ejecutar_legacy(), ejecutar_ai_first() | tests/contract/test_contract.py | Implementado |
| RF-02 | Baseline legacy | legacy_system/src/ | main() en legacy_system | tests/legacy/test_legacy_nonreg.py | Implementado |
| RF-03 | Router ambiguo | ai_first_system/src/router_ambiguedad.py | enrutar_registros(), clasificar_registro() | tests/ai_first/test_router.py | Implementado |
| RF-04 | Grafo de agentes | ai_first_system/src/graph/workflow_graph.py | ejecutar_grafo_manual(), procesar_registro_ambiguo() | tests/ai_first/test_graph.py | Implementado |
| RF-05 | Guardrails + retry | ai_first_system/src/guardrails/ | verificar_respuesta_llm(), aplicar_fallback() | tests/ai_first/test_guardrails.py | Implementado |
| RF-06 | Comparador | metrics/benchmark_runner.py, metrics/metricas.py | ejecutar_benchmark(), comparar_modos() | tests/metrics/test_metricas.py | Implementado |
| RF-07 | Generador sintetico | metrics/data_generator.py | generar(), generar_dataset() | tests/metrics/test_data_generator.py | Implementado |
| RF-08 | Menu root | main.py (root) | main(), parsear_args_cli() | tests/test_root_main.py | Implementado |
| RNF-01 | Trazabilidad | legacy_system/src/logger.py (compartido por ambos modos) | registrar(), inicializar() | tests/legacy/, tests/ai_first/ | Implementado |
| RNF-02 | Rendimiento/costo | metrics/benchmark_runner.py, metrics/metricas.py | calcular_metricas_modo() | tests/metrics/test_metricas.py | Implementado |
| RNF-03 | Mantenibilidad | estructura modular completa | - | revision de arquitectura | Implementado |
| RNF-04 | Reproducibilidad | metrics/data_generator.py | generar(), generar_dataset() | tests/metrics/test_data_generator.py | Implementado |
| RNF-05 | Gobernanza LLM | ai_first_system/src/guardrails/ | registro_a_schema(), aplicar_fallback() | tests/ai_first/test_guardrails.py | Implementado |

---

## 8. Formato de Datos

### 8.1 Entrada (solicitudes.csv / .json / .txt / sintetico)

**CSV**:
```csv
id_solicitud,fecha_solicitud,tipo_producto,id_cliente,monto_o_limite,moneda,pais,flag_prioritario,flag_digital
SOL-001,15/03/2025,cuenta,CLI-100,50000,ARS,Argentina,S,N
SOL-AMB-01,15 marzo 2025,cta ahorro,CLI-101,50k,pesos argentinos,Arg.,N,S
```

**JSON**:
```json
[
    {"id_solicitud": "SOL-001", "fecha_solicitud": "15/03/2025", "tipo_producto": "cuenta", "id_cliente": "CLI-100", "monto_o_limite": "50000", "moneda": "ARS", "pais": "Argentina", "flag_prioritario": "S", "flag_digital": "N"},
    {"id_solicitud": "SOL-AMB-01", "fecha_solicitud": "15 marzo 2025", "tipo_producto": "cta ahorro", "id_cliente": "CLI-101", "monto_o_limite": "50k", "moneda": "pesos argentinos", "pais": "Arg.", "flag_prioritario": "N", "flag_digital": "S"}
]
```

**TXT** (pipe):
```
id_solicitud|fecha_solicitud|tipo_producto|id_cliente|monto_o_limite|moneda|pais|flag_prioritario|flag_digital
SOL-001|15/03/2025|cuenta|CLI-100|50000|ARS|Argentina|S|N
SOL-AMB-01|15 marzo 2025|cta ahorro|CLI-101|50k|pesos argentinos|Arg.|N|S
```

### 8.2 Salida Normalizada (`.../solicitudes_limpias.csv`)

```csv
id_solicitud,fecha_solicitud,tipo_producto,id_cliente,monto_o_limite,moneda,pais,flag_prioritario,flag_digital,categoria_riesgo,estado,motivos_falla,origen_procesamiento
SOL-001,15/03/2025,CUENTA,CLI-100,50000,ARS,Argentina,S,N,BAJO,VALIDO,,rule_path
SOL-AMB-01,15/03/2025,CUENTA,CLI-101,50000,ARS,Argentina,N,S,BAJO,VALIDO,,llm_path
```

### 8.3 Reporte de Calidad (`.../reporte_calidad.json`)

```json
{
    "timestamp": "2026-02-14 10:15:22",
    "archivo_entrada": "solicitudes_ambiguas.csv",
    "resumen": {
        "total_procesados": 10000,
        "total_validos": 9250,
        "total_invalidos": 750,
        "porcentaje_cumplimiento": 92.5
    },
    "ai_first": {
        "enrutamiento": {
            "total_registros": 10000,
            "rule_path": 8300,
            "llm_path": 1700,
            "porcentaje_llm": 17.0,
            "validos_directos": 7900,
            "invalidos_directos": 400,
            "ambiguous_detected": 1700,
            "ambiguous_sent_llm": 1700,
            "batches_total": 90,
            "batch_size_promedio": 18.9,
            "rounds_total": 2,
            "total_fallbacks": 37,
            "total_retries_llm": 210,
            "sinonimos_resueltos": 420
        },
        "performance": {
            "tiempo_total": 18.4,
            "tiempo_preclasificacion": 0.11,
            "tiempo_llm": 17.9,
            "tiempo_postproceso": 0.39
        },
        "llm_provider": {
            "provider": "gemini",
            "modelo": "gemini-2.0-flash",
            "total_llamadas": 1700,
            "total_llamadas_fallidas": 12,
            "total_llamadas_exitosas": 1688,
            "total_llamadas_con_tokens": 1600,
            "total_llamadas_sin_tokens": 88,
            "token_usage_disponible": true,
            "token_usage_estado": "parcial",
            "total_tokens_prompt": 420000,
            "total_tokens_completion": 190000,
            "costo_estimado_usd": 4.27,
            "costo_estimado_estado": "parcial"
        }
    },
    "detalle_reglas": {
        "R1_campos_obligatorios": {"total_fallas": 210},
        "R2_formato_fecha_moneda": {"total_fallas": 330},
        "R3_rango_monto": {"total_fallas": 290}
    }
}
```

**Salida comparativa adicional (`metrics/reports/benchmark_*.json`)**:
- tiempos legacy vs ai_first
- throughput legacy vs ai_first
- calidad global y calidad en subset ambiguo
- costo estimado y eficiencia por 1k registros
- estado de disponibilidad de tokens/costo (`completo`, `parcial`, `sin_datos`, `no_disponible`)

Si el SDK no devuelve usage metadata, el benchmark publica tokens/costo como
`NO_DISPONIBLE` (`null` en JSON) para evitar subreporte silencioso en `0`.
