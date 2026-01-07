# Migration des Pages Existantes vers BaseDetailsPage

Ce document explique comment les pages existantes `RepositoryDetails` et `IssueDetails` peuvent être refactorisées pour utiliser la nouvelle classe abstraite `BaseDetailsPage`.

## État Actuel

Les deux pages partagent une structure similaire :
- Gestion du mode création/édition basé sur un paramètre d'URL
- État du formulaire avec champs spécifiques
- États de chargement et d'erreur
- Chargement de l'entité en mode édition
- Soumission du formulaire (création ou mise à jour)
- Navigation vers la liste après succès

## Migration de RepositoryDetails

### Avant (code actuel simplifié)

```typescript
export function RepositoryDetails() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const { id } = useParams<{ id: string }>();
  const isEditMode = !!id;

  const [formData, setFormData] = useState({
    name: "",
    description: "",
    private: false,
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  // Load repository data in edit mode
  useEffect(() => {
    if (isEditMode && id) {
      const loadRepository = async () => {
        try {
          setLoading(true);
          const repo = await repositoryService.getById(id);
          setFormData({
            name: repo.name,
            description: repo.description || "",
            private: repo.is_private,
          });
        } catch (err) {
          setError(err?.message || "Erreur lors du chargement");
        } finally {
          setLoading(false);
        }
      };
      loadRepository();
    }
  }, [isEditMode, id]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    // Validation et soumission...
  };

  // Rendu du formulaire...
}
```

### Après (avec BaseDetailsPage)

```typescript
import { useDetailPage, DetailPageConfig } from "@/pages/common/BaseDetailsPage";
import { useCallback } from "react";

interface RepositoryFormData {
  name: string;
  description: string;
  private: boolean;
}

export function RepositoryDetails() {
  const { user } = useAuth();

  const config: DetailPageConfig = {
    idParamName: "id",
    listPath: "/repositories",
    createTitle: "Créer un nouveau repository",
    editTitle: "Éditer le repository",
    createDescription: "Assurez-vous d'avoir configuré votre token GitHub",
    editDescription: "Modifiez le nom et/ou la description de votre repository",
    backButtonLabel: "Retour aux repositories",
    createButtonLabel: "Créer le repository",
    editButtonLabel: "Mettre à jour",
    cancelButtonLabel: "Annuler",
  };

  const onLoadEntity = useCallback(async (id: string) => {
    const repo = await repositoryService.getById(id);
    return {
      name: repo.name,
      description: repo.description || "",
      private: repo.is_private,
    };
  }, []);

  const onCreateEntity = useCallback(async (data: RepositoryFormData) => {
    await repositoryService.create({
      name: data.name.trim(),
      description: data.description.trim() || undefined,
      private: data.private,
    });
  }, []);

  const onUpdateEntity = useCallback(async (id: string, data: RepositoryFormData) => {
    await repositoryService.update(id, {
      name: data.name.trim(),
      description: data.description.trim() || undefined,
    });
  }, []);

  const validateForm = useCallback((data: RepositoryFormData) => {
    if (!data.name.trim()) {
      return "Le nom du repository est requis";
    }
    if (!user?.github_token) {
      return "Veuillez configurer votre token GitHub dans les paramètres de votre profil";
    }
    return null;
  }, [user?.github_token]);

  const { state, handlers, isEditMode } = useDetailPage<RepositoryFormData>(
    config,
    { name: "", description: "", private: false },
    { onLoadEntity, onCreateEntity, onUpdateEntity, validateForm }
  );

  // Rendu utilisant state.formData, handlers.updateFormData, etc.
}
```

## Migration de IssueDetails

### Avant (code actuel simplifié)

```typescript
export function IssueDetails() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const { issueId } = useParams<{ issueId?: string }>();
  const repositoryIdParam = searchParams.get("repository");
  const isEditMode = !!issueId;

  const [formData, setFormData] = useState<IssueDetailsData>({
    title: "",
    description: "",
    priority: "medium",
    type: "feature",
    status: "open",
    repository_id: repositoryIdParam || "",
  });

  const [loading, setLoading] = useState(false);
  const [loadingIssue, setLoadingIssue] = useState(isEditMode);
  const [error, setError] = useState("");

  // Load issue data for edit mode
  useEffect(() => {
    // ... chargement de l'issue
  }, [issueId, isEditMode, getIssue]);

  const handleSubmit = async (e: React.FormEvent) => {
    // ... validation et soumission
  };

  // Rendu du formulaire...
}
```

### Après (avec BaseDetailsPage)

```typescript
import { useDetailPage, DetailPageConfig } from "@/pages/common/BaseDetailsPage";
import { useCallback } from "react";
import { useSearchParams } from "react-router-dom";

interface IssueFormData {
  title: string;
  description: string;
  priority: IssuePriority;
  type: IssueType;
  status: IssueStatus;
  repository_id: string;
}

export function IssueDetails() {
  const [searchParams] = useSearchParams();
  const repositoryIdParam = searchParams.get("repository");
  const { getIssue, createIssue, updateIssue } = useIssues(repositoryIdParam || "");

  const config: DetailPageConfig = {
    idParamName: "issueId",
    listPath: "/repositories",
    createTitle: "Create New Issue",
    editTitle: "Edit Issue",
    createDescription: "Fill in the details to create a new issue",
    editDescription: "Update the issue information",
    backButtonLabel: "Back",
    createButtonLabel: "Create Issue",
    editButtonLabel: "Update Issue",
    cancelButtonLabel: "Cancel",
  };

  const onLoadEntity = useCallback(async (id: string) => {
    const issue = await getIssue(id);
    return {
      title: issue.title,
      description: issue.description || "",
      priority: issue.priority,
      type: issue.issue_type,
      status: issue.status,
      repository_id: issue.repository_id,
    };
  }, [getIssue]);

  const onCreateEntity = useCallback(async (data: IssueFormData) => {
    await createIssue({
      title: data.title.trim(),
      description: data.description.trim() || undefined,
      priority: data.priority,
      issue_type: data.type,
      repository_id: data.repository_id,
    });
  }, [createIssue]);

  const onUpdateEntity = useCallback(async (id: string, data: IssueFormData) => {
    await updateIssue(id, {
      title: data.title.trim(),
      description: data.description.trim() || undefined,
      priority: data.priority,
      status: data.status,
    });
  }, [updateIssue]);

  const validateForm = useCallback((data: IssueFormData) => {
    if (!data.title.trim()) return "Title is required";
    if (!data.repository_id && !isEditMode) return "Please select a repository";
    return null;
  }, []);

  const getListPath = useCallback((data: IssueFormData) => {
    return data.repository_id 
      ? `/repositories/${data.repository_id}/issues`
      : "/repositories";
  }, []);

  const { state, handlers, isEditMode } = useDetailPage<IssueFormData>(
    config,
    {
      title: "",
      description: "",
      priority: "medium",
      type: "feature",
      status: "open",
      repository_id: repositoryIdParam || "",
    },
    { onLoadEntity, onCreateEntity, onUpdateEntity, validateForm, getListPath }
  );

  // Rendu utilisant state.formData, handlers.updateFormData, etc.
}
```

## Avantages de la Migration

1. **Moins de code boilerplate** : ~50-100 lignes de code en moins par page
2. **Logique standardisée** : Tous les détails (chargement, validation, soumission) fonctionnent de la même manière
3. **Maintenance simplifiée** : Les bugs et améliorations dans la logique commune bénéficient à toutes les pages
4. **Meilleure testabilité** : La logique commune peut être testée une seule fois
5. **Type safety améliorée** : TypeScript garantit que tous les callbacks sont correctement typés

## Notes de Migration

- La migration est **optionnelle** - les pages existantes continuent de fonctionner
- La migration peut se faire **progressivement**, une page à la fois
- Les tests existants devront être légèrement adaptés mais la fonctionnalité reste identique
- L'UI peut rester exactement la même, seule la logique change

## Recommandations

1. Migrer une page à la fois pour minimiser les risques
2. Tester manuellement après chaque migration
3. Utiliser `useCallback` pour tous les callbacks afin d'éviter les re-renders inutiles
4. Conserver les features spécifiques (comme l'info card de RepositoryDetails) avec `additionalContent`
