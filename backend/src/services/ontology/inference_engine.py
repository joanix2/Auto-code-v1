"""
Inference Engine — Deductive inference for the Open World ontology.

The engine applies registered inference rules against the current
set of concepts and facts to generate new (inferred) facts.

Key principles:
- Inferred facts are *distinct* from declared facts (different source).
- Each inferred fact carries a confidence = source_confidence × rule_discount.
- Every inferred fact is traceable via its justification string.
- Fixpoint iteration runs rules until no new facts are generated.
"""

from __future__ import annotations

import logging
import re
import uuid
from typing import Any

from src.services.ontology.ontology_models import (
    Concept,
    Fact,
    FactSource,
    InferenceRule,
    OntologyGraph,
)

logger = logging.getLogger(__name__)


class InferenceEngine:
    """Engine for applying inference rules to an ontology.

    Usage::

        engine = InferenceEngine()
        engine.register_rule(rule)
        result = engine.run_inference(ontology)
        # Or run until fixpoint:
        result = engine.run_fixpoint(ontology, max_iterations=10)
    """

    def __init__(self) -> None:
        """Initialize an empty inference engine."""
        self._rules: dict[str, InferenceRule] = {}

    # ------------------------------------------------------------------
    # Rule management
    # ------------------------------------------------------------------

    def register_rule(self, rule: InferenceRule) -> None:
        """Register an inference rule.

        Args:
            rule: The InferenceRule to register.
        """
        self._rules[rule.id] = rule
        logger.debug(f"Registered inference rule: {rule.id} ({rule.name})")

    def register_rules(self, rules: list[InferenceRule]) -> None:
        """Register multiple inference rules.

        Args:
            rules: A list of InferenceRule objects.
        """
        for rule in rules:
            self.register_rule(rule)

    def unregister_rule(self, rule_id: str) -> None:
        """Unregister an inference rule by ID.

        Args:
            rule_id: The ID of the rule to unregister.
        """
        self._rules.pop(rule_id, None)
        logger.debug(f"Unregistered inference rule: {rule_id}")

    def get_rules(self) -> list[InferenceRule]:
        """Get all registered rules.

        Returns:
            A list of all registered InferenceRule objects.
        """
        return list(self._rules.values())

    def clear_rules(self) -> None:
        """Remove all registered rules."""
        self._rules.clear()
        logger.debug("Cleared all inference rules")

    # ------------------------------------------------------------------
    # Inference execution
    # ------------------------------------------------------------------

    def run_inference(self, ontology: OntologyGraph) -> list[Fact]:
        """Run all registered rules once against the ontology.

        Applies every rule to the current set of facts and concepts.
        Only generates facts that are not already present.

        Args:
            ontology: The ontology to run inference on.

        Returns:
            A list of newly inferred Facts.
        """
        new_facts: list[Fact] = []

        for rule in self._rules.values():
            inferred = self._apply_rule(rule, ontology)
            new_facts.extend(inferred)

        logger.info(
            f"Inference run complete: {len(new_facts)} new fact(s) generated "
            f"from {len(self._rules)} rule(s)"
        )
        return new_facts

    def run_fixpoint(
        self, ontology: OntologyGraph, max_iterations: int = 10
    ) -> list[Fact]:
        """Run inference repeatedly until no new facts are generated.

        This is the fixpoint (closure) computation. Each iteration
        applies all rules, and the resulting facts are added to the
        ontology before the next iteration. The process stops when
        no new facts are produced or after max_iterations.

        Args:
            ontology: The ontology to run inference on.
                New inferred facts are added directly to this ontology.
            max_iterations: Maximum number of iterations (default 10).

        Returns:
            A list of all newly inferred Facts across all iterations.

        Raises:
            ValueError: If max_iterations is less than 1.
        """
        if max_iterations < 1:
            raise ValueError("max_iterations must be at least 1")

        all_new_facts: list[Fact] = []
        fact_count_before = len(ontology.facts)

        for iteration in range(1, max_iterations + 1):
            new_facts = self.run_inference(ontology)

            if not new_facts:
                logger.info(
                    f"Fixpoint reached at iteration {iteration} "
                    f"(no new facts generated)"
                )
                break

            # Add new facts to the ontology
            for fact in new_facts:
                ontology.add_fact(fact)

            all_new_facts.extend(new_facts)
            logger.info(
                f"Iteration {iteration}: {len(new_facts)} new fact(s) "
                f"(total so far: {len(all_new_facts)})"
            )
        else:
            logger.warning(
                f"Fixpoint did not converge after {max_iterations} iterations. "
                f"Generated {len(all_new_facts)} fact(s) total."
            )

        total_new = len(ontology.facts) - fact_count_before
        logger.info(
            f"Fixpoint complete: {total_new} new fact(s) in {len(all_new_facts)} "
            f"batch(es) across {len(self._rules)} rule(s)"
        )
        return all_new_facts

    # ------------------------------------------------------------------
    # Rule application
    # ------------------------------------------------------------------

    def _apply_rule(
        self, rule: InferenceRule, ontology: OntologyGraph
    ) -> list[Fact]:
        """Apply a single rule to the ontology.

        The rule's condition template is parsed to extract variable
        patterns. For each matching combination of facts/concepts,
        the conclusion template is instantiated and a new Fact is
        created (if not already present).

        Args:
            rule: The rule to apply.
            ontology: The current ontology state.

        Returns:
            A list of newly inferred Facts for this rule.
        """
        # Parse variables from condition (e.g. "is_a(?X, ?Y) AND is_a(?Y, ?Z)")
        # We extract patterns like predicate(?var1, ?var2)
        condition_patterns = self._parse_condition(rule.condition)
        conclusion_template = rule.conclusion

        if not condition_patterns:
            logger.warning(
                f"Rule '{rule.id}' has unparseable condition: {rule.condition}"
            )
            return []

        # For each condition pattern, find matching facts
        matches = self._find_matches(condition_patterns, ontology)

        if not matches:
            return []

        # Generate new facts from matches
        new_facts: list[Fact] = []
        existing_statements = {f.statement for f in ontology.facts.values()}

        for match in matches:
            # Instantiate conclusion with variable bindings
            statement = self._instantiate_template(conclusion_template, match)

            if statement in existing_statements:
                continue  # Already have this fact

            # Compute discounted confidence
            source_confidences = [
                ontology.get_facts_by_statement(s)
                for s in match.get("_source_statements", [])
            ]
            base_confidence = self._compute_base_confidence(source_confidences)
            confidence = base_confidence * rule.confidence_discount

            # Build justification
            justification = self._build_justification(
                rule, match, base_confidence, confidence
            )

            fact = Fact(
                id=str(uuid.uuid4()),
                statement=statement,
                source=FactSource.INFERRED,
                confidence=round(min(confidence, 1.0), 4),
                justification=justification,
            )
            new_facts.append(fact)
            existing_statements.add(statement)

        return new_facts

    @staticmethod
    def _parse_condition(condition: str) -> list[dict[str, Any]]:
        """Parse a condition template string into structured patterns.

        Handles patterns like:
            is_a(?X, ?Y) AND is_a(?Y, ?Z)
            has_property(?X, ?P)

        Args:
            condition: The condition template string.

        Returns:
            A list of pattern dicts, each with 'predicate' and 'args'.
        """
        patterns = []
        # Split on AND/and (case-insensitive)
        parts = re.split(r"\s+(?:AND|and)\s+", condition.strip())

        for part in parts:
            part = part.strip()
            match = re.match(r"(\w+)\(([^)]*)\)", part)
            if match:
                predicate = match.group(1)
                args_str = match.group(2)
                args = [arg.strip() for arg in args_str.split(",") if arg.strip()]
                patterns.append({"predicate": predicate, "args": args})

        return patterns

    @staticmethod
    def _find_matches(
        patterns: list[dict[str, Any]], ontology: OntologyGraph
    ) -> list[dict[str, str]]:
        """Find all variable bindings that satisfy the condition patterns.

        Performs a simple unification: for each predicate pattern,
        find all matching facts in the ontology and try to unify
        variable bindings across patterns.

        Args:
            patterns: List of parsed condition patterns.
            ontology: The ontology to search.

        Returns:
            List of variable binding dicts (variable → value).
        """
        if not patterns:
            return [{}]

        # Simple approach: collect all facts as predicate(arg1, arg2) strings
        # and try to match patterns against them
        fact_statements = [
            {
                "statement": f.statement,
                "confidence": f.confidence,
            }
            for f in ontology.facts.values()
        ]

        # Also generate statements from concepts
        for concept in ontology.concepts.values():
            stmt = f"is_a({concept.name}, Concept)"
            if stmt not in {fs["statement"] for fs in fact_statements}:
                fact_statements.append({"statement": stmt, "confidence": concept.confidence})

        # For each relation, generate relation statements
        for rel in ontology.relations.values():
            source = ontology.get_concept(rel.source_id)
            target = ontology.get_concept(rel.target_id)
            if source and target:
                stmt = f"{rel.relation_type}({source.name}, {target.name})"
                if stmt not in {fs["statement"] for fs in fact_statements}:
                    fact_statements.append({
                        "statement": stmt,
                        "confidence": min(source.confidence, target.confidence),
                    })

        # Now try to match patterns against fact statements
        # This is a simplified forward-chaining approach
        # We'll try each pattern as a template and unify variables

        matches: list[dict[str, str]] = []
        # Start with all possible bindings from the first pattern
        first_pattern = patterns[0]
        first_pred = first_pattern["predicate"]
        first_args = first_pattern["args"]

        for fs in fact_statements:
            binding = InferenceEngine._match_statement(
                fs["statement"], first_pred, first_args
            )
            if binding is not None:
                binding["_source_statements"] = [fs["statement"]]
                matches.append(binding)

        # For subsequent patterns, filter matches
        for pattern in patterns[1:]:
            pred = pattern["predicate"]
            args = pattern["args"]
            new_matches: list[dict[str, str]] = []

            for existing_match in matches:
                # Try to match this pattern against facts given existing bindings
                matched_any = False
                for fs in fact_statements:
                    # Substitute known bindings into the pattern
                    concrete_args = [
                        existing_match.get(a, a) for a in args
                    ]
                    binding = InferenceEngine._match_statement(
                        fs["statement"], pred, concrete_args
                    )
                    if binding is not None:
                        # Merge bindings (must be consistent)
                        merged = {**existing_match}
                        conflict = False
                        for k, v in binding.items():
                            if k.startswith("_"):
                                continue
                            if k in merged and merged[k] != v:
                                conflict = True
                                break
                            merged[k] = v
                        if not conflict:
                            merged["_source_statements"] = (
                                existing_match.get("_source_statements", [])
                                + [fs["statement"]]
                            )
                            new_matches.append(merged)
                            matched_any = True

                if not matched_any and len(patterns) == 1:
                    new_matches.append(existing_match)

            matches = new_matches
            if not matches:
                break

        return matches

    @staticmethod
    def _match_statement(
        statement: str, predicate: str, args: list[str]
    ) -> dict[str, str] | None:
        """Try to match a fact statement against a predicate + args pattern.

        Example:
            statement = "is_a(Car, Vehicle)"
            predicate = "is_a"
            args = ["?X", "?Y"]
            Returns {"?X": "Car", "?Y": "Vehicle"}

        Args:
            statement: The fact statement string.
            predicate: The predicate name.
            args: List of argument patterns (possibly with ?vars).

        Returns:
            A variable binding dict, or None if no match.
        """
        # Parse the statement
        stmt_match = re.match(r"(\w+)\(([^)]*)\)", statement)
        if not stmt_match:
            return None

        stmt_pred = stmt_match.group(1)
        stmt_args_str = stmt_match.group(2)
        stmt_args = [a.strip() for a in stmt_args_str.split(",") if a.strip()]

        # Predicate must match
        if stmt_pred != predicate:
            return None

        # Argument count must match
        if len(stmt_args) != len(args):
            return None

        # Try to unify
        binding: dict[str, str] = {}
        for stmt_arg, pattern_arg in zip(stmt_args, args):
            if pattern_arg.startswith("?"):
                # Variable — bind it
                var_name = pattern_arg
                if var_name in binding:
                    if binding[var_name] != stmt_arg:
                        return None  # Inconsistent binding
                else:
                    binding[var_name] = stmt_arg
            else:
                # Constant — must match exactly
                if stmt_arg != pattern_arg:
                    return None

        return binding

    @staticmethod
    def _instantiate_template(
        template: str, bindings: dict[str, str]
    ) -> str:
        """Fill in a template string with variable bindings.

        Replaces ?VarName with the corresponding bound value.

        Args:
            template: The template string (e.g. "is_a(?X, ?Z)").
            bindings: Variable bindings dict (e.g. {"?X": "Car", "?Z": "Vehicle"}).

        Returns:
            The instantiated statement string.
        """
        result = template
        for var, value in bindings.items():
            if not var.startswith("_"):
                result = result.replace(var, value)
        return result

    @staticmethod
    def _compute_base_confidence(
        source_confidences: list[list[Fact]],
    ) -> float:
        """Compute the base confidence from source facts.

        Uses the minimum confidence among all source facts
        (conservative approach).

        Args:
            source_confidences: A list of fact lists per statement.

        Returns:
            The base confidence value.
        """
        if not source_confidences:
            return 1.0

        all_confidences: list[float] = []
        for fact_list in source_confidences:
            for fact in fact_list:
                all_confidences.append(fact.confidence)

        if not all_confidences:
            return 1.0

        return min(all_confidences)

    @staticmethod
    def _build_justification(
        rule: InferenceRule,
        bindings: dict[str, str],
        base_confidence: float,
        final_confidence: float,
    ) -> str:
        """Build a human-readable justification string for an inferred fact.

        Args:
            rule: The rule that fired.
            bindings: Variable bindings used.
            base_confidence: The source confidence.
            final_confidence: The resulting confidence.

        Returns:
            A justification string.
        """
        source_stmts = bindings.get("_source_statements", [])
        if isinstance(source_stmts, list):
            source_str = "; ".join(source_stmts)
        else:
            source_str = str(source_stmts)

        return (
            f"Inferred by rule '{rule.name}' ({rule.id}): "
            f"condition='{rule.condition}', conclusion='{rule.conclusion}' | "
            f"source statements: [{source_str}] | "
            f"base_confidence={base_confidence:.3f}, "
            f"discount={rule.confidence_discount}, "
            f"final_confidence={final_confidence:.3f}"
        )
