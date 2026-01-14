"""
Controllers - API Endpoints (Clean Architecture)
"""
from .auth_controller import router as auth_router
from .repository_controller import router as repository_router
from .issue_controller import router as issue_router
from .message_controller import router as message_router
from .copilot_assignment_routes import router as copilot_assignment_router
from .metamodel_controller import router as metamodel_router

__all__ = [
    "auth_router",
    "repository_router",
    "issue_router",
    "message_router",
    "copilot_assignment_router",
    "metamodel_router",
]

