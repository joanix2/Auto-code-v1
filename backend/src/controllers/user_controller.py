"""User controller - API endpoints for users""""""

from fastapi import APIRouter, Depends, HTTPException, status, HeaderContrôleur FastAPI pour les Users

from typing import Optional"""

from src.models.user import User, UserLogin, UserResponsefrom fastapi import APIRouter, HTTPException, Query

from src.repositories.user_repository import UserRepositoryfrom typing import List

from src.services.github_service import GitHubServicefrom src.models.user import User, UserCreate, UserUpdate

from src.database import Neo4jConnectionfrom src.repositories.user_repository import UserRepository

from src.utils.auth import create_access_token, decode_access_token

router = APIRouter(prefix="/users", tags=["users"])

router = APIRouter()



@router.post("/", response_model=User, status_code=201)

def get_user_repo():async def create_user(user: UserCreate):

    """Dependency to get user repository"""    """Crée un nouvel utilisateur"""

    db = Neo4jConnection()    try:

    return UserRepository(db)        # Vérifier si le username existe déjà

        existing_user = UserRepository.get_by_username(user.username)

        if existing_user:

@router.post("/users/login", response_model=dict)            raise HTTPException(status_code=400, detail="Ce nom d'utilisateur existe déjà")

async def login(        

    user_login: UserLogin,        return UserRepository.create(user)

    user_repo: UserRepository = Depends(get_user_repo)    except HTTPException:

):        raise

    """Login or register user with GitHub token"""    except Exception as e:

    try:        raise HTTPException(status_code=500, detail=f"Erreur lors de la création de l'utilisateur: {str(e)}")

        # Verify GitHub token

        github_service = GitHubService(user_login.github_token)

        github_user = await github_service.get_authenticated_user()@router.get("/", response_model=List[User])

        async def get_users(

        if not github_user:    skip: int = Query(0, ge=0, description="Nombre d'éléments à ignorer"),

            raise HTTPException(    limit: int = Query(100, ge=1, le=1000, description="Nombre maximum d'éléments à retourner")

                status_code=status.HTTP_401_UNAUTHORIZED,):

                detail="Invalid GitHub token"    """Récupère la liste de tous les utilisateurs"""

            )    try:

                return UserRepository.get_all(skip=skip, limit=limit)

        # Check if user exists    except Exception as e:

        username = github_user["login"]        raise HTTPException(status_code=500, detail=f"Erreur lors de la récupération des utilisateurs: {str(e)}")

        user = await user_repo.get_user_by_username(username)

        

        if not user:@router.get("/{user_id}", response_model=User)

            # Create new userasync def get_user(user_id: str):

            from src.models.user import UserCreate    """Récupère un utilisateur par son ID"""

            user_data = UserCreate(    user = UserRepository.get_by_id(user_id)

                username=username,    if not user:

                email=github_user.get("email"),        raise HTTPException(status_code=404, detail="Utilisateur non trouvé")

                name=github_user.get("name"),    return user

                avatar_url=github_user.get("avatar_url"),

                github_token=user_login.github_token

            )@router.put("/{user_id}", response_model=User)

            user = await user_repo.create_user(user_data)async def update_user(user_id: str, user: UserUpdate):

            """Met à jour un utilisateur"""

        # Create access token    updated_user = UserRepository.update(user_id, user)

        access_token = create_access_token({"sub": user.username})    if not updated_user:

                raise HTTPException(status_code=404, detail="Utilisateur non trouvé")

        return {    return updated_user

            "access_token": access_token,

            "token_type": "bearer",

            "user": UserResponse(**user.model_dump())@router.delete("/{user_id}", status_code=204)

        }async def delete_user(user_id: str):

            """Supprime un utilisateur"""

    except HTTPException:    deleted = UserRepository.delete(user_id)

        raise    if not deleted:

    except Exception as e:        raise HTTPException(status_code=404, detail="Utilisateur non trouvé")

        raise HTTPException(    return None

            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Login error: {str(e)}"
        )


@router.get("/users/me", response_model=UserResponse)
async def get_current_user_info(
    authorization: Optional[str] = Header(None),
    user_repo: UserRepository = Depends(get_user_repo)
):
    """Get current user information"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid authorization header"
        )
    
    token = authorization.replace("Bearer ", "")
    
    # Decode token and get user
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )
    
    username = payload.get("sub")
    user = await user_repo.get_user_by_username(username)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return UserResponse(**user.model_dump())
