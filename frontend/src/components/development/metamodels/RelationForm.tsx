/**
 * RelationForm - Formulaire pour éditer les relations (nœuds de type relation)
 * Note: Les connexions aux concepts se font via les liens du graphe (domain/range)
 */
import React from "react";
import { NodeForm, NodeData, NodeFormProps } from "@/components/common/Form/NodeForm";
import { SelectField } from "@/components/common/Form/Fields";

export interface RelationData extends NodeData {
  name: string;
  description?: string;
  relationType: "is_a" | "has_part" | "has_subclass" | "part_of" | "other" | null; // Type de relation (null en création)
}

/**
 * Formulaire de relation
 * Hérite de NodeForm qui gère automatiquement la section "Informations"
 * Ce formulaire contient uniquement le type de relation
 * Les connexions aux concepts (domain/range) se font via les liens du graphe
 */
export class RelationForm extends NodeForm<RelationData> {
  /**
   * Validation des champs spécifiques aux relations
   */
  protected validateSpecificFields(data: RelationData): Record<string, string> {
    const errors: Record<string, string> = {};

    if (!data.relationType) {
      errors.relationType = "Le type de relation est requis";
    }

    return errors;
  }

  /**
   * Rendu des champs spécifiques aux relations
   */
  protected renderSpecificFields(): React.ReactNode {
    const { data, errors } = this.state;
    const { edit } = this.props;
    const isCreation = this.isCreation();

    const relationTypeOptions = [
      { value: "is_a", label: "Is A (Héritage)" },
      { value: "has_part", label: "Has Part (Composition)" },
      { value: "has_subclass", label: "Has Subclass" },
      { value: "part_of", label: "Part Of" },
      { value: "other", label: "Autre" },
    ];

    return (
      <>
        <SelectField
          name="relationType"
          label="Type de relation"
          value={data.relationType}
          options={relationTypeOptions}
          onChange={this.handleFieldChange}
          edit={edit}
          error={errors.relationType}
          required
          allowNull={isCreation}
          nullLabel="Sélectionner un type"
          placeholder={isCreation ? "Choisissez le type de relation" : undefined}
        />
      </>
    );
  }
}

export default RelationForm;
