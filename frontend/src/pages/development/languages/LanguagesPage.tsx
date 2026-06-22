/**
 * Languages Page — list all rewriting-logic languages.
 */

import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Plus, FileText, Trash2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { languageService, type Language } from "@/services/languageService";

export function LanguagesPage() {
  const [languages, setLanguages] = useState<Language[]>([]);
  const [loading, setLoading] = useState(true);
  const [newName, setNewName] = useState("");

  async function load() {
    try {
      setLoading(true);
      const data = await languageService.list();
      setLanguages(data);
    } catch (err) {
      console.error("Failed to load languages", err);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { load(); }, []);

  async function handleCreate() {
    if (!newName.trim()) return;
    await languageService.create({ name: newName.trim() });
    setNewName("");
    load();
  }

  async function handleDelete(id: string) {
    await languageService.delete(id);
    load();
  }

  if (loading) return <div className="p-6">Chargement...</div>;

  return (
    <div className="p-6 max-w-2xl mx-auto">
      <h1 className="text-2xl font-bold mb-6">Languages</h1>

      {/* Create form */}
      <div className="flex gap-2 mb-6">
        <input
          className="flex-1 px-3 py-2 border rounded"
          placeholder="New language name..."
          value={newName}
          onChange={(e) => setNewName(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && handleCreate()}
        />
        <Button onClick={handleCreate} disabled={!newName.trim()}>
          <Plus className="w-4 h-4 mr-1" /> Create
        </Button>
      </div>

      {/* Language list */}
      <div className="space-y-2">
        {languages.map((lang) => (
          <div
            key={lang.id}
            className="flex items-center justify-between p-3 border rounded hover:bg-gray-50"
          >
            <Link to={`/development/languages/${lang.id}`} className="flex items-center gap-3 flex-1">
              <FileText className="w-5 h-5 text-blue-500" />
              <div>
                <div className="font-medium">{lang.name}</div>
                <div className="text-sm text-gray-500">
                  {lang.node_count} nodes, {lang.edge_count} edges
                </div>
              </div>
            </Link>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => handleDelete(lang.id)}
              disabled={languages.length <= 1}
            >
              <Trash2 className="w-4 h-4 text-red-400" />
            </Button>
          </div>
        ))}
      </div>
    </div>
  );
}
