import React from "react";
import { useNavigate } from "react-router-dom";
import { MetamodelList } from "@/components/development/metamodels/MetamodelList";
import { useMetamodels } from "@/hooks/useMetamodels";
import { useToast } from "@/components/ui/use-toast";

export function Metamodels() {
  const navigate = useNavigate();
  const { toast } = useToast();
  const { metamodels, loading, deleteMetamodel, refetch } = useMetamodels();

  const handleDelete = async (id: string) => {
    try {
      await deleteMetamodel(id);
      toast({
        title: "Métamodèle supprimé",
        description: "Le métamodèle a été supprimé avec succès.",
      });
    } catch (error) {
      toast({
        title: "Erreur",
        description: "Impossible de supprimer le métamodèle.",
        variant: "destructive",
      });
    }
  };

  const handleEdit = (id: string) => {
    navigate(`/development/metamodeles/${id}/edit`);
  };

  const handleClick = (id: string) => {
    navigate(`/development/metamodeles/${id}`);
  };

  return (
    <div className="p-6">
      <div className="mb-6">
        <h1 className="text-3xl font-bold">Métamodèles</h1>
        <p className="text-muted-foreground mt-2">Gérez vos métamodèles MDE (Model-Driven Engineering)</p>
      </div>

      <MetamodelList items={metamodels} onDelete={handleDelete} onEdit={handleEdit} onClick={handleClick} loading={loading} createUrl="/development/metamodeles/new" showSync={false} />
    </div>
  );
}
