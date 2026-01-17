/**
 * TextField - Champ texte concret
 *
 * En mode lecture : affiche le texte
 * En mode édition : affiche un input de type text
 */
import React from "react";
import { Field, FieldProps } from "./Field";
import { Input } from "@/components/ui/input";

export interface TextFieldProps extends Omit<FieldProps<string>, "value" | "onChange"> {
  /**
   * Valeur actuelle du champ
   */
  value: string;

  /**
   * Callback appelé lors du changement de valeur
   */
  onChange: (name: string, value: string) => void;

  /**
   * Type d'input HTML (text, email, password, etc.)
   */
  type?: "text" | "email" | "password" | "url";

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
 * Champ texte qui hérite de Field
 */
export class TextField extends Field<string> {
  declare props: TextFieldProps;

  /**
   * Rendu en mode lecture : affiche le texte
   */
  protected renderReadMode(): React.ReactNode {
    const { label, value, className } = this.props;

    return (
      <div className={`field-container flex justify-between items-start ${className || ""}`}>
        <span className="text-sm text-gray-700 font-semibold">{label}:</span>
        <span className="text-sm text-gray-900 text-right flex-1 ml-4">{value || <span className="text-gray-400 italic">Non renseigné</span>}</span>
      </div>
    );
  }

  /**
   * Rendu en mode édition : affiche un input
   */
  protected renderEditMode(): React.ReactNode {
    const { label, value, placeholder, disabled, required, error, className } = this.props;
    const type = this.props.type || "text";
    const minLength = this.props.minLength;
    const maxLength = this.props.maxLength;

    return (
      <div className={`field-container ${className || ""}`}>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          {label}
          {required && <span className="text-red-500 ml-1">*</span>}
        </label>
        <Input
          type={type}
          value={value}
          onChange={(e) => this.handleChange(e.target.value)}
          placeholder={placeholder}
          disabled={disabled}
          required={required}
          minLength={minLength}
          maxLength={maxLength}
          className="w-full"
        />
        {error && <p className="mt-1 text-sm text-red-600">{error}</p>}
      </div>
    );
  }
}

export default TextField;
