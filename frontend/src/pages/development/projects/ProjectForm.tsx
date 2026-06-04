import React, { useState, useEffect } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { ArrowLeft, Save } from "lucide-react";
import { useProjects } from "@/hooks/useProjects";
import { useToast } from "@/components/ui/use-toast";

export function ProjectForm() {
  const { projectId } = useParams<{ projectId?: string }>();
  const navigate = useNavigate();
  const { toast } = useToast();
  const { getProject, createProject, updateProject } = useProjects();
  const isEditing = !!projectId;

  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [saving, setSaving] = useState(false);
  const [loading, setLoading] = useState(isEditing);

  useEffect(() => {
    if (isEditing && projectId) {
      getProject(projectId)
        .then((project) => {
          setName(project.name);
          setDescription(project.description || "");
        })
        .catch(() => {
          toast({
            title: "Erreur",
            description: "Impossible de charger le projet.",
            variant: "destructive",
          });
          navigate("/development/projets");
        })
        .finally(() => setLoading(false));
    }
  }, [isEditing, projectId, getProject, navigate, toast]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) {
      toast({
        title: "Validation",
        description: "Le nom du projet est requis.",
        variant: "destructive",
      });
      return;
    }

    setSaving(true);
    try {
      if (isEditing && projectId) {
        await updateProject(projectId, { name, description });
        toast({
          title: "Projet mis à jour",
          description: "Le projet a été modifié avec succès.",
        });
      } else {
        const project = await createProject({ name, description });
        toast({
          title: "Projet créé",
          description: "Le projet a été créé avec succès.",
        });
        navigate(`/development/projets/${project.id}`);
        return;
      }
      navigate(`/development/projets/${projectId}`);
    } catch {
      toast({
        title: "Erreur",
        description: isEditing ? "Impossible de modifier le projet." : "Impossible de créer le projet.",
        variant: "destructive",
      });
    } finally {
      setSaving(false);
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

      <div className="mb-6">
        <h1 className="text-2xl sm:text-3xl font-bold text-gray-900">{isEditing ? "Modifier le projet" : "Nouveau projet"}</h1>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        <div className="space-y-2">
          <Label htmlFor="name">Nom du projet</Label>
          <Input id="name" value={name} onChange={(e) => setName(e.target.value)} placeholder="Mon projet" required />
        </div>

        <div className="space-y-2">
          <Label htmlFor="description">Description</Label>
          <Textarea id="description" value={description} onChange={(e) => setDescription(e.target.value)} placeholder="Description du projet..." rows={4} />
        </div>

        <div className="flex gap-3">
          <Button type="submit" disabled={saving}>
            <Save className="h-4 w-4 mr-2" />
            {saving ? "Enregistrement..." : isEditing ? "Enregistrer" : "Créer le projet"}
          </Button>
          <Button type="button" variant="outline" onClick={() => navigate("/development/projets")}>
            Annuler
          </Button>
        </div>
      </form>
    </div>
  );
}
