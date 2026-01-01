"""Package des contrôleurs FastAPI"""
from . import (
    auth_controller,
    user_controller, 
    project_controller, 
    classe_controller, 
    individu_controller, 
    relation_controller
)

__all__ = [
    "auth_controller",
    "user_controller",
    "project_controller",
    "classe_controller",
    "individu_controller",
    "relation_controller"
]
