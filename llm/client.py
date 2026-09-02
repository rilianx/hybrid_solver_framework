"""Clientes LLM intercambiables.

`LLMClient` es lo único que el generador conoce: `complete(system, user) -> str`.
- `AnthropicClient`: usa la API de Anthropic (requiere ANTHROPIC_API_KEY).
- `ScriptedClient`: devuelve respuestas predefinidas en orden; sirve para
  tests determinísticos del ciclo generar → validar → corregir, y para
  reproducir sesiones grabadas (`TranscriptClient`).
- `TranscriptClient`: graba cada intercambio de otro cliente a disco, para
  medir después tasas de aprobación sin volver a llamar a la API (§9.3).
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol


class LLMClient(Protocol):
    def complete(self, system: str, user: str) -> str: ...


@dataclass
class AnthropicClient:
    model: str = "claude-sonnet-4-5"
    max_tokens: int = 8000
    temperature: float = 0.7
    api_key: str | None = None

    def __post_init__(self) -> None:
        import anthropic  # import perezoso: el resto del framework no depende del SDK

        self._client = anthropic.Anthropic(api_key=self.api_key or os.environ.get("ANTHROPIC_API_KEY"))

    def complete(self, system: str, user: str) -> str:
        resp = self._client.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            temperature=self.temperature,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        return "".join(block.text for block in resp.content if getattr(block, "type", "") == "text")


@dataclass
class OpenAIClient:
    """Cliente OpenAI (Responses API). Default: gpt-5.4-mini. Requiere OPENAI_API_KEY."""

    model: str = "gpt-5.4-mini"
    max_output_tokens: int = 8000
    temperature: float | None = None  # los modelos de razonamiento no aceptan temperature
    reasoning_effort: str | None = "low"
    api_key: str | None = None

    def __post_init__(self) -> None:
        import openai  # import perezoso

        self._client = openai.OpenAI(api_key=self.api_key or os.environ.get("OPENAI_API_KEY"))

    def complete(self, system: str, user: str) -> str:
        kwargs: dict = dict(
            model=self.model,
            instructions=system,
            input=user,
            max_output_tokens=self.max_output_tokens,
        )
        if self.temperature is not None:
            kwargs["temperature"] = self.temperature
        if self.reasoning_effort is not None:
            kwargs["reasoning"] = {"effort": self.reasoning_effort}
        resp = self._client.responses.create(**kwargs)
        return resp.output_text


@dataclass
class ScriptedClient:
    """Devuelve `responses` en orden; registra los prompts recibidos."""

    responses: list[str]
    calls: list[tuple[str, str]] = field(default_factory=list)

    def complete(self, system: str, user: str) -> str:
        self.calls.append((system, user))
        if not self.responses:
            raise RuntimeError("ScriptedClient sin respuestas restantes")
        return self.responses.pop(0)


@dataclass
class TranscriptClient:
    """Envuelve otro cliente y guarda cada intercambio como JSON en `directory`."""

    inner: LLMClient
    directory: Path

    def __post_init__(self) -> None:
        self.directory = Path(self.directory)
        self.directory.mkdir(parents=True, exist_ok=True)
        self._n = 0

    def complete(self, system: str, user: str) -> str:
        t0 = time.time()
        text = self.inner.complete(system, user)
        self._n += 1
        (self.directory / f"call_{self._n:03d}.json").write_text(
            json.dumps({"system": system, "user": user, "response": text, "seconds": time.time() - t0}, ensure_ascii=False, indent=2)
        )
        return text
