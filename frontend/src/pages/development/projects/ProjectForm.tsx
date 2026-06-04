import React from "react";
import { useNavigate, useParams } from "react-router-dom";
import { ArrowLeft } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Form } from "@/components/common/Form/Form";
import { TextField } from "@/components/common/Form/Fields/TextField";
import { TextAreaField } from "@/components/common/Form/Fields/TextAreaField";
import { projectService } from "@/services/project.service";
import { useToast } from "@/components/ui/use-toast";
import { Project } from "@/types/project";

interface ProjectFormData {
  name: string;
  description: string;
}

export class ProjectFormComponent extends Form<ProjectFormData> {
  protected validate(data: ProjectFormData): Record<string, string> {
    const errors: Record<string, string> = {};
    if (!data.name || data.name.trim().length < 1) {
      errors.name = "Le nom du projet est requis.";
    }
    return errors;
  }

  protected renderFields(): React.ReactNode {
    const { data, errors } = this.state;

    return (
      <>
        <div className="mb-6">
          <h1 className="text-2xl sm:text-3xl font-bold text-gray-900">
            {this.props.isCreation ? "Nouveau projet" : "Modifier le projet"}
          </h1>
        </div>
        <TextField
          name="name"
          label="Nom du projet"
          value={data.name || ""}
          onChange={this.handleFieldChange}
          edit={true}
          required
          placeholder="Mon projet"
          error={errors.name}
        />
        <TextAreaField
          name="description"
          label="Description"
          value={data.description || ""}
          onChange={this.handleFieldChange}
          edit={true}
          placeholder="Description du projet..."
          rows={4}
          error={errors.description}
        />
      </>
    );
  }
}

export function ProjectForm() {
  const { projectId } = useParams<{ projectId?: string }>();
  const navigate = useNavigate();
  const { toast } = useToast();
  const [loading, setLoading] = React.useState(!!projectId);
  const [initialData, setInitialData] = React.useState<ProjectFormData | undefined>();
  const isEditing = !!projectId;

  React.useEffect(() => {
    if (isEditing && projectId) {
      projectService
        .getById(projectId)
        .then((project: Project) => {
          setInitialData({ name: project.name, description: project.description || "" });
        })
        .catch(() => {
          toast({ title: "Erreur", description: "Impossible de charger le projet.", variant: "destructive" });
          navigate("/development/projets");
        })
        .finally(() => setLoading(false));
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [projectId, isEditing]);

  const handleSubmit = async (data: ProjectFormData) => {
    try {
      if (isEditing && projectId) {
        await projectService.update(projectId, { name: data.name, description: data.description });
        toast({ title: "Projet mis à jour", description: "Le projet a été modifié avec succès." });
        navigate(`/development/projets/${projectId}`);
      } else {
        const project = await projectService.create({ name: data.name, description: data.description });
        toast({ title: "Projet créé", description: "Le projet a été créé avec succès." });
        navigate(`/development/projets/${project.id}`);
      }
    } catch {
      toast({
        title: "Erreur",
        description: isEditing ? "Impossible de modifier le projet." : "Impossible de créer le projet.",
        variant: "destructive",
      });
    }
  };

  if (loading) {
    return (
      <div className="container mx-auto max-w-2xl p-6">
        <div className="flex items-center justify-center h-64">
          <p className="text-gray-500">Chargement...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto max-w-2xl p-3 sm:p-6">
      <Button variant="ghost" size="sm" onClick={() => navigate("/development/projets")} className="mb-3 sm:mb-4">
        <ArrowLeft className="h-4 w-4 mr-2" />
        Retour aux projets
      </Button>

      <ProjectFormComponent
        initialData={initialData}
        edit={true}
        isCreation={!isEditing}
        onSubmit={handleSubmit}
        onCancel={() => navigate("/development/projets")}
      />
    </div>
  );
}
