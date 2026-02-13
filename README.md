# Challenge Tecnico - Mini-Workflow Supervisado Back-Office

Mini-workflow para una unidad de Back-Office que procesa solicitudes de alta de productos (cuentas, tarjetas y servicios).  
Lee un CSV, normaliza, valida con 3 reglas de elegibilidad, genera un reporte de calidad JSON y registra logs con trazabilidad completa.

## Estructura del Proyecto

```text
challenge/
├── src/
│   ├── main.py
│   ├── ingesta.py
│   ├── normalizador.py
│   ├── validador.py
│   ├── calidad.py
│   └── logger.py
├── data/
│   ├── solicitudes.csv
│   └── ejecuciones/
│       └── ejecucion_YYYYMMDD_HHMMSS_<archivo>/
│           ├── solicitudes_limpias.csv
│           ├── reporte_calidad.json
│           └── workflow.log
├── tests/
│   ├── test_ingesta.py
│   ├── test_normalizador.py
│   ├── test_validador.py
│   ├── test_calidad.py
│   └── test_main.py
├── docs/
│   ├── diseno_resumido.md
│   ├── diseno_srs.md
│   ├── registro_decisiones.md
│   └── challenge_tecnico.md
└── README.md
```

## Requisitos

- Python 3.10+
- Sin dependencias externas (stdlib unicamente)
- `pytest` (solo para ejecutar tests)

## Ejecucion

### 1. Correr el workflow completo

```bash
cd challenge
python src/main.py
```

Cada ejecucion crea una carpeta unica dentro de `data/ejecuciones/` y guarda ahi:
- `solicitudes_limpias.csv`
- `reporte_calidad.json`
- `workflow.log`

Esto evita sobreescrituras cuando se corre varias veces el mismo dia.

### 2. Correr los tests

```bash
cd challenge
python -m pytest tests/ -v
```

## Flujo del Workflow

```text
solicitudes.csv
    |
    v
[1] INGESTA -> lee CSV y arma registros
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

## Reglas de Validacion

| Regla | Que valida | Criterio de falla |
|---|---|---|
| R1 | Campos obligatorios | Algun campo obligatorio vacio |
| R2 | Fecha y moneda | Fecha no valida para DD/MM/YYYY o moneda fuera de [ARS, USD, EUR] |
| R3 | Rango de monto | monto <= 0 o monto > 999999999 |

## Campos de Entrada

`id_solicitud, fecha_solicitud, tipo_producto, id_cliente, monto_o_limite, moneda, pais, flag_prioritario, flag_digital`

## Documentacion

- `docs/diseno_resumido.md`: version corta para entrega (1-2 paginas).
- `docs/diseno_srs.md`: especificacion completa (SRS extendido).
- `docs/registro_decisiones.md`: decisiones tecnicas del proyecto.
- `docs/challenge_tecnico.md`: enunciado original.
