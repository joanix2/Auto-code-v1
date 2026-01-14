import React from "react";
import { Link } from "react-router-dom";
import { Home, ArrowLeft } from "lucide-react";
import { Button } from "@/components/ui/button";

export function NotFound() {
  return (
    <div className="min-h-[calc(100vh-73px)] flex items-center justify-center bg-gray-50">
      <div className="text-center px-4">
        {/* 404 Large */}
        <h1 className="text-9xl font-bold text-primary mb-4">404</h1>

        {/* Message */}
        <h2 className="text-3xl font-semibold text-gray-800 mb-4">Page non trouvée</h2>

        <p className="text-gray-600 mb-8 max-w-md mx-auto">Désolé, la page que vous recherchez n'existe pas ou a été déplacée.</p>

        {/* Actions */}
        <div className="flex flex-col sm:flex-row gap-4 justify-center items-center">
          <Button asChild variant="default" size="lg">
            <Link to="/" className="flex items-center gap-2">
              <Home className="h-5 w-5" />
              Retour à l'accueil
            </Link>
          </Button>

          <Button asChild variant="outline" size="lg" onClick={() => window.history.back()}>
            <button className="flex items-center gap-2">
              <ArrowLeft className="h-5 w-5" />
              Page précédente
            </button>
          </Button>
        </div>

        {/* Illustration optionnelle */}
        <div className="mt-12">
          <svg className="mx-auto h-64 w-64 text-gray-300" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M9.172 16.172a4 4 0 015.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        </div>
      </div>
    </div>
  );
}
