"""
Ontology Store — JSON persistence for the ontology graph.

Provides save/load operations to persist an OntologyGraph to
JSON files on disk, using standard serialization via model_dump().
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from src.services.ontology.ontology_models import OntologyGraph

logger = logging.getLogger(__name__)


class OntologyStore:
    """JSON file persistence for OntologyGraph objects.

    Usage::

        store = OntologyStore(storage_dir="./data/ontology")
        store.save(ontology, "my_ontology.json")
        loaded = store.load("my_ontology.json")
    """

    def __init__(self, storage_dir: str | Path = "./data/ontology"):
        """Initialize the store with a storage directory.

        Args:
            storage_dir: Directory path for storing ontology JSON files.
                Created automatically if it doesn't exist.
        """
        self.storage_dir = Path(storage_dir)

    def _ensure_dir(self) -> None:
        """Create the storage directory if it doesn't exist."""
        self.storage_dir.mkdir(parents=True, exist_ok=True)

    def save(
        self, ontology: OntologyGraph, path: str | Path | None = None
    ) -> str:
        """Save an ontology to a JSON file.

        Args:
            ontology: The OntologyGraph to save.
            path: Optional file path. If None, uses
                ``{storage_dir}/{ontology.id}.json``.

        Returns:
            The absolute file path where the ontology was saved.

        Raises:
            IOError: If writing fails.
        """
        self._ensure_dir()

        if path is None:
            path = self.storage_dir / f"{ontology.id}.json"
        else:
            path = Path(path)
            if not path.is_absolute():
                path = self.storage_dir / path

        data = self.to_dict(ontology)
        path.write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")
        logger.info(f"Saved ontology '{ontology.id}' to {path}")
        return str(path.absolute())

    def load(self, path: str | Path) -> OntologyGraph:
        """Load an ontology from a JSON file.

        Args:
            path: File path to load from. If relative, resolved against
                the storage directory. If the file doesn't exist and the
                path has no extension, ``.json`` is appended automatically.

        Returns:
            The deserialized OntologyGraph.

        Raises:
            FileNotFoundError: If the file doesn't exist.
            ValueError: If the JSON is malformed or doesn't match the schema.
        """
        path = Path(path)
        if not path.is_absolute():
            path = self.storage_dir / path

        if not path.exists():
            # Try appending .json extension
            if path.suffix != ".json":
                path_with_json = path.with_suffix(".json")
                if path_with_json.exists():
                    path = path_with_json

        if not path.exists():
            raise FileNotFoundError(f"Ontology file not found: {path}")

        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in ontology file '{path}': {e}") from e

        ontology = self.from_dict(data)
        logger.info(f"Loaded ontology '{ontology.id}' from {path}")
        return ontology

    def exists(self, ontology_id: str) -> bool:
        """Check if an ontology file exists on disk.

        Args:
            ontology_id: The ontology ID (used as filename).

        Returns:
            True if the file exists.
        """
        return (self.storage_dir / f"{ontology_id}.json").exists()

    def delete(self, ontology_id: str) -> bool:
        """Delete an ontology file from disk.

        Args:
            ontology_id: The ontology ID to delete.

        Returns:
            True if the file was deleted, False if it didn't exist.
        """
        path = self.storage_dir / f"{ontology_id}.json"
        if path.exists():
            path.unlink()
            logger.info(f"Deleted ontology file: {path}")
            return True
        return False

    def list_ontologies(self) -> list[dict[str, Any]]:
        """List all available ontology files on disk.

        Returns:
            List of dicts with 'id', 'filename', 'size_bytes', 'modified_at'.
        """
        self._ensure_dir()
        result = []
        for f in self.storage_dir.iterdir():
            if f.suffix == ".json":
                result.append({
                    "filename": f.name,
                    "id": f.stem,
                    "size_bytes": f.stat().st_size,
                    "modified_at": f.stat().st_mtime,
                })
        return sorted(result, key=lambda x: x["filename"])

    @staticmethod
    def to_dict(ontology: OntologyGraph) -> dict[str, Any]:
        """Serialize an OntologyGraph to a plain dictionary.

        Args:
            ontology: The ontology to serialize.

        Returns:
            Dictionary representation suitable for JSON serialization.
        """
        return ontology.model_dump(mode="json")

    @staticmethod
    def from_dict(data: dict[str, Any]) -> OntologyGraph:
        """Deserialize a dictionary to an OntologyGraph.

        Args:
            data: Dictionary representation of the ontology.

        Returns:
            The deserialized OntologyGraph.

        Raises:
            ValueError: If the data doesn't match the OntologyGraph schema.
        """
        try:
            return OntologyGraph.model_validate(data)
        except Exception as e:
            raise ValueError(f"Failed to parse ontology data: {e}") from e
