/**
 * RelationForm - Formulaire pour éditer les relations (Object Properties)
 */
import React from "react";
import { NodeForm, NodeData } from "@/components/common/Form/NodeForm";
import { TextField } from "@/components/common/Form/Fields/TextField";

export interface RelationData extends NodeData {
  name: string;
  description?: string;
  sourceType?: string; // Propriété spécifique aux relations
  targetType?: string; // Propriété spécifique aux relations
}

/**
 * Formulaire de relation
 * Hérite de NodeForm qui gère automatiquement la section "Informations"
 * Ce formulaire contient uniquement les propriétés spécifiques : sourceType et targetType
 */
export class RelationForm extends NodeForm<RelationData> {
  /**
   * Validation des champs spécifiques aux relations
   */
  protected validateSpecificFields(data: RelationData): Record<string, string> {
    const errors: Record<string, string> = {};

    // sourceType et targetType sont optionnels, pas de validation nécessaire

    return errors;
  }

  /**
   * Rendu des champs spécifiques aux relations
   */
  protected renderSpecificFields(): React.ReactNode {
    const { data, errors } = this.state;
    const { edit } = this.props;

    return (
      <>
        <TextField
          name="sourceType"
          label="Type source"
          value={data.sourceType || ""}
          onChange={this.handleFieldChange}
          edit={edit}
          error={errors.sourceType}
          placeholder="Ex: Utilisateur, Commande..."
        />

        <TextField name="targetType" label="Type cible" value={data.targetType || ""} onChange={this.handleFieldChange} edit={edit} error={errors.targetType} placeholder="Ex: Produit, Adresse..." />
      </>
    );
  }
}

export default RelationForm;
