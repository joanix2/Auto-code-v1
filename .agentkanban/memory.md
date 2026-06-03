# Memory — Contexte persistant

## Dernière mise à jour : 2026-06-03T23:00

### Statut MVPs

| MVP | Statut | Notes |
|-----|--------|-------|
| A — Consolidation IR | ✅ Terminé | JSON schema, endpoints graph/load/save, PATCH/DELETE edges, roundtrip tests |
| B — Requêtes | ❌ Non commencé | Dépend de A |
| C — Templates | ❌ Non commencé | Dépend de B |
| D — Validation | ❌ Non commencé | |
| E — Héritage | ❌ Non commencé | |
| F — Ontologie | ❌ Non commencé | |
| G — Agents | ❌ Non commencé | |

### P0/P1 Terminés

- `fix_mypy_errors` ✅
- `fix_eslint_frontend` ✅
- `add_backend_tests` ✅ 110 tests
- `add_frontend_tests` ✅ 22 tests
- `mvp_a_consolidation` ✅
- `refactor_controller` ✅
- `bug_metamodel_create` ✅
- `bug_error_helper` ✅
- `bug_ticket_status_sync` ✅

### P0 Restants

- `bug_relation_update` — Fix mise à jour relations
- `bug_graph_mobile` — Bugs graph D3.js (drag, attraction, flèches, logs)

### Agents opencode disponibles (`.opencode/agents/`)

| Agent | Usage |
|-------|-------|
| `@consolidation-ir` | Consolidation IR |
| `@backend-tests` | Tests pytest backend |
| `@frontend-tests` | Tests Vitest frontend |
| `@refactor-controllers` | Refactoring double héritage |
