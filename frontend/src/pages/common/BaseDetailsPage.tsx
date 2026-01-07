import React, { useState, useEffect } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { ArrowLeft, Loader2, AlertCircle } from "lucide-react";

/**
 * Configuration for detail pages
 */
export interface DetailPageConfig {
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
  /** Card title for edit mode */
  editCardTitle?: string;
  /** Card title for create mode */
  createCardTitle?: string;
  /** Card description for edit mode */
  editCardDescription?: string;
  /** Card description for create mode */
  createCardDescription?: string;
}

/**
 * State for detail page logic
 */
export interface DetailPageState<TFormData> {
  formData: TFormData;
  loading: boolean;
  loadingEntity: boolean;
  error: string;
}

/**
 * Handlers for detail page operations
 */
export interface DetailPageHandlers<TFormData> {
  handleSubmit: (e: React.FormEvent) => Promise<void>;
  handleCancel: () => void;
  updateFormData: (updates: Partial<TFormData>) => void;
  setError: (error: string) => void;
}

/**
 * Hook to manage detail page state and logic
 * Provides common functionality for form-based detail pages (create/edit)
 */
export function useDetailPage<TFormData>(
  config: DetailPageConfig,
  initialFormData: TFormData,
  options: {
    onLoadEntity?: (id: string) => Promise<TFormData>;
    onCreateEntity: (data: TFormData) => Promise<void>;
    onUpdateEntity: (id: string, data: TFormData) => Promise<void>;
    validateForm?: (data: TFormData) => string | null;
    getListPath?: (formData: TFormData) => string;
  }
): {
  state: DetailPageState<TFormData>;
  handlers: DetailPageHandlers<TFormData>;
  isEditMode: boolean;
  entityId: string | undefined;
  navigate: ReturnType<typeof useNavigate>;
} {
  const navigate = useNavigate();
  const params = useParams();
  const entityId = params[config.idParamName] as string | undefined;
  const isEditMode = !!entityId;

  const [formData, setFormData] = useState<TFormData>(initialFormData);
  const [loading, setLoading] = useState(false);
  const [loadingEntity, setLoadingEntity] = useState(isEditMode);
  const [error, setError] = useState("");

  // Load entity data in edit mode
  useEffect(() => {
    const loadEntity = async () => {
      if (!isEditMode || !entityId || !options.onLoadEntity) {
        setLoadingEntity(false);
        return;
      }

      try {
        setLoadingEntity(true);
        setError("");
        const data = await options.onLoadEntity(entityId);
        setFormData(data);
      } catch (err) {
        const errorMsg = err instanceof Error ? err.message : "Erreur lors du chargement";
        setError(errorMsg);
      } finally {
        setLoadingEntity(false);
      }
    };

    loadEntity();
    // Note: options.onLoadEntity is intentionally omitted from deps to avoid re-running on every render.
    // The parent component should ensure onLoadEntity is stable (e.g., using useCallback).
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isEditMode, entityId]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    // Validate form
    if (options.validateForm) {
      const validationError = options.validateForm(formData);
      if (validationError) {
        setError(validationError);
        return;
      }
    }

    try {
      setLoading(true);
      setError("");

      if (isEditMode && entityId) {
        await options.onUpdateEntity(entityId, formData);
      } else {
        await options.onCreateEntity(formData);
      }

      // Navigate to list path
      const listPath = options.getListPath ? options.getListPath(formData) : config.listPath;
      navigate(listPath);
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : `Erreur lors de ${isEditMode ? "la mise à jour" : "la création"}`;
      setError(errorMsg);
    } finally {
      setLoading(false);
    }
  };

  const handleCancel = () => {
    const listPath = options.getListPath ? options.getListPath(formData) : config.listPath;
    navigate(listPath);
  };

  const updateFormData = (updates: Partial<TFormData>) => {
    setFormData((prev) => ({ ...prev, ...updates }));
  };

  return {
    state: { formData, loading, loadingEntity, error },
    handlers: { handleSubmit, handleCancel, updateFormData, setError },
    isEditMode,
    entityId,
    navigate,
  };
}

/**
 * Base component props for detail page layout
 */
export interface BaseDetailPageLayoutProps {
  config: DetailPageConfig;
  isEditMode: boolean;
  loading: boolean;
  loadingEntity: boolean;
  error: string;
  onCancel: () => void;
  onSubmit: (e: React.FormEvent) => Promise<void>;
  children?: React.ReactNode;
  additionalContent?: React.ReactNode;
}

/**
 * Abstract base component for detail page layout
 * Provides common UI structure for detail pages
 * 
 * @template TProps - Extended props type that includes form-specific properties
 */
export abstract class BaseDetailPageLayout<TProps extends BaseDetailPageLayoutProps = BaseDetailPageLayoutProps> extends React.Component<TProps> {
  /**
   * Render form fields - must be implemented by derived class
   */
  protected abstract renderFormFields(): React.ReactNode;

  /**
   * Render the page header
   */
  protected renderHeader(): React.ReactNode {
    const { config, isEditMode, onCancel } = this.props;
    return (
      <div className="mb-4 sm:mb-6">
        <Button variant="ghost" size="sm" onClick={onCancel} className="mb-3 sm:mb-4">
          <ArrowLeft className="h-4 w-4 mr-2" />
          {config.backButtonLabel}
        </Button>
        <h1 className="text-2xl sm:text-3xl font-bold text-gray-900">
          {isEditMode ? config.editTitle : config.createTitle}
        </h1>
        <p className="mt-1 sm:mt-2 text-sm text-gray-600">
          {isEditMode ? config.editDescription : config.createDescription}
        </p>
      </div>
    );
  }

  /**
   * Render error alert
   */
  protected renderError(): React.ReactNode {
    if (!this.props.error) return null;

    return (
      <Alert variant="destructive" className="mb-6">
        <AlertCircle className="h-4 w-4" />
        <AlertDescription>{this.props.error}</AlertDescription>
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
   * Render the form card
   */
  protected renderFormCard(): React.ReactNode {
    const { config, isEditMode, loading, onSubmit } = this.props;

    return (
      <Card>
        <CardHeader>
          <CardTitle>
            {isEditMode
              ? config.editCardTitle || "Informations"
              : config.createCardTitle || "Nouvelle entrée"}
          </CardTitle>
          <CardDescription>
            {isEditMode
              ? config.editCardDescription || "Modifiez les champs que vous souhaitez mettre à jour"
              : config.createCardDescription || "Fournissez les informations nécessaires"}
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={onSubmit} className="space-y-6">
            {this.renderFormFields()}

            {/* Action Buttons */}
            <div className="flex gap-3 pt-4">
              <Button type="button" variant="outline" onClick={this.props.onCancel} disabled={loading} className="flex-1">
                {config.cancelButtonLabel}
              </Button>
              <Button type="submit" disabled={loading} className="flex-1">
                {loading ? (
                  <>
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    {isEditMode ? "Mise à jour..." : "Création..."}
                  </>
                ) : (
                  <>{isEditMode ? config.editButtonLabel : config.createButtonLabel}</>
                )}
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>
    );
  }

  /**
   * Main render method
   */
  render(): React.ReactNode {
    if (this.props.loadingEntity) {
      return this.renderLoading();
    }

    return (
      <div className="container mx-auto max-w-2xl px-3 sm:px-4 py-4 sm:py-6">
        {this.renderHeader()}
        {this.renderError()}
        {this.props.additionalContent}
        {this.renderFormCard()}
        {this.props.children}
      </div>
    );
  }
}
