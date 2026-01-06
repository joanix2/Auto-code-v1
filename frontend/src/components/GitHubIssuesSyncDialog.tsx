import { useState, useEffect } from "react";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Loader2, Github, CheckCircle2, XCircle, Download, AlertCircle } from "lucide-react";
import { apiClient, GitHubIssueWithImportStatus } from "@/services/api.service";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";

interface GitHubIssuesSyncDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  repositoryId: string;
  repositoryName: string;
  onImportComplete?: () => void;
}

export function GitHubIssuesSyncDialog({ open, onOpenChange, repositoryId, repositoryName, onImportComplete }: GitHubIssuesSyncDialogProps) {
  const [loading, setLoading] = useState(true);
  const [issues, setIssues] = useState<GitHubIssueWithImportStatus[]>([]);
  const [filteredIssues, setFilteredIssues] = useState<GitHubIssueWithImportStatus[]>([]);
  const [importingIssues, setImportingIssues] = useState<Set<number>>(new Set());
  const [importingAll, setImportingAll] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [stats, setStats] = useState({ total: 0, imported: 0, notImported: 0 });
  const [selectedTab, setSelectedTab] = useState<"all" | "not-imported" | "imported">("not-imported");

  const loadIssues = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await apiClient.getGitHubIssues(repositoryId, "all");
      setIssues(response.issues);
      setStats({
        total: response.total,
        imported: response.imported,
        notImported: response.not_imported,
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erreur lors du chargement des issues");
    } finally {
      setLoading(false);
    }
  };

  // Charger les issues depuis GitHub
  useEffect(() => {
    if (open) {
      loadIssues();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open, repositoryId]);

  // Filtrer les issues selon l'onglet sélectionné
  useEffect(() => {
    switch (selectedTab) {
      case "not-imported":
        setFilteredIssues(issues.filter((i) => !i.is_imported));
        break;
      case "imported":
        setFilteredIssues(issues.filter((i) => i.is_imported));
        break;
      default:
        setFilteredIssues(issues);
    }
  }, [selectedTab, issues]);

  const handleImportIssue = async (issueNumber: number) => {
    try {
      setImportingIssues((prev) => new Set(prev).add(issueNumber));
      setError(null);
      setSuccess(null);

      const response = await apiClient.importGitHubIssue(repositoryId, issueNumber);
      setSuccess(`Issue #${issueNumber} importée avec succès !`);

      // Recharger les issues pour mettre à jour le statut
      await loadIssues();
      onImportComplete?.();
    } catch (err) {
      setError(err instanceof Error ? err.message : `Erreur lors de l'import de l'issue #${issueNumber}`);
    } finally {
      setImportingIssues((prev) => {
        const newSet = new Set(prev);
        newSet.delete(issueNumber);
        return newSet;
      });
    }
  };

  const handleImportAll = async () => {
    try {
      setImportingAll(true);
      setError(null);
      setSuccess(null);

      const response = await apiClient.importAllGitHubIssues(repositoryId, "open");

      const { summary } = response;
      setSuccess(`Import terminé: ${summary.imported} importées, ${summary.skipped} ignorées, ${summary.errors} erreurs`);

      // Recharger les issues
      await loadIssues();
      onImportComplete?.();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erreur lors de l'import en masse");
    } finally {
      setImportingAll(false);
    }
  };

  const getIssueTypeLabel = (labels: string[]): string | null => {
    if (labels.includes("bug")) return "bug";
    if (labels.includes("enhancement") || labels.includes("feature")) return "enhancement";
    if (labels.includes("documentation")) return "documentation";
    if (labels.includes("refactor")) return "refactor";
    return null;
  };

  const getIssuePriorityLabel = (labels: string[]): string | null => {
    const priorities = ["critical", "high", "medium", "low"];
    for (const priority of priorities) {
      if (labels.includes(priority) || labels.includes(`priority: ${priority}`)) {
        return priority;
      }
    }
    return null;
  };

  const getPriorityColor = (priority: string | null): "destructive" | "default" | "secondary" | "outline" => {
    switch (priority) {
      case "critical":
        return "destructive";
      case "high":
        return "destructive";
      case "medium":
        return "default";
      case "low":
        return "secondary";
      default:
        return "outline";
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-4xl max-h-[80vh] overflow-hidden flex flex-col">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Github className="h-5 w-5" />
            Synchroniser avec GitHub
          </DialogTitle>
          <DialogDescription>
            Importez les issues de <span className="font-semibold">{repositoryName}</span> comme tickets AutoCode
          </DialogDescription>
        </DialogHeader>

        {error && (
          <Alert variant="destructive">
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}

        {success && (
          <Alert className="border-green-500 bg-green-50 dark:bg-green-950">
            <CheckCircle2 className="h-4 w-4 text-green-600" />
            <AlertDescription className="text-green-600">{success}</AlertDescription>
          </Alert>
        )}

        {loading ? (
          <div className="flex items-center justify-center py-12">
            <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
          </div>
        ) : (
          <>
            <Tabs value={selectedTab} onValueChange={(v) => setSelectedTab(v as typeof selectedTab)} className="flex-1 flex flex-col">
              <TabsList className="grid w-full grid-cols-3">
                <TabsTrigger value="not-imported">À importer ({stats.notImported})</TabsTrigger>
                <TabsTrigger value="imported">Déjà importées ({stats.imported})</TabsTrigger>
                <TabsTrigger value="all">Toutes ({stats.total})</TabsTrigger>
              </TabsList>

              <TabsContent value={selectedTab} className="flex-1 overflow-y-auto mt-4 space-y-3">
                {filteredIssues.length === 0 ? (
                  <div className="text-center py-8 text-muted-foreground">
                    {selectedTab === "not-imported" ? "Aucune issue à importer" : selectedTab === "imported" ? "Aucune issue déjà importée" : "Aucune issue trouvée"}
                  </div>
                ) : (
                  filteredIssues.map((item) => {
                    const { issue, is_imported, ticket_id } = item;
                    const typeLabel = getIssueTypeLabel(issue.labels);
                    const priorityLabel = getIssuePriorityLabel(issue.labels);
                    const isImporting = importingIssues.has(issue.number);

                    return (
                      <Card key={issue.number}>
                        <CardHeader>
                          <div className="flex items-start justify-between gap-4">
                            <div className="flex-1">
                              <CardTitle className="text-base flex items-center gap-2">
                                <a href={issue.html_url} target="_blank" rel="noopener noreferrer" className="hover:underline flex items-center gap-1">
                                  <Github className="h-4 w-4" />#{issue.number}
                                </a>
                                {issue.title}
                              </CardTitle>
                              <CardDescription className="mt-1 flex items-center gap-2">
                                <span>Par {issue.user.login}</span>
                                <span>•</span>
                                <span>{new Date(issue.created_at).toLocaleDateString()}</span>
                                {issue.state === "closed" && (
                                  <>
                                    <span>•</span>
                                    <Badge variant="secondary" className="text-xs">
                                      Fermée
                                    </Badge>
                                  </>
                                )}
                              </CardDescription>
                            </div>

                            {is_imported ? (
                              <Badge variant="default" className="flex items-center gap-1">
                                <CheckCircle2 className="h-3 w-3" />
                                Importée
                              </Badge>
                            ) : (
                              <Button size="sm" onClick={() => handleImportIssue(issue.number)} disabled={isImporting || importingAll}>
                                {isImporting ? (
                                  <>
                                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                                    Import...
                                  </>
                                ) : (
                                  <>
                                    <Download className="h-4 w-4 mr-2" />
                                    Importer
                                  </>
                                )}
                              </Button>
                            )}
                          </div>
                        </CardHeader>
                        <CardContent>
                          <p className="text-sm text-muted-foreground line-clamp-2 mb-3">{issue.body || "Pas de description"}</p>
                          <div className="flex flex-wrap gap-1">
                            {typeLabel && <Badge variant="outline">{typeLabel}</Badge>}
                            {priorityLabel && <Badge variant={getPriorityColor(priorityLabel)}>{priorityLabel}</Badge>}
                            {issue.labels
                              .filter((l) => !["bug", "enhancement", "feature", "documentation", "refactor", "critical", "high", "medium", "low"].includes(l) && !l.startsWith("priority:"))
                              .map((label) => (
                                <Badge key={label} variant="secondary" className="text-xs">
                                  {label}
                                </Badge>
                              ))}
                          </div>
                        </CardContent>
                      </Card>
                    );
                  })
                )}
              </TabsContent>
            </Tabs>
          </>
        )}

        <DialogFooter className="flex items-center justify-between">
          <div className="text-sm text-muted-foreground">
            {stats.notImported > 0 && (
              <span>
                {stats.notImported} issue{stats.notImported > 1 ? "s" : ""} à importer
              </span>
            )}
          </div>
          <div className="flex gap-2">
            <Button variant="outline" onClick={() => onOpenChange(false)}>
              Fermer
            </Button>
            {stats.notImported > 0 && (
              <Button onClick={handleImportAll} disabled={importingAll || loading}>
                {importingAll ? (
                  <>
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    Import en cours...
                  </>
                ) : (
                  <>
                    <Download className="h-4 w-4 mr-2" />
                    Importer tout ({stats.notImported})
                  </>
                )}
              </Button>
            )}
          </div>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
