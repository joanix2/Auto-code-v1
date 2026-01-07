"""
Helper pour la gestion des erreurs dans les controllers
Évite les redondances de code en centralisant la gestion des erreurs courantes
"""
import logging
import json
from typing import Callable, Any, TypeVar, Optional
from functools import wraps
from fastapi import HTTPException, status
import httpx

logger = logging.getLogger(__name__)

T = TypeVar('T')


def handle_controller_errors(
    resource_name: str,
    operation: str = "operation"
):
    """
    Décorateur pour gérer les erreurs courantes dans les controllers
    
    Args:
        resource_name: Nom de la ressource (e.g., 'issue', 'repository')
        operation: Type d'opération (e.g., 'creation', 'update', 'deletion')
    
    Usage:
        @handle_controller_errors(resource_name="issue", operation="creation")
        async def create(self, data, current_user, db):
            # ... code
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            try:
                return await func(*args, **kwargs)
            except HTTPException:
                # Re-raise HTTPException as-is (already formatted)
                raise
            except httpx.HTTPStatusError as e:
                # Handle GitHub API errors
                logger.error(f"GitHub API error: {e.response.status_code} - {e.response.text}")
                raise HTTPException(
                    status_code=e.response.status_code,
                    detail=f"GitHub API error: {e.response.text}"
                )
            except Exception as e:
                # Handle generic errors
                logger.error(f"{resource_name.capitalize()} {operation} error: {str(e)}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to {operation} {resource_name}: {str(e)}"
                )
        return wrapper
    return decorator


def handle_github_api_error(e: httpx.HTTPStatusError) -> HTTPException:
    """
    Convertit une erreur HTTP de l'API GitHub en HTTPException
    
    Args:
        e: Exception httpx.HTTPStatusError
        
    Returns:
        HTTPException formatée pour FastAPI
    """
    error_detail = "Unknown error"
    
    try:
        # Essayer de récupérer le message d'erreur de la réponse JSON
        if e.response:
            error_data = e.response.json()
            error_detail = error_data.get("message", e.response.text)
    except json.JSONDecodeError:
        # Si le parsing JSON échoue, utiliser le texte brut
        if e.response:
            error_detail = e.response.text
        else:
            error_detail = str(e)
    
    logger.error(f"GitHub API error: {e.response.status_code if e.response else 'unknown'} - {error_detail}")
    
    return HTTPException(
        status_code=e.response.status_code if e.response else status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail=f"GitHub API error: {error_detail}"
    )


def validate_github_token(github_token: Optional[str], detail: Optional[str] = None) -> None:
    """
    Valide la présence d'un token GitHub
    
    Args:
        github_token: Token GitHub à valider
        detail: Message d'erreur personnalisé (optionnel)
        
    Raises:
        HTTPException: Si le token est manquant
    """
    if not github_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail or "GitHub account not connected. Please connect your GitHub account in your profile settings."
        )


def validate_resource_exists(resource: Any, resource_name: str, resource_id: Optional[str] = None) -> None:
    """
    Valide qu'une ressource existe
    
    Args:
        resource: La ressource à vérifier
        resource_name: Nom de la ressource (e.g., 'issue', 'repository')
        resource_id: ID de la ressource (optionnel, pour les logs)
        
    Raises:
        HTTPException: Si la ressource n'existe pas
    """
    if not resource:
        detail = f"{resource_name.capitalize()} not found"
        if resource_id:
            logger.warning(f"{detail}: {resource_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail
        )


def validate_authorization(condition: bool, detail: str = "Not authorized to perform this action") -> None:
    """
    Valide une condition d'autorisation
    
    Args:
        condition: Condition à vérifier (True = autorisé)
        detail: Message d'erreur personnalisé
        
    Raises:
        HTTPException: Si la condition n'est pas remplie
    """
    if not condition:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail
        )
