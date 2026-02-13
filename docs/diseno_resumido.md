# Diseno Resumido (Etapa 1)
# Mini-Workflow Supervisado - Back-Office

**Version**: 1.2  
**Fecha**: Febrero 2026  
**Formato**: version compacta para exportar a PDF (objetivo: 1-2 paginas)

## 1. Objetivo

Disenar un mini-workflow batch para procesar solicitudes de alta recibidas en CSV, con foco en trazabilidad, validaciones simples y control de calidad.

## 2. Arquitectura Minima

Flujo principal:
`Entrada CSV -> Ingesta -> Normalizacion -> Validacion -> Control de calidad -> Salidas`

Componentes:
- `src/main.py`: orquesta todo el flujo.
- `src/ingesta.py`: lectura de CSV.
- `src/normalizador.py`: trimming, fechas estandar y casing.
- `src/validador.py`: reglas R1/R2/R3 y estado por registro.
- `src/calidad.py`: reporte de calidad en JSON.
- `src/logger.py`: logging transversal con `INFO`, `WARN`, `ERROR`.

Puntos de control:
- Validacion en etapa 3 (reglas de elegibilidad).
- Calidad en etapa 4 (totales, porcentaje de cumplimiento, detalle por regla).
- Logs en todas las etapas (inicio, pasos, warnings, errores, cierre).

## 3. Estandares y Convenciones

- Nombres: archivos y funciones en `snake_case`.
- Estructura: `src/` (codigo), `data/` (entrada + `ejecuciones/`), `tests/` (validacion), `docs/` (documentacion).
- Trazabilidad por corrida: cada ejecucion crea `data/ejecuciones/ejecucion_YYYYMMDD_HHMMSS_<archivo>/`.
- Formato log: `[YYYY-MM-DD HH:MM:SS] [NIVEL] [MODULO] Mensaje`.
- Errores:
  - Criticos (ej. archivo inexistente): aborta el workflow.
  - De datos (ej. moneda invalida): marca registro como `INVALIDO` y continua.
- Supuestos tecnicos: UTF-8, separador `,`, archivo con header, fechas entrada (`DD/MM/YYYY`, `YYYY-MM-DD`, `DD-MM-YYYY`) y salida `DD/MM/YYYY`.

## 4. Supervision Tecnica

Mantenibilidad:
- Modulos con responsabilidad unica.
- Reglas concentradas en `validador.py`.
- Tests unitarios por modulo y prueba end-to-end.

Code review:
- Trazabilidad completa (logs y motivos de falla).
- Coherencia entre requerimientos y salidas.
- Cobertura de casos borde (vacios, formato invalido, monto no numerico).
- Simplicidad y legibilidad del codigo.

Riesgos y mitigacion:
- Datos incompletos -> R1 (obligatorios) + motivo explicito.
- Formatos invalidos -> normalizacion + R2.
- Montos fuera de rango/no numericos -> R3.
- Falta de auditabilidad -> logging estructurado en todo el flujo.

## 5. Entregables

- `data/ejecuciones/ejecucion_YYYYMMDD_HHMMSS_<archivo>/solicitudes_limpias.csv`
- `data/ejecuciones/ejecucion_YYYYMMDD_HHMMSS_<archivo>/reporte_calidad.json`
- `data/ejecuciones/ejecucion_YYYYMMDD_HHMMSS_<archivo>/workflow.log`

Documento de referencia ampliado: `docs/diseno_srs.md`.
