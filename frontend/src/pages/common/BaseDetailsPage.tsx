import { useState, useEffect } from "react";
import { useNavigate, useParams } from "react-router-dom";

/**
 * Base state interface for detail pages
 */
export interface BaseDetailsState<TFormData> {
  formData: TFormData;
  loading: boolean;
  error: string;
}

/**
 * Hook to manage detail page logic (create/edit)
 * Centralizes common patterns from RepositoryDetails and IssueDetails
 */
export function useBaseDetails<TFormData>(
  idParamName: string,
  initialFormData: TFormData,
  options: {
    onLoadEntity?: (id: string) => Promise<TFormData>;
    onCreateEntity: (data: TFormData) => Promise<void>;
    onUpdateEntity: (id: string, data: TFormData) => Promise<void>;
    validateForm?: (data: TFormData, isEditMode: boolean) => string | null;
    getSuccessPath?: (formData: TFormData) => string;
    defaultSuccessPath: string;
  }
) {
  const navigate = useNavigate();
  const params = useParams();
  const entityId = params[idParamName] as string | undefined;
  const isEditMode = !!entityId;

  const [formData, setFormData] = useState<TFormData>(initialFormData);
  const [loading, setLoading] = useState(false);
  const [loadingEntity, setLoadingEntity] = useState(isEditMode);
  const [error, setError] = useState("");

  // Load entity in edit mode
  useEffect(() => {
    const loadEntity = async () => {
      if (!isEditMode || !entityId || !options.onLoadEntity) {
        setLoadingEntity(false);
        return;
      }

      try {
        setLoading(true);
        const data = await options.onLoadEntity(entityId);
        setFormData(data);
      } catch (err) {
        const error = err as { message?: string; detail?: string };
        setError(error?.message || error?.detail || "Erreur lors du chargement");
      } finally {
        setLoading(false);
        setLoadingEntity(false);
      }
    };

    loadEntity();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isEditMode, entityId]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    // Validate form
    if (options.validateForm) {
      const validationError = options.validateForm(formData, isEditMode);
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

      // Navigate to success path
      const successPath = options.getSuccessPath 
        ? options.getSuccessPath(formData) 
        : options.defaultSuccessPath;
      navigate(successPath);
    } catch (err) {
      const error = err as { message?: string; detail?: string };
      setError(error?.message || error?.detail || `Erreur lors de ${isEditMode ? "la mise à jour" : "la création"}`);
    } finally {
      setLoading(false);
    }
  };

  const handleCancel = () => {
    const cancelPath = options.getSuccessPath 
      ? options.getSuccessPath(formData) 
      : options.defaultSuccessPath;
    navigate(cancelPath);
  };

  const updateFormData = (updates: Partial<TFormData>) => {
    setFormData((prev) => ({ ...prev, ...updates }));
  };

  return {
    formData,
    loading,
    loadingEntity,
    error,
    isEditMode,
    entityId,
    setFormData,
    setError,
    handleSubmit,
    handleCancel,
    updateFormData,
    navigate,
  };
}
