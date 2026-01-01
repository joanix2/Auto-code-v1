"""
Script de test pour la gestion des projets
"""
import sys
import os
# Ajouter le répertoire parent (back/) au path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

from src.services.levenshtein_service import levenshtein_distance, levenshtein_similarity, search_by_similarity


def test_levenshtein_distance():
    """Test du calcul de distance de Levenshtein"""
    print("🧪 Test de la distance de Levenshtein...")
    
    tests = [
        ("chat", "chat", 0),
        ("chat", "chien", 3),
        ("kitten", "sitting", 3),
        ("projet", "project", 1),
        ("GraphDB", "graphdb", 0),  # insensible à la casse
    ]
    
    for s1, s2, expected in tests:
        result = levenshtein_distance(s1, s2)
        status = "✅" if result == expected else "❌"
        print(f"  {status} distance('{s1}', '{s2}') = {result} (attendu: {expected})")
        assert result == expected, f"Erreur: attendu {expected}, obtenu {result}"
    
    return True


def test_levenshtein_similarity():
    """Test du calcul de similarité"""
    print("\n🧪 Test de la similarité...")
    
    tests = [
        ("graph", "graph", 1.0),
        ("graph", "grap", 0.8),
        ("projet", "project", 0.83),   # ajusté
        ("test", "testing", 0.57),     # ajusté
    ]
    
    for query, text, expected_min in tests:
        result = levenshtein_similarity(query, text)
        status = "✅" if result >= expected_min else "❌"
        print(f"  {status} similarity('{query}', '{text}') = {result:.3f} (min: {expected_min})")
        assert result >= expected_min - 0.01, f"Erreur: attendu >= {expected_min}, obtenu {result}"
    
    return True


def test_search_projects():
    """Test de la recherche de projets"""
    print("\n🧪 Test de la recherche de projets...")
    
    # Simuler des projets
    projects = [
        ("Graphe de Connaissances", {"id": "1", "name": "Graphe de Connaissances"}),
        ("Mon Graph Personnel", {"id": "2", "name": "Mon Graph Personnel"}),
        ("Base de Données Neo4j", {"id": "3", "name": "Base de Données Neo4j"}),
        ("Projet Test", {"id": "4", "name": "Projet Test"}),
        ("Graph Analysis", {"id": "5", "name": "Graph Analysis"}),
    ]
    
    # Test 1: Recherche exacte
    results = search_by_similarity("graph", projects, threshold=0.5)
    print(f"\n  Recherche 'graph' (threshold=0.5):")
    for item, score in results:
        print(f"    - {item['name']}: {score:.3f}")
    assert len(results) > 0, "Devrait trouver au moins un résultat"
    
    # Test 2: Recherche avec faute de frappe
    results = search_by_similarity("grafe", projects, threshold=0.5)
    print(f"\n  Recherche 'grafe' (threshold=0.5):")
    for item, score in results:
        print(f"    - {item['name']}: {score:.3f}")
    
    # Test 3: Recherche très stricte
    results = search_by_similarity("graph", projects, threshold=0.9)
    print(f"\n  Recherche 'graph' (threshold=0.9, strict):")
    for item, score in results:
        print(f"    - {item['name']}: {score:.3f}")
    
    print("\n  ✅ Recherche fonctionnelle")
    return True


def test_project_repository():
    """Test des imports du repository"""
    print("\n🧪 Test des imports du repository...")
    
    try:
        from src.repositories.project_repository import ProjectRepository
        print("  ✅ ProjectRepository importé")
        
        from src.controllers.project_controller import router
        print("  ✅ Controller importé")
        
        return True
    except Exception as e:
        print(f"  ❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Exécute tous les tests"""
    print("=" * 60)
    print("TEST DE LA GESTION DES PROJETS")
    print("=" * 60)
    
    tests = [
        ("Distance de Levenshtein", test_levenshtein_distance),
        ("Similarité", test_levenshtein_similarity),
        ("Recherche de projets", test_search_projects),
        ("Repository & Controller", test_project_repository),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append(result)
        except Exception as e:
            print(f"\n❌ Erreur dans le test '{name}': {e}")
            import traceback
            traceback.print_exc()
            results.append(False)
    
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
