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

  /**
   * Callback appelé quand le type de nœud change
   * Permet au parent de réagir au changement de type
   */
  onTypeChange?: (newType: string) => void;
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
   * Détermine si c'est une création (nouveau nœud) ou une modification (nœud existant)
   */
  protected isCreation(): boolean {
    // Utiliser la prop isCreation du parent Form
    return this.props.isCreation === true;
  }

  /**
   * Gère le changement de type et notifie le parent
   */
  protected handleTypeChange = (name: string, value: unknown) => {
    // Appeler handleFieldChange du parent pour mettre à jour l'état
    this.handleFieldChange(name, value);

    // Si c'est le champ "type" et qu'un callback est fourni, le notifier
    // Accepter à la fois string et null
    if (name === "type" && this.props.onTypeChange) {
      if (typeof value === "string") {
        this.props.onTypeChange(value);
      } else if (value === null && this.props.onTypeChange) {
        // Si la valeur est null, on peut notifier avec une chaîne vide ou ne pas notifier
        // Pour l'instant, on ne notifie pas pour éviter les erreurs
      }
    }
  };

  /**
   * Validation commune pour les nœuds
   * Vérifie que le nom est renseigné et valide
   */
  protected validateNode(data: T): Record<string, string> {
    const errors: Record<string, string> = {};
    const isCreation = this.isCreation();

    // Validation du nom (obligatoire)
    if (!data.name || data.name.trim().length === 0) {
      errors.name = isCreation ? "Le nom est obligatoire pour créer un nœud" : "Le nom ne peut pas être vide";
    } else if (data.name.trim().length < 2) {
      errors.name = isCreation ? "Le nom doit contenir au moins 2 caractères" : "Le nom doit contenir au moins 2 caractères";
    }

    // Validation du type (obligatoire en création)
    if (isCreation && (!data.type || data.type.trim().length === 0)) {
      errors.type = "Veuillez sélectionner un type de nœud";
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
    const isCreation = this.isCreation();

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
          {/* Type - Editable seulement en mode création */}
          <SelectField
            name="type"
            label="Type de nœud"
            value={data.type || nodeType || null}
            onChange={this.handleTypeChange} // ✅ Utiliser handleTypeChange pour notifier le parent
            edit={edit && isCreation === true} // Editable seulement si edit=true ET isCreation=true
            options={typeOptions}
            error={errors.type}
            placeholder={isCreation ? "Choisissez le type de nœud" : undefined}
          />

          {/* Label */}
          <TextField
            name="name"
            label="Label"
            value={data.name}
            onChange={this.handleFieldChange}
            edit={edit}
            required
            error={errors.name}
            placeholder={isCreation ? "Entrez le nom du nouveau nœud" : "Nom du nœud"}
          />

          {/* Description */}
          <TextAreaField
            name="description"
            label="Description"
            value={data.description || ""}
            onChange={this.handleFieldChange}
            edit={edit}
            placeholder={isCreation ? "Décrivez le nouveau nœud (optionnel)" : "Description du nœud"}
            rows={3}
          />
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

  /**
   * Surcharge le rendu des boutons d'action avec des labels contextuels
   */
  protected renderActions(): JSX.Element | null {
    const { edit, showActions = true } = this.props;
    const { isSubmitting } = this.state;
    const isCreation = this.isCreation();

    if (!showActions || !edit) {
      return null;
    }

    return (
      <div className="flex justify-end gap-3 mt-6">
        <button
          type="button"
          onClick={this.handleCancel}
          disabled={isSubmitting}
          className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50"
        >
          Annuler
        </button>
        <button type="submit" disabled={isSubmitting} className="px-4 py-2 text-sm font-medium text-white bg-blue-600 border border-transparent rounded-md hover:bg-blue-700 disabled:opacity-50">
          {isSubmitting ? (isCreation ? "Création..." : "Enregistrement...") : isCreation ? "Créer" : "Enregistrer"}
        </button>
      </div>
    );
  }
}

export default NodeForm;
