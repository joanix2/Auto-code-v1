import React from "react";
import { useNavigate } from "react-router-dom";
import { ProjectList } from "@/components/development/projects/ProjectList";
import { useProjects } from "@/hooks/useProjects";
import { useToast } from "@/components/ui/use-toast";

export function Projects() {
  const navigate = useNavigate();
  const { toast } = useToast();
  const { projects, loading, deleteProject, loadProjects } = useProjects();

  const handleDelete = async (id: string) => {
    try {
      await deleteProject(id);
      toast({
        title: "Projet supprimé",
        description: "Le projet a été supprimé avec succès.",
      });
    } catch {
      toast({
        title: "Erreur",
        description: "Impossible de supprimer le projet.",
        variant: "destructive",
      });
    }
  };

  const handleEdit = (id: string) => {
    navigate(`/development/projets/${id}/edit`);
  };

  const handleClick = (id: string) => {
    const project = projects.find((p) => p.id === id);
    navigate(`/development/projets/${id}`, { state: { projectName: project?.name } });
  };

  return (
    <div className="container mx-auto max-w-7xl p-3 sm:p-6">
      <div className="mb-4 sm:mb-6">
        <h1 className="text-2xl sm:text-3xl font-bold text-gray-900">Projets</h1>
        <p className="mt-1 sm:mt-2 text-sm text-gray-600">Gérez vos projets de développement</p>
      </div>

      <ProjectList
        items={projects}
        loading={loading}
        onClick={handleClick}
        onEdit={handleEdit}
        onDelete={handleDelete}
        onSync={loadProjects}
        createUrl="/development/projets/new"
      />
    </div>
  );
}
