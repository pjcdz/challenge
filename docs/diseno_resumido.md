# Diseno Resumido - Etapa 1
# Plataforma Dual Legacy + AI-First

**Version**: 2.0  
**Fecha**: Febrero 2026  
**Formato**: resumen compacto para entrega (1-2 paginas)

---

## a) Arquitectura Minima

### Flujo general

```text
Entrada (CSV/JSON/TXT)
    |
    v
main.py (root)
    |
    +--> Modo Legacy
    |      ingesta -> normalizacion -> validacion -> calidad -> export
    |
    +--> Modo AI-First
    |      ingesta -> router -> regla_path o llm_path
    |      llm_path -> grafo/guardrails/retry/fallback -> validacion -> calidad
    |
    `--> Modo Comparar
           ejecuta ambos modos y genera benchmark JSON/MD
```

### Componentes principales

| Componente | Responsabilidad | Requerimiento |
|------------|-----------------|---------------|
| `main.py` | Menu unificado + CLI (`legacy`, `ai_first`, `comparar`, `generar`) | RF-08 |
| `legacy_system/src/` | Baseline deterministico de negocio (R1/R2/R3) | RF-02 |
| `ai_first_system/src/router_ambiguedad.py` | Clasificacion `rule_path` vs `llm_path` | RF-03 |
| `ai_first_system/src/graph/workflow_graph.py` | Orquestacion de procesamiento ambiguo con fallback manual si falta LangGraph | RF-04 |
| `ai_first_system/src/guardrails/` | Schema estricto + verificacion de salida LLM | RF-05 |
| `ai_first_system/src/adapters/gemini_adapter.py` | Integracion Gemini real (SDK nuevo + legacy) | RF-05 |
| `metrics/benchmark_runner.py` + `metrics/metricas.py` | Comparador legacy vs AI-First y reportes | RF-06 |
| `metrics/data_generator.py` | Dataset sintetico + ground truth | RF-07 |

### Politica operativa AI-First

- Provider por defecto: `gemini`.
- No se permiten mocks/stubs/fakes en runtime ni en tests de contrato/integracion.
- Configuracion obligatoria en `.env.local`: `GEMINI_API_KEY`, `GEMINI_GEMMA_MODEL`, `GEMINI_EMBEDDING_MODEL`.
- Si falta configuracion, AI-First falla con error claro (sin fallback mock).

### Salidas por corrida

| Salida | Ubicacion |
|--------|-----------|
| Workflow Legacy/AI-First | `data/ejecuciones/ejecucion_YYYYMMDD_HHMMSS_<archivo>/` |
| CSV limpio | `.../solicitudes_limpias.csv` |
| Reporte calidad | `.../reporte_calidad.json` |
| Log workflow | `.../workflow.log` |
| Benchmark JSON/MD | `metrics/reports/benchmark_YYYYMMDD_HHMMSS.(json|md)` |

### Trazabilidad y observabilidad

- Logging transversal via `legacy_system/src/logger.py` en ambos modos.
- En AI-First cada registro queda trazado con `origen_procesamiento` (`rule_path` o `llm_path`).
- Se registran `retries_llm` y `fallback_aplicado` por registro cuando aplica.
- El reporte AI-First incorpora:
  - metricas de enrutamiento (`rule_path`, `llm_path`, `% llm`, `fallbacks`, `retries`)
  - metricas del provider (`total_llamadas`, tokens, costo estimado, estados de disponibilidad)

---

## b) Estandares y Convenciones

### Convenciones tecnicas

- Codigo Python en estilo defendible del challenge (variables simples, flujo explicito, sin abstraccion innecesaria).
- Modulos separados por responsabilidad.
- Formatos de entrada soportados: CSV, JSON, TXT.
- Formato de salida principal: CSV + JSON + LOG por corrida.

### Convenciones LLM/metricas

- LLM solo para casos ambiguos; regla-path primero.
- `token_usage_estado`: `sin_llamadas`, `completo`, `parcial`, `sin_datos`.
- `costo_estimado_estado`: `sin_llamadas`, `completo`, `parcial`, `no_disponible`.
- Si hubo llamadas reales pero el SDK no devolvio usage, benchmark publica tokens/costo como `NO_DISPONIBLE` (`null` en JSON) para evitar subreporte en `0`.

### Estructura de carpetas relevante

| Carpeta | Contenido |
|---------|-----------|
| `legacy_system/src/` | Baseline legacy |
| `ai_first_system/src/` | Router, adapters Gemini, guardrails, graph |
| `metrics/` | Generador sintetico, comparador y metricas |
| `tests/` | Suite unificada (`legacy`, `ai_first`, `contract`, `integration`, `metrics`) |
| `docs/` | SRS legacy, SRS AI-First, resumen y decisiones |

---

## c) Supervision Tecnica

### Mantenibilidad

- Arquitectura dual desacoplada: cambios en AI-First no rompen baseline legacy.
- Contrato comun de salida para comparar ambos modos sobre el mismo input.
- Configuracion LLM centralizada en `ai_first_system/src/config.py`.
- Cobertura de escenarios criticos con tests reales de provider.

### Checklist de revision

- [ ] El router envia a LLM solo casos ambiguos.
- [ ] Se valida `stats["llm_path"] > 0` en escenarios ambiguos de contrato.
- [ ] Las metricas del provider aumentan en llamadas reales (`total_llamadas` o equivalente).
- [ ] No hay subreporte silencioso de tokens/costo cuando existen llamadas LLM.
- [ ] README/SRS/registro de decisiones reflejan estructura y politica actual.

### Riesgos y mitigaciones

| Riesgo | Mitigacion |
|--------|------------|
| Configuracion incompleta de Gemini | Validacion estricta de `.env.local` y error explicito |
| Llamadas LLM sin usage metadata | Estados de disponibilidad + `NO_DISPONIBLE` en benchmark |
| Deriva de calidad en ambiguos | Contrato real + integration tests con provider real |
| Desorden de artefactos de corrida | Salidas versionadas por timestamp y carpetas dedicadas |

---

**Estado de validacion actual**: `python -m pytest -q` en verde (175 tests).
