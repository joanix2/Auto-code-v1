"""IR Controller - JSON persistence endpoints for the Intermediate Representation."""

import json
import logging
import os
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, status

from src.controllers.MDE.M2.metamodel_controller import get_metamodel_controller
from src.database import get_db
from src.models.MDE.M2.metamodel_edge import MetamodelEdgeType
from src.models.oauth.user import User
from src.utils.auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/ir", tags=["ir"])

# Default persistence directory
IR_STORAGE_DIR = Path(os.getenv("IR_STORAGE_DIR", "./data/ir"))


def _ensure_storage_dir():
    """Create the storage directory if it doesn't exist."""
    IR_STORAGE_DIR.mkdir(parents=True, exist_ok=True)


@router.get("/graph/{metamodel_id}")
async def get_ir_graph(
    metamodel_id: str,
    current_user: User = Depends(get_current_user),
    db=Depends(get_db),
    controller=Depends(get_metamodel_controller),
):
    """
    Get the complete IR graph for a metamodel.

    Returns the graph in the standard IR JSON format
    with metadata, nodes, edges, and edgeConstraints.
    """
    from src.services.MDE.M2.metamodel_service import MetamodelService

    from ....repositories.MDE.M2.attribute_repository import AttributeRepository
    from ....repositories.MDE.M2.concept_repository import ConceptRepository
    from ....repositories.MDE.M2.metamodel_edge_repository import MetamodelEdgeRepository
    from ....repositories.MDE.M2.metamodel_repository import MetamodelRepository
    from ....repositories.MDE.M2.relationship_repository import RelationshipRepository

    metamodel_repo = MetamodelRepository(db)
    concept_repo = ConceptRepository(db)
    attribute_repo = AttributeRepository(db)
    relationship_repo = RelationshipRepository(db)
    edge_repo = MetamodelEdgeRepository(db)

    service = MetamodelService(
        repository=metamodel_repo,
        concept_repository=concept_repo,
        attribute_repository=attribute_repo,
        relationship_repository=relationship_repo,
        edge_repository=edge_repo,
    )

    try:
        graph_data = await service.get_metamodel_with_graph(metamodel_id)
        return graph_data
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting IR graph: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve IR graph: {str(e)}",
        )


@router.post("/save/{metamodel_id}")
async def save_ir_graph(
    metamodel_id: str,
    current_user: User = Depends(get_current_user),
    db=Depends(get_db),
    controller=Depends(get_metamodel_controller),
):
    """
    Save the current IR graph for a metamodel as a JSON file.

    Returns:
        Dict with the file path where the graph was saved.
    """
    _ensure_storage_dir()

    from src.services.MDE.M2.metamodel_service import MetamodelService

    from ....repositories.MDE.M2.attribute_repository import AttributeRepository
    from ....repositories.MDE.M2.concept_repository import ConceptRepository
    from ....repositories.MDE.M2.metamodel_edge_repository import MetamodelEdgeRepository
    from ....repositories.MDE.M2.metamodel_repository import MetamodelRepository
    from ....repositories.MDE.M2.relationship_repository import RelationshipRepository

    metamodel_repo = MetamodelRepository(db)
    concept_repo = ConceptRepository(db)
    attribute_repo = AttributeRepository(db)
    relationship_repo = RelationshipRepository(db)
    edge_repo = MetamodelEdgeRepository(db)

    service = MetamodelService(
        repository=metamodel_repo,
        concept_repository=concept_repo,
        attribute_repository=attribute_repo,
        relationship_repository=relationship_repo,
        edge_repository=edge_repo,
    )

    try:
        graph_data = await service.get_metamodel_with_graph(metamodel_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting IR graph for save: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve IR graph: {str(e)}",
        )

    # Build the IR JSON document
    metamodel = graph_data["metamodel"]
    ir_document = {
        "metadata": {
            "id": metamodel.id,
            "name": metamodel.name,
            "description": metamodel.description,
            "version": metamodel.version,
            "status": metamodel.status,
            "owner_id": metamodel.owner_id,
            "created_at": metamodel.created_at.isoformat() if metamodel.created_at else None,
            "updated_at": metamodel.updated_at.isoformat() if metamodel.updated_at else None,
            "node_count": metamodel.node_count,
            "edge_count": metamodel.edge_count,
            "allowed_node_types": [nt.model_dump() for nt in metamodel.allowed_node_types],
            "allowed_edge_types": [et.model_dump() for et in metamodel.allowed_edge_types],
        },
        "nodes": graph_data["nodes"],
        "edges": graph_data["edges"],
        "edgeConstraints": graph_data.get("edgeConstraints", []),
    }

    file_path = IR_STORAGE_DIR / f"{metamodel_id}.json"
    file_path.write_text(json.dumps(ir_document, indent=2, default=str), encoding="utf-8")

    logger.info(f"Saved IR graph for {metamodel_id} to {file_path}")
    return {
        "message": "IR graph saved successfully",
        "file_path": str(file_path.absolute()),
        "node_count": len(ir_document["nodes"]),
        "edge_count": len(ir_document["edges"]),
    }


@router.post("/load/{metamodel_id}")
async def load_ir_graph(
    metamodel_id: str,
    current_user: User = Depends(get_current_user),
    db=Depends(get_db),
):
    """
    Load an IR graph from a JSON file and replace the Neo4j graph.

    This is a destructive operation: it will clear all existing
    nodes and edges for the given metamodel and replace them
    with the content of the JSON file.
    """
    _ensure_storage_dir()

    file_path = IR_STORAGE_DIR / f"{metamodel_id}.json"
    if not file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No saved IR graph found for metamodel {metamodel_id} at {file_path}",
        )

    try:
        ir_document = json.loads(file_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid JSON in saved IR graph: {e}",
        )

    # Validate the IR document structure
    from src.models.graph.schema import validate_ir_graph

    errors = validate_ir_graph(ir_document)
    if errors:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid IR graph format: {'; '.join(errors[:5])}",
        )

    from ....repositories.MDE.M2.attribute_repository import AttributeRepository
    from ....repositories.MDE.M2.concept_repository import ConceptRepository
    from ....repositories.MDE.M2.metamodel_edge_repository import MetamodelEdgeRepository
    from ....repositories.MDE.M2.metamodel_repository import MetamodelRepository
    from ....repositories.MDE.M2.relationship_repository import RelationshipRepository

    metamodel_repo = MetamodelRepository(db)
    concept_repo = ConceptRepository(db)
    attribute_repo = AttributeRepository(db)
    relationship_repo = RelationshipRepository(db)
    edge_repo = MetamodelEdgeRepository(db)

    # Verify the metamodel exists
    metamodel = await metamodel_repo.get_by_id(metamodel_id)
    if not metamodel:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Metamodel {metamodel_id} not found in database",
        )

    # Clear existing graph data (nodes + edges)
    # DETACH DELETE cascades to all Neo4j relationships automatically
    await concept_repo.delete_all_by_metamodel(metamodel_id)
    await attribute_repo.delete_all_by_metamodel(metamodel_id)
    await relationship_repo.delete_all_by_metamodel(metamodel_id)

    # Recreate nodes and edges from the IR document
    results = {"concepts": 0, "attributes": 0, "relations": 0, "edges": 0}

    for node_data in ir_document["nodes"]:
        node_type = node_data.get("type", "")
        graph_data = {
            "id": node_data["id"],
            "name": node_data["name"],
            "description": node_data.get("description", ""),
            "graph_id": metamodel_id,
            "x_position": node_data.get("x"),
            "y_position": node_data.get("y"),
        }

        try:
            if node_type == "concept":
                graph_data["node_type"] = "concept"
                await concept_repo.create(graph_data)
                results["concepts"] += 1
            elif node_type == "attribute":
                graph_data["type"] = node_data.get("dataType", "string")
                graph_data["is_required"] = node_data.get("isRequired", False)
                graph_data["is_unique"] = node_data.get("isUnique", False)
                graph_data["concept_id"] = node_data.get("concept_id")
                await attribute_repo.create(graph_data)
                results["attributes"] += 1
            elif node_type == "relation":
                graph_data["type"] = node_data.get("relationType", "other")
                await relationship_repo.create_standalone(graph_data)
                results["relations"] += 1
        except Exception as e:
            logger.warning(f"Skipping node {node_data.get('id')}: {e}")

    # Recreate edges
    for edge_data in ir_document["edges"]:
        try:
            edge_type_str = edge_data.get("type", "").lower()
            edge_type_enum = None
            for et in MetamodelEdgeType.__members__.values():
                if et.value == edge_type_str:
                    edge_type_enum = et
                    break
            if edge_type_enum:
                await edge_repo.create_edge(
                    metamodel_id,
                    edge_data["source"],
                    edge_data["target"],
                    edge_type_enum,
                )
                results["edges"] += 1
        except Exception as e:
            logger.warning(f"Skipping edge {edge_data.get('id')}: {e}")

    logger.info(f"Loaded IR graph for {metamodel_id}: {results}")
    return {
        "message": "IR graph loaded successfully",
        "file_path": str(file_path.absolute()),
        **results,
    }


@router.get("/files")
async def list_ir_files(
    _current_user: User = Depends(get_current_user),
):
    """List all saved IR JSON files on disk."""
    _ensure_storage_dir()

    files = []
    for f in IR_STORAGE_DIR.iterdir():
        if f.suffix == ".json":
            files.append(
                {
                    "filename": f.name,
                    "metamodel_id": f.stem,
                    "size_bytes": f.stat().st_size,
                    "modified_at": f.stat().st_mtime,
                }
            )

    return {"files": sorted(files, key=lambda x: x["filename"])}
