# BaseDetailsPage - Classe Abstraite pour les Pages de Détail

## Vue d'ensemble

`BaseDetailsPage` fournit une classe abstraite et un hook personnalisé (`useDetailPage`) pour simplifier la création de pages de détail (création/modification) dans l'application. Cette solution évite la duplication de code entre les pages de détails comme `RepositoryDetails` et `IssueDetails`.

## Composants

### 1. `useDetailPage<TFormData>` - Hook

Hook personnalisé qui gère la logique commune des pages de détail :
- État du formulaire
- États de chargement
- Gestion des erreurs
- Détection du mode (création vs édition)
- Chargement de l'entité en mode édition
- Soumission du formulaire (création ou mise à jour)
- Navigation

### 2. `BaseDetailPageLayout` - Classe Abstraite

Classe abstraite qui fournit la structure UI commune :
- En-tête de la page avec bouton retour
- Affichage des erreurs
- État de chargement
- Carte de formulaire avec boutons d'action
- Méthode abstraite `renderFormFields()` pour le contenu spécifique

## Utilisation

### Exemple avec un Hook (Recommandé pour les nouveaux composants)

```typescript
import { useDetailPage, DetailPageConfig } from "@/pages/common/BaseDetailsPage";

interface MyFormData {
  name: string;
  description: string;
}

export function MyDetailsPage() {
  const config: DetailPageConfig = {
    idParamName: "id",
    listPath: "/my-entities",
    createTitle: "Créer une entité",
    editTitle: "Modifier l'entité",
    createDescription: "Remplissez les informations",
    editDescription: "Modifiez les informations",
    backButtonLabel: "Retour à la liste",
    createButtonLabel: "Créer",
    editButtonLabel: "Mettre à jour",
    cancelButtonLabel: "Annuler",
  };

  const { state, handlers, isEditMode } = useDetailPage<MyFormData>(
    config,
    { name: "", description: "" }, // initialFormData
    {
      onLoadEntity: async (id) => {
        // Charger l'entité depuis l'API
        const entity = await myService.getById(id);
        return { name: entity.name, description: entity.description };
      },
      onCreateEntity: async (data) => {
        await myService.create(data);
      },
      onUpdateEntity: async (id, data) => {
        await myService.update(id, data);
      },
      validateForm: (data) => {
        if (!data.name.trim()) return "Le nom est requis";
        return null;
      },
    }
  );

  if (state.loadingEntity) {
    return <div>Chargement...</div>;
  }

  return (
    <div className="container mx-auto max-w-2xl px-3 sm:px-4 py-4 sm:py-6">
      {/* En-tête */}
      <div className="mb-4 sm:mb-6">
        <Button variant="ghost" size="sm" onClick={handlers.handleCancel}>
          <ArrowLeft className="h-4 w-4 mr-2" />
          {config.backButtonLabel}
        </Button>
        <h1 className="text-2xl sm:text-3xl font-bold">
          {isEditMode ? config.editTitle : config.createTitle}
        </h1>
      </div>

      {/* Erreur */}
      {state.error && (
        <Alert variant="destructive">
          <AlertDescription>{state.error}</AlertDescription>
        </Alert>
      )}

      {/* Formulaire */}
      <Card>
        <CardContent>
          <form onSubmit={handlers.handleSubmit}>
            <Input
              value={state.formData.name}
              onChange={(e) => handlers.updateFormData({ name: e.target.value })}
            />
            {/* Autres champs... */}
            
            <div className="flex gap-3">
              <Button type="button" onClick={handlers.handleCancel}>
                {config.cancelButtonLabel}
              </Button>
              <Button type="submit" disabled={state.loading}>
                {state.loading ? "..." : isEditMode ? config.editButtonLabel : config.createButtonLabel}
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
```

### Exemple avec la Classe Abstraite (Pour une structure plus rigide)

```typescript
import { BaseDetailPageLayout, useDetailPage, DetailPageConfig } from "@/pages/common/BaseDetailsPage";

interface MyFormData {
  name: string;
  description: string;
}

class MyDetailPageLayout extends BaseDetailPageLayout {
  protected renderFormFields(): React.ReactNode {
    const { formData, updateFormData } = this.props as any; // Type selon vos besoins
    
    return (
      <>
        <div className="space-y-2">
          <Label htmlFor="name">Nom *</Label>
          <Input
            id="name"
            value={formData.name}
            onChange={(e) => updateFormData({ name: e.target.value })}
          />
        </div>
        
        <div className="space-y-2">
          <Label htmlFor="description">Description</Label>
          <Textarea
            id="description"
            value={formData.description}
            onChange={(e) => updateFormData({ description: e.target.value })}
          />
        </div>
      </>
    );
  }
}

export function MyDetailsPage() {
  const config: DetailPageConfig = {
    // ... configuration
  };

  const { state, handlers, isEditMode } = useDetailPage<MyFormData>(
    config,
    { name: "", description: "" },
    {
      // ... options
    }
  );

  return (
    <MyDetailPageLayout
      config={config}
      isEditMode={isEditMode}
      loading={state.loading}
      loadingEntity={state.loadingEntity}
      error={state.error}
      onCancel={handlers.handleCancel}
      onSubmit={handlers.handleSubmit}
      // Passer les props nécessaires pour renderFormFields
      {...state}
      {...handlers}
    />
  );
}
```

## Avantages

1. **Réduction de la duplication** : La logique commune est centralisée
2. **Cohérence** : Toutes les pages de détail ont la même structure et comportement
3. **Maintenabilité** : Les changements à la logique commune se font en un seul endroit
4. **Flexibilité** : Les pages peuvent personnaliser le comportement via les callbacks
5. **Type-safe** : Support complet de TypeScript avec génériques

## Configuration

Le `DetailPageConfig` permet de personnaliser :
- Les titres et descriptions pour les modes création/édition
- Les labels des boutons
- Le nom du paramètre d'URL pour l'ID
- Le chemin de navigation après succès

## Migration des Pages Existantes

Pour migrer une page de détail existante :

1. Identifier les données du formulaire et créer un type `TFormData`
2. Utiliser le hook `useDetailPage` avec la configuration appropriée
3. Remplacer la logique de chargement/soumission par les callbacks du hook
4. Utiliser `state` et `handlers` fournis par le hook
5. Optionnellement, utiliser `BaseDetailPageLayout` pour la structure UI

## Notes

- Le hook gère automatiquement le chargement de l'entité en mode édition
- La validation du formulaire est optionnelle et personnalisable
- Le chemin de navigation peut être dynamique via `getListPath`
- Les erreurs sont capturées et affichées automatiquement
