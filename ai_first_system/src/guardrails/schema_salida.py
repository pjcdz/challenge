# schema_salida.py - Schema estricto de salida con Pydantic (RF-06)
# Define el schema que toda salida LLM debe cumplir
# NOTA: Pydantic requiere type hints y decoradores - excepcion justificada por framework

from pydantic import BaseModel, field_validator


class SolicitudNormalizada(BaseModel):
    # Schema estricto para una solicitud procesada
    # Toda salida del LLM debe poder parsearse a este modelo
    id_solicitud: str
    fecha_solicitud: str
    tipo_producto: str
    id_cliente: str
    monto_o_limite: str
    moneda: str
    pais: str
    estado: str = ""
    motivos_falla: str = ""
    origen_procesamiento: str = "rule_path"
    flag_prioritario: str = ""
    flag_digital: str = ""
    categoria_riesgo: str = ""
    retries_llm: int = 0
    fallback_aplicado: bool = False

    @field_validator("moneda")
    @classmethod
    def validar_moneda(cls, v):
        monedas = ["ARS", "USD", "EUR"]
        if v.upper() not in monedas:
            raise ValueError("Moneda no soportada: " + v)
        return v.upper()

    @field_validator("estado")
    @classmethod
    def validar_estado(cls, v):
        if v != "" and v not in ["VALIDO", "INVALIDO"]:
            raise ValueError("Estado debe ser VALIDO o INVALIDO: " + v)
        return v

    @field_validator("fecha_solicitud")
    @classmethod
    def validar_fecha(cls, v):
        # Debe estar en formato DD/MM/YYYY
        v = v.strip()
        if len(v) != 10:
            raise ValueError("Fecha debe ser DD/MM/YYYY: " + v)
        if v[2] != "/" or v[5] != "/":
            raise ValueError("Fecha debe ser DD/MM/YYYY: " + v)
        dia = v[0:2]
        mes = v[3:5]
        anio = v[6:10]
        if not dia.isdigit() or not mes.isdigit() or not anio.isdigit():
            raise ValueError("Fecha con componentes no numericos: " + v)
        if int(dia) < 1 or int(dia) > 31:
            raise ValueError("Dia fuera de rango: " + v)
        if int(mes) < 1 or int(mes) > 12:
            raise ValueError("Mes fuera de rango: " + v)
        return v

    @field_validator("tipo_producto")
    @classmethod
    def validar_tipo_producto(cls, v):
        tipos = ["CUENTA", "TARJETA", "SERVICIO", "PRESTAMO", "SEGURO"]
        if v.upper() not in tipos:
            raise ValueError("Tipo producto no canonico: " + v)
        return v.upper()

    @field_validator("monto_o_limite")
    @classmethod
    def validar_monto(cls, v):
        v = v.strip()
        if v == "":
            raise ValueError("Monto vacio")
        # Verificar que es numerico
        es_numero = True
        val = v
        if val[0] == "-":
            rest = val[1:]
            if rest == "" or not rest.isdigit():
                es_numero = False
        else:
            if not val.isdigit():
                es_numero = False
        if not es_numero:
            raise ValueError("Monto no numerico: " + v)
        return v

    @field_validator("origen_procesamiento")
    @classmethod
    def validar_origen(cls, v):
        origenes = ["rule_path", "llm_path"]
        if v not in origenes:
            raise ValueError("Origen debe ser rule_path o llm_path: " + v)
        return v


def registro_a_schema(reg):
    # Convierte un diccionario de registro a SolicitudNormalizada
    # Retorna (schema, None) si ok, (None, error_str) si falla
    try:
        datos = {}
        for campo in reg.keys():
            # Saltar campos internos
            if campo[0] == "_":
                continue
            datos[campo] = reg[campo]

        # Asegurar que campos requeridos existan
        campos_requeridos = [
            "id_solicitud",
            "fecha_solicitud",
            "tipo_producto",
            "id_cliente",
            "monto_o_limite",
            "moneda",
            "pais",
        ]
        for campo in campos_requeridos:
            if campo not in datos.keys():
                datos[campo] = ""

        schema = SolicitudNormalizada(**datos)
        return schema, None

    except Exception as e:
        return None, str(e)


def schema_a_dict(schema):
    # Convierte un SolicitudNormalizada a diccionario plano
    d = {
        "id_solicitud": schema.id_solicitud,
        "fecha_solicitud": schema.fecha_solicitud,
        "tipo_producto": schema.tipo_producto,
        "id_cliente": schema.id_cliente,
        "monto_o_limite": schema.monto_o_limite,
        "moneda": schema.moneda,
        "pais": schema.pais,
        "estado": schema.estado,
        "motivos_falla": schema.motivos_falla,
        "origen_procesamiento": schema.origen_procesamiento,
        "flag_prioritario": schema.flag_prioritario,
        "flag_digital": schema.flag_digital,
        "categoria_riesgo": schema.categoria_riesgo,
        "retries_llm": schema.retries_llm,
        "fallback_aplicado": schema.fallback_aplicado,
    }
    return d
