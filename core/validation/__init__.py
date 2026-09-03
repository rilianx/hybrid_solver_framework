"""Validación autónoma por capas (§7 de la propuesta)."""

from .base import CheckResult, DiversityProbe, ValidationContext, ValidationReport
from .operational import VariantRunner
from .pipeline import (
    validate_component,
    validate_component_file,
    validate_problem_model,
    validate_variant,
)

__all__ = [
    "CheckResult",
    "DiversityProbe",
    "ValidationContext",
    "ValidationReport",
    "VariantRunner",
    "validate_component",
    "validate_component_file",
    "validate_problem_model",
    "validate_variant",
]
