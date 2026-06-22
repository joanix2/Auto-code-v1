"""Project Service — gestion des projets, programmes, tickets, triples, ontologies."""

from __future__ import annotations

import re

from src.models.project import Ontology, Program, Project, Ticket, Triple


class ProjectService:
    """Service mémoire pour l'ensemble projet → ticket → triple → ontologie."""

    def __init__(self) -> None:
        self._projects: dict[str, Project] = {}
        self._programs: dict[str, Program] = {}
        self._tickets: dict[str, Ticket] = {}
        self._ontologies: dict[str, Ontology] = {}

    # ── Projects ─────────────────────────────────

    def create_project(self, name: str, description: str = "") -> Project:
        p = Project(name=name, description=description)
        self._projects[p.id] = p
        return p

    def get_project(self, project_id: str) -> Project | None:
        return self._projects.get(project_id)

    def list_projects(self) -> list[Project]:
        return list(self._projects.values())

    # ── Programs ─────────────────────────────────

    def create_program(
        self, name: str, language_id: str, project_id: str, source_code: str = ""
    ) -> Program:
        p = Program(
            name=name, language_id=language_id, project_id=project_id, source_code=source_code
        )
        self._programs[p.id] = p
        return p

    def get_programs_by_project(self, project_id: str) -> list[Program]:
        return [p for p in self._programs.values() if p.project_id == project_id]

    # ── Tickets ──────────────────────────────────

    _TRIPLE_RE = re.compile(r"(\w+)\s*[-–—>]+\s*(\w+)\s*[-–—>]+\s*(\w+)")

    def create_ticket(self, title: str, description: str, project_id: str) -> Ticket:
        t = Ticket(title=title, description=description, project_id=project_id)
        self._tickets[t.id] = t
        return t

    def get_tickets_by_project(self, project_id: str) -> list[Ticket]:
        return [t for t in self._tickets.values() if t.project_id == project_id]

    def extract_triples(self, ticket_id: str) -> list[Triple]:
        ticket = self._tickets.get(ticket_id)
        if not ticket:
            return []
        ontology = self._find_ontology_for_ticket(ticket.project_id)
        triples: list[Triple] = []
        for match in self._TRIPLE_RE.finditer(ticket.description):
            t = Triple(
                subject=match.group(1),
                predicate=match.group(2),
                object=match.group(3),
                ticket_id=ticket_id,
                ontology_id=ontology.id if ontology else "",
            )
            triples.append(t)
            if ontology:
                ontology.triples.append(t)
        return triples

    def _find_ontology_for_ticket(self, project_id: str) -> Ontology | None:
        for o in self._ontologies.values():
            if o.project_id == project_id:
                return o
        return None

    # ── Ontologies ───────────────────────────────

    def create_ontology(self, name: str, project_id: str) -> Ontology:
        o = Ontology(name=name, project_id=project_id)
        self._ontologies[o.id] = o
        return o

    def get_ontology(self, project_id: str) -> Ontology | None:
        for o in self._ontologies.values():
            if o.project_id == project_id:
                return o
        return None
