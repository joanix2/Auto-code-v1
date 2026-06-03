"""
Script de test pour l'authentification
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.utils.auth import (
    create_access_token,
    decode_access_token,
    get_password_hash,
    verify_password,
)


def test_password_hashing():
    """Test du hachage et vérification de mot de passe"""
    print("🧪 Test du hachage de mot de passe...")

    password = "mon_super_mot_de_passe"
    hashed = get_password_hash(password)

    print(f"  Mot de passe: {password}")
    print(f"  Hash: {hashed[:50]}...")

    # Vérifier que le mot de passe correspond
    assert verify_password(password, hashed), "❌ La vérification a échoué"
    print("  ✅ Vérification OK")

    # Vérifier qu'un mauvais mot de passe ne correspond pas
    assert not verify_password("mauvais_mdp", hashed), "❌ Un mauvais mot de passe a été accepté"
    print("  ✅ Rejet du mauvais mot de passe OK")

    return True


def test_jwt_tokens():
    """Test de création et décodage de tokens JWT"""
    print("\n🧪 Test des tokens JWT...")

    # Créer un token
    data = {"sub": "user-123", "username": "testuser"}
    token = create_access_token(data)

    print(f"  Token créé: {token[:50]}...")

    # Décoder le token
    payload = decode_access_token(token)

    assert payload is not None, "❌ Le décodage a échoué"
    assert payload.get("sub") == "user-123", "❌ Le user_id ne correspond pas"
    assert payload.get("username") == "testuser", "❌ Le username ne correspond pas"
    print(f"  ✅ Token décodé: {payload}")

    # Test avec un mauvais token
    bad_payload = decode_access_token("mauvais.token.jwt")
    assert bad_payload is None, "❌ Un mauvais token a été accepté"
    print("  ✅ Rejet du mauvais token OK")

    return True


def test_auth_workflow():
    """Test du workflow complet d'authentification"""
    print("\n🧪 Test du workflow d'authentification...")

    # Simuler une inscription
    password = "password123"
    hashed_password = get_password_hash(password)
    print("  1. ✅ Mot de passe haché lors de l'inscription")

    # Simuler une connexion
    is_valid = verify_password(password, hashed_password)
    assert is_valid, "❌ La connexion a échoué"
    print("  2. ✅ Mot de passe vérifié lors de la connexion")

    # Créer un token pour l'utilisateur
    user_data = {"sub": "user-456", "username": "john_doe"}
    token = create_access_token(user_data)
    print("  3. ✅ Token JWT créé")

    # Vérifier le token
    payload = decode_access_token(token)
    assert payload is not None, "❌ La vérification du token a échoué"
    assert payload["sub"] == "user-456", "❌ Les données du token sont incorrectes"
    print("  4. ✅ Token vérifié avec succès")

    return True


def main():
    """Exécute tous les tests"""
    print("=" * 60)
    print("TEST DE L'AUTHENTIFICATION")
    print("=" * 60)

    tests = [
        ("Hachage de mot de passe", test_password_hashing),
        ("Tokens JWT", test_jwt_tokens),
        ("Workflow complet", test_auth_workflow),
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
