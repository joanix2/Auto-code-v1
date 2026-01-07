import React, { useState, useEffect } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { ArrowLeft, Loader2, AlertCircle } from "lucide-react";

/**
 * Configuration for BaseDetailsPage
 */
export interface BaseDetailsPageConfig {
  /** Route parameter name for the entity ID (e.g., 'id', 'issueId') */
  idParamName: string;
  /** Path to navigate back to after cancel/success */
  listPath: string;
  /** Title for create mode */
  createTitle: string;
  /** Title for edit mode */
  editTitle: string;
  /** Description for create mode */
  createDescription: string;
  /** Description for edit mode */
  editDescription: string;
  /** Label for back button */
  backButtonLabel: string;
  /** Label for submit button in create mode */
  createButtonLabel: string;
  /** Label for submit button in edit mode */
  editButtonLabel: string;
  /** Label for cancel button */
  cancelButtonLabel: string;
}

/**
 * Props for BaseDetailsPage
 */
export interface BaseDetailsPageProps<TFormData> {
  config: BaseDetailsPageConfig;
  initialFormData: TFormData;
  onLoadEntity?: (id: string) => Promise<TFormData>;
  onCreateEntity: (data: TFormData) => Promise<void>;
  onUpdateEntity: (id: string, data: TFormData) => Promise<void>;
  validateForm?: (data: TFormData) => string | null;
  getListPath?: (formData: TFormData) => string;
}

/**
 * Abstract base component for detail pages (create/edit)
 * Provides common functionality for form-based detail pages
 */
export abstract class BaseDetailsPage<TFormData, TProps extends BaseDetailsPageProps<TFormData> = BaseDetailsPageProps<TFormData>> extends React.Component<
  TProps,
  {
    formData: TFormData;
    loading: boolean;
    loadingEntity: boolean;
    error: string;
  }
> {
  protected navigate: ReturnType<typeof useNavigate>;
  protected params: ReturnType<typeof useParams>;
  protected isEditMode: boolean;
  protected entityId: string | undefined;

  constructor(props: TProps) {
    super(props);

    // These will be set by withRouter HOC or in derived classes
    this.navigate = (() => {}) as any;
    this.params = {};
    this.entityId = undefined;
    this.isEditMode = false;

    this.state = {
      formData: props.initialFormData,
      loading: false,
      loadingEntity: false,
      error: "",
    };
  }

  /**
   * Initialize navigation and params from hooks
   * Must be called by derived class in render
   */
  protected initializeHooks(navigate: ReturnType<typeof useNavigate>, params: ReturnType<typeof useParams>) {
    this.navigate = navigate;
    this.params = params;
    this.entityId = params[this.props.config.idParamName] as string | undefined;
    this.isEditMode = !!this.entityId;
  }

  /**
   * Load entity data in edit mode
   */
  protected async loadEntity() {
    if (!this.isEditMode || !this.entityId || !this.props.onLoadEntity) {
      return;
    }

    try {
      this.setState({ loadingEntity: true, error: "" });
      const data = await this.props.onLoadEntity(this.entityId);
      this.setState({ formData: data });
    } catch (err) {
      const error = err instanceof Error ? err.message : "Erreur lors du chargement";
      this.setState({ error });
    } finally {
      this.setState({ loadingEntity: false });
    }
  }

  /**
   * Handle form submission
   */
  protected handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    // Validate form
    if (this.props.validateForm) {
      const validationError = this.props.validateForm(this.state.formData);
      if (validationError) {
        this.setState({ error: validationError });
        return;
      }
    }

    try {
      this.setState({ loading: true, error: "" });

      if (this.isEditMode && this.entityId) {
        await this.props.onUpdateEntity(this.entityId, this.state.formData);
      } else {
        await this.props.onCreateEntity(this.state.formData);
      }

      // Navigate to list path
      const listPath = this.props.getListPath ? this.props.getListPath(this.state.formData) : this.props.config.listPath;
      this.navigate(listPath);
    } catch (err) {
      const error = err instanceof Error ? err.message : `Erreur lors de ${this.isEditMode ? "la mise à jour" : "la création"}`;
      this.setState({ error });
    } finally {
      this.setState({ loading: false });
    }
  };

  /**
   * Handle cancel action
   */
  protected handleCancel = () => {
    const listPath = this.props.getListPath ? this.props.getListPath(this.state.formData) : this.props.config.listPath;
    this.navigate(listPath);
  };

  /**
   * Update form data
   */
  protected updateFormData = (updates: Partial<TFormData>) => {
    this.setState((prev) => ({
      formData: { ...prev.formData, ...updates },
    }));
  };

  /**
   * Render the page header
   */
  protected renderHeader(): React.ReactNode {
    const { config } = this.props;
    return (
      <div className="mb-4 sm:mb-6">
        <Button variant="ghost" size="sm" onClick={this.handleCancel} className="mb-3 sm:mb-4">
          <ArrowLeft className="h-4 w-4 mr-2" />
          {config.backButtonLabel}
        </Button>
        <h1 className="text-2xl sm:text-3xl font-bold text-gray-900">
          {this.isEditMode ? config.editTitle : config.createTitle}
        </h1>
        <p className="mt-1 sm:mt-2 text-sm text-gray-600">
          {this.isEditMode ? config.editDescription : config.createDescription}
        </p>
      </div>
    );
  }

  /**
   * Render error alert
   */
  protected renderError(): React.ReactNode {
    if (!this.state.error) return null;

    return (
      <Alert variant="destructive" className="mb-6">
        <AlertCircle className="h-4 w-4" />
        <AlertDescription>{this.state.error}</AlertDescription>
      </Alert>
    );
  }

  /**
   * Render loading state
   */
  protected renderLoading(): React.ReactNode {
    return (
      <div className="container mx-auto max-w-2xl px-3 sm:px-4 py-4 sm:py-6">
        <div className="flex items-center justify-center py-12">
          <Loader2 className="h-8 w-8 animate-spin text-blue-500" />
        </div>
      </div>
    );
  }

  /**
   * Render form fields - must be implemented by derived class
   */
  protected abstract renderFormFields(): React.ReactNode;

  /**
   * Render additional content above the form (optional info cards, etc.)
   */
  protected renderAdditionalContent(): React.ReactNode {
    return null;
  }

  /**
   * Render the form card
   */
  protected renderFormCard(): React.ReactNode {
    const { config } = this.props;
    const { loading } = this.state;

    return (
      <Card>
        <CardHeader>
          <CardTitle>{this.isEditMode ? "Informations" : "Nouvelle entrée"}</CardTitle>
          <CardDescription>
            {this.isEditMode ? "Modifiez les champs que vous souhaitez mettre à jour" : "Fournissez les informations nécessaires"}
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={this.handleSubmit} className="space-y-6">
            {this.renderFormFields()}

            {/* Action Buttons */}
            <div className="flex gap-3 pt-4">
              <Button type="button" variant="outline" onClick={this.handleCancel} disabled={loading} className="flex-1">
                {config.cancelButtonLabel}
              </Button>
              <Button type="submit" disabled={loading} className="flex-1">
                {loading ? (
                  <>
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    {this.isEditMode ? "Mise à jour..." : "Création..."}
                  </>
                ) : (
                  <>{this.isEditMode ? config.editButtonLabel : config.createButtonLabel}</>
                )}
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>
    );
  }

  /**
   * Main render method - can be overridden for custom layout
   */
  render(): React.ReactNode {
    if (this.state.loadingEntity) {
      return this.renderLoading();
    }

    return (
      <div className="container mx-auto max-w-2xl px-3 sm:px-4 py-4 sm:py-6">
        {this.renderHeader()}
        {this.renderError()}
        {this.renderAdditionalContent()}
        {this.renderFormCard()}
      </div>
    );
  }
}

/**
 * Higher-order component to inject router hooks into class component
 */
export function withRouter<P extends object>(Component: React.ComponentType<P>) {
  return function WithRouterComponent(props: P) {
    const navigate = useNavigate();
    const params = useParams();

    return <Component {...props} navigate={navigate} params={params} />;
  };
}
