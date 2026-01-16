#!/bin/bash

###############################################################################
# Script de test de l'API MDE (Model-Driven Engineering)
# Teste toutes les routes: Metamodels, Concepts, Attributes, Relationships
###############################################################################

set -e  # Arrêt en cas d'erreur

# Configuration
API_URL="http://localhost:8000"
API_PID=""
TEST_RESULTS=()
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

# Couleurs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Variables pour stocker les IDs créés
METAMODEL_ID=""
CONCEPT_ID_1=""
CONCEPT_ID_2=""
CONCEPT_ID_3=""
ATTRIBUTE_ID=""
RELATIONSHIP_ID=""
TOKEN=""

###############################################################################
# Fonctions utilitaires
###############################################################################

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[✓]${NC} $1"
    PASSED_TESTS=$((PASSED_TESTS + 1))
    TEST_RESULTS+=("✓ $1")
}

log_error() {
    echo -e "${RED}[✗]${NC} $1"
    FAILED_TESTS=$((FAILED_TESTS + 1))
    TEST_RESULTS+=("✗ $1")
}

log_warning() {
    echo -e "${YELLOW}[⚠]${NC} $1"
}

test_endpoint() {
    local method=$1
    local endpoint=$2
    local data=$3
    local description=$4
    local expected_status=${5:-200}
    
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    
    log_info "Test: $description"
    
    local headers=(-H "Content-Type: application/json")
    if [ -n "$TOKEN" ]; then
        headers+=(-H "Authorization: Bearer $TOKEN")
    fi
    
    if [ -n "$data" ]; then
        response=$(curl -s -w "\n%{http_code}" -X $method "$API_URL$endpoint" \
            "${headers[@]}" \
            -d "$data")
    else
        response=$(curl -s -w "\n%{http_code}" -X $method "$API_URL$endpoint" \
            "${headers[@]}")
    fi
    
    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | sed '$d')
    
    if [ "$http_code" -eq "$expected_status" ]; then
        log_success "$description (HTTP $http_code)"
        echo "$body"
        return 0
    else
        log_error "$description (Expected HTTP $expected_status, got $http_code)"
        echo "Response: $body"
        return 1
    fi
}

start_api() {
    log_info "🚀 Démarrage de l'API..."
    
    # Vérifier si l'API est déjà lancée
    if curl -s "$API_URL/health" > /dev/null 2>&1; then
        log_warning "API déjà en cours d'exécution"
        return 0
    fi
    
    # Lancer l'API en arrière-plan
    cd "$(dirname "$0")/.."
    python main.py > /tmp/api_test.log 2>&1 &
    API_PID=$!
    
    log_info "API PID: $API_PID"
    
    # Attendre que l'API soit prête
    local max_attempts=30
    local attempt=0
    
    while [ $attempt -lt $max_attempts ]; do
        if curl -s "$API_URL/health" > /dev/null 2>&1; then
            log_success "API démarrée avec succès"
            return 0
        fi
        attempt=$((attempt + 1))
        sleep 1
    done
    
    log_error "Échec du démarrage de l'API"
    cat /tmp/api_test.log
    exit 1
}

stop_api() {
    if [ -n "$API_PID" ]; then
        log_info "🛑 Arrêt de l'API (PID: $API_PID)..."
        kill $API_PID 2>/dev/null || true
        wait $API_PID 2>/dev/null || true
        log_success "API arrêtée"
    fi
}

cleanup() {
    log_info "🧹 Nettoyage..."
    stop_api
    
    # Afficher le résumé
    echo ""
    echo "═══════════════════════════════════════════════════════════"
    echo -e "${BLUE}         RÉSUMÉ DES TESTS MDE API${NC}"
    echo "═══════════════════════════════════════════════════════════"
    echo -e "Total tests: ${TOTAL_TESTS}"
    echo -e "${GREEN}Réussis: ${PASSED_TESTS}${NC}"
    echo -e "${RED}Échoués: ${FAILED_TESTS}${NC}"
    echo ""
    
    if [ $FAILED_TESTS -eq 0 ]; then
        echo -e "${GREEN}✓ TOUS LES TESTS SONT PASSÉS !${NC}"
        exit 0
    else
        echo -e "${RED}✗ CERTAINS TESTS ONT ÉCHOUÉ${NC}"
        echo ""
        echo "Détails des échecs:"
        for result in "${TEST_RESULTS[@]}"; do
            if [[ $result == ✗* ]]; then
                echo -e "${RED}$result${NC}"
            fi
        done
        exit 1
    fi
}

trap cleanup EXIT

###############################################################################
# Tests de santé et authentification
###############################################################################

test_health_and_auth() {
    echo ""
    echo "═══════════════════════════════════════════════════════════"
    echo -e "${BLUE}1. TESTS DE SANTÉ ET AUTHENTIFICATION${NC}"
    echo "═══════════════════════════════════════════════════════════"
    
    # Test health
    test_endpoint "GET" "/health" "" "Health check"
    
    # Test root
    test_endpoint "GET" "/" "" "Root endpoint"
    
    # Note: Pour les tests réels, vous devrez implémenter l'authentification
    # Pour l'instant, on simule avec un token vide
    log_warning "Authentication: Tests sans token (à adapter selon votre système)"
}

###############################################################################
# Tests METAMODEL
###############################################################################

test_metamodel_routes() {
    echo ""
    echo "═══════════════════════════════════════════════════════════"
    echo -e "${BLUE}2. TESTS METAMODEL (CRUD)${NC}"
    echo "═══════════════════════════════════════════════════════════"
    
    # CREATE Metamodel
    local response
    response=$(test_endpoint "POST" "/api/metamodels" '{
        "name": "TestMetamodel",
        "description": "Metamodel de test créé par script bash",
        "version": "1.0.0"
    }' "POST /api/metamodels - Créer metamodel" 201)
    
    if [ $? -eq 0 ]; then
        METAMODEL_ID=$(echo "$response" | grep -o '"id":"[^"]*' | cut -d'"' -f4)
        log_info "Metamodel ID créé: $METAMODEL_ID"
    fi
    
    # GET Metamodel by ID
    if [ -n "$METAMODEL_ID" ]; then
        test_endpoint "GET" "/api/metamodels/$METAMODEL_ID" "" \
            "GET /api/metamodels/{id} - Récupérer metamodel"
    fi
    
    # GET All Metamodels
    test_endpoint "GET" "/api/metamodels" "" \
        "GET /api/metamodels - Lister tous les metamodels"
    
    # UPDATE Metamodel
    if [ -n "$METAMODEL_ID" ]; then
        test_endpoint "PUT" "/api/metamodels/$METAMODEL_ID" '{
            "description": "Description mise à jour",
            "version": "1.0.1"
        }' "PUT /api/metamodels/{id} - Mettre à jour metamodel"
    fi
}

###############################################################################
# Tests CONCEPT
###############################################################################

test_concept_routes() {
    echo ""
    echo "═══════════════════════════════════════════════════════════"
    echo -e "${BLUE}3. TESTS CONCEPT (CRUD + Méthodes spécialisées)${NC}"
    echo "═══════════════════════════════════════════════════════════"
    
    if [ -z "$METAMODEL_ID" ]; then
        log_warning "METAMODEL_ID manquant, skip tests concepts"
        return
    fi
    
    # CREATE Concept 1 - Vehicle
    local response
    response=$(test_endpoint "POST" "/api/concepts" '{
        "name": "Vehicle",
        "description": "Concept de véhicule",
        "metamodel_id": "'"$METAMODEL_ID"'",
        "x_position": 100,
        "y_position": 100
    }' "POST /api/concepts - Créer concept Vehicle" 201)
    
    if [ $? -eq 0 ]; then
        CONCEPT_ID_1=$(echo "$response" | grep -o '"id":"[^"]*' | cut -d'"' -f4)
        log_info "Concept Vehicle ID: $CONCEPT_ID_1"
    fi
    
    # CREATE Concept 2 - Car (sous-classe de Vehicle)
    response=$(test_endpoint "POST" "/api/concepts" '{
        "name": "Car",
        "description": "Voiture - sous-classe de Vehicle",
        "metamodel_id": "'"$METAMODEL_ID"'",
        "x_position": 200,
        "y_position": 200
    }' "POST /api/concepts - Créer concept Car" 201)
    
    if [ $? -eq 0 ]; then
        CONCEPT_ID_2=$(echo "$response" | grep -o '"id":"[^"]*' | cut -d'"' -f4)
        log_info "Concept Car ID: $CONCEPT_ID_2"
    fi
    
    # CREATE Concept 3 - Engine
    response=$(test_endpoint "POST" "/api/concepts" '{
        "name": "Engine",
        "description": "Moteur - partie d un véhicule",
        "metamodel_id": "'"$METAMODEL_ID"'",
        "x_position": 300,
        "y_position": 100
    }' "POST /api/concepts - Créer concept Engine" 201)
    
    if [ $? -eq 0 ]; then
        CONCEPT_ID_3=$(echo "$response" | grep -o '"id":"[^"]*' | cut -d'"' -f4)
        log_info "Concept Engine ID: $CONCEPT_ID_3"
    fi
    
    # GET Concept by ID
    if [ -n "$CONCEPT_ID_1" ]; then
        test_endpoint "GET" "/api/concepts/$CONCEPT_ID_1" "" \
            "GET /api/concepts/{id} - Récupérer concept"
    fi
    
    # GET Concepts by Metamodel
    test_endpoint "GET" "/api/concepts?metamodel_id=$METAMODEL_ID" "" \
        "GET /api/concepts?metamodel_id - Concepts par metamodel"
    
    # UPDATE Concept position
    if [ -n "$CONCEPT_ID_1" ]; then
        test_endpoint "PATCH" "/api/concepts/$CONCEPT_ID_1/position" '{
            "x_position": 150,
            "y_position": 150
        }' "PATCH /api/concepts/{id}/position - Mettre à jour position"
    fi
    
    # UPDATE Concept
    if [ -n "$CONCEPT_ID_1" ]; then
        test_endpoint "PUT" "/api/concepts/$CONCEPT_ID_1" '{
            "description": "Concept de véhicule - description mise à jour"
        }' "PUT /api/concepts/{id} - Mettre à jour concept"
    fi
}

###############################################################################
# Tests ATTRIBUTE
###############################################################################

test_attribute_routes() {
    echo ""
    echo "═══════════════════════════════════════════════════════════"
    echo -e "${BLUE}4. TESTS ATTRIBUTE (CRUD + Méthodes spécialisées)${NC}"
    echo "═══════════════════════════════════════════════════════════"
    
    if [ -z "$CONCEPT_ID_1" ]; then
        log_warning "CONCEPT_ID_1 manquant, skip tests attributes"
        return
    fi
    
    # CREATE Attribute
    local response
    response=$(test_endpoint "POST" "/api/attributes" '{
        "name": "brand",
        "type": "String",
        "is_required": true,
        "default_value": null,
        "description": "Marque du véhicule",
        "concept_id": "'"$CONCEPT_ID_1"'"
    }' "POST /api/attributes - Créer attribut" 201)
    
    if [ $? -eq 0 ]; then
        ATTRIBUTE_ID=$(echo "$response" | grep -o '"id":"[^"]*' | cut -d'"' -f4)
        log_info "Attribute ID: $ATTRIBUTE_ID"
    fi
    
    # CREATE another attribute
    test_endpoint "POST" "/api/attributes" '{
        "name": "year",
        "type": "Integer",
        "is_required": false,
        "default_value": "2024",
        "description": "Année de fabrication",
        "concept_id": "'"$CONCEPT_ID_1"'"
    }' "POST /api/attributes - Créer attribut year" 201
    
    # GET Attribute by ID
    if [ -n "$ATTRIBUTE_ID" ]; then
        test_endpoint "GET" "/api/attributes/$ATTRIBUTE_ID" "" \
            "GET /api/attributes/{id} - Récupérer attribut"
    fi
    
    # GET Attributes by Concept
    test_endpoint "GET" "/api/attributes?concept_id=$CONCEPT_ID_1" "" \
        "GET /api/attributes?concept_id - Attributs par concept"
    
    # GET Required Attributes
    test_endpoint "GET" "/api/attributes/required?concept_id=$CONCEPT_ID_1" "" \
        "GET /api/attributes/required - Attributs obligatoires"
    
    # UPDATE Attribute
    if [ -n "$ATTRIBUTE_ID" ]; then
        test_endpoint "PUT" "/api/attributes/$ATTRIBUTE_ID" '{
            "description": "Marque du véhicule (mise à jour)",
            "is_required": false
        }' "PUT /api/attributes/{id} - Mettre à jour attribut"
    fi
}

###############################################################################
# Tests RELATIONSHIP
###############################################################################

test_relationship_routes() {
    echo ""
    echo "═══════════════════════════════════════════════════════════"
    echo -e "${BLUE}5. TESTS RELATIONSHIP (CRUD + Raisonnement ontologique)${NC}"
    echo "═══════════════════════════════════════════════════════════"
    
    if [ -z "$CONCEPT_ID_1" ] || [ -z "$CONCEPT_ID_2" ]; then
        log_warning "CONCEPT_IDs manquants, skip tests relationships"
        return
    fi
    
    # CREATE Relationship IS_A (Car is_a Vehicle)
    # Note: Création automatique de l'inverse HAS_SUBCLASS
    local response
    response=$(test_endpoint "POST" "/api/relationships" '{
        "type": "is_a",
        "description": "Car hérite de Vehicle",
        "source_concept_id": "'"$CONCEPT_ID_2"'",
        "target_concept_id": "'"$CONCEPT_ID_1"'",
        "metamodel_id": "'"$METAMODEL_ID"'"
    }' "POST /api/relationships - Créer relation IS_A (+ inverse auto)" 201)
    
    if [ $? -eq 0 ]; then
        RELATIONSHIP_ID=$(echo "$response" | grep -o '"id":"[^"]*' | cut -d'"' -f4)
        log_info "Relationship IS_A ID: $RELATIONSHIP_ID"
        log_info "→ Relation inverse HAS_SUBCLASS créée automatiquement"
    fi
    
    # CREATE Relationship HAS_PART (Vehicle has_part Engine)
    # Note: Création automatique de l'inverse PART_OF
    if [ -n "$CONCEPT_ID_3" ]; then
        test_endpoint "POST" "/api/relationships" '{
            "type": "has_part",
            "description": "Vehicle contient Engine",
            "source_concept_id": "'"$CONCEPT_ID_1"'",
            "target_concept_id": "'"$CONCEPT_ID_3"'",
            "metamodel_id": "'"$METAMODEL_ID"'"
        }' "POST /api/relationships - Créer relation HAS_PART (+ inverse auto)" 201
        
        log_info "→ Relation inverse PART_OF créée automatiquement"
    fi
    
    # GET Relationship by ID
    if [ -n "$RELATIONSHIP_ID" ]; then
        test_endpoint "GET" "/api/relationships/$RELATIONSHIP_ID" "" \
            "GET /api/relationships/{id} - Récupérer relation"
    fi
    
    # GET Relationships by Concept
    test_endpoint "GET" "/api/relationships?concept_id=$CONCEPT_ID_1" "" \
        "GET /api/relationships?concept_id - Relations d'un concept"
    
    # GET Relationships by Type
    test_endpoint "GET" "/api/relationships?type=is_a" "" \
        "GET /api/relationships?type - Filtrer par type IS_A"
    
    test_endpoint "GET" "/api/relationships?type=has_subclass" "" \
        "GET /api/relationships?type - Filtrer par type HAS_SUBCLASS (inverse)"
    
    # POST Infer Relationships (transitivité)
    # Note: Si A is_a B et B is_a C, alors A is_a C
    log_info "🧠 Test du raisonnement ontologique (transitivité)..."
    test_endpoint "POST" "/api/relationships/infer?metamodel_id=$METAMODEL_ID" "" \
        "POST /api/relationships/infer - Inférence par transitivité"
    
    # UPDATE Relationship
    if [ -n "$RELATIONSHIP_ID" ]; then
        test_endpoint "PUT" "/api/relationships/$RELATIONSHIP_ID" '{
            "description": "Car hérite de Vehicle (description mise à jour)"
        }' "PUT /api/relationships/{id} - Mettre à jour relation"
    fi
}

###############################################################################
# Tests de suppression (CASCADE)
###############################################################################

test_delete_cascade() {
    echo ""
    echo "═══════════════════════════════════════════════════════════"
    echo -e "${BLUE}6. TESTS DELETE (CASCADE)${NC}"
    echo "═══════════════════════════════════════════════════════════"
    
    # DELETE Attribute
    if [ -n "$ATTRIBUTE_ID" ]; then
        test_endpoint "DELETE" "/api/attributes/$ATTRIBUTE_ID" "" \
            "DELETE /api/attributes/{id} - Supprimer attribut" 204
    fi
    
    # DELETE Relationship (+ inverse automatique)
    if [ -n "$RELATIONSHIP_ID" ]; then
        log_info "→ Suppression automatique de la relation inverse"
        test_endpoint "DELETE" "/api/relationships/$RELATIONSHIP_ID" "" \
            "DELETE /api/relationships/{id} - Supprimer relation (+ inverse)" 204
    fi
    
    # DELETE Concepts
    if [ -n "$CONCEPT_ID_3" ]; then
        test_endpoint "DELETE" "/api/concepts/$CONCEPT_ID_3" "" \
            "DELETE /api/concepts/{id} - Supprimer concept Engine" 204
    fi
    
    if [ -n "$CONCEPT_ID_2" ]; then
        test_endpoint "DELETE" "/api/concepts/$CONCEPT_ID_2" "" \
            "DELETE /api/concepts/{id} - Supprimer concept Car" 204
    fi
    
    if [ -n "$CONCEPT_ID_1" ]; then
        log_info "→ Suppression cascade: attributs et relations associés"
        test_endpoint "DELETE" "/api/concepts/$CONCEPT_ID_1" "" \
            "DELETE /api/concepts/{id} - Supprimer concept Vehicle (CASCADE)" 204
    fi
    
    # DELETE Metamodel (cascade: tous concepts, attributes, relationships)
    if [ -n "$METAMODEL_ID" ]; then
        log_info "→ Suppression cascade: TOUS les concepts, attributs et relations"
        test_endpoint "DELETE" "/api/metamodels/$METAMODEL_ID" "" \
            "DELETE /api/metamodels/{id} - Supprimer metamodel (CASCADE TOTAL)" 204
    fi
}

###############################################################################
# Main
###############################################################################

main() {
    echo "═══════════════════════════════════════════════════════════"
    echo -e "${BLUE}    TESTS API MDE - AUTO-CODE PLATFORM${NC}"
    echo "═══════════════════════════════════════════════════════════"
    echo ""
    
    start_api
    
    test_health_and_auth
    test_metamodel_routes
    test_concept_routes
    test_attribute_routes
    test_relationship_routes
    test_delete_cascade
    
    echo ""
    log_success "Tous les tests sont terminés !"
}

main "$@"
