/**
 * Form - Classe abstraite pour les formulaires
 *
 * Gère l'état du formulaire et la validation des champs.
 * Supporte deux modes : lecture (edit=false) et édition (edit=true)
 */
import React from "react";

export interface FormProps<T = Record<string, unknown>> {
  /**
   * Données initiales du formulaire
   */
  initialData?: T;

  /**
   * Mode d'affichage : false = lecture, true = édition
   */
  edit: boolean;

  /**
   * Callback appelé lors de la soumission du formulaire
   */
  onSubmit?: (data: T) => void | Promise<void>;

  /**
   * Callback appelé lors de l'annulation
   */
  onCancel?: () => void;

  /**
   * Classes CSS supplémentaires
   */
  className?: string;

  /**
   * Afficher les boutons de formulaire ?
   */
  showActions?: boolean;
}

export interface FormState<T = Record<string, unknown>> {
  /**
   * Données du formulaire
   */
  data: T;

  /**
   * Erreurs de validation par champ
   */
  errors: Record<string, string>;

  /**
   * Le formulaire est-il en cours de soumission ?
   */
  isSubmitting: boolean;
}

/**
 * Classe abstraite Form
 *
 * Tous les formulaires doivent hériter de cette classe.
 */
export abstract class Form<T = Record<string, unknown>> extends React.Component<FormProps<T>, FormState<T>> {
  constructor(props: FormProps<T>) {
    super(props);
    this.state = {
      data: props.initialData || ({} as T),
      errors: {},
      isSubmitting: false,
    };
  }

  /**
   * Met à jour les données quand les props changent
   */
  componentDidUpdate(prevProps: FormProps<T>) {
    // Si on passe de edit=true à edit=false, réinitialiser avec initialData
    if (prevProps.edit && !this.props.edit && this.props.initialData) {
      this.setState({
        data: this.props.initialData,
        errors: {},
      });
    }
    // Si initialData change (comparaison JSON pour détecter les changements de contenu)
    else if (this.props.initialData && JSON.stringify(prevProps.initialData) !== JSON.stringify(this.props.initialData)) {
      this.setState({ data: this.props.initialData });
    }
  }

  /**
   * Gère le changement d'un champ
   */
  protected handleFieldChange = (name: string, value: unknown) => {
    this.setState((prevState) => ({
      data: {
        ...prevState.data,
        [name]: value,
      },
      // Effacer l'erreur du champ quand il est modifié
      errors: {
        ...prevState.errors,
        [name]: "",
      },
    }));
  };

  /**
   * Méthode abstraite pour valider le formulaire
   * Retourne un objet avec les erreurs par champ
   */
  protected abstract validate(data: T): Record<string, string>;

  /**
   * Méthode abstraite pour le rendu des champs
   */
  protected abstract renderFields(): React.ReactNode;

  /**
   * Gère la soumission du formulaire
   */
  protected handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    // Validation
    const errors = this.validate(this.state.data);

    if (Object.keys(errors).length > 0) {
      this.setState({ errors });
      return;
    }

    // Soumission
    if (this.props.onSubmit) {
      this.setState({ isSubmitting: true });
      try {
        await this.props.onSubmit(this.state.data);
      } catch (error) {
        console.error("Form submission error:", error);
      } finally {
        this.setState({ isSubmitting: false });
      }
    }
  };

  /**
   * Gère l'annulation
   */
  protected handleCancel = () => {
    // Réinitialiser aux données initiales
    this.setState({
      data: this.props.initialData || ({} as T),
      errors: {},
    });

    if (this.props.onCancel) {
      this.props.onCancel();
    }
  };

  /**
   * Rendu des boutons d'action
   */
  protected renderActions() {
    const { edit, showActions = true } = this.props;
    const { isSubmitting } = this.state;

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
          {isSubmitting ? "Enregistrement..." : "Enregistrer"}
        </button>
      </div>
    );
  }

  /**
   * Rendu principal
   */
  render() {
    const { className } = this.props;

    return (
      <form onSubmit={this.handleSubmit} className={className}>
        <div className="space-y-2">{this.renderFields()}</div>
        {this.renderActions()}
      </form>
    );
  }
}

export default Form;
