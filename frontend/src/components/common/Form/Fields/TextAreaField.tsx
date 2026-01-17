/**
 * TextAreaField - Champ texte multiligne
 *
 * En mode lecture : affiche le texte
 * En mode édition : affiche un textarea
 */
import React from "react";
import { Field, FieldProps } from "./Field";
import { Textarea } from "@/components/ui/textarea";

export interface TextAreaFieldProps extends Omit<FieldProps<string>, "value" | "onChange"> {
  /**
   * Valeur actuelle du champ
   */
  value: string;

  /**
   * Callback appelé lors du changement de valeur
   */
  onChange: (name: string, value: string) => void;

  /**
   * Nombre de lignes à afficher
   */
  rows?: number;

  /**
   * Longueur minimale
   */
  minLength?: number;

  /**
   * Longueur maximale
   */
  maxLength?: number;
}

/**
 * Champ textarea qui hérite de Field
 */
export class TextAreaField extends Field<string> {
  declare props: TextAreaFieldProps;

  /**
   * Rendu en mode lecture : affiche le texte
   */
  protected renderReadMode(): React.ReactNode {
    const { label, value, className } = this.props;

    return (
      <div className={`field-container ${className || ""}`}>
        <span className="text-sm text-gray-700 font-semibold block mb-1">{label}:</span>
        <span className="text-sm text-gray-900 block whitespace-pre-wrap">{value || <span className="text-gray-400 italic">Non renseigné</span>}</span>
      </div>
    );
  }

  /**
   * Rendu en mode édition : affiche un textarea
   */
  protected renderEditMode(): React.ReactNode {
    const { label, value, placeholder, disabled, required, error, className, rows } = this.props;
    const minLength = this.props.minLength;
    const maxLength = this.props.maxLength;

    return (
      <div className={`field-container ${className || ""}`}>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          {label}
          {required && <span className="text-red-500 ml-1">*</span>}
        </label>
        <Textarea
          value={value}
          onChange={(e) => this.handleChange(e.target.value)}
          placeholder={placeholder}
          disabled={disabled}
          required={required}
          minLength={minLength}
          maxLength={maxLength}
          rows={rows}
          className="w-full"
        />
        {error && <p className="mt-1 text-sm text-red-600">{error}</p>}
      </div>
    );
  }
}

export default TextAreaField;
