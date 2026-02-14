# Documento de Diseno - SRS
# Mini-Workflow Supervisado: Alta de Productos Back-Office

**Version**: 1.5
**Fecha**: Febrero 2026
**Autor**: Candidato

---

## 1. Introduccion

### 1.1 Proposito

Este documento especifica los requerimientos funcionales y no funcionales del mini-workflow
de procesamiento de solicitudes de alta de productos para una unidad de Back-Office.
Sirve como guia para el diseno, implementacion y validacion del sistema.

### 1.2 Alcance

El sistema procesa archivos CSV con solicitudes de alta de productos (cuentas, tarjetas,
servicios). El alcance incluye:
- Ingesta de archivos de solicitudes
- Normalizacion de campos
- Validacion de reglas de elegibilidad
- Control de calidad con reporte
- Registro de logs y trazabilidad

**Fuera de alcance**: persistencia en base de datos, integracion con sistemas externos,
autenticacion de usuarios, procesamiento en tiempo real.

### 1.3 Definiciones y Acronimos

| Termino | Definicion |
|---------|------------|
| SRS | Software Requirements Specification |
| RF | Requerimiento Funcional |
| RNF | Requerimiento No Funcional |
| CSV | Comma-Separated Values |
| Back-Office | Unidad administrativa que procesa solicitudes internas |
| Solicitud | Registro de alta de un producto financiero |
| Elegibilidad | Cumplimiento de reglas para aprobar una solicitud |

### 1.4 Referencias

- IEEE 830-1998: Recommended Practice for SRS
- Challenge Tecnico: Lider Tecnico / Arquitecto de Solucion
- Conocimiento de Ingenieria de Requerimientos (UCA 2022)

---

## 2. Descripcion General

### 2.1 Perspectiva del Producto

El mini-workflow es un sistema standalone de linea de comandos que procesa archivos
de solicitudes en batch. No requiere frameworks pesados ni dependencias externas
mas alla de la libreria estandar de Python.

### 2.2 Funciones del Producto

```
ENTRADA (solicitudes.csv)
  -> PROCESAMIENTO
     1) Ingesta
     2) Normalizacion (fechas, trimming, upper/lower, campo calculado)
  -> VALIDACION
     3) R1 Campos obligatorios
     4) R2 Fecha y moneda
     5) R3 Rango de monto
  -> SALIDA
     - solicitudes_limpias.csv
     - reporte_calidad.json
     - workflow.log

LOGS transversal en todas las etapas (INFO/WARN/ERROR)
```

### 2.3 Caracteristicas de Usuarios

| Rol | Descripcion | Interaccion |
|-----|-------------|-------------|
| Operador Back-Office | Ejecuta el workflow | Provee archivo CSV de entrada |
| Auditor | Revisa resultados | Consulta reporte y logs |
| Desarrollador | Mantiene el sistema | Modifica reglas y modulos |

### 2.4 Restricciones

- Python 3.10+ (sin dependencias externas)
- Archivos de entrada en codificacion UTF-8
- Formato de fecha de entrada: acepta DD/MM/YYYY, YYYY-MM-DD, DD-MM-YYYY
- Formato de fecha de salida normalizado: DD/MM/YYYY
- Separador CSV: coma (,)

### 2.5 Supuestos Tecnicos

1. Los archivos CSV tienen header (primera linea con nombres de columna)
2. El separador es siempre coma
3. Codificacion UTF-8
4. Un archivo por ejecucion del workflow
5. El archivo cabe en memoria (no se esperan archivos de millones de registros)

---

## 3. Requerimientos Especificos

### 3.1 Requerimientos Funcionales

#### RF-01: Ingesta de Archivos

**Objetivo SMART**: Leer archivos CSV de solicitudes y convertirlos en una estructura
de datos procesable, en menos de 1 segundo para archivos de hasta 1000 registros.

**Descripcion**: El sistema debe leer un archivo CSV con los campos:
`id_solicitud, fecha_solicitud, tipo_producto, id_cliente, monto_o_limite, moneda, pais, flag_prioritario, flag_digital`

**Historia de Usuario**:
```
COMO operador de Back-Office
QUIERO cargar un archivo CSV de solicitudes
PARA iniciar el proceso de alta de productos
```

**Criterios de Aceptacion**:
- DADO un archivo CSV valido con header CUANDO se ejecuta la ingesta ENTONCES se retorna una lista de diccionarios con los datos
- DADO un archivo CSV inexistente CUANDO se intenta la ingesta ENTONCES se registra un error y se detiene el workflow
- DADO un archivo CSV vacio (solo header) CUANDO se ejecuta la ingesta ENTONCES se registra un warning y se retorna lista vacia

**Componente**: `src/ingesta.py`
**Test**: `tests/test_ingesta.py`

---

#### RF-02: Normalizacion de Campos

**Objetivo SMART**: Normalizar el 100% de los campos de cada registro procesado,
convirtiendo fechas, aplicando trimming y estandarizando mayusculas/minusculas.

**Descripcion**: Para cada registro:
- Fechas: convertir a formato DD/MM/YYYY (acepta DD/MM/YYYY, YYYY-MM-DD, DD-MM-YYYY)
- Trimming: eliminar espacios al inicio y final de todos los campos
- Upper/Lower: tipo_producto y moneda en MAYUSCULAS, pais con primera letra mayuscula
- Campo calculado: derivar `categoria_riesgo` segun monto_o_limite:
  - "BAJO" si monto <= 50000
  - "MEDIO" si monto > 50000 y <= 500000
  - "ALTO" si monto > 500000

**Historia de Usuario**:
```
COMO operador de Back-Office
QUIERO que los datos se normalicen automaticamente
PARA tener consistencia en los registros procesados
```

**Criterios de Aceptacion**:
- DADO un registro con fecha "2025-03-15" CUANDO se normaliza ENTONCES la fecha queda "15/03/2025"
- DADO un registro con tipo_producto "  cuenta " CUANDO se normaliza ENTONCES queda "CUENTA"
- DADO un registro con monto 75000 CUANDO se normaliza ENTONCES categoria_riesgo es "MEDIO"

**Componente**: `src/normalizador.py`
**Test**: `tests/test_normalizador.py`

---

#### RF-03: Validacion de Reglas de Elegibilidad

**Objetivo SMART**: Validar cada registro contra 3 reglas de elegibilidad y registrar
el resultado (valido/invalido) con el detalle de reglas incumplidas.

**Descripcion**: Reglas de validacion:

| Regla | Nombre | Descripcion | Criterio |
|-------|--------|-------------|----------|
| R1 | Campos obligatorios | Todos los campos requeridos presentes y no vacios | id_solicitud, fecha_solicitud, tipo_producto, id_cliente, monto_o_limite, moneda, pais no vacios |
| R2 | Formato fecha y moneda | Fecha en formato valido, moneda en lista soportada | Fecha parseable, moneda en ["ARS", "USD", "EUR"] |
| R3 | Rango de monto | Monto dentro de rango valido | monto_o_limite > 0 y <= 999999999 |

**Historia de Usuario**:
```
COMO auditor de Back-Office
QUIERO que cada solicitud se valide contra reglas de elegibilidad
PARA asegurar que solo se procesan solicitudes correctas
```

**Criterios de Aceptacion**:
- DADO un registro con todos los campos completos CUANDO se valida R1 ENTONCES pasa la regla
- DADO un registro con moneda "GBP" CUANDO se valida R2 ENTONCES falla con motivo "moneda no soportada"
- DADO un registro con monto -500 CUANDO se valida R3 ENTONCES falla con motivo "monto fuera de rango"
- DADO un registro que falla multiples reglas CUANDO se valida ENTONCES se registran TODOS los motivos

**Componente**: `src/validador.py`
**Test**: `tests/test_validador.py`

---

#### RF-04: Control de Calidad

**Objetivo SMART**: Generar un reporte JSON con metricas de calidad del procesamiento,
incluyendo totales, detalle por regla y porcentaje de cumplimiento.

**Descripcion**: El reporte debe contener:
- Total de registros procesados
- Total validos e invalidos
- Detalle por regla: cantidad que fallaron, % sobre invalidos, % sobre total, ejemplos de fallas
- Indicadores: % de cumplimiento global
- Timestamp del reporte

**Historia de Usuario**:
```
COMO auditor de Back-Office
QUIERO un reporte de calidad en formato JSON
PARA evaluar la calidad de las solicitudes recibidas
```

**Criterios de Aceptacion**:
- DADO un lote de 10 registros donde 7 son validos CUANDO se genera el reporte ENTONCES muestra 70% de cumplimiento global
- DADO un lote con fallas en R2 CUANDO se genera el reporte ENTONCES el detalle de R2 incluye cantidad, % sobre invalidos, % sobre total y ejemplos
- DADO un lote procesado CUANDO se genera el reporte ENTONCES se guarda como archivo JSON en data/ejecuciones/ejecucion_YYYYMMDD_HHMMSS_<archivo>/reporte_calidad.json

**Componente**: `src/calidad.py`
**Test**: `tests/test_calidad.py`

---

#### RF-05: Orquestacion del Workflow

**Objetivo SMART**: Ejecutar secuencialmente todas las etapas del workflow
(ingesta, normalizacion, validacion, calidad) y generar las salidas correspondientes.

**Descripcion**: El orquestador:
1. Registra inicio del workflow con timestamp
2. Ejecuta ingesta del archivo de entrada
3. Ejecuta normalizacion de cada registro
4. Ejecuta validacion de cada registro normalizado
5. Genera reporte de calidad
6. Exporta datos normalizados a CSV de salida
7. Registra resumen final (tiempo total, totales procesados)

**Componente**: `src/main.py`

---

### 3.2 Requerimientos No Funcionales

#### RNF-01: Logging y Trazabilidad

**Descripcion**: El sistema debe generar logs con:
- Timestamp en formato YYYY-MM-DD HH:MM:SS
- Nivel: INFO, WARN, ERROR
- Mensaje descriptivo
- Componente que genera el log
- Archivo `workflow.log` dentro de una carpeta unica por ejecucion

**Criterios de logging**:

| Evento | Nivel | Ejemplo |
|--------|-------|---------|
| Inicio de workflow | INFO | "Inicio del workflow - archivo: solicitudes.csv" |
| Paso completado | INFO | "Ingesta completada - 15 registros leidos" |
| Dato normalizado con ajuste | WARN | "Fecha convertida de YYYY-MM-DD a DD/MM/YYYY en registro SOL-003" |
| Campo vacio detectado | WARN | "Campo moneda vacio en registro SOL-007" |
| Error de formato | WARN | "Formato de fecha invalido en registro SOL-005: '32/13/2025'" |
| Archivo no encontrado | ERROR | "Archivo no encontrado: datos/entrada.csv" |
| Resumen final | INFO | "Workflow completado en 0.45s - 15 procesados, 9 validos, 6 invalidos" |

**Componente**: `src/logger.py`

#### RNF-02: Rendimiento

- Procesar hasta 1000 registros en menos de 5 segundos
- Sin dependencias externas (solo libreria estandar de Python)

#### RNF-03: Mantenibilidad

- Modulos independientes con responsabilidad unica
- Cada modulo tiene una funcion principal clara
- Agregar una regla nueva no requiere modificar modulos existentes (solo validador.py)

---

## 4. Arquitectura - Diagrama de Flujo

```
WORKFLOW PRINCIPAL (main.py)
  |
  +--> LOG inicio (INFO) -> workflow.log en carpeta de ejecucion
  |
  +--> PASO 1 INGESTA (ingesta.py)
  |      - leer_solicitudes(archivo_entrada)
  |      - INFO exito / ERROR si archivo no existe
  |
  +--> PASO 2 NORMALIZACION (normalizador.py)
  |      - trimming, fecha DD/MM/YYYY, upper/lower, categoria_riesgo
  |      - WARN si hubo conversion/ajuste de datos
  |
  +--> PASO 3 VALIDACION (validador.py)
  |      - R1 obligatorios
  |      - R2 fecha y moneda
  |      - R3 rango de monto
  |      - WARN por registro invalido
  |
  +--> PASO 4 CONTROL DE CALIDAD (calidad.py)
  |      - totales, porcentaje global, detalle por regla
  |      - guarda reporte_calidad.json
  |
  +--> PASO 5 EXPORTAR SALIDA
  |      - guarda solicitudes_limpias.csv
  |
  +--> LOG fin (INFO)
```

---

## 5. Estandares y Convenciones

### 5.1 Convenciones de Nombres

| Elemento | Convencion | Ejemplo |
|----------|-----------|---------|
| Archivos | snake_case.py | `ingesta.py`, `normalizador.py` |
| Funciones | snake_case descriptivo | `leer_solicitudes()`, `normalizar_fecha()` |
| Variables | Cortas, espanol | `ls`, `d`, `arch`, `linea`, `reg` |
| Constantes | UPPER_SNAKE_CASE | `MONEDAS_SOPORTADAS`, `FORMATO_FECHA` |
| Campos CSV | snake_case | `id_solicitud`, `fecha_solicitud` |

### 5.2 Estructura de Carpetas

```
challenge/
├── CLAUDE.md
├── AGENTS.md
├── src/                    # Codigo fuente (1 modulo por responsabilidad)
│   ├── ingesta.py           # RF-01
│   ├── normalizador.py      # RF-02
│   ├── validador.py         # RF-03
│   ├── calidad.py           # RF-04
│   ├── logger.py            # RNF-01
│   └── main.py              # RF-05 (orquestador)
├── data/                   # Datos de entrada y salida
│   ├── solicitudes.csv      # Entrada de ejemplo
│   └── ejecuciones/         # Salidas versionadas por ejecucion
│       └── ejecucion_YYYYMMDD_HHMMSS_<archivo>/
│           ├── solicitudes_limpias.csv
│           ├── reporte_calidad.json
│           └── workflow.log
├── docs/                   # Documentacion
│   ├── challenge_tecnico.md
│   ├── diseno_resumido.md
│   ├── diseno_srs.md
│   └── registro_decisiones.md
├── tests/                  # Tests unitarios
└── README.md               # Instrucciones de ejecucion
```

**Nota de version 1.5**: las salidas de ejecucion ya no se escriben en la raiz de `data/`.  
Ahora cada corrida genera una carpeta unica:
`data/ejecuciones/ejecucion_YYYYMMDD_HHMMSS_<archivo>/`
y dentro guarda `solicitudes_limpias.csv`, `reporte_calidad.json` y `workflow.log`.

### 5.3 Criterios de Logging

| Nivel | Cuando usar | Ejemplo |
|-------|------------|---------|
| INFO | Inicio/fin de paso, resultados exitosos | "Ingesta completada - 15 registros" |
| WARN | Datos ajustados, campos vacios, fallas de validacion | "Moneda no soportada: GBP en SOL-007" |
| ERROR | Errores que impiden continuar | "Archivo no encontrado: datos.csv" |

**Formato de log**: `[YYYY-MM-DD HH:MM:SS] [NIVEL] [MODULO] Mensaje`

### 5.4 Manejo de Errores

| Categoria | Ejemplo | Accion |
|-----------|---------|--------|
| Error critico | Archivo no encontrado | Log ERROR + detener workflow |
| Error de datos | Fecha invalida en registro | Log WARN + marcar registro invalido |
| Warning | Campo opcional vacio | Log WARN + continuar procesamiento |

**Propagacion**: Los errores criticos se propagan al orquestador (main.py) que decide
si continuar o detener. Los errores de datos se acumulan por registro y se reportan.

---

## 6. Supervision Tecnica

### 6.1 Mantenibilidad

- **Modularidad**: Cada modulo tiene UNA responsabilidad (ingesta, normalizacion, validacion, calidad, logs)
- **Independencia**: Modificar una regla de validacion no afecta la ingesta ni la normalizacion
- **Extensibilidad**: Agregar una regla R4 solo requiere agregar una funcion en `validador.py`
- **Legibilidad**: Codigo simple, sin abstracciones innecesarias, comentarios en espanol

### 6.2 Code Review Checklist

En una code review se revisaria:
- [ ] Cada modulo tiene responsabilidad unica
- [ ] Las funciones reciben y retornan datos claros (listas, diccionarios)
- [ ] Los logs cubren inicio, fin, errores y advertencias de cada paso
- [ ] El manejo de errores no oculta fallas (no hay catch vacios)
- [ ] Los nombres de variables y funciones son descriptivos
- [ ] Los supuestos tecnicos estan documentados
- [ ] El reporte de calidad tiene toda la informacion requerida

### 6.3 Riesgos Tecnicos y Mitigaciones

| Riesgo | Probabilidad | Impacto | Mitigacion |
|--------|-------------|---------|------------|
| Formato de fecha inconsistente | Alta | Medio | Intentar multiples formatos, log WARN si se convierte |
| Campos vacios o faltantes | Alta | Bajo | Regla R1 los detecta, se marcan como invalidos |
| Moneda no soportada | Media | Bajo | Regla R2 los detecta, lista de monedas configurable |
| Archivo no encontrado | Baja | Alto | Validar existencia antes de procesar, log ERROR |
| Monto con formato incorrecto | Media | Medio | Intentar conversion, si falla marcar invalido |
| Encoding incorrecto del CSV | Baja | Alto | Asumir UTF-8, documentar supuesto |

---

## 7. Matriz de Trazabilidad

| ID | Requerimiento | Componente | Funcion Principal | Test | Estado |
|----|---------------|------------|-------------------|------|--------|
| RF-01 | Ingesta de archivos | src/ingesta.py | leer_solicitudes() | tests/test_ingesta.py (5/5) | Completo |
| RF-02 | Normalizacion de campos | src/normalizador.py | normalizar_registros() | tests/test_normalizador.py (6/6) | Completo |
| RF-03 | Validacion de elegibilidad | src/validador.py | validar_registros() | tests/test_validador.py (12/12) | Completo |
| RF-04 | Control de calidad | src/calidad.py | generar_reporte() | tests/test_calidad.py (3/3) | Completo |
| RF-05 | Orquestacion workflow | src/main.py | main() | tests/test_main.py (5/5) | Completo |
| RNF-01 | Logging y trazabilidad | src/logger.py | registrar() | Verificado en logs generados | Completo |
| RNF-02 | Rendimiento (<5s/1000 reg) | (todos) | - | 0.01s para 15 registros | Completo |
| RNF-03 | Mantenibilidad | (todos) | - | Modulos independientes, snake_case | Completo |

---

## 8. Formato de Datos

### 8.1 Entrada (solicitudes.csv)

```csv
id_solicitud,fecha_solicitud,tipo_producto,id_cliente,monto_o_limite,moneda,pais,flag_prioritario,flag_digital
SOL-001,15/03/2025,cuenta,CLI-100,50000,ARS,Argentina,S,N
SOL-002,2025-03-16,tarjeta,CLI-101,150000,USD,Brasil,N,S
```

### 8.2 Salida Normalizada (`data/ejecuciones/ejecucion_YYYYMMDD_HHMMSS_<archivo>/solicitudes_limpias.csv`)

```csv
id_solicitud,fecha_solicitud,tipo_producto,id_cliente,monto_o_limite,moneda,pais,flag_prioritario,flag_digital,categoria_riesgo,estado,motivos_falla
SOL-001,15/03/2025,CUENTA,CLI-100,50000,ARS,Argentina,S,N,BAJO,VALIDO,
SOL-002,16/03/2025,TARJETA,CLI-101,150000,USD,Brasil,N,S,MEDIO,VALIDO,
```

### 8.3 Reporte de Calidad (`data/ejecuciones/ejecucion_YYYYMMDD_HHMMSS_<archivo>/reporte_calidad.json`)

```json
{
    "timestamp": "2026-02-12 23:13:33",
    "archivo_entrada": "solicitudes.csv",
    "resumen": {
        "total_procesados": 15,
        "total_validos": 9,
        "total_invalidos": 6,
        "porcentaje_cumplimiento": 60.0
    },
    "detalle_reglas": {
        "R1_campos_obligatorios": {
            "total_fallas": 2,
            "porcentaje_falla_sobre_invalidos": 33.3,
            "porcentaje_falla_sobre_total": 13.3,
            "ejemplos": [
                "SOL-007: campo id_cliente vacio",
                "SOL-015: campo tipo_producto vacio"
            ]
        },
        "R2_formato_fecha_moneda": {
            "total_fallas": 2,
            "porcentaje_falla_sobre_invalidos": 33.3,
            "porcentaje_falla_sobre_total": 13.3,
            "ejemplos": [
                "SOL-010: moneda no soportada: GBP",
                "SOL-012: formato de fecha invalido: '32/13/2025'"
            ]
        },
        "R3_rango_monto": {
            "total_fallas": 2,
            "porcentaje_falla_sobre_invalidos": 33.3,
            "porcentaje_falla_sobre_total": 13.3,
            "ejemplos": [
                "SOL-005: monto fuera de rango: -500 (debe ser > 0)",
                "SOL-011: monto fuera de rango: 0 (debe ser > 0)"
            ]
        }
    }
}
```




