/**
 * Field - Classe abstraite pour tous les champs de formulaire
 *
 * Cette classe définit l'interface commune pour tous les types de champs.
 * En mode édition (edit=false), le champ affiche la valeur en texte.
 * En mode édition (edit=true), le champ affiche un input éditable.
 */
import React from "react";

export interface FieldProps<T = unknown> {
  /**
   * Nom du champ (utilisé comme clé dans le formulaire)
   */
  name: string;

  /**
   * Label affiché au-dessus du champ
   */
  label: string;

  /**
   * Valeur actuelle du champ
   */
  value: T;

  /**
   * Callback appelé lors du changement de valeur
   */
  onChange: (name: string, value: T) => void;

  /**
   * Mode d'affichage : false = lecture seule (texte), true = édition (input)
   */
  edit: boolean;

  /**
   * Le champ est-il requis ?
   */
  required?: boolean;

  /**
   * Message d'erreur à afficher
   */
  error?: string;

  /**
   * Placeholder pour le champ en mode édition
   */
  placeholder?: string;

  /**
   * Le champ est-il désactivé ?
   */
  disabled?: boolean;

  /**
   * Classes CSS supplémentaires
   */
  className?: string;
}

/**
 * Classe abstraite Field
 *
 * Tous les champs (TextField, NumberField, SelectField, etc.) doivent hériter de cette classe.
 * Chaque champ implémente son propre rendu complet (label, valeur, erreur).
 */
export abstract class Field<T = unknown> extends React.Component<FieldProps<T>> {
  /**
   * Méthode abstraite pour le rendu en mode lecture (edit=false)
   * Affiche la valeur sous forme de texte statique
   */
  protected abstract renderReadMode(): React.ReactNode;

  /**
   * Méthode abstraite pour le rendu en mode édition (edit=true)
   * Affiche un input éditable
   */
  protected abstract renderEditMode(): React.ReactNode;

  /**
   * Gère le changement de valeur et appelle le callback onChange
   */
  protected handleChange = (value: T) => {
    this.props.onChange(this.props.name, value);
  };

  /**
   * Rendu principal - délègue au champ concret
   */
  render() {
    const { edit } = this.props;
    return edit ? this.renderEditMode() : this.renderReadMode();
  }
}

export default Field;
