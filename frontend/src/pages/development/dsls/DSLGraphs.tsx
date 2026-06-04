import React from "react";
import { useNavigate } from "react-router-dom";
import { DSLList } from "@/components/development/dsls/DSLList";
import { useDsl } from "@/hooks/useDsl";
import { useToast } from "@/components/ui/use-toast";

export function DSLGraphs() {
  const navigate = useNavigate();
  const { toast } = useToast();
  const { dsls, loading, deleteDSLGraph, refetch } = useDsl();

  const handleDelete = async (id: string) => {
    try {
      await deleteDSLGraph(id);
      toast({
        title: "Métamodèle supprimé",
        description: "Le DSL a été supprimé avec succès.",
      });
    } catch (error) {
      toast({
        title: "Erreur",
        description: "Impossible de supprimer le DSL.",
        variant: "destructive",
      });
    }
  };

  const handleEdit = (id: string) => {
    navigate(`/development/dsles/${id}/edit`);
  };

  const handleClick = (id: string) => {
    navigate(`/development/dsles/${id}`);
  };

  return (
    <div className="p-6">
      <div className="mb-6">
        <h1 className="text-3xl font-bold">Métamodèles</h1>
        <p className="text-muted-foreground mt-2">Gérez vos DSLs MDE (Model-Driven Engineering)</p>
      </div>

      <DSLList items={dsls} onDelete={handleDelete} onEdit={handleEdit} onClick={handleClick} loading={loading} createUrl="/development/dsles/new" showSync={false} />
    </div>
  );
}
