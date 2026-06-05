import logging
from fastapi import APIRouter, Depends, HTTPException, status
from ...database import get_db
from ...models.ontology import OntologyGraph, OntologyGraphCreate, OntologyGraphUpdate
from ...models.oauth.user import User
from ...repositories.project_ontology.ontology_repository import OntologyGraphRepository
from ...services.project_ontology.ontology_service import OntologyService
from ...utils.auth import get_current_user
from ..base_controller import BaseController

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/ontology", tags=["ontologies"])

class OntologyController(BaseController[OntologyGraph, OntologyGraphCreate, OntologyGraphUpdate]):
    def __init__(self, service: OntologyService):
        super().__init__(service)
        self.service = service

    async def validate_create(self, data: OntologyGraphCreate, current_user: User, db):
        return data

    async def validate_update(self, id: str, data: OntologyGraphUpdate, current_user: User, db):
        return data

    async def create(self, data: OntologyGraphCreate, current_user: User, db):
        validated = await self.validate_create(data, current_user, db)
        return await self.service.create(validated.model_dump())

    async def get_by_id(self, resource_id: str, current_user: User, db):
        result = await self.service.get_by_id(resource_id)
        if not result:
            raise HTTPException(status_code=404, detail="Ontology not found")
        return result

    async def get_all(self, current_user: User, db, skip=0, limit=100, **filters):
        return await self.service.get_all(skip, limit)

    async def update(self, id: str, data: OntologyGraphUpdate, current_user: User, db):
        update_dict = data.model_dump(exclude_unset=True)
        result = await self.service.update(id, update_dict)
        if not result:
            raise HTTPException(status_code=404, detail="Ontology not found")
        return result

    async def delete(self, id: str, current_user: User, db):
        deleted = await self.service.delete(id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Ontology not found")
        return {"message": "Ontology deleted"}

def get_controller(db=Depends(get_db)):
    repo = OntologyGraphRepository(db)
    service = OntologyService(repo)
    return OntologyController(service)

@router.get("/", response_model=list[OntologyGraph])
async def list_ontologies(user=Depends(get_current_user), db=Depends(get_db), ctrl=Depends(get_controller)):
    return await ctrl.get_all(user, db)

@router.get("/{id}", response_model=OntologyGraph)
async def get_ontology(id: str, user=Depends(get_current_user), db=Depends(get_db), ctrl=Depends(get_controller)):
    return await ctrl.get_by_id(id, user, db)

@router.post("/", response_model=OntologyGraph, status_code=201)
async def create_ontology(data: OntologyGraphCreate, user=Depends(get_current_user), db=Depends(get_db), ctrl=Depends(get_controller)):
    return await ctrl.create(data, user, db)

@router.put("/{id}", response_model=OntologyGraph)
async def update_ontology(id: str, data: OntologyGraphUpdate, user=Depends(get_current_user), db=Depends(get_db), ctrl=Depends(get_controller)):
    return await ctrl.update(id, data, user, db)

@router.delete("/{id}")
async def delete_ontology(id: str, user=Depends(get_current_user), db=Depends(get_db), ctrl=Depends(get_controller)):
    return await ctrl.delete(id, user, db)
