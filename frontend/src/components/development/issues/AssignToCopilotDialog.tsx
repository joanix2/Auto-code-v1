/**
 * AssignToCopilotDialog - Dialog for assigning issues to GitHub Copilot
 */
import React, { useState } from "react";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { Sparkles, AlertCircle } from "lucide-react";
import { Alert, AlertDescription } from "@/components/ui/alert";

interface AssignToCopilotDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onConfirm: (customInstructions: string) => void;
  issueName: string;
  loading?: boolean;
}

export function AssignToCopilotDialog({ open, onOpenChange, onConfirm, issueName, loading = false }: AssignToCopilotDialogProps) {
  const [instructions, setInstructions] = useState("");

  const handleConfirm = () => {
    onConfirm(instructions);
  };

  const handleCancel = () => {
    setInstructions("");
    onOpenChange(false);
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[525px]">
        <DialogHeader>
          <div className="flex items-center gap-2">
            <Sparkles className="h-5 w-5 text-purple-600" />
            <DialogTitle>Assigner à GitHub Copilot</DialogTitle>
          </div>
          <DialogDescription>GitHub Copilot va automatiquement créer une Pull Request pour résoudre cette issue.</DialogDescription>
        </DialogHeader>

        <div className="space-y-2 py-4">
          <Alert>
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>
              <strong>Issue :</strong> {issueName}
            </AlertDescription>
          </Alert>

          <div className="space-y-2">
            <Label htmlFor="instructions">Instructions personnalisées (optionnel)</Label>
            <Textarea
              id="instructions"
              placeholder="Ex: Utilise TypeScript strict mode, ajoute des tests unitaires..."
              value={instructions}
              onChange={(e) => setInstructions(e.target.value)}
              rows={4}
              disabled={loading}
            />
            <p className="text-sm text-muted-foreground">Copilot suivra ces instructions lors de la création de la PR.</p>
          </div>

          <Alert className="bg-purple-50 border-purple-200">
            <Sparkles className="h-4 w-4 text-purple-600" />
            <AlertDescription className="text-purple-900">
              <strong>Prochaines étapes :</strong>
              <ul className="list-disc list-inside mt-2 space-y-1 text-sm">
                <li>Copilot analyse l'issue et crée une branche</li>
                <li>Le code est généré automatiquement</li>
                <li>Une Pull Request est ouverte sur GitHub</li>
                <li>Vous recevrez une notification GitHub</li>
              </ul>
            </AlertDescription>
          </Alert>
        </div>

        <DialogFooter className="gap-2">
          <Button variant="outline" onClick={handleCancel} disabled={loading}>
            Annuler
          </Button>
          <Button onClick={handleConfirm} disabled={loading} className="bg-purple-600 hover:bg-purple-700">
            {loading ? (
              <>
                <span className="animate-spin mr-2">⏳</span>
                Assignation en cours...
              </>
            ) : (
              <>
                <Sparkles className="h-4 w-4 mr-2" />
                Assigner à Copilot
              </>
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
