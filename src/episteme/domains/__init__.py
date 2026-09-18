"""Domain-specific adapters."""

from .astronomy import (
    ASTRONOMY_DOMAIN,
    ASTRONOMY_SCHEMA,
    make_astronomy_measurement,
    validate_measurement,
)

__all__ = [
    "ASTRONOMY_DOMAIN",
    "ASTRONOMY_SCHEMA",
    "make_astronomy_measurement",
    "validate_measurement",
]
