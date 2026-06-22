"""
Ontology Services — Open World knowledge representation layer.

Provides:
- Ontology models (Concept, SemanticRelation, Taxonomy, InferenceRule, Fact)
- OntologyStore for JSON persistence
- InferenceEngine for deductive inference rules
- OntologyCompiler for ontology ↔ IR graph transformation

Pipeline: Triplets → Ontology → Inference → Validation → IR (Closed World)
"""

from .inference_engine import InferenceEngine
from .ontology_compiler import OntologyCompiler
from .ontology_models import (
    Concept,
    Fact,
    FactSource,
    InferenceRule,
    OntologyGraph,
    Property,
    SemanticRelation,
    Taxonomy,
)
from .ontology_store import OntologyStore

__all__ = [
    "Concept",
    "Property",
    "SemanticRelation",
    "Taxonomy",
    "OntologyGraph",
    "InferenceRule",
    "Fact",
    "FactSource",
    "OntologyStore",
    "InferenceEngine",
    "OntologyCompiler",
]
