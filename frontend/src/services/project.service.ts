import { Project, ProjectCreate, ProjectUpdate } from "../types/project";
import { BaseService } from "./base.service";

class ProjectService extends BaseService<Project, ProjectCreate, ProjectUpdate> {
  protected basePath = "/api/projects";
}

export const projectService = new ProjectService();
export default projectService;
