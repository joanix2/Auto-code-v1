/**
 * ConceptForm - Formulaire pour éditer les concepts
 */
import React from "react";
import { NodeForm, NodeData } from "@/components/common/Form/NodeForm";

export interface ConceptData extends NodeData {
  name: string;
  description?: string;
  // Pas de propriétés spécifiques pour les concepts de base
}

/**
 * Formulaire de concept
 * Hérite de NodeForm qui gère automatiquement la section "Informations"
 * Ce formulaire ne contient que les propriétés spécifiques (pour l'instant aucune)
 */
export class ConceptForm extends NodeForm<ConceptData> {
  /**
   * Validation des champs spécifiques au concept
   * (Pour l'instant, les concepts n'ont pas de champs spécifiques)
   */
  protected validateSpecificFields(data: ConceptData): Record<string, string> {
    // Pas de validation spécifique pour les concepts
    return {};
  }

  /**
   * Rendu des champs spécifiques au concept
   * (Pour l'instant, les concepts n'ont que les champs de base)
   */
  protected renderSpecificFields(): React.ReactNode {
    // Pas de champs spécifiques pour les concepts de base
    return null;
  }
}

export default ConceptForm;
