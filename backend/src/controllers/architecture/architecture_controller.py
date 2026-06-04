import logging
from fastapi import APIRouter, Depends, HTTPException, status
from ...database import get_db
from ...models.architecture import ArchitectureGraph, ArchitectureGraphCreate, ArchitectureGraphUpdate
from ...models.oauth.user import User
from ...repositories.architecture.architecture_repository import ArchitectureGraphRepository
from ...services.architecture.architecture_service import ArchitectureService
from ...utils.auth import get_current_user
from ..base_controller import BaseController
logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/architecture", tags=["architecture"])

class ArchitectureController(BaseController[ArchitectureGraph, ArchitectureGraphCreate, ArchitectureGraphUpdate]):
    def __init__(self, service: ArchitectureService):
        super().__init__(service)
        self.service = service
    async def validate_create(self, data, current_user, db): return data
    async def validate_update(self, id, data, current_user, db): return data

def get_controller(db=Depends(get_db)):
    repo = ArchitectureGraphRepository(db)
    service = ArchitectureService(repo)
    return ArchitectureController(service)

@router.get("/", response_model=list[ArchitectureGraph])
async def list_(user=Depends(get_current_user), db=Depends(get_db), ctrl=Depends(get_controller)):
    return await ctrl.get_all(user, db)
@router.get("/{id}", response_model=ArchitectureGraph)
async def get_(id: str, user=Depends(get_current_user), db=Depends(get_db), ctrl=Depends(get_controller)):
    return await ctrl.get_by_id(id, user, db)
@router.post("/", response_model=ArchitectureGraph, status_code=201)
async def create_(data: ArchitectureGraphCreate, user=Depends(get_current_user), db=Depends(get_db), ctrl=Depends(get_controller)):
    return await ctrl.create(data, user, db)
@router.put("/{id}", response_model=ArchitectureGraph)
async def update_(id: str, data: ArchitectureGraphUpdate, user=Depends(get_current_user), db=Depends(get_db), ctrl=Depends(get_controller)):
    return await ctrl.update(id, data, user, db)
@router.delete("/{id}")
async def delete_(id: str, user=Depends(get_current_user), db=Depends(get_db), ctrl=Depends(get_controller)):
    return await ctrl.delete(id, user, db)
