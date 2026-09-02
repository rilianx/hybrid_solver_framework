"""Validación autónoma por capas (§7 de la propuesta)."""

from .base import CheckResult, ValidationContext, ValidationReport
from .operational import VariantRunner
from .pipeline import (
    validate_component,
    validate_component_file,
    validate_problem_model,
    validate_variant,
)

__all__ = [
    "CheckResult",
    "ValidationContext",
    "ValidationReport",
    "VariantRunner",
    "validate_component",
    "validate_component_file",
    "validate_problem_model",
    "validate_variant",
]
