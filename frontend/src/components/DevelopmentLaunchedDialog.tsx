import { AlertDialog } from "@/components/AlertDialog";
import { CheckCircle2, Code2, GitBranch, PlayCircle, Sparkles } from "lucide-react";

interface DevelopmentLaunchedDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  status: string;
}

export function DevelopmentLaunchedDialog({ open, onOpenChange, status }: DevelopmentLaunchedDialogProps) {
  return (
    <AlertDialog open={open} onOpenChange={onOpenChange} title="Développement automatique lancé avec succès!" variant="success" icon={CheckCircle2} closeLabel="OK, compris">
      <div className="space-y-4">
        <div className="flex items-center gap-2 text-sm font-medium text-gray-700">
          <Sparkles className="h-4 w-4 text-yellow-500" />
          <span>
            Statut: <span className="text-blue-600 font-semibold">{status}</span>
          </span>
        </div>

        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <p className="font-semibold text-blue-900 mb-3">Le workflow LangGraph est en cours d'exécution :</p>
          <ul className="space-y-2 text-sm text-blue-800">
            <li className="flex items-start gap-2">
              <Code2 className="h-4 w-4 mt-0.5 flex-shrink-0" />
              <span>Analyse du ticket avec Claude Opus 4</span>
            </li>
            <li className="flex items-start gap-2">
              <PlayCircle className="h-4 w-4 mt-0.5 flex-shrink-0" />
              <span>Génération et application des modifications</span>
            </li>
            <li className="flex items-start gap-2">
              <GitBranch className="h-4 w-4 mt-0.5 flex-shrink-0" />
              <span>Commit automatique sur une nouvelle branche</span>
            </li>
            <li className="flex items-start gap-2">
              <CheckCircle2 className="h-4 w-4 mt-0.5 flex-shrink-0" />
              <span>Exécution des tests CI/CD</span>
            </li>
          </ul>
        </div>

        <div className="bg-gray-50 border border-gray-200 rounded-lg p-3">
          <p className="text-sm text-gray-700">
            <span className="font-semibold">💡 Info:</span> Le statut du ticket sera mis à jour automatiquement. Connectez-vous au WebSocket pour suivre la progression en temps réel.
          </p>
        </div>
      </div>
    </AlertDialog>
  );
}
