"""Project — contient des programmes, tickets, et une ontologie."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class Project(BaseModel):
    id: str = Field(default_factory=lambda: f"proj_{uuid.uuid4().hex[:12]}")
    name: str
    description: str = ""
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Program(BaseModel):
    id: str = Field(default_factory=lambda: f"prog_{uuid.uuid4().hex[:12]}")
    name: str
    source_code: str = ""
    language_id: str
    project_id: str
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Ticket(BaseModel):
    id: str = Field(default_factory=lambda: f"tkt_{uuid.uuid4().hex[:12]}")
    title: str
    description: str = ""
    project_id: str
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Triple(BaseModel):
    id: str = Field(default_factory=lambda: f"tri_{uuid.uuid4().hex[:12]}")
    subject: str
    predicate: str
    object: str
    ticket_id: str
    ontology_id: str = ""
    confidence: float = 1.0


class Ontology(BaseModel):
    id: str = Field(default_factory=lambda: f"onto_{uuid.uuid4().hex[:12]}")
    name: str
    project_id: str
    triples: list[Triple] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    def add_triple(
        self,
        subject: str,
        predicate: str,
        object: str,
        ticket_id: str = "",
        confidence: float = 1.0,
    ) -> Triple:
        t = Triple(
            subject=subject,
            predicate=predicate,
            object=object,
            ticket_id=ticket_id,
            ontology_id=self.id,
            confidence=confidence,
        )
        self.triples.append(t)
        return t
