import React, { useEffect, useState, useCallback } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { Metamodel } from "@/types/metamodel";
import { metamodelService } from "@/services/metamodelService";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ArrowLeft, Edit, Trash2, CheckCircle, Ban, Database } from "lucide-react";
import { useToast } from "@/components/ui/use-toast";

export function MetamodelDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { toast } = useToast();
  const [metamodel, setMetamodel] = useState<Metamodel | null>(null);
  const [loading, setLoading] = useState(true);

  const loadMetamodel = useCallback(async () => {
    if (!id) return;

    try {
      setLoading(true);
      const data = await metamodelService.getById(id);
      setMetamodel(data);
    } catch (error) {
      toast({
        title: "Erreur",
        description: "Impossible de charger le métamodèle.",
        variant: "destructive",
      });
      navigate("/development/metamodeles");
    } finally {
      setLoading(false);
    }
  }, [id, toast, navigate]);

  useEffect(() => {
    loadMetamodel();
  }, [loadMetamodel]);

  const handleDelete = async () => {
    if (!metamodel || !confirm("Êtes-vous sûr de vouloir supprimer ce métamodèle ?")) return;

    try {
      await metamodelService.delete(metamodel.id);
      toast({
        title: "Métamodèle supprimé",
        description: "Le métamodèle a été supprimé avec succès.",
      });
      navigate("/development/metamodeles");
    } catch (error) {
      toast({
        title: "Erreur",
        description: "Impossible de supprimer le métamodèle.",
        variant: "destructive",
      });
    }
  };

  const handleValidate = async () => {
    if (!metamodel) return;

    try {
      await metamodelService.validate(metamodel.id);
      toast({
        title: "Métamodèle validé",
        description: "Le métamodèle a été validé avec succès.",
      });
      loadMetamodel();
    } catch (error) {
      toast({
        title: "Erreur",
        description: "Impossible de valider le métamodèle.",
        variant: "destructive",
      });
    }
  };

  const handleDeprecate = async () => {
    if (!metamodel || !confirm("Êtes-vous sûr de vouloir marquer ce métamodèle comme obsolète ?")) return;

    try {
      await metamodelService.deprecate(metamodel.id);
      toast({
        title: "Métamodèle obsolète",
        description: "Le métamodèle a été marqué comme obsolète.",
      });
      loadMetamodel();
    } catch (error) {
      toast({
        title: "Erreur",
        description: "Impossible de marquer le métamodèle comme obsolète.",
        variant: "destructive",
      });
    }
  };

  const getStatusBadge = (status?: string) => {
    switch (status) {
      case "draft":
        return <Badge variant="secondary">Brouillon</Badge>;
      case "validated":
        return <Badge variant="default">Validé</Badge>;
      case "deprecated":
        return <Badge variant="destructive">Obsolète</Badge>;
      default:
        return null;
    }
  };

  const formatDate = (dateString?: string) => {
    if (!dateString) return "N/A";
    return new Date(dateString).toLocaleDateString("fr-FR", {
      year: "numeric",
      month: "long",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  if (loading) {
    return (
      <div className="p-6">
        <div className="animate-pulse">
          <div className="h-8 bg-gray-200 rounded w-1/4 mb-4"></div>
          <div className="h-64 bg-gray-200 rounded"></div>
        </div>
      </div>
    );
  }

  if (!metamodel) {
    return (
      <div className="p-6">
        <p>Métamodèle non trouvé</p>
      </div>
    );
  }

  return (
    <div className="p-6">
      {/* Header */}
      <div className="mb-6 flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Button variant="ghost" size="icon" onClick={() => navigate("/development/metamodeles")}>
            <ArrowLeft className="h-5 w-5" />
          </Button>
          <div>
            <h1 className="text-3xl font-bold">{metamodel.name}</h1>
            <p className="text-muted-foreground">Version {metamodel.version}</p>
          </div>
        </div>
        <div className="flex gap-2">
          {metamodel.status === "draft" && (
            <Button onClick={handleValidate} variant="default">
              <CheckCircle className="h-4 w-4 mr-2" />
              Valider
            </Button>
          )}
          {metamodel.status === "validated" && (
            <Button onClick={handleDeprecate} variant="outline">
              <Ban className="h-4 w-4 mr-2" />
              Marquer obsolète
            </Button>
          )}
          <Button onClick={() => navigate(`/development/metamodeles/${metamodel.id}/edit`)} variant="outline">
            <Edit className="h-4 w-4 mr-2" />
            Modifier
          </Button>
          <Button onClick={handleDelete} variant="destructive">
            <Trash2 className="h-4 w-4 mr-2" />
            Supprimer
          </Button>
        </div>
      </div>

      {/* Main Content */}
      <div className="grid gap-6">
        {/* Info Card */}
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <Database className="h-8 w-8 text-primary" />
                <div>
                  <CardTitle>{metamodel.name}</CardTitle>
                  <CardDescription>Métamodèle MDE</CardDescription>
                </div>
              </div>
              {getStatusBadge(metamodel.status)}
            </div>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {metamodel.description && (
                <div>
                  <h3 className="font-semibold mb-2">Description</h3>
                  <p className="text-muted-foreground">{metamodel.description}</p>
                </div>
              )}

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <h3 className="font-semibold mb-2">Concepts</h3>
                  <p className="text-2xl font-bold text-primary">{metamodel.concepts}</p>
                </div>
                <div>
                  <h3 className="font-semibold mb-2">Relations</h3>
                  <p className="text-2xl font-bold text-primary">{metamodel.relations}</p>
                </div>
              </div>

              {metamodel.author && (
                <div>
                  <h3 className="font-semibold mb-2">Auteur</h3>
                  <p className="text-muted-foreground">{metamodel.author}</p>
                </div>
              )}

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <h3 className="font-semibold mb-2">Créé le</h3>
                  <p className="text-muted-foreground">{formatDate(metamodel.created_at)}</p>
                </div>
                {metamodel.updated_at && (
                  <div>
                    <h3 className="font-semibold mb-2">Modifié le</h3>
                    <p className="text-muted-foreground">{formatDate(metamodel.updated_at)}</p>
                  </div>
                )}
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Future: Concepts & Relations Cards */}
        <Card>
          <CardHeader>
            <CardTitle>Concepts et Relations</CardTitle>
            <CardDescription>Visualisation du métamodèle</CardDescription>
          </CardHeader>
          <CardContent>
            <p className="text-muted-foreground text-center py-8">Visualisation à venir...</p>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
