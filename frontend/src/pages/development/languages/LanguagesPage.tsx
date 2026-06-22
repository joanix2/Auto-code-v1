import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { LanguageList } from "@/components/development/languages/LanguageList";
import { languageService, type Language } from "@/services/languageService";

export function LanguagesPage() {
  const navigate = useNavigate();
  const [languages, setLanguages] = useState<Language[]>([]);
  const [loading, setLoading] = useState(true);

  async function load() {
    try {
      setLoading(true);
      setLanguages(await languageService.list());
    } catch (err) {
      console.error("Failed to load languages", err);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { load(); }, []);

  async function handleDelete(id: string) {
    await languageService.delete(id);
    load();
  }

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold mb-6">Languages</h1>
      <LanguageList
        items={languages}
        loading={loading}
        onDelete={handleDelete}
        createUrl="/development/languages/new"
      />
    </div>
  );
}
