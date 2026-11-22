"""AED data standard: schema, validation, source mappers, deduplication, national registry.

Pure Python 3.8+, no third-party dependencies. Public API (used by aed_service and the portal backend):
"""
import copy

from . import schema as _schema
from .build import build_registry, publication_export
from .dedup import CANDIDATE_M, find_candidates, make_id
from .validate import completeness, validate_csv, validate_records

__all__ = ["load_schema", "field_names", "validate_records", "validate_csv", "completeness", "make_id", "find_candidates",
           "CANDIDATE_M",
           "build_registry", "publication_export"]


def load_schema():
    """Parsed schema.json (a copy; safe to modify)."""
    return copy.deepcopy(_schema.SCHEMA)


def field_names():
    return list(_schema.FIELD_NAMES)
