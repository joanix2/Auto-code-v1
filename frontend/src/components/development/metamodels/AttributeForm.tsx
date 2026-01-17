/**
 * AttributeForm - Formulaire pour éditer les attributs (Data Properties)
 */
import React from "react";
import { Form } from "@/components/common/Form/Form";
import { TextField } from "@/components/common/Form/Fields/TextField";

export interface AttributeData {
  name: string;
  description: string;
  dataType?: string;
}

/**
 * Formulaire d'attribut avec nom, description et type de données
 */
export class AttributeForm extends Form<AttributeData> {
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
        <TextField name="name" label="Nom de l'attribut" value={data.name} onChange={this.handleFieldChange} edit={edit} required error={errors.name} placeholder="Ex: email, age, price..." />

        <TextField
          name="description"
          label="Description"
          value={data.description}
          onChange={this.handleFieldChange}
          edit={edit}
          error={errors.description}
          placeholder="Description de l'attribut..."
        />

        <TextField name="dataType" label="Type de données" value={data.dataType || ""} onChange={this.handleFieldChange} edit={edit} placeholder="Ex: string, number, boolean, date..." />
      </>
    );
  }
}

export default AttributeForm;
