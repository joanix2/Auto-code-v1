/**
 * Example implementation showing how to use BaseDetailPageLayout
 * This demonstrates how RepositoryDetails and IssueDetails pages can be refactored
 */

import React from "react";
import { BaseDetailPageLayout, useDetailPage, DetailPageConfig } from "./BaseDetailsPage";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";

/**
 * Example form data interface
 */
interface ExampleFormData {
  name: string;
  description: string;
}

/**
 * Example concrete implementation of BaseDetailPageLayout
 */
class ExampleDetailPageLayout extends BaseDetailPageLayout {
  protected renderFormFields(): React.ReactNode {
    // Access formData and handlers through props
    const formData = (this.props as any).formData as ExampleFormData;
    const updateFormData = (this.props as any).updateFormData as (updates: Partial<ExampleFormData>) => void;

    return (
      <>
        {/* Name field */}
        <div className="space-y-2">
          <Label htmlFor="name">Nom *</Label>
          <Input
            id="name"
            name="name"
            type="text"
            placeholder="Entrez un nom"
            value={formData.name}
            onChange={(e) => updateFormData({ name: e.target.value })}
            required
          />
          <p className="text-xs text-gray-500">Choisissez un nom descriptif</p>
        </div>

        {/* Description field */}
        <div className="space-y-2">
          <Label htmlFor="description">Description</Label>
          <Textarea
            id="description"
            name="description"
            placeholder="Entrez une description..."
            value={formData.description}
            onChange={(e) => updateFormData({ description: e.target.value })}
            rows={4}
          />
          <p className="text-xs text-gray-500">Décrivez brièvement (optionnel)</p>
        </div>
      </>
    );
  }
}

/**
 * Example functional component using the base class
 */
export function ExampleDetailsPage() {
  // Configuration for the detail page
  const config: DetailPageConfig = {
    idParamName: "id",
    listPath: "/examples",
    createTitle: "Créer un nouvel exemple",
    editTitle: "Modifier l'exemple",
    createDescription: "Remplissez les informations pour créer un nouvel exemple",
    editDescription: "Modifiez les informations de l'exemple",
    backButtonLabel: "Retour aux exemples",
    createButtonLabel: "Créer l'exemple",
    editButtonLabel: "Mettre à jour l'exemple",
    cancelButtonLabel: "Annuler",
    createCardTitle: "Nouvel exemple",
    editCardTitle: "Informations de l'exemple",
    createCardDescription: "Fournissez les informations nécessaires",
    editCardDescription: "Modifiez les champs que vous souhaitez mettre à jour",
  };

  // Initial form data
  const initialFormData: ExampleFormData = {
    name: "",
    description: "",
  };

  // Use the detail page hook
  const { state, handlers, isEditMode, entityId } = useDetailPage<ExampleFormData>(config, initialFormData, {
    // Load entity in edit mode
    onLoadEntity: async (id: string) => {
      // Example: load from API
      // const entity = await exampleService.getById(id);
      // return { name: entity.name, description: entity.description };
      
      // Mock data for demonstration
      return {
        name: "Example " + id,
        description: "This is a sample description",
      };
    },

    // Create new entity
    onCreateEntity: async (data: ExampleFormData) => {
      // Example: create via API
      // await exampleService.create(data);
      
      console.log("Creating entity:", data);
    },

    // Update existing entity
    onUpdateEntity: async (id: string, data: ExampleFormData) => {
      // Example: update via API
      // await exampleService.update(id, data);
      
      console.log("Updating entity:", id, data);
    },

    // Validate form before submission
    validateForm: (data: ExampleFormData) => {
      if (!data.name.trim()) {
        return "Le nom est requis";
      }
      if (data.name.length < 3) {
        return "Le nom doit contenir au moins 3 caractères";
      }
      return null;
    },
  });

  // Render using the abstract base class
  return (
    <ExampleDetailPageLayout
      config={config}
      isEditMode={isEditMode}
      loading={state.loading}
      loadingEntity={state.loadingEntity}
      error={state.error}
      onCancel={handlers.handleCancel}
      onSubmit={handlers.handleSubmit}
      // Pass additional props needed by renderFormFields
      formData={state.formData}
      updateFormData={handlers.updateFormData}
    />
  );
}

export default ExampleDetailsPage;
