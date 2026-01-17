/**
 * AttributeForm - Formulaire pour éditer les attributs (Data Properties)
 */
import React from "react";
import { NodeForm, NodeData } from "@/components/common/Form/NodeForm";
import { SelectField } from "@/components/common/Form/Fields/SelectField";
import { BooleanField } from "@/components/common/Form/Fields/BooleanField";

export interface AttributeData extends NodeData {
  name: string;
  description?: string;
  dataType?: string; // Propriété spécifique aux attributs
  isRequired?: boolean; // L'attribut est-il requis ?
  isUnique?: boolean; // La valeur doit-elle être unique ?
}

/**
 * Formulaire d'attribut
 * Hérite de NodeForm qui gère automatiquement la section "Informations"
 * Ce formulaire contient uniquement les propriétés spécifiques : dataType
 */
export class AttributeForm extends NodeForm<AttributeData> {
  /**
   * Validation des champs spécifiques aux attributs
   */
  protected validateSpecificFields(data: AttributeData): Record<string, string> {
    const errors: Record<string, string> = {};

    // dataType est optionnel, pas de validation nécessaire

    return errors;
  }

  /**
   * Rendu des champs spécifiques aux attributs
   */
  protected renderSpecificFields(): React.ReactNode {
    const { data, errors } = this.state;
    const { edit } = this.props;

    const dataTypeOptions = [
      { value: "string", label: "Texte (string)" },
      { value: "integer", label: "Entier (integer)" },
      { value: "float", label: "Décimal (float)" },
      { value: "boolean", label: "Booléen (boolean)" },
      { value: "date", label: "Date" },
    ];

    return (
      <>
        <SelectField
          name="dataType"
          label="Type de données"
          value={data.dataType || ""}
          onChange={this.handleFieldChange}
          edit={edit}
          options={dataTypeOptions}
          placeholder="Sélectionner un type..."
          error={errors.dataType}
        />

        <BooleanField
          name="isRequired"
          label="Attribut requis"
          value={data.isRequired || false}
          onChange={this.handleFieldChange}
          edit={edit}
          description="Cet attribut doit avoir une valeur"
          error={errors.isRequired}
        />

        <BooleanField
          name="isUnique"
          label="Valeur unique"
          value={data.isUnique || false}
          onChange={this.handleFieldChange}
          edit={edit}
          description="La valeur de cet attribut doit être unique"
          error={errors.isUnique}
        />
      </>
    );
  }
}

export default AttributeForm;
