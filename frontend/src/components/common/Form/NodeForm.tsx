/**
 * NodeForm - Classe abstraite pour les formulaires de nœuds de graphe
 *
 * Hérite de Form et ajoute une structure commune pour les nœuds :
 * - Section "Informations" : label, type, description (rendue automatiquement)
 * - Section "Propriétés" : champs spécifiques au type de nœud (renderSpecificFields)
 *
 * Tous les formulaires de nœuds doivent hériter de cette classe.
 */
import React from "react";
import { Form, FormProps, FormState } from "./Form";
import { TextField } from "./Fields/TextField";
import { TextAreaField } from "./Fields/TextAreaField";
import { SelectField } from "./Fields/SelectField";

/**
 * Interface de base pour un nœud de graphe
 * Tous les types de nœuds (Concept, Attribute, Relation) doivent étendre cette interface
 */
export interface NodeData {
  /**
   * Nom/Label du nœud
   */
  name: string;

  /**
   * Type du nœud (concept, attribute, relation, etc.)
   */
  type?: string;

  /**
   * Description du nœud
   */
  description?: string;

  /**
   * Propriétés supplémentaires spécifiques au type de nœud
   */
  [key: string]: unknown;
}

/**
 * Props spécifiques aux formulaires de nœuds
 */
export interface NodeFormProps<T extends NodeData> extends FormProps<T> {
  /**
   * Type de nœud (pour affichage uniquement)
   */
  nodeType?: string;
}

/**
 * Classe abstraite NodeForm
 *
 * Fournit la structure commune pour tous les formulaires de nœuds.
 * Rend automatiquement la section "Informations" (label, type, description).
 * Les sous-classes implémentent renderSpecificFields() pour les propriétés spécifiques.
 */
export abstract class NodeForm<T extends NodeData> extends Form<T> {
  declare props: NodeFormProps<T>;

  /**
   * Validation commune pour les nœuds
   * Vérifie que le nom est renseigné et valide
   */
  protected validateNode(data: T): Record<string, string> {
    const errors: Record<string, string> = {};

    // Validation du nom (obligatoire)
    if (!data.name || data.name.trim().length === 0) {
      errors.name = "Le nom est obligatoire";
    } else if (data.name.trim().length < 2) {
      errors.name = "Le nom doit contenir au moins 2 caractères";
    }

    return errors;
  }

  /**
   * Méthode abstraite pour la validation spécifique au type de nœud
   * Les sous-classes doivent implémenter cette méthode pour valider leurs propriétés spécifiques
   */
  protected abstract validateSpecificFields(data: T): Record<string, string>;

  /**
   * Validation complète : combine la validation commune et la validation spécifique
   */
  protected validate(data: T): Record<string, string> {
    const commonErrors = this.validateNode(data);
    const specificErrors = this.validateSpecificFields(data);

    return {
      ...commonErrors,
      ...specificErrors,
    };
  }

  /**
   * Rendu de la section "Informations" (commune à tous les nœuds)
   */
  protected renderInformationSection(): React.ReactNode {
    const { data, errors } = this.state;
    const { edit, nodeType } = this.props;

    // Options pour le SelectField du type (liste de tous les types possibles)
    const typeOptions = [
      { value: "concept", label: "Concept" },
      { value: "attribute", label: "Attribut" },
      { value: "relation", label: "Relation" },
    ];

    return (
      <div>
        <h3 className="font-semibold mb-2">Informations</h3>
        <div className="space-y-3">
          {/* Label */}
          <TextField name="name" label="Label" value={data.name} onChange={this.handleFieldChange} edit={edit} required error={errors.name} placeholder="Nom du nœud" />

          {/* Type - SelectField en lecture seule */}
          {nodeType && (
            <SelectField
              name="type"
              label="Type"
              value={nodeType}
              onChange={() => {}} // Pas de changement possible
              edit={false} // Toujours en mode lecture
              options={typeOptions}
            />
          )}

          {/* Description */}
          <TextAreaField name="description" label="Description" value={data.description || ""} onChange={this.handleFieldChange} edit={edit} placeholder="Description du nœud" rows={3} />
        </div>
      </div>
    );
  }

  /**
   * Méthode abstraite pour le rendu des champs spécifiques
   * Les sous-classes implémentent cette méthode pour afficher leurs propriétés spécifiques
   */
  protected abstract renderSpecificFields(): React.ReactNode;

  /**
   * Rendu des champs : Section "Informations" + Section "Propriétés"
   */
  protected renderFields(): React.ReactNode {
    const specificFields = this.renderSpecificFields();

    return (
      <>
        {this.renderInformationSection()}

        {specificFields && (
          <div className="mt-4">
            <h3 className="font-semibold mb-2">Propriétés</h3>
            <div className="space-y-2">{specificFields}</div>
          </div>
        )}
      </>
    );
  }
}

export default NodeForm;
