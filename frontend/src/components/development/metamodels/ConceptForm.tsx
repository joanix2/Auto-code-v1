/**
 * ConceptForm - Formulaire pour éditer les concepts
 */
import React from "react";
import { Form } from "@/components/common/Form/Form";
import { TextField } from "@/components/common/Form/Fields/TextField";

export interface ConceptData {
  name: string;
  description: string;
}

/**
 * Formulaire de concept avec nom et description
 */
export class ConceptForm extends Form<ConceptData> {
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
        <TextField name="name" label="Nom du concept" value={data.name} onChange={this.handleFieldChange} edit={edit} required error={errors.name} placeholder="Ex: Utilisateur, Produit..." />

        <TextField name="description" label="Description" value={data.description} onChange={this.handleFieldChange} edit={edit} error={errors.description} placeholder="Description du concept..." />
      </>
    );
  }
}

export default ConceptForm;
