#!/bin/bash
# Auto-Code Headless Development Server
# This script runs continuous development on a server

set -e

# Configuration
REPO_ID="${AUTOCODE_REPO_ID:-}"
API_URL="${AUTOCODE_API_URL:-http://localhost:8000}"
SLEEP_INTERVAL="${AUTOCODE_SLEEP_INTERVAL:-300}"  # 5 minutes par défaut
MAX_TICKETS="${AUTOCODE_MAX_TICKETS:-0}"  # 0 = illimité

# Couleurs pour les logs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Fonction de log
log_info() {
    echo -e "${BLUE}[INFO]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

# Vérification des prérequis
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Vérifier ANTHROPIC_API_KEY
    if [ -z "$ANTHROPIC_API_KEY" ]; then
        log_error "ANTHROPIC_API_KEY not set"
        exit 1
    fi
    
    # Vérifier REPO_ID
    if [ -z "$REPO_ID" ]; then
        log_error "AUTOCODE_REPO_ID not set"
        exit 1
    fi
    
    # Vérifier curl ou jq
    if ! command -v curl &> /dev/null; then
        log_error "curl is required but not installed"
        exit 1
    fi
    
    if ! command -v jq &> /dev/null; then
        log_warning "jq not installed, JSON parsing will be limited"
    fi
    
    log_success "Prerequisites checked"
}

# Authentification
authenticate() {
    log_info "Authenticating..."
    
    local username="${AUTOCODE_USERNAME:-admin}"
    local password="${AUTOCODE_PASSWORD:-admin}"
    
    TOKEN=$(curl -s -X POST "$API_URL/api/auth/login" \
        -H "Content-Type: application/json" \
        -d "{\"username\":\"$username\",\"password\":\"$password\"}" \
        | jq -r '.access_token' 2>/dev/null)
    
    if [ -z "$TOKEN" ] || [ "$TOKEN" = "null" ]; then
        log_error "Authentication failed"
        exit 1
    fi
    
    log_success "Authenticated successfully"
}

# Récupérer le prochain ticket
get_next_ticket() {
    log_info "Fetching next ticket..."
    
    RESPONSE=$(curl -s -X GET "$API_URL/api/tickets/repository/$REPO_ID/next" \
        -H "Authorization: Bearer $TOKEN")
    
    if command -v jq &> /dev/null; then
        TICKET_ID=$(echo "$RESPONSE" | jq -r '.ticket.id // empty')
        TICKET_TITLE=$(echo "$RESPONSE" | jq -r '.ticket.title // empty')
        TOTAL_OPEN=$(echo "$RESPONSE" | jq -r '.total_open_tickets // 0')
        
        if [ -n "$TICKET_ID" ] && [ "$TICKET_ID" != "null" ]; then
            log_info "Next ticket: $TICKET_TITLE ($TICKET_ID)"
            log_info "Total open tickets: $TOTAL_OPEN"
            return 0
        else
            log_warning "No open tickets in queue"
            return 1
        fi
    else
        # Fallback sans jq
        if echo "$RESPONSE" | grep -q "ticket"; then
            log_info "Ticket found in queue"
            return 0
        else
            log_warning "No open tickets in queue"
            return 1
        fi
    fi
}

# Développer le prochain ticket
develop_next_ticket() {
    log_info "Starting development..."
    
    RESPONSE=$(curl -s -w "\n%{http_code}" -X POST \
        "$API_URL/api/tickets/repository/$REPO_ID/develop-next" \
        -H "Authorization: Bearer $TOKEN" \
        -H "Content-Type: application/json" \
        -d '{}')
    
    HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
    BODY=$(echo "$RESPONSE" | sed '$d')
    
    if [ "$HTTP_CODE" = "200" ]; then
        if command -v jq &> /dev/null; then
            TICKET_TITLE=$(echo "$BODY" | jq -r '.ticket_title // "Unknown"')
            MODEL=$(echo "$BODY" | jq -r '.model // "Unknown"')
            INPUT_TOKENS=$(echo "$BODY" | jq -r '.usage.input_tokens // 0')
            OUTPUT_TOKENS=$(echo "$BODY" | jq -r '.usage.output_tokens // 0')
            
            log_success "Ticket developed: $TICKET_TITLE"
            log_info "Model: $MODEL"
            log_info "Tokens: $INPUT_TOKENS input + $OUTPUT_TOKENS output"
            
            # Sauvegarder la réponse
            TIMESTAMP=$(date +%s)
            OUTPUT_FILE="implementation_${TIMESTAMP}.md"
            echo "$BODY" | jq -r '.claude_response' > "$OUTPUT_FILE"
            log_success "Response saved to: $OUTPUT_FILE"
        else
            log_success "Ticket developed successfully"
        fi
        return 0
    elif [ "$HTTP_CODE" = "404" ]; then
        log_warning "No tickets to develop"
        return 1
    else
        log_error "Development failed (HTTP $HTTP_CODE)"
        echo "$BODY"
        return 2
    fi
}

# Boucle principale
main_loop() {
    local tickets_processed=0
    
    log_info "Starting continuous development..."
    log_info "Repository ID: $REPO_ID"
    log_info "Sleep interval: ${SLEEP_INTERVAL}s"
    log_info "Max tickets: ${MAX_TICKETS} (0 = unlimited)"
    
    while true; do
        log_info "=== Iteration $((tickets_processed + 1)) ==="
        
        # Vérifier s'il y a des tickets
        if ! get_next_ticket; then
            log_info "No tickets available, waiting..."
            sleep "$SLEEP_INTERVAL"
            continue
        fi
        
        # Développer le ticket
        if develop_next_ticket; then
            tickets_processed=$((tickets_processed + 1))
            log_success "Total tickets processed: $tickets_processed"
            
            # Vérifier la limite
            if [ "$MAX_TICKETS" -gt 0 ] && [ "$tickets_processed" -ge "$MAX_TICKETS" ]; then
                log_success "Max tickets limit reached ($MAX_TICKETS)"
                break
            fi
        else
            log_warning "Development failed or no tickets"
        fi
        
        # Pause avant le prochain ticket
        log_info "Sleeping for ${SLEEP_INTERVAL}s..."
        sleep "$SLEEP_INTERVAL"
    done
    
    log_success "Continuous development completed"
    log_success "Total tickets processed: $tickets_processed"
}

# Point d'entrée
main() {
    echo "╔════════════════════════════════════════╗"
    echo "║   Auto-Code Headless Development      ║"
    echo "║   Continuous Ticket Development       ║"
    echo "╚════════════════════════════════════════╝"
    echo ""
    
    check_prerequisites
    authenticate
    main_loop
}

# Gestion des signaux (Ctrl+C)
trap 'log_warning "Received interrupt signal, exiting..."; exit 0' INT TERM

# Lancer le script
main "$@"
