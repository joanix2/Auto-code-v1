import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { useAuth } from "../../contexts/AuthContext";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { ArrowLeft } from "lucide-react";
import { repositoryService } from "@/services/repository.service";
import { useBaseDetails } from "../common/BaseDetailsPage";

interface RepositoryFormData {
  name: string;
  description: string;
  private: boolean;
}

export function RepositoryDetails() {
  const { user } = useAuth();

  const {
    formData,
    loading,
    loadingEntity,
    error,
    isEditMode,
    setError,
    handleSubmit,
    handleCancel,
    updateFormData,
  } = useBaseDetails<RepositoryFormData>("id", { name: "", description: "", private: false }, {
    onLoadEntity: async (id: string) => {
      const repo = await repositoryService.getById(id);
      return {
        name: repo.name,
        description: repo.description || "",
        private: repo.is_private,
      };
    },
    onCreateEntity: async (data: RepositoryFormData) => {
      await repositoryService.create({
        name: data.name.trim(),
        description: data.description.trim() || undefined,
        private: data.private,
      });
    },
    onUpdateEntity: async (id: string, data: RepositoryFormData) => {
      await repositoryService.update(id, {
        name: data.name.trim(),
        description: data.description.trim() || undefined,
      });
    },
    validateForm: (data: RepositoryFormData) => {
      if (!data.name.trim()) {
        return "Le nom du repository est requis";
      }
      if (!user?.github_token) {
        return "Veuillez configurer votre token GitHub dans les paramètres de votre profil";
      }
      return null;
    },
    defaultSuccessPath: "/repositories",
  });

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const { name, value, type } = e.target;
    updateFormData({
      [name]: type === "checkbox" ? (e.target as HTMLInputElement).checked : value,
    } as Partial<RepositoryFormData>);
  };

  if (loadingEntity) {
    return (
      <div className="p-3 sm:p-6">
        <div className="flex items-center justify-center py-12">
          <svg className="animate-spin h-8 w-8 text-blue-500" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
          </svg>
        </div>
      </div>
    );
  }

  return (
    <div className="p-3 sm:p-6 gap-2 flex flex-col items-start">
      {/* Header */}
      <Button variant="ghost" size="sm" onClick={handleCancel}>
        <ArrowLeft className="h-4 w-4 mr-2" />
        Retour aux repositories
      </Button>

      {/* Error Alert */}
      {error && (
        <Alert variant="destructive">
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {/* Info Card */}
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

      {/* Form Card */}
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
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Repository Name */}
            <div className="space-y-2">
              <Label htmlFor="name" className="text-sm font-medium">
                Nom du repository {!isEditMode && "*"}
              </Label>
              <Input id="name" name="name" type="text" placeholder="mon-super-projet" value={formData.name} onChange={handleChange} required className="w-full" />
              <p className="text-xs text-slate-500">{isEditMode ? "Le changement de nom sera synchronisé avec GitHub" : "Choisissez un nom court et descriptif pour votre repository"}</p>
            </div>

            {/* Repository Description */}
            <div className="space-y-2">
              <Label htmlFor="description" className="text-sm font-medium">
                Description
              </Label>
              <textarea
                id="description"
                name="description"
                placeholder="Description de votre repository..."
                value={formData.description}
                onChange={handleChange}
                rows={4}
                className="w-full px-3 py-2 text-sm rounded-md border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-950 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
              <p className="text-xs text-slate-500">{isEditMode ? "La description sera synchronisée avec GitHub" : "Décrivez brièvement votre projet (optionnel)"}</p>
            </div>

            {/* Private Checkbox - only in create mode */}
            {!isEditMode && (
              <div className="flex items-start space-x-3 rounded-lg border border-slate-200 dark:border-slate-800 p-4 bg-slate-50 dark:bg-slate-900/50">
                <input
                  id="private"
                  name="private"
                  type="checkbox"
                  checked={formData.private}
                  onChange={handleChange}
                  className="mt-1 h-4 w-4 rounded border-slate-300 text-blue-600 focus:ring-blue-500"
                />
                <div className="flex-1">
                  <Label htmlFor="private" className="text-sm font-medium cursor-pointer">
                    Repository privé
                  </Label>
                  <p className="text-xs text-slate-500 mt-1">Les repositories privés ne sont visibles que par vous et les collaborateurs que vous choisissez</p>
                </div>
              </div>
            )}

            {/* Action Buttons */}
            <div className="flex flex-col-reverse md:flex-row gap-3">
              <Button type="button" variant="outline" onClick={handleCancel} disabled={loading} className="w-full md:w-1/2">
                Annuler
              </Button>
              <Button type="submit" disabled={loading} className="w-full md:w-1/2 bg-gradient-to-r from-blue-600 to-violet-600 hover:from-blue-700 hover:to-violet-700">
                {loading ? (
                  <>
                    <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                    {isEditMode ? "Mise à jour..." : "Création..."}
                  </>
                ) : (
                  <>{isEditMode ? "Mettre à jour" : "Créer le repository"}</>
                )}
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}

export default RepositoryDetails;
