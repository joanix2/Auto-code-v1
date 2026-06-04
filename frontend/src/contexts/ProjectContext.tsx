import React, { createContext, useContext, useState } from "react";

interface ProjectInfo {
  id: string;
  name: string;
}

interface ProjectContextType {
  project: ProjectInfo | null;
  setProject: (project: ProjectInfo) => void;
}

const ProjectContext = createContext<ProjectContextType | null>(null);

export function ProjectProvider({ children }: { children: React.ReactNode }) {
  const [project, setProject] = useState<ProjectInfo | null>(null);
  return <ProjectContext.Provider value={{ project, setProject }}>{children}</ProjectContext.Provider>;
}

export function useProject(): ProjectContextType {
  const ctx = useContext(ProjectContext);
  if (!ctx) throw new Error("useProject must be used within ProjectProvider");
  return ctx;
}
