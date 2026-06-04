import React, { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Button } from "@/components/ui/button";
import { ArrowLeft, Ticket, GitBranch, BarChart3, Network, Layers } from "lucide-react";
import { useProjects } from "@/hooks/useProjects";
import { Project } from "@/types/project";
import { IssueList } from "@/components/development/issues/IssueList";
import { useIssues } from "@/hooks/useIssues";
import { IssueStatusFilter } from "@/components/development/issues/IssueStatusFilter";
import { IssueStatus } from "@/types/issue";
import { Issue } from "@/types";

export function ProjectDetails() {
  const { projectId } = useParams<{ projectId: string }>();
  const navigate = useNavigate();
  const { getProject } = useProjects();
  const [project, setProject] = useState<Project | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (projectId) {
      getProject(projectId)
        .then(setProject)
        .catch(() => navigate("/development/projets"))
        .finally(() => setLoading(false));
    }
  }, [projectId, getProject, navigate]);

  if (loading) {
    return (
      <div className="container mx-auto max-w-7xl p-6">
        <div className="flex items-center justify-center h-64">
          <p className="text-gray-500">Chargement...</p>
        </div>
      </div>
    );
  }

  if (!project) {
    return (
      <div className="container mx-auto max-w-7xl p-6">
        <div className="flex items-center justify-center h-64">
          <p className="text-gray-500">Projet introuvable</p>
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto max-w-7xl p-3 sm:p-6">
      <Button variant="ghost" size="sm" onClick={() => navigate("/development/projets")} className="mb-3 sm:mb-4">
        <ArrowLeft className="h-4 w-4 mr-2" />
        Retour aux projets
      </Button>

      <div className="mb-6">
        <h1 className="text-2xl sm:text-3xl font-bold text-gray-900">{project.name}</h1>
        {project.description && <p className="mt-1 text-sm text-gray-600">{project.description}</p>}
      </div>

      <Tabs defaultValue="tickets" className="w-full">
        <TabsList className="w-full justify-start border-b rounded-none h-auto p-0 bg-transparent">
          <TabsTrigger value="tickets" className="rounded-none border-b-2 border-transparent data-[state=active]:border-primary data-[state=active]:bg-transparent px-4 py-3">
            <Ticket className="h-4 w-4 mr-2" />
            Tickets
          </TabsTrigger>
          <TabsTrigger value="ontologie" className="rounded-none border-b-2 border-transparent data-[state=active]:border-primary data-[state=active]:bg-transparent px-4 py-3">
            <Network className="h-4 w-4 mr-2" />
            Ontologie
          </TabsTrigger>
          <TabsTrigger value="architecture" className="rounded-none border-b-2 border-transparent data-[state=active]:border-primary data-[state=active]:bg-transparent px-4 py-3">
            <Layers className="h-4 w-4 mr-2" />
            Architecture
          </TabsTrigger>
          <TabsTrigger value="deploiement" className="rounded-none border-b-2 border-transparent data-[state=active]:border-primary data-[state=active]:bg-transparent px-4 py-3">
            <GitBranch className="h-4 w-4 mr-2" />
            Déploiement
          </TabsTrigger>
          <TabsTrigger value="monitoring" className="rounded-none border-b-2 border-transparent data-[state=active]:border-primary data-[state=active]:bg-transparent px-4 py-3">
            <BarChart3 className="h-4 w-4 mr-2" />
            Monitoring
          </TabsTrigger>
        </TabsList>

        <TabsContent value="tickets" className="pt-6">
          <ProjectTickets projectId={projectId!} />
        </TabsContent>

        <TabsContent value="ontologie" className="pt-6">
          <ProjectOntologie projectId={projectId!} />
        </TabsContent>

        <TabsContent value="architecture" className="pt-6">
          <ProjectArchitecture projectId={projectId!} />
        </TabsContent>

        <TabsContent value="deploiement" className="pt-6">
          <ProjectDeploiement projectId={projectId!} />
        </TabsContent>

        <TabsContent value="monitoring" className="pt-6">
          <ProjectMonitoring projectId={projectId!} />
        </TabsContent>
      </Tabs>
    </div>
  );
}

function ProjectTickets({ projectId }: { projectId: string }) {
  const { issues, loading, loadIssues, deleteIssue, syncIssues } = useIssues();
  const [selectedStatus, setSelectedStatus] = useState<IssueStatus | "all">("all");

  const filteredIssues = selectedStatus === "all" ? issues : issues.filter((issue) => issue.status === selectedStatus);

  const statusCounts = {
    all: issues.length,
    open: issues.filter((i) => i.status === "open").length,
    in_progress: issues.filter((i) => i.status === "in_progress").length,
    review: issues.filter((i) => i.status === "review").length,
    closed: issues.filter((i) => i.status === "closed").length,
    cancelled: issues.filter((i) => i.status === "cancelled").length,
  };

  return (
    <div>
      <div className="mb-4 flex items-center justify-between">
        <div>
          <h2 className="text-xl font-semibold">Tickets du projet</h2>
          <p className="text-sm text-gray-500">Gérez les tickets associés à ce projet</p>
        </div>
      </div>
      <IssueStatusFilter selectedStatus={selectedStatus} onStatusChange={setSelectedStatus} counts={statusCounts} />
      <div className="mt-4">
        <IssueList
          items={filteredIssues}
          loading={loading}
          onDelete={(id) => deleteIssue(id)}
          createUrl={`/development/issues/new?project_id=${projectId}`}
        />
      </div>
    </div>
  );
}

function ProjectOntologie({ projectId }: { projectId: string }) {
  return (
    <div>
      <h2 className="text-xl font-semibold mb-2">Ontologie</h2>
      <p className="text-sm text-gray-500 mb-6">
        Gérez l'ontologie du projet. Les tickets seront lus pour créer des triplets qui généreront cette ontologie.
      </p>
      <div className="border-2 border-dashed border-gray-300 rounded-lg p-12 text-center text-gray-400">
        <Network className="h-12 w-12 mx-auto mb-4 opacity-50" />
        <p className="text-lg font-medium">Graphe d'ontologie</p>
        <p className="text-sm mt-1">Le visualiseur de graphe sera intégré ici</p>
      </div>
    </div>
  );
}

function ProjectArchitecture({ projectId }: { projectId: string }) {
  return (
    <div>
      <h2 className="text-xl font-semibold mb-2">Architecture</h2>
      <p className="text-sm text-gray-500 mb-6">Définissez les modèles d'architecture liés aux DSLs (métamodèles).</p>
      <div className="border-2 border-dashed border-gray-300 rounded-lg p-12 text-center text-gray-400">
        <Layers className="h-12 w-12 mx-auto mb-4 opacity-50" />
        <p className="text-lg font-medium">Modèles d'architecture</p>
        <p className="text-sm mt-1">Chaque modèle sera lié à un métamodèle (DSL)</p>
      </div>
    </div>
  );
}

function ProjectDeploiement({ projectId }: { projectId: string }) {
  return (
    <div>
      <h2 className="text-xl font-semibold mb-2">Déploiement</h2>
      <p className="text-sm text-gray-500 mb-6">Gérez les repositories Git, CI/CD et le déploiement du projet.</p>
      <div className="border-2 border-dashed border-gray-300 rounded-lg p-12 text-center text-gray-400">
        <GitBranch className="h-12 w-12 mx-auto mb-4 opacity-50" />
        <p className="text-lg font-medium">Déploiement continu</p>
        <p className="text-sm mt-1">CI/CD, gestion des repositories et environnements</p>
      </div>
    </div>
  );
}

function ProjectMonitoring({ projectId }: { projectId: string }) {
  return (
    <div>
      <h2 className="text-xl font-semibold mb-2">Monitoring</h2>
      <p className="text-sm text-gray-500 mb-6">Surveillez l'état de votre application et ses métriques.</p>
      <div className="border-2 border-dashed border-gray-300 rounded-lg p-12 text-center text-gray-400">
        <BarChart3 className="h-12 w-12 mx-auto mb-4 opacity-50" />
        <p className="text-lg font-medium">Monitoring</p>
        <p className="text-sm mt-1">Métriques, logs et état de l'application</p>
      </div>
    </div>
  );
}
