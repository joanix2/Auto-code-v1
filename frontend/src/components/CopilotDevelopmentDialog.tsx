import { useState } from "react";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Loader2, Sparkles, AlertCircle, CheckCircle2, ExternalLink } from "lucide-react";
import { apiClient } from "@/services/api.service";
import type { Ticket } from "@/types";

interface CopilotDevelopmentDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  ticket: Ticket;
  onSuccess?: () => void;
}

export function CopilotDevelopmentDialog({ open, onOpenChange, ticket, onSuccess }: CopilotDevelopmentDialogProps) {
  const [customInstructions, setCustomInstructions] = useState("");
  const [baseBranch, setBaseBranch] = useState("main");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<{
    message: string;
    issueUrl?: string;
    issueNumber?: number;
  } | null>(null);

  const handleStartDevelopment = async () => {
    try {
      setLoading(true);
      setError(null);
      setSuccess(null);

      const response = await apiClient.startCopilotDevelopment({
        ticket_id: ticket.id,
        custom_instructions: customInstructions || undefined,
        base_branch: baseBranch,
      });

      setSuccess({
        message: response.message,
        issueUrl: response.issue_url,
        issueNumber: response.issue_number,
      });

      // Wait a bit before calling onSuccess to show the success message
      setTimeout(() => {
        onSuccess?.();
        onOpenChange(false);
      }, 2000);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Une erreur s'est produite");
    } finally {
      setLoading(false);
    }
  };

  const handleClose = () => {
    if (!loading) {
      setCustomInstructions("");
      setBaseBranch("main");
      setError(null);
      setSuccess(null);
      onOpenChange(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Sparkles className="h-5 w-5 text-purple-600" />
            Développement automatique avec GitHub Copilot
          </DialogTitle>
          <DialogDescription>GitHub Copilot va travailler sur ce ticket et créer une Pull Request automatiquement.</DialogDescription>
        </DialogHeader>

        <div className="space-y-4 py-4">
          {/* Ticket Info */}
          <div className="rounded-lg border p-4 bg-slate-50 dark:bg-slate-900">
            <h3 className="font-semibold text-sm mb-2">Ticket à développer :</h3>
            <p className="font-medium">{ticket.title}</p>
            <p className="text-sm text-muted-foreground mt-1 line-clamp-2">{ticket.description}</p>
            <div className="flex gap-2 mt-2">
              <span className="text-xs px-2 py-1 rounded bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200">{ticket.ticket_type}</span>
              <span className="text-xs px-2 py-1 rounded bg-orange-100 dark:bg-orange-900 text-orange-800 dark:text-orange-200">{ticket.priority}</span>
            </div>
          </div>

          {/* Base Branch */}
          <div className="space-y-2">
            <Label htmlFor="baseBranch">Branche de base</Label>
            <Input id="baseBranch" value={baseBranch} onChange={(e) => setBaseBranch(e.target.value)} placeholder="main" disabled={loading || !!success} />
            <p className="text-xs text-muted-foreground">Copilot créera une nouvelle branche depuis cette branche et ouvrira une PR vers celle-ci.</p>
          </div>

          {/* Custom Instructions */}
          <div className="space-y-2">
            <Label htmlFor="instructions">Instructions personnalisées (optionnel)</Label>
            <Textarea
              id="instructions"
              value={customInstructions}
              onChange={(e) => setCustomInstructions(e.target.value)}
              placeholder="Exemple: Utiliser TypeScript strict, ajouter des tests unitaires, suivre les conventions de code existantes..."
              rows={4}
              disabled={loading || !!success}
            />
            <p className="text-xs text-muted-foreground">Ces instructions seront ajoutées au contexte du ticket pour guider Copilot.</p>
          </div>

          {/* Error Alert */}
          {error && (
            <Alert variant="destructive">
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>
                <p className="font-medium mb-2">{error}</p>
                {error.includes("Copilot") && error.includes("not enabled") && (
                  <div className="mt-3 text-sm space-y-2">
                    <p className="font-semibold">Pour activer GitHub Copilot Agent :</p>
                    <ol className="list-decimal list-inside space-y-1 ml-2">
                      <li>Assurez-vous d'avoir un abonnement GitHub Copilot actif</li>
                      <li>
                        Visitez{" "}
                        <a href="https://github.com/features/copilot" target="_blank" rel="noopener noreferrer" className="underline hover:no-underline">
                          github.com/features/copilot
                        </a>
                      </li>
                      <li>Activez la fonctionnalité "Copilot Agent" dans vos paramètres GitHub</li>
                    </ol>
                  </div>
                )}
              </AlertDescription>
            </Alert>
          )}

          {/* Success Alert */}
          {success && (
            <Alert className="border-green-500 bg-green-50 dark:bg-green-950">
              <CheckCircle2 className="h-4 w-4 text-green-600" />
              <AlertDescription className="text-green-600 dark:text-green-400">
                <p className="font-medium mb-2">{success.message}</p>
                {success.issueUrl && (
                  <a href={success.issueUrl} target="_blank" rel="noopener noreferrer" className="inline-flex items-center gap-1 text-sm underline hover:no-underline">
                    Voir l'issue #{success.issueNumber} sur GitHub
                    <ExternalLink className="h-3 w-3" />
                  </a>
                )}
              </AlertDescription>
            </Alert>
          )}

          {/* Info */}
          <div className="rounded-lg border p-4 bg-blue-50 dark:bg-blue-950 border-blue-200 dark:border-blue-800">
            <h4 className="font-semibold text-sm mb-2 flex items-center gap-2 text-blue-900 dark:text-blue-100">
              <Sparkles className="h-4 w-4" />
              Comment ça marche ?
            </h4>
            <ul className="text-sm text-blue-800 dark:text-blue-200 space-y-1">
              <li>• Copilot va analyser le ticket et créer une issue GitHub (ou utiliser l'existante)</li>
              <li>• Il va créer une branche de travail et implémenter les changements</li>
              <li>• Une Pull Request sera automatiquement créée et vous serez ajouté comme reviewer</li>
              <li>• Vous recevrez une notification GitHub quand la PR sera prête</li>
            </ul>
          </div>
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={handleClose} disabled={loading}>
            Annuler
          </Button>
          <Button onClick={handleStartDevelopment} disabled={loading || !!success} className="bg-purple-600 hover:bg-purple-700">
            {loading ? (
              <>
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                Démarrage en cours...
              </>
            ) : success ? (
              <>
                <CheckCircle2 className="h-4 w-4 mr-2" />
                Démarré !
              </>
            ) : (
              <>
                <Sparkles className="h-4 w-4 mr-2" />
                Lancer le développement
              </>
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
