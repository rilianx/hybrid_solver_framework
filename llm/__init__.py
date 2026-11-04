"""Generación con LLM del backend nativo: el modelo C++ del problema (`native_model_generator`,
`native_model_optimizer`) y sus componentes C++ (`native_generator`, `native_optimizer`), sobre un cliente
intercambiable (`client`)."""

from .client import AnthropicClient, LLMClient, OpenAIClient, ScriptedClient, TokenUsage, TranscriptClient, price_per_mtok

__all__ = ["AnthropicClient", "LLMClient", "OpenAIClient", "ScriptedClient", "TranscriptClient", "TokenUsage",
           "price_per_mtok"]
