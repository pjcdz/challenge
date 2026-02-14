# Diseno Resumido - Etapa 1
# Mini-Workflow Supervisado - Back-Office

**Version**: 1.5  
**Fecha**: Febrero 2026  
**Formato**: version compacta para exportar a PDF (objetivo: 1-2 paginas)

---

## a) Arquitectura Minima

### Diagrama de flujo

```
solicitudes.csv / .json / .txt
      |
      v
[1] INGESTA (ingesta.py)               ---> LOG INFO: registros leidos
      |   - detecta formato por extension    LOG ERROR: archivo no encontrado
      |   - CSV (coma), JSON (array),        LOG ERROR: formato no soportado
      |     TXT (pipe |)
      v
[2] NORMALIZACION (normalizador.py)     ---> LOG WARN: fecha convertida de formato
      |   - trimming de espacios             LOG INFO: normalizacion completada
      |   - fechas -> DD/MM/YYYY
      |   - upper/lower segun campo
      |   - campo calculado: categoria_riesgo
      v
[3] VALIDACION (validador.py)           ---> LOG WARN: registro invalido + motivos
      |   - R1: campos obligatorios          LOG INFO: totales validos/invalidos
      |   - R2: formato fecha + moneda
      |   - R3: rango de monto
      v
[4] CONTROL DE CALIDAD (calidad.py)     ---> LOG INFO: % cumplimiento global
      |   - totales y porcentajes
      |   - detalle por regla (fallas, %, ejemplos)
      v
[5] EXPORTACION (main.py)              ---> LOG INFO: artefactos generados
      |
      v
  SALIDAS en data/ejecuciones/ejecucion_YYYYMMDD_HHMMSS_<archivo>/
      |- solicitudes_limpias.csv   (datos normalizados + estado por registro)
      |- reporte_calidad.json      (metricas de calidad)
      |- workflow.log              (log completo de la ejecucion)
```

### Componentes

| Modulo | Responsabilidad | Requerimiento |
|--------|-----------------|---------------|
| `main.py` | Orquesta el flujo secuencial, selecciona archivo (CLI o menu) y exporta CSV | RF-05 |
| `ingesta.py` | Lee CSV, JSON o TXT y retorna lista de diccionarios | RF-01 |
| `normalizador.py` | Normaliza fechas, casing, trimming, campo calculado | RF-02 |
| `validador.py` | Aplica R1, R2, R3 y marca estado VALIDO/INVALIDO | RF-03 |
| `calidad.py` | Genera reporte JSON con metricas por regla | RF-04 |
| `logger.py` | Logging transversal: INFO, WARN, ERROR a archivo y consola | RNF-01 |

### Donde y como se generan logs

- Se generan en todas las etapas via `src/logger.py`.
- Formato: `[YYYY-MM-DD HH:MM:SS] [NIVEL] [MODULO] Mensaje`.
- Archivo por corrida: `data/ejecuciones/ejecucion_YYYYMMDD_HHMMSS_<archivo>/workflow.log`.

### Validaciones y controles de calidad

- **Etapa 3 - Validacion**: cada registro se evalua contra 3 reglas. Si falla alguna, se marca INVALIDO con todos los motivos acumulados.
- **Etapa 4 - Calidad**: metricas globales (% cumplimiento) y detalle por regla (cantidad de fallas, porcentaje sobre total e invalidos, hasta 3 ejemplos).
- **Logs en todas las etapas**: inicio, cada paso, warnings por datos ajustados o invalidos, errores criticos, y resumen final con tiempo de ejecucion.

---

## b) Estandares y Convenciones

**Convenciones de nombres**:
- Archivos y funciones: `snake_case` (ej. `normalizar_fecha()`, `validar_r1()`).
- Variables: cortas, en espanol (ej. `reg`, `linea`, `d`, `ls`).
- Constantes: `UPPER_SNAKE_CASE` (ej. `MONEDAS_SOPORTADAS`, `CAMPOS_OBLIGATORIOS`).

**Estructura de carpetas**:

| Carpeta | Contenido |
|---------|-----------|
| `src/` | Codigo fuente, 1 modulo por responsabilidad |
| `data/` | Archivos de entrada (CSV/JSON/TXT) + `ejecuciones/` (salidas versionadas por corrida) |
| `tests/` | Tests unitarios por modulo + end-to-end |
| `docs/` | Documentacion de diseno y decisiones |

**Criterios de logging (que, cuando, nivel)**:

| Nivel | Cuando | Ejemplo |
|-------|--------|---------|
| INFO | Inicio/fin de paso, resultados exitosos | "Ingesta completada - 15 registros leidos" |
| WARN | Datos ajustados, campos vacios, registro invalido | "Fecha convertida: '2025-03-15' -> '15/03/2025'" |
| ERROR | Errores que impiden continuar | "Archivo no encontrado: entrada.csv" |

Formato de cada linea: `[YYYY-MM-DD HH:MM:SS] [NIVEL] [MODULO] Mensaje`.

**Manejo de errores (categorias, mensajes, propagacion)**:

| Categoria | Ejemplo | Accion |
|-----------|---------|--------|
| Critico | Archivo inexistente | LOG ERROR, detener workflow, retornar estado "error" |
| De datos | Moneda "GBP" no soportada | LOG WARN, marcar registro INVALIDO, continuar |
| Warning | Campo opcional vacio | LOG WARN, continuar procesamiento |

Propagacion: errores criticos se propagan al orquestador (`main.py`) que detiene el flujo. Errores de datos se acumulan por registro y se reportan en el JSON de calidad.

**Supuestos tecnicos**:
- Codificacion UTF-8. Separador CSV: coma (campos con comas se manejan entre comillas). Separador TXT: pipe (`|`).
- Archivos CSV y TXT con header en primera linea. Archivos JSON como array de objetos.
- Formato detectado automaticamente por extension (.csv, .json, .txt).
- Un archivo por ejecucion, cabe en memoria.
- Fechas de entrada: `DD/MM/YYYY`, `YYYY-MM-DD`, `DD-MM-YYYY`. Salida: siempre `DD/MM/YYYY`.
- Python 3.10+, sin dependencias externas (solo stdlib; pytest para tests).

---

## c) Supervision Tecnica

**Mantenibilidad**:
- Modulos con responsabilidad unica: modificar una regla no afecta ingesta ni normalizacion.
- Agregar una regla R4 solo requiere una funcion nueva en `validador.py`; el reporte de calidad la detecta automaticamente (deteccion dinamica de reglas en `calidad.py`).
- Tests unitarios por modulo (36 tests) + prueba end-to-end del workflow completo (CSV y JSON).
- Decisiones tecnicas documentadas en `docs/registro_decisiones.md` con justificacion.

**Code review - que revisaria**:
- Trazabilidad completa: cada registro tiene estado, motivos de falla y log asociado.
- Coherencia requerimiento -> componente -> test (matriz de trazabilidad en SRS).
- Cobertura de casos borde: campos vacios, monto no numerico, monto solo "-", solo espacios.
- Que no haya catch vacios ni errores silenciados.
- Simplicidad: codigo legible sin abstracciones innecesarias.

**Riesgos tecnicos y mitigacion**:

| Riesgo | Mitigacion implementada |
|--------|------------------------|
| Datos incompletos o campos vacios | R1 detecta campos obligatorios faltantes con motivo explicito |
| Formatos de fecha inconsistentes | Normalizacion acepta 3 formatos, convierte a DD/MM/YYYY, LOG WARN si ajusta |
| Montos fuera de rango o no numericos | R3 valida rango y tipo; guards contra strings vacios y "-" solitario |
| Moneda no soportada | R2 valida contra lista configurable ["ARS", "USD", "EUR"] |
| Sobreescritura de resultados entre corridas | Cada ejecucion crea carpeta unica con timestamp |
| Falta de auditabilidad | Logging estructurado en todas las etapas + reporte JSON con detalle |

---

Documento de referencia ampliado: `docs/diseno_srs.md`.
