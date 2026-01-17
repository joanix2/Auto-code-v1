/**
 * RelationForm - Formulaire pour éditer les relations (Object Properties)
 */
import React from "react";
import { Form } from "@/components/common/Form/Form";
import { TextField } from "@/components/common/Form/Fields/TextField";

export interface RelationData {
  name: string;
  description: string;
  sourceType?: string;
  targetType?: string;
}

/**
 * Formulaire de relation avec nom, description, source et cible
 */
export class RelationForm extends Form<RelationData> {
  /**
   * Valide les données du formulaire
   */
  protected validate(): Record<string, string> {
    const errors: Record<string, string> = {};
    const { name } = this.state.data;

    if (!name || name.trim() === "") {
      errors.name = "Le nom est requis";
    } else if (name.length < 2) {
      errors.name = "Le nom doit contenir au moins 2 caractères";
    }

    return errors;
  }

  /**
   * Rendu des champs du formulaire
   */
  protected renderFields(): React.ReactNode {
    const { data, errors } = this.state;
    const { edit } = this.props;

    return (
      <>
        <TextField
          name="name"
          label="Nom de la relation"
          value={data.name}
          onChange={this.handleFieldChange}
          edit={edit}
          required
          error={errors.name}
          placeholder="Ex: possède, appartientÀ, contient..."
        />

        <TextField
          name="description"
          label="Description"
          value={data.description}
          onChange={this.handleFieldChange}
          edit={edit}
          error={errors.description}
          placeholder="Description de la relation..."
        />

        <TextField name="sourceType" label="Type source" value={data.sourceType || ""} onChange={this.handleFieldChange} edit={edit} placeholder="Ex: Utilisateur, Commande..." />

        <TextField name="targetType" label="Type cible" value={data.targetType || ""} onChange={this.handleFieldChange} edit={edit} placeholder="Ex: Produit, Adresse..." />
      </>
    );
  }
}

export default RelationForm;
