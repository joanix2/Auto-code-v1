import React, { useState, useEffect } from "react";
import { useParams, useNavigate, useSearchParams } from "react-router-dom";
import { Network, Layers, GitBranch, BarChart3, Plus, FolderKanban, Loader2 } from "lucide-react";
import { useProjects } from "@/hooks/useProjects";
import { Project } from "@/types/project";
import { IssueList } from "@/components/development/issues/IssueList";
import { useIssues } from "@/hooks/useIssues";
import { IssueStatusFilter } from "@/components/development/issues/IssueStatusFilter";
import { IssueStatus } from "@/types/issue";
import { Button } from "@/components/ui/button";
import { OntologyGraphViewer } from "@/components/ontology/OntologyGraphViewer";
import { ArchitectureGraphViewer } from "@/components/architecture/ArchitectureGraphViewer";

export function ProjectDetails() {
  const { projectId } = useParams<{ projectId: string }>();
  const navigate = useNavigate();
  const { getProject } = useProjects();
  const [project, setProject] = useState<Project | null>(null);
  const [loading, setLoading] = useState(true);
  const [searchParams] = useSearchParams();
  const isGraphTab = (searchParams.get("tab") || "tickets") === "ontologie" || (searchParams.get("tab") || "tickets") === "architecture";

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
      <div className="p-6">
        <div className="flex items-center justify-center h-64">
          <p className="text-gray-500">Chargement...</p>
        </div>
      </div>
    );
  }

  if (!project) {
    return (
      <div className="p-6">
        <div className="flex items-center justify-center h-64">
          <p className="text-gray-500">Projet introuvable</p>
        </div>
      </div>
    );
  }

  return (
    <div className={isGraphTab ? "absolute inset-0" : "pb-20 md:pb-6"}>
      {!isGraphTab && (
        <div className="px-3 sm:px-6 pt-3 sm:pt-6 pb-2 flex-shrink-0">
          <h1 className="text-xl sm:text-2xl font-bold text-gray-900">{project.name}</h1>
          {project.description && <p className="mt-0.5 text-sm text-gray-500">{project.description}</p>}
        </div>
      )}
      <ProjectTabContent projectId={projectId!} />
    </div>
  );
}

function ProjectTabContent({ projectId }: { projectId: string }) {
  const [searchParams] = useSearchParams();
  const activeTab = searchParams.get("tab") || "tickets";
  const isGraphTab = activeTab === "ontologie" || activeTab === "architecture";

  const content = (() => {
    switch (activeTab) {
      case "tickets":
        return <ProjectTickets projectId={projectId} />;
      case "ontologie":
        return <ProjectOntologie />;
      case "architecture":
        return <ProjectArchitecture />;
      case "deploiement":
        return <ProjectDeploiement />;
      case "monitoring":
        return <ProjectMonitoring />;
      default:
        return <ProjectTickets projectId={projectId} />;
    }
  })();

  if (isGraphTab) return content;
  return <div className="overflow-y-auto">{content}</div>;
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
    <div className="p-3 sm:p-6">
      <IssueList
        items={filteredIssues}
        loading={loading}
        onDelete={(id) => deleteIssue(id)}
        createUrl={`/development/issues/new?project_id=${projectId}`}
        renderBeforeCards={<IssueStatusFilter selectedStatus={selectedStatus} onStatusChange={setSelectedStatus} counts={statusCounts} />}
      />
    </div>
  );
}

function ProjectOntologie() {
  const { issues } = useIssues();
  return <OntologyGraphViewer issues={issues} />;
}

function ProjectArchitecture() {
  return <ArchitectureGraphViewer />;
}

function ProjectDeploiement() {
  return (
    <div className="p-3 sm:p-6">
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

function ProjectMonitoring() {
  return (
    <div className="p-3 sm:p-6">
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
