# gemini_adapter.py - Adaptador para Google Gemini
# Implementa LLMProvider usando la API de Gemini (Google AI Studio)

import os
import sys
import json
import warnings

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import (
    GEMINI_API_KEY,
    GEMINI_GEMMA_MODEL,
    GEMINI_EMBEDDING_MODEL,
    TIMEOUT_LLM_SEGUNDOS,
)
from llm_provider import LLMProvider

MODULO = "GEMINI_ADAPTER"


def importar_sdk_legacy():
    # Importa SDK legacy de Gemini sin propagar FutureWarning de deprecacion
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=FutureWarning)
        import google.generativeai as genai

    return genai


class GeminiAdapter(LLMProvider):
    # Adaptador concreto para Google Gemini
    # Usa preferentemente google.genai SDK (nuevo)
    # Mantiene fallback a google-generativeai por compatibilidad

    def __init__(self, api_key=None, modelo=None):
        if api_key == None or api_key == "":
            api_key = GEMINI_API_KEY
        if modelo == None or modelo == "":
            modelo = GEMINI_GEMMA_MODEL

        LLMProvider.__init__(self, "gemini", modelo, api_key)
        self.cliente = None
        self.sdk_en_uso = ""
        self.modelo_embedding = GEMINI_EMBEDDING_MODEL
        self.total_embedding_calls = 0
        self.total_embedding_latencia = 0.0

    def _obtener_valor(self, obj, claves):
        # Busca un valor por nombre de atributo o clave de diccionario
        if obj == None:
            return None
        i = 0
        while i < len(claves):
            clave = claves[i]
            if hasattr(obj, clave):
                return getattr(obj, clave)
            if type(obj) == dict and clave in obj.keys():
                return obj[clave]
            i = i + 1
        return None

    def _a_entero_no_negativo(self, x):
        # Convierte x a entero no negativo. Si no es parseable, retorna None
        if x == None:
            return None
        try:
            n = int(x)
            if n < 0:
                n = 0
            return n
        except Exception:
            return None

    def _extraer_tokens_usage(self, usage):
        # Extrae tokens prompt/completion desde una estructura usage
        if usage == None:
            return 0, 0, False

        claves_prompt = [
            "prompt_token_count",
            "promptTokenCount",
            "prompt_tokens",
            "promptTokens",
            "input_tokens",
            "inputTokens",
            "input_token_count",
            "request_token_count",
            "requestTokenCount",
        ]
        claves_completion = [
            "candidates_token_count",
            "candidatesTokenCount",
            "completion_token_count",
            "completionTokenCount",
            "completion_tokens",
            "completionTokens",
            "output_tokens",
            "outputTokens",
            "output_token_count",
            "response_token_count",
            "responseTokenCount",
        ]

        p = self._obtener_valor(usage, claves_prompt)
        c = self._obtener_valor(usage, claves_completion)

        p = self._a_entero_no_negativo(p)
        c = self._a_entero_no_negativo(c)

        if p == None and c == None:
            return 0, 0, False
        if p == None:
            p = 0
        if c == None:
            c = 0
        return p, c, True

    def _extraer_tokens_respuesta(self, respuesta):
        # Extrae tokens de respuesta Gemini (SDK nuevo y legacy)
        fuentes = []

        # 1) Atributos comunes
        if hasattr(respuesta, "usage_metadata"):
            fuentes.append(respuesta.usage_metadata)
        if hasattr(respuesta, "usage"):
            fuentes.append(respuesta.usage)

        # 2) Response metadata (dict u objeto)
        metadata = None
        if hasattr(respuesta, "response_metadata"):
            metadata = respuesta.response_metadata
        elif type(respuesta) == dict:
            if "response_metadata" in respuesta.keys():
                metadata = respuesta["response_metadata"]
            elif "responseMetadata" in respuesta.keys():
                metadata = respuesta["responseMetadata"]
        if metadata != None:
            um = self._obtener_valor(metadata, ["usage_metadata", "usageMetadata", "usage"])
            if um != None:
                fuentes.append(um)

        # 3) to_dict() para SDK que expone solo diccionario serializable
        if hasattr(respuesta, "to_dict"):
            try:
                d = respuesta.to_dict()
                um = self._obtener_valor(
                    d, ["usage_metadata", "usageMetadata", "usage"]
                )
                if um != None:
                    fuentes.append(um)
            except Exception:
                pass

        i = 0
        while i < len(fuentes):
            tp, tc, ok = self._extraer_tokens_usage(fuentes[i])
            if ok:
                return tp, tc, True
            i = i + 1

        return 0, 0, False

    def _inicializar_cliente(self):
        # Inicializa el cliente de Gemini si no esta creado
        if self.cliente != None:
            return True

        # Intentar primero SDK nuevo google.genai
        try:
            from google import genai
            from google.genai import types

            opciones_http = types.HttpOptions(timeout=TIMEOUT_LLM_SEGUNDOS)
            self.cliente = genai.Client(
                api_key=self.api_key, http_options=opciones_http
            )
            self.sdk_en_uso = "google.genai"
            return True
        except Exception as e:
            pass

        # Fallback SDK legacy
        try:
            genai = importar_sdk_legacy()

            genai.configure(api_key=self.api_key)
            self.cliente = genai.GenerativeModel(self.modelo)
            self.sdk_en_uso = "google.generativeai"
            return True
        except Exception as e:
            return False

    def generar(self, prompt, contexto=""):
        # Genera respuesta usando Gemini
        self.total_llamadas = self.total_llamadas + 1

        if self.api_key == "" or self.api_key == None:
            self.total_llamadas_fallidas = self.total_llamadas_fallidas + 1
            return {
                "texto": "",
                "tokens_prompt": 0,
                "tokens_completion": 0,
                "tokens_disponibles": False,
                "error": "GEMINI_API_KEY no configurada",
            }

        ok_init = self._inicializar_cliente()
        if not ok_init:
            self.total_llamadas_fallidas = self.total_llamadas_fallidas + 1
            return {
                "texto": "",
                "tokens_prompt": 0,
                "tokens_completion": 0,
                "tokens_disponibles": False,
                "error": "No se pudo inicializar cliente Gemini. Verificar google.genai/google-generativeai instalado.",
            }

        # Construir prompt completo
        prompt_completo = prompt
        if contexto != "":
            prompt_completo = contexto + "\n\n" + prompt

        try:
            respuesta = None
            if self.sdk_en_uso == "google.genai":
                try:
                    respuesta = self.cliente.models.generate_content(
                        model=self.modelo,
                        contents=prompt_completo,
                        config={
                            "temperature": 0.1,
                            "max_output_tokens": 2048,
                        },
                    )
                except Exception as e_genai:
                    # Fallback automatico a SDK legacy si el SDK nuevo falla en runtime
                    genai = importar_sdk_legacy()

                    genai.configure(api_key=self.api_key)
                    cliente_legacy = genai.GenerativeModel(self.modelo)
                    respuesta = cliente_legacy.generate_content(
                        prompt_completo,
                        generation_config=genai.types.GenerationConfig(
                            temperature=0.1,
                            max_output_tokens=2048,
                        ),
                        request_options={"timeout": TIMEOUT_LLM_SEGUNDOS},
                    )
                    self.cliente = cliente_legacy
                    # Mantener valor canonico del SDK para evitar estados invalidos
                    self.sdk_en_uso = "google.generativeai"
            elif (
                self.sdk_en_uso == "google.generativeai"
                or self.sdk_en_uso == "google.generativeai-fallback"
            ):
                genai = importar_sdk_legacy()

                respuesta = self.cliente.generate_content(
                    prompt_completo,
                    generation_config=genai.types.GenerationConfig(
                        temperature=0.1,
                        max_output_tokens=2048,
                    ),
                    request_options={"timeout": TIMEOUT_LLM_SEGUNDOS},
                )
            else:
                self.total_llamadas_fallidas = self.total_llamadas_fallidas + 1
                return {
                    "texto": "",
                    "tokens_prompt": 0,
                    "tokens_completion": 0,
                    "tokens_disponibles": False,
                    "error": "SDK Gemini no inicializado",
                }

            texto = ""
            if respuesta.text != None:
                texto = respuesta.text

            # Extraer usage metadata (SDK nuevo y legacy)
            tokens_prompt, tokens_completion, tokens_disponibles = (
                self._extraer_tokens_respuesta(respuesta)
            )

            return {
                "texto": texto,
                "tokens_prompt": tokens_prompt,
                "tokens_completion": tokens_completion,
                "tokens_disponibles": tokens_disponibles,
                "error": None,
            }

        except Exception as e:
            self.total_llamadas_fallidas = self.total_llamadas_fallidas + 1
            return {
                "texto": "",
                "tokens_prompt": 0,
                "tokens_completion": 0,
                "tokens_disponibles": False,
                "error": "Error Gemini: " + str(e),
            }

    def generar_embedding(self, texto):
        # Genera embedding usando el modelo de embedding de Gemini
        # Retorna diccionario con "embedding" (lista de floats) o "error"
        if self.api_key == "" or self.api_key == None:
            return {
                "embedding": None,
                "error": "GEMINI_API_KEY no configurada",
            }

        try:
            import time

            inicio = time.time()
            embedding = None

            if self.cliente == None or self.sdk_en_uso == "":
                ok_init = self._inicializar_cliente()
                if not ok_init:
                    return {
                        "embedding": None,
                        "error": "No se pudo inicializar cliente Gemini para embeddings",
                    }

            if self.sdk_en_uso == "google.genai":
                try:
                    resultado = self.cliente.models.embed_content(
                        model=self.modelo_embedding,
                        contents=texto,
                    )
                    if (
                        hasattr(resultado, "embeddings")
                        and resultado.embeddings != None
                        and len(resultado.embeddings) > 0
                    ):
                        emb = resultado.embeddings[0]
                        if hasattr(emb, "values") and emb.values != None:
                            embedding = emb.values
                except Exception as e_genai:
                    genai = importar_sdk_legacy()

                    genai.configure(api_key=self.api_key)
                    resultado = genai.embed_content(
                        model="models/" + self.modelo_embedding,
                        content=texto,
                    )
                    embedding = resultado["embedding"]
                    # Actualizar cliente legacy para llamadas generativas siguientes
                    self.cliente = genai.GenerativeModel(self.modelo)
                    # Mantener valor canonico del SDK para evitar estados invalidos
                    self.sdk_en_uso = "google.generativeai"

            elif (
                self.sdk_en_uso == "google.generativeai"
                or self.sdk_en_uso == "google.generativeai-fallback"
            ):
                genai = importar_sdk_legacy()

                genai.configure(api_key=self.api_key)
                resultado = genai.embed_content(
                    model="models/" + self.modelo_embedding,
                    content=texto,
                )
                embedding = resultado["embedding"]

            else:
                return {
                    "embedding": None,
                    "error": "SDK Gemini no inicializado para embeddings",
                }

            fin = time.time()

            self.total_embedding_calls = self.total_embedding_calls + 1
            self.total_embedding_latencia = self.total_embedding_latencia + (
                fin - inicio
            )

            if embedding == None:
                return {
                    "embedding": None,
                    "error": "No se pudo obtener embedding desde Gemini",
                }

            return {
                "embedding": embedding,
                "error": None,
            }

        except Exception as e:
            return {
                "embedding": None,
                "error": "Error embedding Gemini: " + str(e),
            }

    def calcular_similitud(self, embedding_a, embedding_b):
        # Calcula similitud coseno entre dos embeddings
        # Retorna float entre -1 y 1
        if embedding_a == None or embedding_b == None:
            return 0.0
        if len(embedding_a) != len(embedding_b):
            return 0.0

        dot = 0.0
        norm_a = 0.0
        norm_b = 0.0
        i = 0
        while i < len(embedding_a):
            dot = dot + (embedding_a[i] * embedding_b[i])
            norm_a = norm_a + (embedding_a[i] * embedding_a[i])
            norm_b = norm_b + (embedding_b[i] * embedding_b[i])
            i = i + 1

        if norm_a == 0.0 or norm_b == 0.0:
            return 0.0

        norm_a = norm_a**0.5
        norm_b = norm_b**0.5
        return dot / (norm_a * norm_b)

    def obtener_metricas(self):
        # Extiende metricas base con datos de embedding
        metricas = LLMProvider.obtener_metricas(self)
        metricas["total_embedding_calls"] = self.total_embedding_calls
        metricas["total_embeddings"] = self.total_embedding_calls
        if self.total_embedding_calls > 0:
            metricas["latencia_promedio_embedding"] = round(
                self.total_embedding_latencia / self.total_embedding_calls, 4
            )
        else:
            metricas["latencia_promedio_embedding"] = 0.0
        metricas["latencia_promedio_ms"] = round(
            metricas["latencia_promedio_embedding"] * 1000.0, 3
        )
        return metricas
