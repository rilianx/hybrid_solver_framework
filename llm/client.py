"""Clientes LLM intercambiables.

`LLMClient` es lo único que el generador conoce: `complete(system, user) -> str`.
Además, quien pueda, expone `last_usage` / `usage` (`TokenUsage`) para contar
tokens gastados: el generador los suma si están y los ignora si no.
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


# --------------------------------------------------------------------------- tokens y costo


@dataclass
class TokenUsage:
    """Tokens gastados. `cached_input` y `reasoning` son subconjuntos informativos de
    `input_tokens` y `output_tokens` (no se suman aparte al total)."""

    input_tokens: int = 0
    output_tokens: int = 0
    cached_input_tokens: int = 0
    reasoning_tokens: int = 0
    calls: int = 0

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens

    def add(self, other: "TokenUsage") -> None:
        self.input_tokens += other.input_tokens
        self.output_tokens += other.output_tokens
        self.cached_input_tokens += other.cached_input_tokens
        self.reasoning_tokens += other.reasoning_tokens
        self.calls += other.calls

    def cost_usd(self, model: str | None = None) -> float | None:
        """Costo estimado, o None si no hay precios configurados. Los precios NO vienen
        cableados (cambian y dependen del proveedor): se toman de las variables de entorno
        `LLM_PRICE_IN` / `LLM_PRICE_OUT`, en USD por millón de tokens."""
        price = price_per_mtok(model)
        if price is None:
            return None
        p_in, p_out = price
        return (self.input_tokens * p_in + self.output_tokens * p_out) / 1e6

    def as_dict(self, model: str | None = None) -> dict:
        d = {
            "calls": self.calls,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "total_tokens": self.total_tokens,
        }
        if self.cached_input_tokens:
            d["cached_input_tokens"] = self.cached_input_tokens
        if self.reasoning_tokens:
            d["reasoning_tokens"] = self.reasoning_tokens
        cost = self.cost_usd(model)
        if cost is not None:
            d["cost_usd"] = round(cost, 4)
        return d

    def __str__(self) -> str:
        parts = [f"{self.total_tokens:,} tokens ({self.input_tokens:,} in + {self.output_tokens:,} out)"]
        if self.cached_input_tokens:
            parts.append(f"{self.cached_input_tokens:,} de entrada en caché")
        if self.reasoning_tokens:
            parts.append(f"{self.reasoning_tokens:,} de razonamiento")
        cost = self.cost_usd()
        if cost is not None:
            parts.append(f"≈ USD {cost:.4f}")
        return ", ".join(parts)


def price_per_mtok(model: str | None = None) -> tuple[float, float] | None:
    """(precio entrada, precio salida) en USD por millón de tokens, desde el entorno."""
    try:
        p_in = os.environ.get("LLM_PRICE_IN")
        p_out = os.environ.get("LLM_PRICE_OUT")
        if p_in is None or p_out is None:
            return None
        return float(p_in), float(p_out)
    except ValueError:
        return None


def _int(obj, *names) -> int:
    for n in names:
        v = getattr(obj, n, None) if not isinstance(obj, dict) else obj.get(n)
        if isinstance(v, (int, float)):
            return int(v)
    return 0


def usage_from_openai(resp) -> TokenUsage:
    u = getattr(resp, "usage", None)
    if u is None:
        return TokenUsage(calls=1)
    details = getattr(u, "output_tokens_details", None) or {}
    cached = getattr(u, "input_tokens_details", None) or {}
    return TokenUsage(
        input_tokens=_int(u, "input_tokens", "prompt_tokens"),
        output_tokens=_int(u, "output_tokens", "completion_tokens"),
        cached_input_tokens=_int(cached, "cached_tokens"),
        reasoning_tokens=_int(details, "reasoning_tokens"),
        calls=1,
    )


def usage_from_anthropic(resp) -> TokenUsage:
    u = getattr(resp, "usage", None)
    if u is None:
        return TokenUsage(calls=1)
    return TokenUsage(
        input_tokens=_int(u, "input_tokens"),
        output_tokens=_int(u, "output_tokens"),
        cached_input_tokens=_int(u, "cache_read_input_tokens"),
        calls=1,
    )


@dataclass
class AnthropicClient:
    model: str = "claude-sonnet-4-5"
    max_tokens: int = 8000
    temperature: float = 0.7
    api_key: str | None = None
    usage: TokenUsage = field(default_factory=TokenUsage)  # acumulado
    last_usage: TokenUsage | None = None  # de la última llamada

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
        self.last_usage = usage_from_anthropic(resp)
        self.usage.add(self.last_usage)
        return "".join(block.text for block in resp.content if getattr(block, "type", "") == "text")


@dataclass
class OpenAIClient:
    """Cliente OpenAI (Responses API). Default: gpt-5.4-mini. Requiere OPENAI_API_KEY."""

    model: str = "gpt-5.4-mini"
    max_output_tokens: int = 8000
    temperature: float | None = None  # los modelos de razonamiento no aceptan temperature
    reasoning_effort: str | None = "low"
    api_key: str | None = None
    usage: TokenUsage = field(default_factory=TokenUsage)  # acumulado
    last_usage: TokenUsage | None = None  # de la última llamada

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
        self.last_usage = usage_from_openai(resp)
        self.usage.add(self.last_usage)
        return resp.output_text


@dataclass
class ScriptedClient:
    """Devuelve `responses` en orden; registra los prompts recibidos."""

    responses: list[str]
    calls: list[tuple[str, str]] = field(default_factory=list)
    # Uso simulado por llamada: permite probar la contabilidad de tokens sin API.
    usage_per_call: TokenUsage | None = None
    usage: TokenUsage = field(default_factory=TokenUsage)
    last_usage: TokenUsage | None = None

    def complete(self, system: str, user: str) -> str:
        self.calls.append((system, user))
        if not self.responses:
            raise RuntimeError("ScriptedClient sin respuestas restantes")
        if self.usage_per_call is not None:
            u = self.usage_per_call
            self.last_usage = TokenUsage(u.input_tokens, u.output_tokens, u.cached_input_tokens, u.reasoning_tokens, 1)
            self.usage.add(self.last_usage)
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

    @property
    def last_usage(self) -> TokenUsage | None:
        return getattr(self.inner, "last_usage", None)

    @property
    def usage(self) -> TokenUsage | None:
        return getattr(self.inner, "usage", None)

    def complete(self, system: str, user: str) -> str:
        t0 = time.time()
        text = self.inner.complete(system, user)
        self._n += 1
        used = self.last_usage
        record = {"system": system, "user": user, "response": text, "seconds": time.time() - t0}
        if used is not None:
            record["usage"] = used.as_dict(getattr(self.inner, "model", None))
        (self.directory / f"call_{self._n:03d}.json").write_text(
            json.dumps(record, ensure_ascii=False, indent=2)
        )
        return text
