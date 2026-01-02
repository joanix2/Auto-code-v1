# File Modification Service - LangChain Integration

## 🎯 Objectif

Service pour appliquer automatiquement les modifications de fichiers générées par le LLM en utilisant les outils **LangChain**.

## Architecture

```
ClaudeAgent (LLM)
      │
      ▼
Génère JSON:
{
  "files": [
    {
      "path": "src/new_file.py",
      "action": "create",
      "content": "class NewClass:\n    pass",
      "explanation": "..."
    }
  ]
}
      │
      ▼
FileModificationService
      │
      ├─► Parse JSON
      ├─► Sanitize paths (sécurité)
      ├─► LangChain WriteFileTool → Create file
      ├─► LangChain CopyFileTool → Backup
      └─► WebSocket logs → Frontend
```

## LangChain Tools Utilisés

### 1. FileManagementToolkit

```python
from langchain_community.agent_toolkits.file_management.toolkit import FileManagementToolkit

toolkit = FileManagementToolkit(
    root_dir="/tmp/autocode-workspace/owner/repo",
    selected_tools=["read_file", "write_file", "list_directory", "copy_file"]
)
```

### 2. WriteFileTool

```python
from langchain_community.tools.file_management import WriteFileTool

write_tool = WriteFileTool(root_dir="/path/to/repo")
write_tool.run({
    "file_path": "src/new_file.py",
    "text": "file content here",
    "append": False
})
```

### 3. ReadFileTool

```python
from langchain_community.tools.file_management import ReadFileTool

read_tool = ReadFileTool(root_dir="/path/to/repo")
content = read_tool.run({"file_path": "src/existing_file.py"})
```

### 4. CopyFileTool (pour backups)

```python
from langchain_community.tools.file_management import CopyFileTool

copy_tool = CopyFileTool(root_dir="/path/to/repo")
copy_tool.run({
    "source_path": "file.py",
    "destination_path": "file.py.backup"
})
```

## Usage

### Dans le Workflow

```python
# ticket_workflow.py → _call_llm()

# 1. LLM génère le code
agent = ClaudeAgent()
result = agent.run(...)

# 2. Applique les modifications avec LangChain
file_service = FileModificationService(state.repo_path)
mod_results = file_service.apply_modifications(result["final_output"])

# 3. Log résultats via WebSocket
if mod_results["success"]:
    logger.info(f"✅ {mod_results['succeeded']} fichier(s) modifié(s)")
```

### Format JSON Attendu

```json
{
  "files": [
    {
      "path": "backend/src/services/new_service.py",
      "action": "create",
      "content": "class NewService:\n    def method(self):\n        pass",
      "explanation": "Service pour gérer X"
    },
    {
      "path": "backend/src/models/user.py",
      "action": "modify",
      "content": "class User:\n    name: str\n    age: int  # NEW",
      "explanation": "Ajout du champ age"
    },
    {
      "path": "old_file.py",
      "action": "delete",
      "explanation": "Fichier obsolète"
    }
  ],
  "summary": "Ajout de NewService et modification du modèle User"
}
```

## Sécurité

### Path Sanitization

```python
def _sanitize_path(self, path: str) -> str:
    """Prevent directory traversal attacks"""
    # Remove leading slashes
    path = path.lstrip("/")

    # Resolve to absolute path
    abs_path = (self.working_directory / path).resolve()

    # Check it's within working directory
    if not str(abs_path).startswith(str(self.working_directory.resolve())):
        raise ValueError(f"Path {path} is outside working directory")

    return str(abs_path.relative_to(self.working_directory))
```

**Bloque** :

- `../../../etc/passwd` ❌
- `/etc/passwd` ❌
- `../../outside.py` ❌

**Autorise** :

- `src/file.py` ✅
- `backend/models/user.py` ✅

## Backups Automatiques

Lors de la modification d'un fichier existant :

```python
# Avant modification
original: src/file.py

# Backup créé
backup: src/file.py.backup

# Nouvelle version
modified: src/file.py
```

## WebSocket Integration

```python
# Chaque fichier modifié envoie un log
asyncio.create_task(manager.send_log(
    ticket_id,
    "INFO",
    "➕ CREATE: backend/src/services/new_service.py"
))

asyncio.create_task(manager.send_log(
    ticket_id,
    "INFO",
    "   → Service pour gérer X"
))
```

## Résultat

```python
{
  "success": True,
  "files_modified": [
    {
      "success": True,
      "path": "src/new_file.py",
      "action": "create",
      "explanation": "...",
      "result": "File written successfully to src/new_file.py"
    }
  ],
  "total": 3,
  "succeeded": 3,
  "failed": 0,
  "summary": "Overall changes summary"
}
```

## Exemple Complet

```python
# 1. Initialiser le service
service = FileModificationService("/tmp/autocode-workspace/owner/repo")

# 2. LLM response (JSON string)
llm_response = """
{
  "files": [
    {
      "path": "src/utils/helper.py",
      "action": "create",
      "content": "def helper():\\n    return 'Hello'",
      "explanation": "Utility helper function"
    }
  ],
  "summary": "Added helper utility"
}
"""

# 3. Appliquer modifications
results = service.apply_modifications(llm_response)

# 4. Vérifier résultats
print(f"Success: {results['success']}")
print(f"Files modified: {results['succeeded']}")

# 5. Summary lisible
summary = service.get_modified_files_summary(results)
print(summary)
# Output:
# ✅ Successfully modified 1 file(s)
#
# ➕ CREATE: src/utils/helper.py
#    → Utility helper function
```

## Gestion d'Erreurs

### JSON Invalide

```python
# LLM retourne du texte au lieu de JSON
llm_response = "I created a new file..."

results = service.apply_modifications(llm_response)
# {
#   "success": False,
#   "error": "No valid modifications found in LLM response",
#   "files_modified": []
# }
```

### Fichier en Dehors du Repo

```python
# Path malveillant
{
  "path": "../../../etc/passwd",
  "action": "modify",
  "content": "..."
}

# Résultat:
# {
#   "success": False,
#   "error": "Path ../../../etc/passwd is outside working directory"
# }
```

### Permission Denied

```python
# Fichier en lecture seule
{
  "path": "readonly_file.txt",
  "action": "modify",
  "content": "..."
}

# Résultat:
# {
#   "success": False,
#   "error": "Permission denied"
# }
```

## Dependencies

```txt
langchain-core==0.3.26
langchain-community==0.3.5  # File management tools
```

## Tests

```python
import pytest
from services.file_modification_service import FileModificationService

def test_create_file(tmp_path):
    service = FileModificationService(str(tmp_path))

    llm_response = {
        "files": [{
            "path": "test.py",
            "action": "create",
            "content": "print('hello')"
        }]
    }

    results = service.apply_modifications(json.dumps(llm_response))

    assert results["success"]
    assert (tmp_path / "test.py").exists()
    assert (tmp_path / "test.py").read_text() == "print('hello')"
```

## Workflow Complet

```
1. User clicks "Développer automatiquement"
2. Ticket → PENDING
3. Workflow starts (LangGraph)
4. prepare_repository → Clone/pull repo
5. load_conversation → Get messages
6. call_llm → Claude generates code (JSON)
   ├─► analyze_ticket()
   ├─► generate_code() → JSON with files
   └─► FileModificationService.apply_modifications() ✅ NEW
       ├─► Parse JSON
       ├─► Sanitize paths
       ├─► Create backups
       ├─► Write files (LangChain tools)
       └─► Send WebSocket logs
7. commit_changes → Git commit
8. run_ci → Tests
9. await_validation → Human review
```

## Avantages de LangChain

✅ **Tools standardisés** - Pas besoin de réinventer la roue  
✅ **Sécurité intégrée** - Path validation dans les tools  
✅ **Testés et maintenus** - Par la communauté LangChain  
✅ **Extensible** - Facile d'ajouter d'autres tools  
✅ **Compatible** - S'intègre avec le reste de l'écosystème LangChain

## Next Steps

- [ ] Ajouter support pour les patches (modifications partielles)
- [ ] Implémenter rollback en cas d'erreur
- [ ] Ajouter validation du code généré (linters)
- [ ] Support pour les fichiers binaires
- [ ] Gestion des conflits de merge
