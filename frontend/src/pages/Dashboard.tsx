import React from "react";
import { useNavigate } from "react-router-dom";
import { FolderGit2, FileText, TrendingUp, Activity } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { useRepositories } from "@/hooks/useRepositories";
import { useIssues } from "@/hooks/useIssues";

interface StatCardProps {
  title: string;
  value: number;
  description: string;
  icon: React.ReactNode;
  onClick?: () => void;
}

function StatCard({ title, value, description, icon, onClick }: StatCardProps) {
  return (
    <Card className={cn("hover:shadow-lg transition-shadow", onClick && "cursor-pointer hover:border-primary")} onClick={onClick}>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium">{title}</CardTitle>
        {icon}
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-bold">{value}</div>
        <p className="text-xs text-muted-foreground">{description}</p>
      </CardContent>
    </Card>
  );
}

export function Dashboard() {
  const navigate = useNavigate();
  const { repositories, loading: loadingRepos } = useRepositories();
  const { issues, loading: loadingIssues } = useIssues();

  const stats = {
    repositories: repositories?.length || 0,
    issues: issues?.length || 0,
    openIssues: issues?.filter((issue) => issue.status === "open").length || 0,
    inProgressIssues: issues?.filter((issue) => issue.status === "in_progress").length || 0,
  };

  if (loadingRepos || loadingIssues) {
    return (
      <div className="min-h-[calc(100vh-73px)] flex items-center justify-center">
        <div className="text-lg">Chargement...</div>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Dashboard</h1>
        <p className="text-muted-foreground">Vue d'ensemble de vos projets et tâches</p>
      </div>

      {/* Stats Grid */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <StatCard
          title="Repositories"
          value={stats.repositories}
          description="Projets totaux"
          icon={<FolderGit2 className="h-4 w-4 text-muted-foreground" />}
          onClick={() => navigate("/development/repositories")}
        />

        <StatCard title="Issues" value={stats.issues} description="Tâches totales" icon={<FileText className="h-4 w-4 text-muted-foreground" />} onClick={() => navigate("/development/issues")} />

        <StatCard
          title="Issues ouvertes"
          value={stats.openIssues}
          description="En attente de traitement"
          icon={<Activity className="h-4 w-4 text-purple-500" />}
          onClick={() => navigate("/development/issues")}
        />

        <StatCard
          title="En cours"
          value={stats.inProgressIssues}
          description="Issues en développement"
          icon={<TrendingUp className="h-4 w-4 text-amber-500" />}
          onClick={() => navigate("/development/issues")}
        />
      </div>

      {/* Recent Activity Section (pour plus tard) */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-7">
        <Card className="col-span-4">
          <CardHeader>
            <CardTitle>Activité récente</CardTitle>
            <CardDescription>Vos dernières actions</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="text-sm text-muted-foreground text-center py-8">Aucune activité récente</div>
          </CardContent>
        </Card>

        <Card className="col-span-3">
          <CardHeader>
            <CardTitle>Statistiques</CardTitle>
            <CardDescription>Aperçu de la progression</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium">Taux de complétion</span>
                <span className="text-sm text-muted-foreground">{stats.issues > 0 ? Math.round(((stats.issues - stats.openIssues - stats.inProgressIssues) / stats.issues) * 100) : 0}%</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium">Issues par projet</span>
                <span className="text-sm text-muted-foreground">{stats.repositories > 0 ? Math.round((stats.issues / stats.repositories) * 10) / 10 : 0}</span>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

// Helper function (si pas déjà importé)
function cn(...classes: (string | boolean | undefined)[]) {
  return classes.filter(Boolean).join(" ");
}
