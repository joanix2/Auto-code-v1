import React, { useState, useEffect } from "react";
import { BrowserRouter as Router, Routes, Route, Navigate, useParams } from "react-router-dom";
import { AuthProvider, useAuth } from "./contexts/AuthContext";
import { Layout } from "./components/layout/Layout";
import { Login } from "./pages/auth/Login";
import { Dashboard } from "./pages/Dashboard";
import { Repositories } from "./pages/development/repository/Repositories";
import { RepositoryDetails } from "./pages/development/repository/RepositoryDetails";
import { Issues } from "./pages/development/issues/Issues";
import IssueDetails from "./pages/development/issues/IssueDetails";
import { Messages } from "./pages/development/messages/Messages";
import { M3Page } from "./pages/development/m3/M3Page";
import { LanguagesPage } from "./pages/development/languages/LanguagesPage";
import { LanguageDetailPage } from "./pages/development/languages/LanguageDetailPage";
import { Projects } from "./pages/development/projects/Projects";
import { ProjectDetails } from "./pages/development/projects/ProjectDetails";
import { ProjectForm } from "./pages/development/projects/ProjectForm";
import { ProjectDetailLayout } from "./components/layout/ProjectDetailLayout";
import Profile from "./pages/profile/Profile";
import { NotFound } from "./pages/NotFound";
import { Toaster } from "@/components/ui/toaster";

// Protected Route Component
function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, loading } = useAuth();

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-lg">Loading...</div>
      </div>
    );
  }

  return isAuthenticated ? children : <Navigate to="/login" replace />;
}

// Authenticated Layout Wrapper
function AuthenticatedLayout({ children }: { children: React.ReactNode }) {
  const { user, signOut } = useAuth();

  return (
    <Layout user={user} onSignOut={signOut}>
      {children}
    </Layout>
  );
}

// Project Detail Wrapper (no sidebar, tabs in header/bottom nav)
function ProjectDetailPageWrapper({ children }: { children: React.ReactNode }) {
  const { projectId } = useParams<{ projectId: string }>();
  const { user, signOut } = useAuth();

  return (
    <ProjectDetailLayout projectId={projectId || ""} user={user} onSignOut={signOut}>
      {children}
    </ProjectDetailLayout>
  );
}

function DSLRedirect() {
  const { id } = useParams<{ id: string }>();
  return <Navigate to={`/development/languages/${id}`} replace />;
}

function App() {
  return (
    <Router>
      <AuthProvider>
        <Routes>
          {/* Protected Routes with Layout */}
          <Route
            path="/development/repositories"
            element={
              <ProtectedRoute>
                <AuthenticatedLayout>
                  <Repositories />
                </AuthenticatedLayout>
              </ProtectedRoute>
            }
          />

          <Route
            path="/development/repositories/new"
            element={
              <ProtectedRoute>
                <AuthenticatedLayout>
                  <RepositoryDetails />
                </AuthenticatedLayout>
              </ProtectedRoute>
            }
          />

          <Route
            path="/development/repositories/:id/edit"
            element={
              <ProtectedRoute>
                <AuthenticatedLayout>
                  <RepositoryDetails />
                </AuthenticatedLayout>
              </ProtectedRoute>
            }
          />

          <Route
            path="/development/repositories/:repositoryId/issues"
            element={
              <ProtectedRoute>
                <AuthenticatedLayout>
                  <Issues />
                </AuthenticatedLayout>
              </ProtectedRoute>
            }
          />

          <Route
            path="/development/issues"
            element={
              <ProtectedRoute>
                <AuthenticatedLayout>
                  <Issues />
                </AuthenticatedLayout>
              </ProtectedRoute>
            }
          />

          {/* Projects routes */}
          <Route
            path="/development/projets"
            element={
              <ProtectedRoute>
                <AuthenticatedLayout>
                  <Projects />
                </AuthenticatedLayout>
              </ProtectedRoute>
            }
          />
          <Route
            path="/development/projets/new"
            element={
              <ProtectedRoute>
                <AuthenticatedLayout>
                  <ProjectForm />
                </AuthenticatedLayout>
              </ProtectedRoute>
            }
          />
          <Route
            path="/development/projets/:projectId"
            element={
              <ProtectedRoute>
                <ProjectDetailPageWrapper>
                  <ProjectDetails />
                </ProjectDetailPageWrapper>
              </ProtectedRoute>
            }
          />
          <Route
            path="/development/projets/:projectId/edit"
            element={
              <ProtectedRoute>
                <AuthenticatedLayout>
                  <ProjectForm />
                </AuthenticatedLayout>
              </ProtectedRoute>
            }
          />

          {/* M3 rewriting-logic graph route */}
          <Route
            path="/development/m3"
            element={
              <ProtectedRoute>
                <AuthenticatedLayout>
                  <M3Page />
                </AuthenticatedLayout>
              </ProtectedRoute>
            }
          />

          {/* Languages routes */}
          <Route
            path="/development/languages"
            element={
              <ProtectedRoute>
                <AuthenticatedLayout>
                  <LanguagesPage />
                </AuthenticatedLayout>
              </ProtectedRoute>
            }
          />
          <Route
            path="/development/languages/:langId"
            element={
              <ProtectedRoute>
                <AuthenticatedLayout>
                  <LanguageDetailPage />
                </AuthenticatedLayout>
              </ProtectedRoute>
            }
          />

          {/* DSL routes → redirect to languages */}
          <Route path="/development/dsls" element={<Navigate to="/development/languages" replace />} />
          <Route path="/development/dsls/new" element={<Navigate to="/development/languages" replace />} />
          <Route path="/development/dsls/:id" element={<DSLRedirect />} />
          <Route path="/development/dsls/:id/edit" element={<Navigate to="/development/languages" replace />} />

          <Route
            path="/development/issues/new"
            element={
              <ProtectedRoute>
                <AuthenticatedLayout>
                  <IssueDetails />
                </AuthenticatedLayout>
              </ProtectedRoute>
            }
          />

          <Route
            path="/development/issues/:issueId"
            element={
              <ProtectedRoute>
                <AuthenticatedLayout>
                  <IssueDetails />
                </AuthenticatedLayout>
              </ProtectedRoute>
            }
          />

          <Route
            path="/development/issues/:issueId/edit"
            element={
              <ProtectedRoute>
                <AuthenticatedLayout>
                  <IssueDetails />
                </AuthenticatedLayout>
              </ProtectedRoute>
            }
          />

          <Route
            path="/development/issues/:issueId/messages"
            element={
              <ProtectedRoute>
                <AuthenticatedLayout>
                  <Messages />
                </AuthenticatedLayout>
              </ProtectedRoute>
            }
          />

          {/* Profile route */}
          <Route
            path="/profile"
            element={
              <ProtectedRoute>
                <AuthenticatedLayout>
                  <Profile />
                </AuthenticatedLayout>
              </ProtectedRoute>
            }
          />

          {/* Login route - public */}
          <Route path="/login" element={<Login />} />

          {/* Dashboard - page d'accueil */}
          <Route
            path="/"
            element={
              <ProtectedRoute>
                <AuthenticatedLayout>
                  <Dashboard />
                </AuthenticatedLayout>
              </ProtectedRoute>
            }
          />

          {/* 404 - Page non trouvée */}
          <Route
            path="*"
            element={
              <ProtectedRoute>
                <AuthenticatedLayout>
                  <NotFound />
                </AuthenticatedLayout>
              </ProtectedRoute>
            }
          />
        </Routes>
        <Toaster />
      </AuthProvider>
    </Router>
  );
}

export default App;
