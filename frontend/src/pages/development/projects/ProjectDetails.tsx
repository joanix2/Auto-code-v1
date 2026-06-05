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
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { architectureService, ArchitectureGraph } from "@/services/architectureService";
import { GraphViewer, GraphData } from "@/components/common/GraphViewer";
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
    <div className={isGraphTab ? "h-full flex flex-col" : "pb-20 md:pb-6"}>
      <div className="px-3 sm:px-6 pt-3 sm:pt-6 pb-2 flex-shrink-0">
        <h1 className="text-xl sm:text-2xl font-bold text-gray-900">{project.name}</h1>
        {project.description && <p className="mt-0.5 text-sm text-gray-500">{project.description}</p>}
      </div>
      <div className={isGraphTab ? "flex-1 relative" : ""}>
        <ProjectTabContent projectId={projectId!} />
      </div>
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

  if (isGraphTab) {
    return <div className="absolute inset-0">{content}</div>;
  }
  return content;
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
  return (
    <div className="h-full flex flex-col">
      <div className="p-3 sm:px-6 pt-3 sm:pt-4 pb-2 flex-shrink-0">
        <h2 className="text-lg font-semibold">Ontologie (Open World)</h2>
        <p className="text-sm text-gray-500">Graphe d'ontologie généré à partir des tickets du projet.</p>
      </div>
      <div className="flex-1 border-t overflow-hidden">
        <OntologyGraphViewer issues={issues} />
      </div>
    </div>
  );
}

function ProjectArchitecture() {
  const [archs, setArchs] = useState<ArchitectureGraph[]>([]);
  const [loading, setLoading] = useState(true);
  const [selected, setSelected] = useState<ArchitectureGraph | null>(null);

  useEffect(() => {
    architectureService.getAll().then(setArchs).catch(() => {}).finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="p-6 flex justify-center"><Loader2 className="h-6 w-6 animate-spin" /></div>;

  if (selected) {
    return (
      <div className="h-full flex flex-col">
        <div className="flex items-center justify-between p-3 sm:px-6 pt-3 sm:pt-4 pb-2 flex-shrink-0">
          <Button variant="ghost" size="sm" onClick={() => setSelected(null)}>← Retour</Button>
          <div className="text-xs text-gray-500">
            <span className="font-medium">{selected.name}</span>
            {selected.parent_dsl_id && <span className="ml-2">DSL: {selected.parent_dsl_id}</span>}
          </div>
        </div>
        <div className="flex-1 border-t overflow-hidden">
          <ArchitectureGraphViewer architectureName={selected.name} />
        </div>
      </div>
    );
  }

  return (
    <div className="p-3 sm:p-6">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h2 className="text-xl font-semibold">Architecture</h2>
          <p className="text-sm text-gray-500">Modèles d'architecture liés aux DSLs</p>
        </div>
        <Button variant="outline" size="sm" onClick={async () => {
          const name = prompt("Nom du modèle d'architecture :");
          if (name) {
            const created = await architectureService.create({ name });
            setArchs((prev) => [...prev, created]);
          }
        }}>
          <Plus className="h-4 w-4 mr-1" /> Nouveau
        </Button>
      </div>

      {archs.length === 0 ? (
        <div className="border-2 border-dashed border-gray-300 rounded-lg p-12 text-center text-gray-400">
          <Layers className="h-12 w-12 mx-auto mb-4 opacity-50" />
          <p className="text-lg font-medium">Aucun modèle d'architecture</p>
          <p className="text-sm mt-1">Créez un modèle d'architecture lié à un DSL</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {archs.map((arch) => (
            <Card key={arch.id} className="cursor-pointer hover:shadow-md transition-shadow" onClick={() => setSelected(arch)}>
              <CardHeader>
                <CardTitle className="text-base">{arch.name}</CardTitle>
                {arch.description && <CardDescription>{arch.description}</CardDescription>}
              </CardHeader>
              <CardContent className="text-sm text-gray-500">
                {arch.node_count} nœuds · {arch.edge_count} liens
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
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
