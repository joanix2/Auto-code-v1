import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { OntologyGraph } from "@/types/ontology";
import { ontologyService } from "@/services/ontologyService";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Network, Plus, Loader2 } from "lucide-react";

export function Ontologies() {
  const navigate = useNavigate();
  const [ontologies, setOntologies] = useState<OntologyGraph[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => { ontologyService.getAll().then(setOntologies).catch(() => {}).finally(() => setLoading(false)); }, []);

  if (loading) return <div className="p-6 flex justify-center"><Loader2 className="h-6 w-6 animate-spin" /></div>;

  return (
    <div className="p-6">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-3xl font-bold">Ontologies</h1>
          <p className="text-muted-foreground mt-1">Gérez vos ontologies Open World</p>
        </div>
        <Button variant="outline" onClick={async () => {
          const name = prompt("Nom de l'ontologie :");
          if (name) {
            const created = await ontologyService.create({ name });
            setOntologies((prev) => [...prev, created]);
          }
        }}>
          <Plus className="h-4 w-4 mr-1" /> Nouvelle
        </Button>
      </div>
      {ontologies.length === 0 ? (
        <div className="border-2 border-dashed border-gray-300 rounded-lg p-12 text-center text-gray-400">
          <Network className="h-12 w-12 mx-auto mb-4 opacity-50" />
          <p className="text-lg font-medium">Aucune ontologie</p>
          <p className="text-sm mt-1">Créez votre première ontologie</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {ontologies.map((onto) => (
            <Card key={onto.id} className="cursor-pointer hover:shadow-md transition-shadow" onClick={() => navigate(`/development/ontologies/${onto.id}`)}>
              <CardHeader>
                <CardTitle className="text-base flex items-center gap-2">
                  <Network className="h-4 w-4 text-primary" />
                  {onto.name}
                </CardTitle>
                {onto.description && <CardDescription>{onto.description}</CardDescription>}
              </CardHeader>
              <CardContent className="text-sm text-gray-500">
                {onto.node_count} nœuds · {onto.edge_count} liens
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
