# Version GPT

- **Reasoning / planning** (plan d’action, étapes, décisions, alternatives)
- **ReadFile** (par chemin + options `start_line/end_line` ou `offset/length` + `max_size` + encodage)
- **WriteFile / UpdateFile** (écriture + patch/diff, création dossiers, sauvegarde atomique, rollback)
- **ListDir / Workspace index** (lister fichiers, filtrer par extension, exclure vendored/artefacts, stats)
- **SearchInRepo (regex)** (multi-fichiers, options: casse, glob, limites, aperçu des matchs)
- **GoToDefinition / Symbol index** (indexation AST/LS, navigation symboles, refs, rename)
- **Diagnostics / Lint / Typecheck** (exécuter linters, parse erreurs, liens vers lignes)
- **RunCommand / Terminal** (exécuter scripts/tests/build, capturer stdout/stderr, timeouts)
- **Unit tests & coverage** (run ciblé, résumé échecs, suggestions de corrections)
- **Summarize** (fichiers/dossiers/PR/diffs + “ce qui change” + risques)
- **Diff / Patch viewer** (générer diff, appliquer, vérifier)
- **Dependency / package tools** (install, audit vulnérabilités, lockfile, versions)
- **WebDocSearch** (recherche web, filtrage sources, citations, “best answer”)
- **FetchURL / ReadWebPage** (récupérer contenu, extraire sections pertinentes)
- **RAG / Knowledge base** (ingestion docs, chunking, embeddings, retrieval, re-ranking)
- **Context builder** (sélection automatique des fichiers pertinents selon la tâche)
- **Secrets & safety scanner** (détecter clés, PII, policy checks avant écriture)
- **Auth + Permissions** (scopes: read-only, write, run; sandbox; allowlist)
- **Telemetry / logs** (traces, replay, coûts tokens, latence, erreurs)
- **Prompt templates / policies** (règles de style, conventions repo, “definition of done”)
- **PR / Git tools** (status, branch, commit, open PR, review commentaires)
- **Task memory (court terme)** (notes de travail, TODOs, décisions prises)
- **Multi-agent orchestration** (planner ↔ coder ↔ reviewer ↔ tester, avec garde-fous)

# Ma version

- **Reasoning / planning** (plan d’action, étapes, décisions, alternatives)
- **Task memory (court terme)** (notes de travail, TODOs, décisions prises)
- **ListDir / Workspace index** (lister fichiers, filtrer par extension, exclure vendored/artefacts, stats)
- **Context builder** (sélection automatique des fichiers pertinents selon la tâche)

- **ReadFile** (par chemin + options `start_line/end_line` ou `offset/length` + `max_size` + encodage)
- **WriteFile / UpdateFile** (écriture + patch/diff, création dossiers, sauvegarde atomique, rollback)
- **Dependency / package tools** (install, audit vulnérabilités, lockfile, versions)

- **GoToDefinition / Symbol index** (indexation AST/LS, navigation symboles, refs, rename)
- **Diagnostics / Lint / Typecheck** (exécuter linters, parse erreurs, liens vers lignes)
- **Diff / Patch viewer** (générer diff, appliquer, vérifier)

- **SearchInRepo (regex)** (multi-fichiers, options: casse, glob, limites, aperçu des matchs)
- **WebDocSearch** (recherche web, filtrage sources, citations, “best answer”)
- **FetchURL / ReadWebPage** (récupérer contenu, extraire sections pertinentes)
- **Summarize** (fichiers/dossiers/PR/diffs + “ce qui change” + risques)

- **Prompt templates / policies** (règles de style, conventions repo, “definition of done”)

- **Telemetry / logs** (traces, replay, coûts tokens, latence, erreurs)
- **RAG / Knowledge base** (ingestion docs, chunking, embeddings, retrieval, re-ranking)
- **Multi-agent orchestration** (planner ↔ coder ↔ reviewer ↔ tester, avec garde-fous)
