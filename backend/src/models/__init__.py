"""Package des modèles Pydantic"""
from .user import User, UserCreate, UserUpdate
from .project import Project, ProjectCreate, ProjectUpdate
from .classe import Classe, ClasseCreate, ClasseUpdate
from .individu import Individu, IndividuCreate, IndividuUpdate
from .relation import Relation, RelationCreate, RelationUpdate, RelationType, RelationTypeCreate, RelationTypeUpdate

__all__ = [
    "User", "UserCreate", "UserUpdate",
    "Project", "ProjectCreate", "ProjectUpdate",
    "Classe", "ClasseCreate", "ClasseUpdate",
    "Individu", "IndividuCreate", "IndividuUpdate",
    "Relation", "RelationCreate", "RelationUpdate",
    "RelationType", "RelationTypeCreate", "RelationTypeUpdate"
]
