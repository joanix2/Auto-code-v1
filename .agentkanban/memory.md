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

- `fix_mypy_errors` ✅ 81→0 erreurs (implicit Optional, signatures, doublons, pyproject.toml)
- `fix_eslint_frontend` ✅ 2→0 erreurs (textarea.tsx, command.tsx)
- `add_backend_tests` ✅ 110 tests (repositories, services, controllers, models)
- `add_frontend_tests` ✅ 22 tests (GraphViewer, hooks, services)
- `mvp_a_consolidation` ✅ IR schema, endpoints roundtrip, PATCH/DELETE edges
- `refactor_controller` ✅ GitHubSyncMixin extrait, double héritage appliqué

### P0 Restants (segmentés)

- `bug_error_helper` — Helper erreurs controllers
- `bug_relation_update` — Fix mise à jour relations
- `bug_graph_mobile` — Bugs graph D3.js (drag, attraction, flèches, logs)
- Bug ticket status (en attente → open)
- `bug_metamodel_create` — Metamodel creation fails: id Field required (extra fields MetamodelCreate → Metamodel)

### Bugs connus

- **Création Metamodel** : `MetamodelCreate` a des champs (`settings`, `metadata`, `type`, `tags`, `is_public`, `repository_path`) qui n'existent pas sur `Metamodel`. Stockés dans Neo4j mais causent des erreurs Pydantic au retour. Voir `.agentkanban/tasks/task_20260603_bug_metamodel_create.md`

### Commits récents

```
3a68993 test: ajouter tests repositories, services, controllers
c14bd4e refactor: extraire GitHubSyncMixin et double héritage controllers
eff7874 feat: consolidation IR - endpoints, schema, roundtrip
1aded55 test: ajouter Vitest et tests frontend
```

### Agents opencode disponibles (`.opencode/agents/`)

| Agent | Usage |
|-------|-------|
| `@consolidation-ir` | Consolidation IR |
| `@backend-tests` | Tests pytest backend |
| `@frontend-tests` | Tests Vitest frontend |
| `@refactor-controllers` | Refactoring double héritage |
