/**
 * BooleanField - Champ booléen (checkbox/switch)
 *
 * En mode lecture : affiche "Oui" ou "Non"
 * En mode édition : affiche une checkbox
 */
import React from "react";
import { Field, FieldProps } from "./Field";
import { Checkbox } from "@/components/ui/checkbox";

export interface BooleanFieldProps extends Omit<FieldProps<boolean>, "value" | "onChange"> {
  /**
   * Valeur actuelle du champ
   */
  value: boolean;

  /**
   * Callback appelé lors du changement de valeur
   */
  onChange: (name: string, value: boolean) => void;

  /**
   * Texte à afficher à côté de la checkbox en mode édition
   */
  description?: string;

  /**
   * Texte personnalisé pour true (par défaut "Oui")
   */
  trueLabel?: string;

  /**
   * Texte personnalisé pour false (par défaut "Non")
   */
  falseLabel?: string;
}

/**
 * Champ booléen qui hérite de Field
 */
export class BooleanField extends Field<boolean> {
  declare props: BooleanFieldProps;

  /**
   * Rendu en mode lecture : affiche "Oui" ou "Non"
   */
  protected renderReadMode(): React.ReactNode {
    const { label, value, className, trueLabel = "Oui", falseLabel = "Non" } = this.props;

    return (
      <div className={`field-container flex justify-between items-start ${className || ""}`}>
        <span className="text-sm text-gray-700 font-semibold">{label}:</span>
        <span className={`text-sm font-medium text-right flex-1 ml-4 ${value ? "text-green-600" : "text-gray-500"}`}>{value ? trueLabel : falseLabel}</span>
      </div>
    );
  }

  /**
   * Rendu en mode édition : affiche une checkbox
   */
  protected renderEditMode(): React.ReactNode {
    const { label, value, description, disabled, required, error, className } = this.props;

    return (
      <div className={`field-container ${className || ""}`}>
        <div className="flex items-center justify-between">
          <div className="flex-1">
            <label htmlFor={this.props.name} className="text-sm font-medium text-gray-700 cursor-pointer select-none">
              {label}
              {required && <span className="text-red-500 ml-1">*</span>}
            </label>
            {description && <p className="text-sm text-gray-500 mt-1">{description}</p>}
          </div>
          <Checkbox
            id={this.props.name}
            checked={value}
            onCheckedChange={(checked) => {
              // checked peut être boolean ou "indeterminate"
              this.handleChange(checked === true);
            }}
            disabled={disabled}
            required={required}
            className="ml-4"
          />
        </div>
        {error && <p className="mt-1 text-sm text-red-600">{error}</p>}
      </div>
    );
  }
}

export default BooleanField;
