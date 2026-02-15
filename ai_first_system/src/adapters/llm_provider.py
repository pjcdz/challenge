# llm_provider.py - Interfaz abstracta para proveedores LLM
# Define la interfaz que deben implementar todos los adaptadores de LLM
# Patron adapter: permite intercambiar Gemini por otro provider sin cambiar el resto

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import MAX_RETRIES_LLM, TIMEOUT_LLM_SEGUNDOS

MODULO = "LLM_PROVIDER"


class LLMProvider:
    # Clase base para todos los proveedores LLM
    # Los adaptadores concretos deben heredar e implementar los metodos

    def __init__(self, nombre, modelo, api_key):
        self.nombre = nombre
        self.modelo = modelo
        self.api_key = api_key
        self.max_retries = MAX_RETRIES_LLM
        self.timeout = TIMEOUT_LLM_SEGUNDOS
        self.total_tokens_prompt = 0
        self.total_tokens_completion = 0
        # Llamadas exitosas con/ sin metadata de tokens
        self.total_llamadas_con_tokens = 0
        self.total_llamadas_sin_tokens = 0
        # total_llamadas: total de intentos al provider (exitos + fallos)
        self.total_llamadas = 0
        # total_llamadas_fallidas: intentos que devolvieron error
        self.total_llamadas_fallidas = 0

    def _normalizar_entero(self, x):
        # Convierte x a entero no negativo
        if x == None:
            return 0
        try:
            n = int(x)
            if n < 0:
                return 0
            return n
        except Exception:
            return 0

    def _tokens_disponibles(self, resultado):
        # Determina si una respuesta exitosa trae usage de tokens confiable
        if resultado == None:
            return False
        if "tokens_disponibles" in resultado.keys():
            return bool(resultado["tokens_disponibles"])

        # Compatibilidad hacia atras: inferir por presencia de tokens > 0
        tp = self._normalizar_entero(resultado.get("tokens_prompt", 0))
        tc = self._normalizar_entero(resultado.get("tokens_completion", 0))
        if tp > 0 or tc > 0:
            return True
        return False

    def registrar_resultado_exitoso(self, resultado):
        # Acumula metricas de tokens para una llamada exitosa al LLM
        # Se usa tanto en generar_con_retry como en rutas que llaman generar() directo
        if resultado == None:
            self.total_llamadas_sin_tokens = self.total_llamadas_sin_tokens + 1
            return

        tokens_prompt = self._normalizar_entero(resultado.get("tokens_prompt", 0))
        tokens_completion = self._normalizar_entero(
            resultado.get("tokens_completion", 0)
        )

        if self._tokens_disponibles(resultado):
            self.total_tokens_prompt = self.total_tokens_prompt + tokens_prompt
            self.total_tokens_completion = (
                self.total_tokens_completion + tokens_completion
            )
            self.total_llamadas_con_tokens = self.total_llamadas_con_tokens + 1
        else:
            self.total_llamadas_sin_tokens = self.total_llamadas_sin_tokens + 1

    def generar(self, prompt, contexto=""):
        # Genera una respuesta a partir de un prompt
        # Debe retornar un diccionario con:
        #   "texto": string con la respuesta
        #   "tokens_prompt": int o 0 si no disponible
        #   "tokens_completion": int o 0 si no disponible
        #   "tokens_disponibles": bool (True si el SDK reporto usage real)
        #   "error": None si ok, string con mensaje si fallo
        raise NotImplementedError("El adaptador debe implementar generar()")

    def generar_con_retry(
        self, prompt, contexto="", prompt_correctivo="", max_intentos=None
    ):
        # Intenta generar con reintentos acotados
        # Si falla despues de max_intentos, retorna error
        # max_intentos representa el presupuesto total de intentos permitidos
        if max_intentos == None:
            max_intentos = self.max_retries
        if max_intentos < 1:
            max_intentos = 1

        intento = 0
        ultimo_error = None

        while intento < max_intentos:
            if intento > 0 and prompt_correctivo != "":
                # En reintentos, agregar prompt correctivo
                prompt_usado = prompt + "\n\n" + prompt_correctivo
            else:
                prompt_usado = prompt

            resultado = self.generar(prompt_usado, contexto)

            if resultado["error"] == None:
                # Exito - acumular tokens o marcar llamada sin usage
                self.registrar_resultado_exitoso(resultado)
                resultado["intento"] = intento + 1
                return resultado

            ultimo_error = resultado["error"]
            intento = intento + 1

        # Todos los intentos fallaron
        return {
            "texto": "",
            "tokens_prompt": 0,
            "tokens_completion": 0,
            "error": "Fallaron todos los intentos ("
            + str(max_intentos)
            + "): "
            + str(ultimo_error),
            "intento": intento,
        }

    def obtener_metricas(self):
        # Retorna metricas acumuladas del provider
        llamadas_exitosas = max(0, self.total_llamadas - self.total_llamadas_fallidas)
        token_usage_estado = "sin_llamadas"
        token_usage_disponible = False
        if llamadas_exitosas > 0:
            if self.total_llamadas_sin_tokens == 0:
                token_usage_estado = "completo"
                token_usage_disponible = True
            elif self.total_llamadas_con_tokens > 0:
                token_usage_estado = "parcial"
                token_usage_disponible = True
            else:
                token_usage_estado = "sin_datos"
                token_usage_disponible = False

        costo_estimado = None
        costo_estado = "sin_llamadas"
        if llamadas_exitosas == 0:
            costo_estimado = 0.0
            costo_estado = "sin_llamadas"
        elif token_usage_disponible:
            # Estimacion basica de costo (Gemini pricing aprox)
            # Input: ~$0.075/1M tokens, Output: ~$0.30/1M tokens
            costo_estimado = (self.total_tokens_prompt * 0.000000075) + (
                self.total_tokens_completion * 0.0000003
            )
            costo_estimado = round(costo_estimado, 6)
            if token_usage_estado == "parcial":
                costo_estado = "parcial"
            else:
                costo_estado = "completo"
        else:
            costo_estimado = None
            costo_estado = "no_disponible"

        metricas = {
            "provider": self.nombre,
            "modelo": self.modelo,
            "total_llamadas": self.total_llamadas,
            "total_llamadas_fallidas": self.total_llamadas_fallidas,
            "total_llamadas_exitosas": llamadas_exitosas,
            "total_llamadas_con_tokens": self.total_llamadas_con_tokens,
            "total_llamadas_sin_tokens": self.total_llamadas_sin_tokens,
            "token_usage_disponible": token_usage_disponible,
            "token_usage_estado": token_usage_estado,
            "total_tokens_prompt": self.total_tokens_prompt,
            "total_tokens_completion": self.total_tokens_completion,
            "costo_estimado_usd": costo_estimado,
            "costo_estimado_estado": costo_estado,
        }
        return metricas

    def resetear_metricas(self):
        # Resetea contadores de metricas
        self.total_tokens_prompt = 0
        self.total_tokens_completion = 0
        self.total_llamadas_con_tokens = 0
        self.total_llamadas_sin_tokens = 0
        self.total_llamadas = 0
        self.total_llamadas_fallidas = 0
