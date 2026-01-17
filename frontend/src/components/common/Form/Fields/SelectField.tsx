/**
 * SelectField - Champ de sélection
 *
 * En mode lecture : affiche un badge/tag coloré
 * En mode édition : affiche un select
 */
import React from "react";
import { Field, FieldProps } from "./Field";
import { Badge } from "@/components/ui/badge";

export interface SelectOption {
  value: string;
  label: string;
  color?: string; // Couleur pour le badge en mode lecture
}

export interface SelectFieldProps extends Omit<FieldProps<string>, "value" | "onChange"> {
  /**
   * Valeur actuelle du champ
   */
  value: string;

  /**
   * Callback appelé lors du changement de valeur
   */
  onChange: (name: string, value: string) => void;

  /**
   * Options disponibles
   */
  options: SelectOption[];
}

/**
 * Champ de sélection qui affiche un badge en lecture et un select en édition
 */
export class SelectField extends Field<string> {
  declare props: SelectFieldProps;

  /**
   * Trouve l'option sélectionnée
   */
  private getSelectedOption(): SelectOption | undefined {
    return this.props.options.find((opt) => opt.value === this.props.value);
  }

  /**
   * Rendu en mode lecture : affiche un badge
   */
  protected renderReadMode(): React.ReactNode {
    const { label, className } = this.props;
    const selectedOption = this.getSelectedOption();

    return (
      <div className={`field-container flex justify-between items-center py-2 ${className || ""}`}>
        <span className="text-sm text-gray-700 font-semibold">{label}:</span>
        <div className="text-right ml-4">
          {selectedOption ? (
            <Badge variant="secondary" className={selectedOption.color ? `bg-${selectedOption.color}-100 text-${selectedOption.color}-800` : ""}>
              {selectedOption.label}
            </Badge>
          ) : (
            <span className="text-gray-400 italic text-sm">Non sélectionné</span>
          )}
        </div>
      </div>
    );
  }

  /**
   * Rendu en mode édition : affiche un select
   */
  protected renderEditMode(): React.ReactNode {
    const { label, value, placeholder, disabled, required, error, className, options } = this.props;

    return (
      <div className={`field-container ${className || ""}`}>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          {label}
          {required && <span className="text-red-500 ml-1">*</span>}
        </label>
        <select
          value={value}
          onChange={(e) => this.handleChange(e.target.value)}
          disabled={disabled}
          required={required}
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        >
          {placeholder && (
            <option value="" disabled>
              {placeholder}
            </option>
          )}
          {options.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
        {error && <p className="mt-1 text-sm text-red-600">{error}</p>}
      </div>
    );
  }
}

export default SelectField;
