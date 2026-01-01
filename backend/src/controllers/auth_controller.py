"""
Controller pour l'authentification
"""
from fastapi import APIRouter, HTTPException, status
from src.models.auth import Token, LoginRequest, RegisterRequest
from src.models.user import UserCreate
from src.repositories.user_repository import UserRepository
from src.utils.auth import create_access_token

router = APIRouter(prefix="/api/auth", tags=["authentication"])


@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
async def register(register_data: RegisterRequest):
    """Inscription d'un nouveau utilisateur"""
    try:
        # Vérifier si le username existe déjà
        existing_user = UserRepository.get_by_username(register_data.username)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Ce nom d'utilisateur est déjà utilisé"
            )
        
        # Créer l'utilisateur
        user_data = UserCreate(
            username=register_data.username,
            email=register_data.email,
            password=register_data.password,
            full_name=register_data.full_name
        )
        
        user = UserRepository.create(user_data)
        
        # Créer le token
        access_token = create_access_token(
            data={"sub": user.id, "username": user.username}
        )
        
        return Token(access_token=access_token, token_type="bearer")
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de l'inscription: {str(e)}"
        )


@router.post("/login", response_model=Token)
async def login(login_data: LoginRequest):
    """Connexion d'un utilisateur"""
    try:
        # Authentifier l'utilisateur
        user = UserRepository.authenticate(
            username=login_data.username,
            password=login_data.password
        )
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Nom d'utilisateur ou mot de passe incorrect",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Compte désactivé"
            )
        
        # Créer le token
        access_token = create_access_token(
            data={"sub": user.id, "username": user.username}
        )
        
        return Token(access_token=access_token, token_type="bearer")
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la connexion: {str(e)}"
        )


@router.post("/verify-token")
async def verify_token(token: str):
    """Vérifie la validité d'un token"""
    from src.utils.auth import decode_access_token
    
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token invalide ou expiré"
        )
    
    user_id = payload.get("sub")
    user = UserRepository.get_by_id(user_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Utilisateur non trouvé"
        )
    
    return {
        "valid": True,
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "full_name": user.full_name
        }
    }
