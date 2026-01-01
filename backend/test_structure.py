"""
Script de test pour vérifier la nouvelle structure backend
"""
import sys
import os

# Ajouter le répertoire parent au path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test que tous les modules peuvent être importés"""
    print("🧪 Test des imports...")
    
    try:
        # Models
        from src.models import (
            User, UserCreate, UserUpdate,
            Project, ProjectCreate, ProjectUpdate,
            Classe, ClasseCreate, ClasseUpdate,
            Individu, IndividuCreate, IndividuUpdate,
            Relation, RelationCreate, RelationUpdate,
            RelationType, RelationTypeCreate, RelationTypeUpdate
        )
        print("✅ Tous les modèles importés avec succès")
        
        # Repositories
        from src.repositories import (
            UserRepository,
            ProjectRepository,
            ClasseRepository,
            IndividuRepository,
            RelationRepository,
            RelationTypeRepository
        )
        print("✅ Tous les repositories importés avec succès")
        
        # Controllers
        from src.controllers import (
            user_controller,
            project_controller,
            classe_controller,
            individu_controller,
            relation_controller
        )
        print("✅ Tous les controllers importés avec succès")
        
        return True
    except Exception as e:
        print(f"❌ Erreur d'import: {e}")
        return False


def test_model_creation():
    """Test la création d'instances de modèles"""
    print("\n🧪 Test de création de modèles...")
    
    try:
        from src.models import (
            UserCreate, ProjectCreate, ClasseCreate,
            IndividuCreate, RelationCreate, RelationTypeCreate
        )
        
        # Test User
        user = UserCreate(
            username="testuser",
            email="test@example.com",
            password="password123",
            full_name="Test User"
        )
        print(f"✅ UserCreate: {user.username}")
        
        # Test Project
        project = ProjectCreate(
            user_id="user-123",
            name="Test Project",
            description="A test project",
            settings={"test": "value"}
        )
        print(f"✅ ProjectCreate: {project.name}")
        
        # Test Classe
        classe = ClasseCreate(
            project_id="project-123",
            name="Person",
            description="A person class",
            color="#3B82F6",
            properties_schema={"name": {"type": "string", "required": True}}
        )
        print(f"✅ ClasseCreate: {classe.name}")
        
        # Test Individu
        individu = IndividuCreate(
            classe_id="classe-123",
            project_id="project-123",
            label="John Doe",
            properties={"name": "John Doe", "age": 30}
        )
        print(f"✅ IndividuCreate: {individu.label}")
        
        # Test RelationType
        rel_type = RelationTypeCreate(
            project_id="project-123",
            name="KNOWS",
            description="Knows relationship",
            color="#6B7280"
        )
        print(f"✅ RelationTypeCreate: {rel_type.name}")
        
        # Test Relation
        relation = RelationCreate(
            type_id="reltype-123",
            from_individu_id="individu-123",
            to_individu_id="individu-456",
            project_id="project-123",
            properties={"since": "2020-01-01"}
        )
        print(f"✅ RelationCreate: {relation.type_id}")
        
        return True
    except Exception as e:
        print(f"❌ Erreur de création de modèle: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Exécute tous les tests"""
    print("=" * 60)
    print("TEST DE LA NOUVELLE STRUCTURE BACKEND")
    print("=" * 60)
    
    results = []
    
    # Test 1: Imports
    results.append(test_imports())
    
    # Test 2: Model creation
    results.append(test_model_creation())
    
    # Résumé
    print("\n" + "=" * 60)
    print("RÉSUMÉ")
    print("=" * 60)
    passed = sum(results)
    total = len(results)
    print(f"✅ Tests réussis: {passed}/{total}")
    
    if passed == total:
        print("\n🎉 Tous les tests sont passés avec succès!")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) échoué(s)")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
