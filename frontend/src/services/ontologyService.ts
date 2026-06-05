import { BaseService } from "./base.service";
import { OntologyGraph, OntologyGraphCreate, OntologyGraphUpdate } from "../types/ontology";

class OntologyService extends BaseService<OntologyGraph, OntologyGraphCreate, OntologyGraphUpdate> {
  protected basePath = "/api/ontology";
}

export const ontologyService = new OntologyService();
export default ontologyService;
