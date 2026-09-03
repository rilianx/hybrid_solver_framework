"""Generación de componentes con LLM (§6): cliente intercambiable, prompts por
slot, parser de respuestas y ciclo generar → validar → corregir."""

from .client import AnthropicClient, LLMClient, OpenAIClient, ScriptedClient, TokenUsage, TranscriptClient, price_per_mtok
from .generator import GeneratedComponent, GenerationStats, generate_slot, register_generated, validate_generated_module
from .prompts import ProblemSpec, correction_prompt, generation_prompt

__all__ = [
    "AnthropicClient",
    "LLMClient",
    "OpenAIClient",
    "ScriptedClient",
    "TranscriptClient",
    "TokenUsage",
    "price_per_mtok",
    "GeneratedComponent",
    "GenerationStats",
    "generate_slot",
    "register_generated",
    "validate_generated_module",
    "ProblemSpec",
    "correction_prompt",
    "generation_prompt",
]
