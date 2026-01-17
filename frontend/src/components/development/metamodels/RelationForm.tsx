/**
 * RelationForm - Formulaire pour éditer les relations entre concepts
 */
import React from "react";
import { NodeForm, NodeData, NodeFormProps } from "@/components/common/Form/NodeForm";
import { SelectField } from "@/components/common/Form/Fields";

export interface RelationData extends NodeData {
  name: string;
  description?: string;
  sourceConceptId: string; // ID du concept source
  targetConceptId: string; // ID du concept cible
  relationType: "is_a" | "has_part" | "has_subclass" | "part_of" | "other";
}

// Étendre NodeFormProps pour ajouter la propriété concepts
export interface RelationFormProps extends NodeFormProps<RelationData> {
  concepts: Array<{ id: string; label: string }>; // Concepts disponibles
}

/**
 * Formulaire de relation
 * Hérite de NodeForm qui gère automatiquement la section "Informations"
 * Ce formulaire contient les champs spécifiques : type de relation, concept source, concept cible
 */
export class RelationForm extends NodeForm<RelationData> {
  // Typer explicitement les props pour qu'elles soient reconnues
  declare props: RelationFormProps;
  private concepts: Array<{ id: string; label: string }>;

  constructor(props: RelationFormProps) {
    super(props);
    this.concepts = props.concepts || [];
  }

  /**
   * Validation des champs spécifiques aux relations
   */
  protected validateSpecificFields(data: RelationData): Record<string, string> {
    const errors: Record<string, string> = {};

    if (!data.sourceConceptId) {
      errors.sourceConceptId = "Le concept source est requis";
    }
    if (!data.targetConceptId) {
      errors.targetConceptId = "Le concept cible est requis";
    }
    if (data.sourceConceptId === data.targetConceptId) {
      errors.targetConceptId = "Le concept source et le concept cible doivent être différents";
    }
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

    const relationTypeOptions = [
      { value: "is_a", label: "Is A (Héritage)" },
      { value: "has_part", label: "Has Part (Composition)" },
      { value: "has_subclass", label: "Has Subclass" },
      { value: "part_of", label: "Part Of" },
      { value: "other", label: "Autre" },
    ];

    const conceptOptions = this.concepts.map((c) => ({
      value: c.id,
      label: c.label,
    }));

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
        />

        <SelectField
          name="sourceConceptId"
          label="Concept source"
          value={data.sourceConceptId}
          options={conceptOptions}
          onChange={this.handleFieldChange}
          edit={edit}
          error={errors.sourceConceptId}
          required
        />

        <SelectField
          name="targetConceptId"
          label="Concept cible"
          value={data.targetConceptId}
          options={conceptOptions}
          onChange={this.handleFieldChange}
          edit={edit}
          error={errors.targetConceptId}
          required
        />
      </>
    );
  }
}

export default RelationForm;
