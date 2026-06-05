import React, { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { OntologyGraph } from "@/types/ontology";
import { ontologyService } from "@/services/ontologyService";
import { OntologyGraphViewer } from "@/components/ontology/OntologyGraphViewer";
import { Button } from "@/components/ui/button";
import { ArrowLeft, Loader2 } from "lucide-react";

export function OntologyDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [ontology, setOntology] = useState<OntologyGraph | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!id) return;
    ontologyService.getById(id).then(setOntology).catch(() => {}).finally(() => setLoading(false));
  }, [id]);

  if (loading) return <div className="p-6 flex justify-center"><Loader2 className="h-6 w-6 animate-spin" /></div>;
  if (!ontology) return <div className="p-6"><p className="text-gray-500">Ontologie introuvable</p></div>;

  return (
    <div className="h-full flex flex-col">
      <div className="flex items-center gap-2 px-4 py-2 border-b bg-white flex-shrink-0">
        <Button variant="ghost" size="sm" onClick={() => navigate("/development/ontologies")}><ArrowLeft className="h-4 w-4" /></Button>
        <span className="font-semibold text-sm">{ontology.name}</span>
        <span className="text-xs text-gray-400 ml-auto">{ontology.node_count} nœuds · {ontology.edge_count} liens</span>
      </div>
      <div className="flex-1">
        <OntologyGraphViewer issues={[]} />
      </div>
    </div>
  );
}
