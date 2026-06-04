"""
Ontology Controller — REST API endpoints for the Open World ontology system.

Endpoints:
- ``POST /api/ontology`` — create ontology from JSON body
- ``GET /api/ontology/{ontology_id}`` — get ontology
- ``POST /api/ontology/{ontology_id}/infer`` — run inference on ontology
- ``POST /api/ontology/{ontology_id}/compile`` — compile ontology → IR graph
- ``POST /api/ontology/{ontology_id}/store`` — save ontology to file
- ``GET /api/ontology/{ontology_id}/load`` — load ontology from file
- ``GET /api/ontology/{ontology_id}/facts`` — get all facts (with optional source filter)
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Body, Depends, HTTPException, Query, status

from src.models.oauth.user import User
from src.services.ontology import (
    FactSource,
    InferenceEngine,
    InferenceRule,
    OntologyCompiler,
    OntologyGraph,
    OntologyStore,
)
from src.services.ontology.ontology_models import Concept, Fact, SemanticRelation, Taxonomy
from src.utils.auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/ontology", tags=["ontology"])

# Default storage directory
import os

_DEFAULT_STORAGE = os.getenv("ONTOLOGY_STORAGE_DIR", "./data/ontology")


# ------------------------------------------------------------------
# Dependencies
# ------------------------------------------------------------------

def get_ontology_store() -> OntologyStore:
    """FastAPI dependency for OntologyStore."""
    return OntologyStore(storage_dir=_DEFAULT_STORAGE)


def get_inference_engine() -> InferenceEngine:
    """FastAPI dependency for InferenceEngine."""
    return InferenceEngine()


def get_ontology_compiler() -> OntologyCompiler:
    """FastAPI dependency for OntologyCompiler."""
    return OntologyCompiler()


# In-memory ontology storage for the API session
_ontologies: dict[str, OntologyGraph] = {}


# ------------------------------------------------------------------
# CRUD endpoints
# ------------------------------------------------------------------


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_ontology(
    ontology_data: dict[str, Any] = Body(...),
    current_user: User = Depends(get_current_user),
):
    """Create a new ontology from a JSON body.

    The JSON body must include at minimum an ``id`` and ``name``.
    Optional fields include ``description``, ``version``, ``concepts``,
    ``relations``, ``taxonomies``, ``rules``, ``facts``.

    Returns:
        The created OntologyGraph.
    """
    logger.info(f"Creating ontology (user={current_user.username})")

    try:
        ontology = OntologyGraph.model_validate(ontology_data)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid ontology data: {e}",
        )

    _ontologies[ontology.id] = ontology
    logger.info(f"Created ontology: {ontology.id} ({ontology.name})")
    return ontology.model_dump(mode="json")


@router.get("/{ontology_id}")
async def get_ontology(
    ontology_id: str,
    current_user: User = Depends(get_current_user),
):
    """Get an ontology by ID.

    Args:
        ontology_id: The ontology's unique identifier.

    Returns:
        The OntologyGraph if found, or 404.
    """
    logger.info(f"Getting ontology: {ontology_id} (user={current_user.username})")

    ontology = _ontologies.get(ontology_id)
    if ontology is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ontology '{ontology_id}' not found",
        )

    return ontology.model_dump(mode="json")


@router.delete("/{ontology_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_ontology(
    ontology_id: str,
    current_user: User = Depends(get_current_user),
):
    """Delete an ontology from memory.

    Args:
        ontology_id: The ontology's unique identifier.
    """
    logger.info(f"Deleting ontology: {ontology_id} (user={current_user.username})")

    if ontology_id not in _ontologies:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ontology '{ontology_id}' not found",
        )

    del _ontologies[ontology_id]


# ------------------------------------------------------------------
# Fact management
# ------------------------------------------------------------------


@router.get("/{ontology_id}/facts")
async def get_ontology_facts(
    ontology_id: str,
    source: str | None = Query(
        None,
        description="Filter by source: 'DECLARED', 'INFERRED', or None (all)",
    ),
    current_user: User = Depends(get_current_user),
):
    """Get all facts in an ontology.

    Args:
        ontology_id: The ontology's unique identifier.
        source: Optional source filter (DECLARED or INFERRED).

    Returns:
        A list of facts with count.
    """
    ontology = _ontologies.get(ontology_id)
    if ontology is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ontology '{ontology_id}' not found",
        )

    if source == "DECLARED":
        facts = ontology.get_declared_facts()
    elif source == "INFERRED":
        facts = ontology.get_inferred_facts()
    else:
        facts = list(ontology.facts.values())

    return {
        "ontology_id": ontology_id,
        "count": len(facts),
        "facts": [f.model_dump(mode="json") for f in facts],
    }


@router.post("/{ontology_id}/facts", status_code=status.HTTP_201_CREATED)
async def add_ontology_fact(
    ontology_id: str,
    fact_data: dict[str, Any] = Body(...),
    current_user: User = Depends(get_current_user),
):
    """Add a declared fact to an ontology.

    Args:
        ontology_id: The ontology's unique identifier.
        fact_data: Fact data (must include 'id', 'statement', optional fields).

    Returns:
        The created Fact.
    """
    ontology = _ontologies.get(ontology_id)
    if ontology is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ontology '{ontology_id}' not found",
        )

    try:
        fact = Fact.model_validate(fact_data)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid fact data: {e}",
        )

    ontology.add_fact(fact)
    logger.info(f"Added fact '{fact.id}' to ontology '{ontology_id}'")
    return fact.model_dump(mode="json")


# ------------------------------------------------------------------
# Inference
# ------------------------------------------------------------------


@router.post("/{ontology_id}/infer")
async def run_inference(
    ontology_id: str,
    rules: list[dict[str, Any]] | None = Body(
        None,
        description="Optional list of inference rules to register before running",
    ),
    fixpoint: bool = Query(
        True,
        description="Run fixpoint (multiple iterations) or single pass",
    ),
    max_iterations: int = Query(
        10, ge=1, le=100,
        description="Maximum fixpoint iterations",
    ),
    current_user: User = Depends(get_current_user),
    engine: InferenceEngine = Depends(get_inference_engine),
):
    """Run inference on an ontology.

    Registers any provided rules (temporary), runs the inference engine,
    and returns all newly inferred facts (which are also added to the
    ontology).

    Args:
        ontology_id: The ontology's unique identifier.
        rules: Optional list of inference rules to register.
        fixpoint: If True, run fixpoint inference (default).
        max_iterations: Maximum fixpoint iterations (default 10).

    Returns:
        Dict with count of new facts and the facts themselves.
    """
    ontology = _ontologies.get(ontology_id)
    if ontology is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ontology '{ontology_id}' not found",
        )

    # Register any rules provided in the request
    if rules:
        for rule_data in rules:
            try:
                rule = InferenceRule.model_validate(rule_data)
                engine.register_rule(rule)
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid rule data: {e}",
                )

    # Also register any rules already in the ontology
    for rule in ontology.rules.values():
        engine.register_rule(rule)

    try:
        if fixpoint:
            new_facts = engine.run_fixpoint(ontology, max_iterations=max_iterations)
        else:
            new_facts = engine.run_inference(ontology)
            for fact in new_facts:
                ontology.add_fact(fact)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    logger.info(
        f"Inference on '{ontology_id}': {len(new_facts)} new fact(s) "
        f"(fixpoint={fixpoint})"
    )

    return {
        "ontology_id": ontology_id,
        "new_facts_count": len(new_facts),
        "total_facts": len(ontology.facts),
        "facts": [f.model_dump(mode="json") for f in new_facts],
    }


# ------------------------------------------------------------------
# Compilation
# ------------------------------------------------------------------


@router.post("/{ontology_id}/compile")
async def compile_ontology(
    ontology_id: str,
    confidence_threshold: float = Query(
        0.5,
        ge=0.0, le=1.0,
        description="Minimum confidence threshold for inclusion in IR",
    ),
    current_user: User = Depends(get_current_user),
):
    """Compile an ontology to an IR graph.

    The compilation transforms:
    - Concepts → IR nodes (type="concept")
    - Properties → IR attribute nodes linked via HAS_ATTRIBUTE
    - SemanticRelations → IR edges
    - Taxonomies → SUBCLASS_OF edges

    Concepts with confidence < threshold are excluded.

    Args:
        ontology_id: The ontology's unique identifier.
        confidence_threshold: Minimum confidence for inclusion (default 0.5).

    Returns:
        An IR graph dict compatible with schema.py.
    """
    ontology = _ontologies.get(ontology_id)
    if ontology is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ontology '{ontology_id}' not found",
        )

    compiler = OntologyCompiler(confidence_threshold=confidence_threshold)
    ir_graph = compiler.compile_to_ir(ontology)

    logger.info(
        f"Compiled ontology '{ontology_id}' to IR: "
        f"{ir_graph['metadata']['node_count']} nodes, "
        f"{ir_graph['metadata']['edge_count']} edges"
    )

    return ir_graph


# ------------------------------------------------------------------
# Persistence
# ------------------------------------------------------------------


@router.post("/{ontology_id}/store")
async def store_ontology(
    ontology_id: str,
    file_path: str | None = Body(
        None,
        embed=True,
        description="Optional file path (relative to storage dir)",
    ),
    current_user: User = Depends(get_current_user),
    store: OntologyStore = Depends(get_ontology_store),
):
    """Save an ontology to a JSON file on disk.

    Args:
        ontology_id: The ontology's unique identifier.
        file_path: Optional file path. If None, uses ``{ontology_id}.json``.

    Returns:
        Dict with the saved file path.
    """
    ontology = _ontologies.get(ontology_id)
    if ontology is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ontology '{ontology_id}' not found",
        )

    try:
        saved_path = store.save(ontology, file_path)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save ontology: {e}",
        )

    return {
        "message": "Ontology saved successfully",
        "file_path": saved_path,
        "ontology_id": ontology_id,
    }


@router.get("/{ontology_id}/load")
async def load_ontology(
    ontology_id: str,
    file_path: str | None = Query(
        None,
        description="Optional file path. If None, uses '{ontology_id}.json'.",
    ),
    current_user: User = Depends(get_current_user),
    store: OntologyStore = Depends(get_ontology_store),
):
    """Load an ontology from a JSON file on disk.

    Args:
        ontology_id: The ontology's unique identifier.
        file_path: Optional file path. If None, uses ``{ontology_id}.json``.

    Returns:
        The loaded OntologyGraph.
    """
    try:
        path = file_path or f"{ontology_id}.json"
        ontology = store.load(path)
    except FileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ontology file not found for '{ontology_id}'",
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    # Store in memory
    _ontologies[ontology.id] = ontology

    return ontology.model_dump(mode="json")


# ------------------------------------------------------------------
# List ontologies
# ------------------------------------------------------------------


@router.get("")
async def list_ontologies(
    current_user: User = Depends(get_current_user),
):
    """List all ontologies currently in memory.

    Returns:
        Dict with list of ontology summaries.
    """
    ontologies = []
    for oid, ontology in _ontologies.items():
        ontologies.append({
            "id": oid,
            "name": ontology.name,
            "version": ontology.version,
            "concepts_count": len(ontology.concepts),
            "relations_count": len(ontology.relations),
            "facts_count": len(ontology.facts),
            "taxonomies_count": len(ontology.taxonomies),
            "created_at": ontology.created_at.isoformat() if ontology.created_at else None,
        })

    return {"count": len(ontologies), "ontologies": ontologies}


# ------------------------------------------------------------------
# Store management
# ------------------------------------------------------------------


@router.get("/store/files")
async def list_store_files(
    current_user: User = Depends(get_current_user),
    store: OntologyStore = Depends(get_ontology_store),
):
    """List all ontology JSON files on disk.

    Returns:
        Dict with list of file metadata.
    """
    files = store.list_ontologies()
    return {"count": len(files), "files": files}
