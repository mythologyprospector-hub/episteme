"""Domain-specific adapters."""

from .biology import (
    BIOLOGY_DOMAIN,
    BIOLOGY_SCHEMA,
    make_biology_observation,
    validate_observation,
)
from .astronomy import (
    ASTRONOMY_DOMAIN,
    ASTRONOMY_SCHEMA,
    make_astronomy_measurement,
    validate_measurement,
)

__all__ = [
    "BIOLOGY_DOMAIN",
    "BIOLOGY_SCHEMA",
    "make_biology_observation",
    "validate_observation",
    "ASTRONOMY_DOMAIN",
    "ASTRONOMY_SCHEMA",
    "make_astronomy_measurement",
    "validate_measurement",
]
