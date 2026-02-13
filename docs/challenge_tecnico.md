# Challenge Tecnico - Lider Tecnico / Arquitecto de Solucion (AI & Sistemas Legados)

**Modalidad**: Desarrollo offline + presentacion tecnica
**Fecha**: Febrero 2026

---

## 1) Contexto del Challenge

Una unidad de Back-Office recibe solicitudes de alta de productos (p. ej., cuentas, tarjetas o servicios) provenientes de distintos canales. Cada solicitud llega en un archivo CSV/JSON/TXT con campos basicos (identificador, fecha, tipo de producto, identificador del cliente, importe/limite, pais, moneda y un par de flags). Se requiere un mini-workflow que:

- Ingesta el archivo de solicitudes.
- Procesa y normaliza campos minimos (fechas, mayusculas/minusculas, trimming).
- Valida un subconjunto de reglas de elegibilidad simples (ejemplos a eleccion del candidato, p. ej.: campos obligatorios presentes, formatos validos, rangos de importes, moneda soportada).
- Aplica control de calidad (resumen de cuantos registros pasaron/fallaron, motivos de falla por regla).
- Supervisa con logs y un breve reporte de validacion/calidad.

**Objetivo**: diseno claro, estandares, validaciones y trazabilidad (que se hizo, cuando y por que).

## 2) Consigna General

Construye un mini-workflow supervisado que incluya:

1. Diseno.
2. Implementacion (pequena y funcional).
3. Validacion (al menos 1-3 reglas sencillas).
4. Control de calidad (resumen de resultados).
5. Logs y registro de decisiones.

El candidato puede usar el lenguaje y tooling que prefiera. No es necesario ningun framework pesado.

## 3) Etapa 1 - Diseno (max. 1-2 paginas)

### a) Arquitectura minima

Un diagrama simple (bloques/secuencia/flujo) que muestre:

- Entrada -> procesamiento -> validacion -> salida.
- Componentes del workflow.
- Donde y como se generan logs.
- En que puntos se aplican validaciones y controles de calidad.

(Se evaluara claridad del diseno y trazabilidad entre etapas).

### b) Estandares y convenciones

- Convenciones de nombres.
- Estructura de carpetas/modulos.
- Criterios de logging (que, cuando y nivel).
- Manejo de errores (categorias, mensajes, propagacion).
- Supuestos tecnicos (p. ej., codificacion, formato de fechas).

### c) Supervision tecnica

- Como asegurarias mantenibilidad?
- Que revisarias en una code review?
- Riesgos tecnicos y como los mitigarias (p. ej., errores de formato, datos faltantes, inconsistencias).

## 4) Etapa 2 - Implementacion del Mini-Workflow

### Entrada

Un archivo CSV, JSON o TXT (pueden ser generados por el candidato). Debe incluir al menos: `id_solicitud`, `fecha_solicitud`, `tipo_producto`, `id_cliente`, `monto_o_limite`, `moneda`, `pais`, y 1-2 flags a eleccion.

### Proceso

Normalizacion minima (fechas al mismo formato, trimming, upper/lower segun corresponda) y transformacion sencilla (derivar un campo calculado o clasificar solicitudes por tipo).

### Validacion (elegir 1-3 reglas simples)

- Campos obligatorios presentes.
- Formato de fecha y moneda validos.
- Rangos de valores para `monto_o_limite`.
- Moneda incluida en una lista corta (p. ej., ["ARS", "USD", "EUR"]).

### Control de calidad

Generar un reporte (JSON) con: totales procesados, validos e invalidos; detalle por regla (cuantos cayeron y ejemplos); e indicadores simples (p. ej., % de cumplimiento por regla).

### Logs

- Inicio de workflow.
- Pasos ejecutados.
- Errores y advertencias.
- Resumen final (tiempo, totales).

Valoramos registro claro, con timestamps y nivel (info/warn/error), alineado a buenas practicas de auditabilidad.

### Salida

- Datos transformados (p. ej., archivo limpio/normalizado).
- Reporte de validacion/calidad.
- Logs.

## 5) Etapa 3 - Presentacion Tecnica (20-30 minutos)

- Diseno (arquitectura + estandares) y su racional.
- Implementacion (decisiones, supuestos, manejo de errores).
- Demo breve o explicacion de ejecucion.
- Como lo extenderias o escalarias (mas reglas, mas fuentes).
- Controles adicionales en entornos con mayores exigencias de trazabilidad y calidad.

## 6) Entrega

- Documento de diseno (PDF o Markdown).
- Codigo fuente y archivos necesarios (zip o repo).
- Instrucciones minimas para ejecutar (README breve).

## 7) Criterios de evaluacion

- Claridad de diseno y calidad del diagrama.
- Estandares aplicados (nombres, estructura, logs, errores).
- Calidad de validaciones y del reporte de control.
- Simplicidad efectiva: hace lo necesario sin complejidad innecesaria.
- Comunicacion tecnica en la presentacion.
