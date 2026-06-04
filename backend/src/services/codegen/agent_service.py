"""
Agent Service — Abstract interfaces and mock implementations for all pipeline agents.

Each agent implements the BaseAgentService interface with a `process()` method
that takes dict input and returns dict output. The mock implementations ship
structured responses without real LLM calls, ready for future LLM integration.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import Any

logger = logging.getLogger(__name__)


# ======================================================================
# Abstract Base
# ======================================================================


class BaseAgentService(ABC):
    """Abstract interface for all pipeline agents.

    Each agent receives a dict of input data and produces a dict of
    output data. The structure of input/output varies by agent type.
    """

    agent_name: str = "base"

    @abstractmethod
    def process(self, input_data: dict[str, Any]) -> dict[str, Any]:
        """Process input data and return output.

        Args:
            input_data: Agent-specific input dictionary.

        Returns:
            Agent-specific output dictionary.
        """
        ...

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}>"


# ======================================================================
# ProductOwnerAgent
# ======================================================================


class ProductOwnerAgent(BaseAgentService):
    """Agent: prompt → structured tickets.

    Takes a natural language prompt and produces structured tickets
    with title, description, acceptance criteria, and priority.
    """

    agent_name = "product_owner"

    def process(self, input_data: dict[str, Any]) -> dict[str, Any]:
        """Convert a prompt into structured tickets."""
        prompt = input_data.get("prompt", "")
        context = input_data.get("context", {})

        if not prompt:
            return {
                "success": False,
                "error": "No prompt provided",
                "tickets": [],
            }

        # Mock implementation: produce a structured ticket from the prompt
        tickets = [
            {
                "id": "ticket-1",
                "title": _extract_title(prompt),
                "description": prompt,
                "priority": context.get("priority", "medium"),
                "acceptance_criteria": [
                    f"The system should support {prompt[:50]}...",
                    "Generated code should follow project conventions",
                    "All tests should pass",
                ],
                "estimated_hours": context.get("estimated_hours", 8),
            }
        ]

        return {
            "success": True,
            "tickets": tickets,
            "summary": f"Generated {len(tickets)} ticket(s) from prompt",
        }


# ======================================================================
# NERAgent
# ======================================================================


class NERAgent(BaseAgentService):
    """Agent: tickets → entity/relation triplets.

    Extracts named entities and relationships from structured tickets.
    Produces (entity, relation, entity) triplets.
    """

    agent_name = "ner"

    def process(self, input_data: dict[str, Any]) -> dict[str, Any]:
        """Extract entities and relations from tickets."""
        tickets = input_data.get("tickets", [])
        context = input_data.get("context", {})

        if not tickets:
            return {
                "success": False,
                "error": "No tickets provided",
                "entities": [],
                "relations": [],
            }

        # Mock implementation: extract mock entities/relations from tickets
        entities = []
        relations = []
        entity_counter = 0

        for ticket in tickets:
            title = ticket.get("title", "Unknown")
            # Create a main entity from the ticket title
            entity_counter += 1
            main_entity = {
                "id": f"entity-{entity_counter}",
                "name": _to_entity_name(title),
                "type": "concept",
                "source_ticket": ticket.get("id", ""),
            }
            entities.append(main_entity)

            # Create some standard sub-entities
            for sub_name, sub_type in [
                ("name", "attribute"),
                ("description", "attribute"),
                ("created_at", "attribute"),
            ]:
                entity_counter += 1
                sub_entity = {
                    "id": f"entity-{entity_counter}",
                    "name": sub_name,
                    "type": sub_type,
                    "source_ticket": ticket.get("id", ""),
                }
                entities.append(sub_entity)
                relations.append({
                    "source_id": main_entity["id"],
                    "target_id": sub_entity["id"],
                    "relation": "HAS_ATTRIBUTE",
                })

        return {
            "success": True,
            "entities": entities,
            "relations": relations,
            "summary": f"Extracted {len(entities)} entities and {len(relations)} relations",
        }


# ======================================================================
# OntologistAgent
# ======================================================================


class OntologistAgent(BaseAgentService):
    """Agent: triplets → ontology concepts.

    Takes entity/relation triplets and produces an ontology with
    concepts, attributes, relationships, and constraints.
    """

    agent_name = "ontologist"

    def process(self, input_data: dict[str, Any]) -> dict[str, Any]:
        """Build ontology from entity/relation triplets."""
        entities = input_data.get("entities", [])
        relations = input_data.get("relations", [])

        if not entities:
            return {
                "success": False,
                "error": "No entities provided",
                "concepts": [],
            }

        # Group entities by type
        concepts = []
        attributes = []

        for entity in entities:
            if entity.get("type") == "concept":
                concepts.append({
                    "id": entity["id"],
                    "name": entity["name"],
                    "description": f"Concept derived from {entity.get('source_ticket', 'unknown')}",
                    "attributes": [],
                    "relations": [],
                })
            elif entity.get("type") == "attribute":
                attributes.append({
                    "id": entity["id"],
                    "name": entity["name"],
                    "data_type": "string",
                    "is_required": False,
                })

        # Link attributes to concepts via relations
        for relation in relations:
            source_id = relation.get("source_id")
            target_id = relation.get("target_id")
            rel_type = relation.get("relation", "RELATED_TO")

            # Find the concept and add the attribute
            for concept in concepts:
                if concept["id"] == source_id:
                    attr = next((a for a in attributes if a["id"] == target_id), None)
                    if attr:
                        concept["attributes"].append(attr)
                    break

            for concept in concepts:
                if concept["id"] == target_id and rel_type != "HAS_ATTRIBUTE":
                    source_concept = next(
                        (c for c in concepts if c["id"] == source_id), None
                    )
                    if source_concept:
                        concept["relations"].append({
                            "target_id": source_id,
                            "target_name": source_concept["name"],
                            "type": rel_type,
                        })
                    break

        return {
            "success": True,
            "concepts": concepts,
            "summary": f"Built ontology with {len(concepts)} concepts",
        }


# ======================================================================
# GraphEngineerAgent
# ======================================================================


class GraphEngineerAgent(BaseAgentService):
    """Agent: ontology → IR graph.

    Transforms an ontology into a concrete IR (Intermediate Representation)
    graph with nodes and edges suitable for code generation.
    """

    agent_name = "graph_engineer"

    def process(self, input_data: dict[str, Any]) -> dict[str, Any]:
        """Build an IR graph from ontology concepts."""
        concepts = input_data.get("concepts", [])

        if not concepts:
            return {
                "success": False,
                "error": "No concepts provided",
                "nodes": [],
                "edges": [],
            }

        nodes = []
        edges = []
        node_counter = 0

        for concept in concepts:
            # Create a node for the concept
            node_counter += 1
            concept_node = {
                "id": concept.get("id", f"node-{node_counter}"),
                "name": concept["name"],
                "kind": "concept",
                "properties": {
                    "description": concept.get("description", ""),
                },
            }
            nodes.append(concept_node)

            # Create nodes for attributes and edges to concept
            for attr in concept.get("attributes", []):
                node_counter += 1
                attr_node = {
                    "id": attr["id"],
                    "name": attr["name"],
                    "kind": "attribute",
                    "properties": {
                        "data_type": attr.get("data_type", "string"),
                        "is_required": attr.get("is_required", False),
                    },
                }
                nodes.append(attr_node)
                edges.append({
                    "source_id": concept_node["id"],
                    "target_id": attr_node["id"],
                    "edge_type": "HAS_ATTRIBUTE",
                })

            # Create edges for relations
            for rel in concept.get("relations", []):
                edges.append({
                    "source_id": concept_node["id"],
                    "target_id": rel["target_id"],
                    "edge_type": rel.get("type", "RELATED_TO"),
                })

        return {
            "success": True,
            "nodes": nodes,
            "edges": edges,
            "summary": f"Built IR graph with {len(nodes)} nodes and {len(edges)} edges",
        }


# ======================================================================
# TemplateEngineerAgent
# ======================================================================


class TemplateEngineerAgent(BaseAgentService):
    """Agent: IR graph + templates → rendered files.

    Takes an IR graph and registered templates, then renders them
    to produce generated code files.
    """

    agent_name = "template_engineer"

    def process(self, input_data: dict[str, Any]) -> dict[str, Any]:
        """Render templates against an IR graph."""
        nodes = input_data.get("nodes", [])
        edges = input_data.get("edges", [])
        templates = input_data.get("templates", [])
        context = input_data.get("context", {})

        if not nodes:
            return {
                "success": False,
                "error": "No graph nodes provided",
                "files": [],
            }

        # Mock implementation: produce file entries for each concept node
        files = []
        for node in nodes:
            if node.get("kind") == "concept":
                name = node["name"]
                snake = _to_snake_case(name)
                files.append({
                    "path": f"models/{snake}.py",
                    "content": (
                        f"# Generated model for {name}\n"
                        f"# From node: {node.get('id')}\n"
                        f"class {name}(BaseModel):\n"
                        f"    \"\"\"{node.get('properties', {}).get('description', '')}\"\"\"\n"
                        f"    pass\n"
                    ),
                    "template_used": "python_model.j2",
                })
                files.append({
                    "path": f"routes/{snake}_api.py",
                    "content": (
                        f"# Generated API router for {name}\n"
                        f"from fastapi import APIRouter\n\n"
                        f"router = APIRouter(prefix='/{snake}')\n\n"
                        f"# TODO: implement endpoints for {name}\n"
                    ),
                    "template_used": "api_route.j2",
                })

        return {
            "success": True,
            "files": files,
            "summary": f"Generated {len(files)} file(s) from templates",
        }


# ======================================================================
# ValidatorAgent
# ======================================================================


class ValidatorAgent(BaseAgentService):
    """Agent: IR graph → validation report.

    Validates an IR graph for structural correctness and business rules.
    """

    agent_name = "validator"

    def process(self, input_data: dict[str, Any]) -> dict[str, Any]:
        """Validate an IR graph."""
        nodes = input_data.get("nodes", [])
        edges = input_data.get("edges", [])
        files = input_data.get("files", [])

        errors = []
        warnings = []

        # Check nodes for required fields
        for node in nodes:
            if not node.get("name"):
                errors.append(f"Node {node.get('id', 'unknown')} is missing 'name'")
            if not node.get("kind"):
                warnings.append(f"Node {node.get('id', 'unknown')} is missing 'kind'")

        # Check edges for valid references
        node_ids = {n["id"] for n in nodes}
        for edge in edges:
            if edge.get("source_id") not in node_ids:
                errors.append(
                    f"Edge references unknown source node: {edge.get('source_id')}"
                )
            if edge.get("target_id") not in node_ids:
                errors.append(
                    f"Edge references unknown target node: {edge.get('target_id')}"
                )

        # Validate files have content
        for f in files:
            if not f.get("content"):
                warnings.append(f"Generated file {f.get('path', 'unknown')} is empty")

        is_valid = len(errors) == 0

        return {
            "success": True,
            "is_valid": is_valid,
            "errors": errors,
            "warnings": warnings,
            "summary": (
                f"Validation {'passed' if is_valid else 'failed'}: "
                f"{len(errors)} error(s), {len(warnings)} warning(s)"
            ),
        }


# ======================================================================
# RewriteAgent
# ======================================================================


class RewriteAgent(BaseAgentService):
    """Agent: IR graph → rewritten graph.

    Applies rewrite rules to transform or optimize the IR graph.
    """

    agent_name = "rewrite"

    def process(self, input_data: dict[str, Any]) -> dict[str, Any]:
        """Rewrite an IR graph using transformation rules."""
        nodes = input_data.get("nodes", [])
        edges = input_data.get("edges", [])
        rules = input_data.get("rules", ["normalize_names", "add_timestamps"])

        if not nodes:
            return {
                "success": False,
                "error": "No graph nodes provided",
                "nodes": [],
                "edges": [],
            }

        # Mock implementation: apply simple transformations
        rewritten_nodes = []
        transformations = []

        for node in nodes:
            rewritten = dict(node)
            props = dict(rewritten.get("properties", {}))

            if "normalize_names" in rules:
                old_name = rewritten.get("name", "")
                rewritten["name"] = _to_pascal_case(old_name)
                if old_name != rewritten["name"]:
                    transformations.append(
                        f"Normalized name: '{old_name}' → '{rewritten['name']}'"
                    )

            if "add_timestamps" in rules:
                props["created_at"] = "2025-01-01T00:00:00Z"
                props["updated_at"] = "2025-01-01T00:00:00Z"
                transformations.append(f"Added timestamps to '{rewritten['name']}'")

            rewritten["properties"] = props
            rewritten_nodes.append(rewritten)

        return {
            "success": True,
            "nodes": rewritten_nodes,
            "edges": edges,
            "transformations": transformations,
            "summary": f"Applied {len(transformations)} transformation(s)",
        }


# ======================================================================
# CodegenPlannerAgent
# ======================================================================


class CodegenPlannerAgent(BaseAgentService):
    """Agent: requirements → generation plan.

    Analyzes requirements and produces a GenerationPlan with ordered
    steps, templates, and dependencies for code generation.
    """

    agent_name = "codegen_planner"

    def process(self, input_data: dict[str, Any]) -> dict[str, Any]:
        """Create a generation plan from requirements."""
        nodes = input_data.get("nodes", [])
        files = input_data.get("files", [])
        requirements = input_data.get("requirements", {})

        if not nodes and not requirements:
            return {
                "success": False,
                "error": "No nodes or requirements provided",
                "plan": None,
            }

        concept_nodes = [n for n in nodes if n.get("kind") == "concept"]

        # Build steps from concept nodes
        steps = []
        step_counter = 0

        for concept in concept_nodes:
            name = concept["name"]
            snake = _to_snake_case(name)
            step_counter += 1

            # Model step
            step_id = f"gen_{snake}_model"
            steps.append({
                "name": step_id,
                "template_name": "python_model.j2",
                "entity_id": concept.get("id"),
                "depends_on": [],
                "output_path": f"models/{snake}.py",
            })

            # API step (depends on model)
            step_counter += 1
            api_step_id = f"gen_{snake}_api"
            steps.append({
                "name": api_step_id,
                "template_name": "api_route.j2",
                "entity_id": concept.get("id"),
                "depends_on": [step_id],
                "output_path": f"routes/{snake}_api.py",
            })

            # SQL step (depends on model)
            step_counter += 1
            sql_step_id = f"gen_{snake}_sql"
            steps.append({
                "name": sql_step_id,
                "template_name": "sql_table.j2",
                "entity_id": concept.get("id"),
                "depends_on": [step_id],
                "output_path": f"sql/{snake}.sql",
            })

        plan = {
            "name": requirements.get("name", "generated-plan"),
            "steps": steps,
            "execution_mode": "sequential",
            "error_strategy": "abort",
        }

        return {
            "success": True,
            "plan": plan,
            "summary": f"Created generation plan with {len(steps)} step(s)",
        }


# ======================================================================
# GitIntegratorAgent
# ======================================================================


class GitIntegratorAgent(BaseAgentService):
    """Agent: generated files → patch/commit summary.

    Produces a structured summary of changes suitable for creating
    git commits or pull requests.
    """

    agent_name = "git_integrator"

    def process(self, input_data: dict[str, Any]) -> dict[str, Any]:
        """Create a commit/patch summary from generated files."""
        files = input_data.get("files", [])
        validation = input_data.get("validation", {})
        plan = input_data.get("plan", {})

        if not files:
            return {
                "success": False,
                "error": "No generated files provided",
                "commit_summary": None,
            }

        additions = []
        for f in files:
            additions.append({
                "path": f.get("path", "unknown"),
                "action": "create",
                "size_bytes": len(f.get("content", "")),
                "summary": f.get("content", "")[:80].strip() + "...",
            })

        commit = {
            "branch": "feature/generated-code",
            "message": f"Auto-generated: {len(files)} file(s) added",
            "changes": {
                "additions": additions,
                "modifications": [],
                "deletions": [],
            },
            "stats": {
                "files_changed": len(files),
                "additions": sum(a["size_bytes"] for a in additions),
                "deletions": 0,
            },
        }

        return {
            "success": True,
            "commit_summary": commit,
            "summary": f"Prepared commit with {len(files)} file(s)",
        }


# ======================================================================
# ReviewerAgent
# ======================================================================


class ReviewerAgent(BaseAgentService):
    """Agent: review all artifacts → validation.

    Reviews all pipeline artifacts (tickets, ontology, graph, files, plan)
    and produces a final quality check report.
    """

    agent_name = "reviewer"

    def process(self, input_data: dict[str, Any]) -> dict[str, Any]:
        """Review all pipeline artifacts."""
        tickets = input_data.get("tickets", [])
        concepts = input_data.get("concepts", [])
        graph = {"nodes": input_data.get("nodes", []), "edges": input_data.get("edges", [])}
        files = input_data.get("files", [])
        plan = input_data.get("plan", {})
        validation = input_data.get("validation", {})
        commit = input_data.get("commit_summary", {})

        issues = []
        suggestions = []

        # Check tickets
        if not tickets:
            issues.append("No tickets were generated")
        else:
            for t in tickets:
                if not t.get("acceptance_criteria"):
                    suggestions.append(f"Ticket '{t.get('title')}' has no acceptance criteria")

        # Check ontology
        if not concepts:
            issues.append("No ontology concepts were defined")

        # Check graph
        if not graph.get("nodes"):
            issues.append("IR graph is empty (no nodes)")

        # Check files
        if not files:
            issues.append("No files were generated")
        else:
            for f in files:
                if not f.get("content"):
                    suggestions.append(f"File '{f.get('path')}' has no content")

        # Check validation
        if validation and not validation.get("is_valid", True):
            issues.append(f"Validation failed: {len(validation.get('errors', []))} error(s)")

        # Check plan
        if not plan or not plan.get("steps"):
            issues.append("No generation plan was created")

        # Check commit
        if not commit:
            suggestions.append("No commit summary was prepared")

        is_approved = len(issues) == 0

        return {
            "success": True,
            "is_approved": is_approved,
            "issues": issues,
            "suggestions": suggestions,
            "files_reviewed": len(files),
            "summary": (
                f"Review {'passed' if is_approved else 'needs attention'}: "
                f"{len(issues)} issue(s), {len(suggestions)} suggestion(s)"
            ),
        }


# ======================================================================
# Agent Registry
# ======================================================================

# Map stage names to agent instances
AGENT_REGISTRY: dict[str, BaseAgentService] = {
    "product_owner": ProductOwnerAgent(),
    "ner": NERAgent(),
    "ontologist": OntologistAgent(),
    "graph_engineer": GraphEngineerAgent(),
    "template_engineer": TemplateEngineerAgent(),
    "validator": ValidatorAgent(),
    "rewrite": RewriteAgent(),
    "codegen_planner": CodegenPlannerAgent(),
    "git_integrator": GitIntegratorAgent(),
    "reviewer": ReviewerAgent(),
}


def get_agent(stage_name: str) -> BaseAgentService | None:
    """Get an agent by its stage name.

    Args:
        stage_name: The string key of the agent (e.g., "product_owner").

    Returns:
        The agent instance, or None if not found.
    """
    return AGENT_REGISTRY.get(stage_name)


# ======================================================================
# Internal helpers
# ======================================================================


def _extract_title(prompt: str) -> str:
    """Extract a title from a prompt string."""
    # Take the first meaningful line or first N chars
    lines = [l.strip() for l in prompt.split("\n") if l.strip()]
    if lines:
        title = lines[0]
    else:
        title = prompt[:60]
    # Capitalize and limit length
    return title[:80].capitalize()


def _to_entity_name(name: str) -> str:
    """Convert a human-readable name to an entity name."""
    # Remove special chars, PascalCase
    clean = "".join(c for c in name if c.isalnum() or c in " _-")
    words = clean.replace("-", " ").replace("_", " ").split()
    return "".join(w.capitalize() for w in words)


def _to_snake_case(name: str) -> str:
    """Convert PascalCase or Title to snake_case."""
    result = ""
    for char in name:
        if char.isupper() and result:
            result += "_"
        result += char.lower()
    return result


def _to_pascal_case(name: str) -> str:
    """Convert snake_case or mixed to PascalCase."""
    words = name.replace("_", " ").replace("-", " ").split()
    return "".join(w.capitalize() for w in words)
