import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { useNavigate, useParams } from "react-router-dom";
import { useAuth } from "../../../contexts/AuthContext";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { ArrowLeft, Loader2 } from "lucide-react";
import { repositoryService } from "@/services/repository.service";
import { Form } from "@/components/common/Form/Form";
import { TextField } from "@/components/common/Form/Fields/TextField";
import { BooleanField } from "@/components/common/Form/Fields/BooleanField";

interface RepositoryFormData {
  name: string;
  description: string;
  private: boolean;
}

class RepositoryFormComponent extends Form<RepositoryFormData> {
  protected validate(data: RepositoryFormData): Record<string, string> {
    const errors: Record<string, string> = {};
    if (!data.name.trim()) {
      errors.name = "Le nom du repository est requis";
    }
    return errors;
  }

  protected renderActions() {
    const { isSubmitting } = this.state;
    const isEditMode = !this.props.isCreation;

    return (
      <div className="flex flex-col-reverse md:flex-row gap-3">
        <button type="button" onClick={this.handleCancel} disabled={isSubmitting} className="w-full md:w-1/2 px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50">
          Annuler
        </button>
        <button type="submit" disabled={isSubmitting} className="w-full md:w-1/2 px-4 py-2 text-sm font-medium text-white bg-gradient-to-r from-blue-600 to-violet-600 hover:from-blue-700 hover:to-violet-700 rounded-md disabled:opacity-50">
          {isSubmitting ? (
            <>{isEditMode ? "Mise à jour..." : "Création..."}</>
          ) : (
            <>{isEditMode ? "Mettre à jour" : "Créer le repository"}</>
          )}
        </button>
      </div>
    );
  }

  protected renderFields(): React.ReactNode {
    const { data, errors } = this.state;
    const isEditMode = !this.props.isCreation;

    return (
      <>
        <Card className="border-blue-200 bg-blue-50 dark:border-blue-900 dark:bg-blue-950/30">
          <CardContent className="pt-6">
            <div className="flex gap-3">
              <svg className="h-5 w-5 text-blue-600 dark:text-blue-400 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <div className="space-y-1">
                <h3 className="text-sm font-semibold text-blue-900 dark:text-blue-100">À propos de la création</h3>
                <p className="text-xs text-blue-800 dark:text-blue-300">
                  Ce formulaire créera automatiquement le repository sur GitHub avant de l'enregistrer dans la base de données. Vous pouvez également synchroniser vos repositories existants depuis
                  GitHub en utilisant le bouton "Sync GitHub" dans la liste des projets.
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="border-slate-200 dark:border-slate-800">
          <CardHeader className="flex flex-col gap-2">
            <CardTitle>{isEditMode ? "Éditer le repository" : "Créer un nouveau repository"}</CardTitle>
            <CardDescription>
              {isEditMode ? (
                "Modifiez le nom et/ou la description de votre repository. Les changements seront synchronisés avec GitHub."
              ) : (
                <>
                  Assurez-vous d'avoir configuré votre token GitHub dans votre{" "}
                  <Link to="/profile" className="text-blue-600 hover:underline">
                    profil
                  </Link>
                </>
              )}
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            <div>
              <TextField
                name="name"
                label="Nom du repository"
                value={data.name || ""}
                onChange={this.handleFieldChange}
                edit={true}
                required={!isEditMode}
                placeholder="mon-super-projet"
                error={errors.name}
              />
              <p className="text-xs text-slate-500 mt-1">{isEditMode ? "Le changement de nom sera synchronisé avec GitHub" : "Choisissez un nom court et descriptif pour votre repository"}</p>
            </div>

            <div>
              <TextField
                name="description"
                label="Description"
                value={data.description || ""}
                onChange={this.handleFieldChange}
                edit={true}
                placeholder="Description de votre repository..."
                error={errors.description}
              />
              <p className="text-xs text-slate-500 mt-1">{isEditMode ? "La description sera synchronisée avec GitHub" : "Décrivez brièvement votre projet (optionnel)"}</p>
            </div>

            {!isEditMode && (
              <div className="rounded-lg border border-slate-200 dark:border-slate-800 p-4 bg-slate-50 dark:bg-slate-900/50">
                <BooleanField
                  name="private"
                  label="Repository privé"
                  value={!!data.private}
                  onChange={this.handleFieldChange}
                  edit={true}
                  description="Les repositories privés ne sont visibles que par vous et les collaborateurs que vous choisissez"
                />
              </div>
            )}
          </CardContent>
        </Card>
      </>
    );
  }
}

export function RepositoryDetails() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const { id } = useParams<{ id?: string }>();
  const isEditMode = !!id;
  const [loadingEntity, setLoadingEntity] = useState(isEditMode);
  const [initialData, setInitialData] = useState<RepositoryFormData | undefined>();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!isEditMode || !id) {
      setLoadingEntity(false);
      return;
    }
    repositoryService
      .getById(id)
      .then((repo) => {
        setInitialData({ name: repo.name, description: repo.description || "", private: repo.is_private });
      })
      .catch((err) => {
        setError(err?.message || "Erreur lors du chargement");
      })
      .finally(() => setLoadingEntity(false));
  }, [isEditMode, id]);

  const handleSubmit = async (data: RepositoryFormData) => {
    if (!user?.github_token) {
      setError("Veuillez configurer votre token GitHub dans les paramètres de votre profil");
      return;
    }
    setLoading(true);
    setError("");
    try {
      if (isEditMode && id) {
        await repositoryService.update(id, { name: data.name.trim(), description: data.description.trim() || undefined });
      } else {
        await repositoryService.create({ name: data.name.trim(), description: data.description.trim() || undefined, private: data.private });
      }
      navigate("/development/repositories");
    } catch (err) {
      setError(err?.message || `Erreur lors de ${isEditMode ? "la mise à jour" : "la création"}`);
    } finally {
      setLoading(false);
    }
  };

  if (loadingEntity) {
    return (
      <div className="p-3 sm:p-6">
        <div className="flex items-center justify-center py-12">
          <Loader2 className="h-8 w-8 animate-spin text-blue-500" />
        </div>
      </div>
    );
  }

  return (
    <div className="p-3 sm:p-6 gap-2 flex flex-col items-start">
      <Button variant="ghost" size="sm" onClick={() => navigate("/development/repositories")}>
        <ArrowLeft className="h-4 w-4 mr-2" />
        Retour aux repositories
      </Button>

      {error && (
        <Alert variant="destructive">
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      <RepositoryFormComponent
        initialData={initialData}
        edit={true}
        isCreation={!isEditMode}
        onSubmit={handleSubmit}
        onCancel={() => navigate("/development/repositories")}
      />
    </div>
  );
}

export default RepositoryDetails;
