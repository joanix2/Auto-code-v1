import React from "react";
import { MetamodelCreate } from "@/types/metamodel";
import { metamodelService } from "@/services/metamodelService";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { ArrowLeft, Save, Loader2 } from "lucide-react";
import { useToast } from "@/components/ui/use-toast";
import { useAuth } from "@/contexts/AuthContext";
import { useBaseDetails } from "../../common/BaseDetailsPage";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { AlertCircle } from "lucide-react";

interface MetamodelFormData {
  name: string;
  description: string;
  version: string;
}

export function MetamodelForm() {
  const { toast } = useToast();
  const { user } = useAuth();

  const { formData, loading, loadingEntity, error, isEditMode, handleSubmit, handleCancel, updateFormData } = useBaseDetails<MetamodelFormData>(
    "id",
    {
      name: "",
      description: "",
      version: "1.0.0",
    },
    {
      onLoadEntity: async (id: string) => {
        const data = await metamodelService.getById(id);
        return {
          name: data.name,
          description: data.description || "",
          version: data.version,
        };
      },
      onCreateEntity: async (data: MetamodelFormData) => {
        const createData: MetamodelCreate = {
          ...data,
          concepts: 0,
          relations: 0,
          author: user?.username || "",
          status: "draft",
        };
        await metamodelService.create(createData);
        toast({
          title: "Métamodèle créé",
          description: "Le métamodèle a été créé avec succès.",
        });
      },
      onUpdateEntity: async (id: string, data: MetamodelFormData) => {
        await metamodelService.update(id, data);
        toast({
          title: "Métamodèle modifié",
          description: "Le métamodèle a été modifié avec succès.",
        });
      },
      validateForm: (data: MetamodelFormData) => {
        if (!data.name.trim()) return "Le nom est requis";
        if (!data.version.trim()) return "La version est requise";
        return null;
      },
      defaultSuccessPath: "/development/metamodeles",
    }
  );

  if (loadingEntity) {
    return (
      <div className="p-6">
        <div className="flex items-center justify-center py-12">
          <Loader2 className="h-8 w-8 animate-spin text-blue-500" />
        </div>
      </div>
    );
  }

  return (
    <div className="p-6">
      {/* Header */}
      <div className="mb-6 flex items-center gap-4">
        <Button variant="ghost" size="icon" onClick={handleCancel}>
          <ArrowLeft className="h-5 w-5" />
        </Button>
        <div>
          <h1 className="text-3xl font-bold">{isEditMode ? "Modifier le métamodèle" : "Nouveau métamodèle"}</h1>
          <p className="text-muted-foreground">Remplissez les informations du métamodèle</p>
        </div>
      </div>

      {/* Error Alert */}
      {error && (
        <Alert variant="destructive" className="mb-6">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {/* Form */}
      <Card>
        <CardHeader>
          <CardTitle>Informations du métamodèle</CardTitle>
          <CardDescription>Les champs marqués d'un * sont obligatoires</CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Name */}
            <div className="space-y-2">
              <Label htmlFor="name">
                Nom <span className="text-destructive">*</span>
              </Label>
              <Input id="name" placeholder="E-Commerce" value={formData.name} onChange={(e) => updateFormData({ name: e.target.value })} required />
            </div>

            {/* Description */}
            <div className="space-y-2">
              <Label htmlFor="description">Description</Label>
              <Textarea id="description" placeholder="Description du métamodèle..." value={formData.description} onChange={(e) => updateFormData({ description: e.target.value })} rows={4} />
            </div>

            {/* Version */}
            <div className="space-y-2">
              <Label htmlFor="version">
                Version <span className="text-destructive">*</span>
              </Label>
              <Input id="version" placeholder="1.0.0" value={formData.version} onChange={(e) => updateFormData({ version: e.target.value })} required />
            </div>

            {/* Actions */}
            <div className="flex gap-4 justify-end">
              <Button type="button" variant="outline" onClick={handleCancel} disabled={loading}>
                Annuler
              </Button>
              <Button type="submit" disabled={loading}>
                {loading ? (
                  <>
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    {isEditMode ? "Mise à jour..." : "Création..."}
                  </>
                ) : (
                  <>
                    <Save className="h-4 w-4 mr-2" />
                    {isEditMode ? "Mettre à jour" : "Enregistrer"}
                  </>
                )}
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
