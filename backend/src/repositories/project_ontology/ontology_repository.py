import logging
from typing import Any
from uuid import uuid4
from ...models.ontology import OntologyGraph
from ..base import BaseRepository, convert_neo4j_types, prepare_neo4j_properties

logger = logging.getLogger(__name__)

class OntologyGraphRepository(BaseRepository[OntologyGraph]):
    def __init__(self, db):
        super().__init__(db, OntologyGraph, "OntologyGraph")

    async def create(self, data: dict[str, Any]) -> OntologyGraph:
        if "id" not in data:
            data["id"] = str(uuid4())
        prepared = prepare_neo4j_properties(data)
        query = f"CREATE (n:{{self.label}} $props) SET n.created_at = datetime() RETURN n"
        result = self.db.execute_query(query, {"props": prepared})
        if not result:
            raise ValueError("Failed to create OntologyGraph")
        return self.model(**convert_neo4j_types(result[0]["n"]))
