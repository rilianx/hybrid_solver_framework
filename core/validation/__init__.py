"""Validación autónoma por capas (§7 de la propuesta)."""

from .base import CheckResult, DiversityProbe, ValidationContext, ValidationReport
from .pipeline import validate_component

__all__ = ["CheckResult", "DiversityProbe", "ValidationContext", "ValidationReport", "validate_component"]
