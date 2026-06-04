import React from "react";
import { useNavigate, useParams } from "react-router-dom";
import { ArrowLeft, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { AlertCircle } from "lucide-react";
import { Form } from "@/components/common/Form/Form";
import { TextField } from "@/components/common/Form/Fields/TextField";
import { TextAreaField } from "@/components/common/Form/Fields/TextAreaField";
import { metamodelService } from "@/services/metamodelService";
import { MetamodelCreate } from "@/types/metamodel";

interface MetamodelFormData {
  name: string;
  description: string;
  version: string;
}

class MetamodelFormComponent extends Form<MetamodelFormData> {
  protected validate(data: MetamodelFormData): Record<string, string> {
    const errors: Record<string, string> = {};
    if (!data.name.trim()) errors.name = "Le nom est requis";
    if (!data.version.trim()) errors.version = "La version est requise";
    return errors;
  }

  protected renderFields(): React.ReactNode {
    const { data, errors } = this.state;

    return (
      <>
        <div className="mb-6 flex items-center gap-4">
          <Button variant="ghost" size="icon" onClick={this.handleCancel}>
            <ArrowLeft className="h-5 w-5" />
          </Button>
          <div>
            <h1 className="text-3xl font-bold">{this.props.isCreation ? "Nouveau métamodèle" : "Modifier le métamodèle"}</h1>
            <p className="text-muted-foreground">Remplissez les informations du métamodèle</p>
          </div>
        </div>

        <Card>
          <CardHeader>
            <CardTitle>Informations du métamodèle</CardTitle>
            <CardDescription>Les champs marqués d'un * sont obligatoires</CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            <TextField
              name="name"
              label="Nom"
              value={data.name || ""}
              onChange={this.handleFieldChange}
              edit={true}
              required
              placeholder="E-Commerce"
              error={errors.name}
            />
            <TextAreaField
              name="description"
              label="Description"
              value={data.description || ""}
              onChange={this.handleFieldChange}
              edit={true}
              placeholder="Description du métamodèle..."
              rows={4}
              error={errors.description}
            />
            <TextField
              name="version"
              label="Version"
              value={data.version || ""}
              onChange={this.handleFieldChange}
              edit={true}
              required
              placeholder="1.0.0"
              error={errors.version}
            />
          </CardContent>
        </Card>
      </>
    );
  }
}

export function MetamodelForm() {
  const navigate = useNavigate();
  const { id } = useParams<{ id?: string }>();
  const isEditMode = !!id;
  const [loadingEntity, setLoadingEntity] = React.useState(isEditMode);
  const [initialData, setInitialData] = React.useState<MetamodelFormData | undefined>();
  const [error, setError] = React.useState("");

  React.useEffect(() => {
    if (!isEditMode || !id) {
      setLoadingEntity(false);
      return;
    }
    metamodelService
      .getById(id)
      .then((data) => {
        setInitialData({ name: data.name, description: data.description || "", version: data.version });
      })
      .catch((err) => {
        setError(err?.message || "Erreur lors du chargement");
      })
      .finally(() => setLoadingEntity(false));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isEditMode, id]);

  const handleSubmit = async (data: MetamodelFormData) => {
    try {
      if (isEditMode && id) {
        await metamodelService.update(id, data);
      } else {
        const createData: MetamodelCreate = { ...data, node_count: 0, edge_count: 0, status: "draft" };
        await metamodelService.create(createData);
      }
      navigate("/development/metamodeles");
    } catch (err) {
      setError(err?.message || `Erreur lors de ${isEditMode ? "la mise à jour" : "la création"}`);
    }
  };

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
      {error && (
        <Alert variant="destructive" className="mb-6">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      <MetamodelFormComponent
        initialData={initialData}
        edit={true}
        isCreation={!isEditMode}
        onSubmit={handleSubmit}
        onCancel={() => navigate("/development/metamodeles")}
      />
    </div>
  );
}
