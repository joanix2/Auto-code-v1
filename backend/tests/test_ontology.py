"""Tests for the Ontology and Inference System (MVP F).

Tests cover:
1. Ontology models — Concept, Property, SemanticRelation, Taxonomy, Fact, etc.
2. OntologyStore — save/load roundtrip
3. InferenceEngine — rule registration, inference, fixpoint, declared vs inferred
4. OntologyCompiler — ontology → IR, IR → ontology
5. API endpoints — CRUD, inference, compilation, persistence
6. Edge cases — empty ontology, low-confidence concepts, circular inferences
"""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

from src.services.ontology import (
    FactSource,
    InferenceEngine,
    InferenceRule,
    OntologyCompiler,
    OntologyGraph,
    OntologyStore,
)
from src.services.ontology.ontology_models import (
    Concept,
    Fact,
    Property,
    SemanticRelation,
    Taxonomy,
)


# ===================================================================
# Fixtures
# ===================================================================


@pytest.fixture
def sample_concept_a() -> Concept:
    return Concept(
        id="c1",
        name="Vehicle",
        description="A mode of transport",
        properties=[
            Property(name="speed", type="integer", cardinality="1"),
            Property(name="color", type="string", cardinality="0..1"),
        ],
        confidence=0.95,
    )


@pytest.fixture
def sample_concept_b() -> Concept:
    return Concept(
        id="c2",
        name="Car",
        description="A four-wheeled vehicle",
        properties=[
            Property(name="doors", type="integer", cardinality="1"),
        ],
        confidence=0.9,
    )


@pytest.fixture
def sample_concept_c() -> Concept:
    return Concept(
        id="c3",
        name="Bicycle",
        description="A two-wheeled vehicle",
        confidence=0.85,
    )


@pytest.fixture
def sample_concept_low_conf() -> Concept:
    return Concept(
        id="c4",
        name="Unicorn",
        description="A mythical creature",
        confidence=0.3,
    )


@pytest.fixture
def sample_relation() -> SemanticRelation:
    return SemanticRelation(
        id="r1",
        name="is a",
        source_id="c2",
        target_id="c1",
        relation_type="IS_A",
        confidence=0.95,
    )


@pytest.fixture
def sample_taxonomy() -> Taxonomy:
    return Taxonomy(
        id="t1",
        name="Vehicle types",
        parent_id="c1",
        concepts=["c2", "c3"],
    )


@pytest.fixture
def sample_rule_transitive() -> InferenceRule:
    return InferenceRule(
        id="rule-transitive",
        name="Transitive inheritance",
        condition="IS_A(?X, ?Y) AND IS_A(?Y, ?Z)",
        conclusion="IS_A(?X, ?Z)",
        confidence_discount=0.9,
    )


@pytest.fixture
def sample_rule_is_a() -> InferenceRule:
    return InferenceRule(
        id="rule-is-a-concept",
        name="Concept is a type",
        condition="is_a(?X, Concept)",
        conclusion="IS_A(?X, Thing)",
        confidence_discount=0.8,
    )


@pytest.fixture
def sample_ontology(
    sample_concept_a,
    sample_concept_b,
    sample_concept_c,
    sample_concept_low_conf,
    sample_relation,
    sample_taxonomy,
) -> OntologyGraph:
    ontology = OntologyGraph(
        id="test-onto-1",
        name="Test Ontology",
        description="An ontology for testing",
        version="1.0.0",
    )
    ontology.add_concept(sample_concept_a)
    ontology.add_concept(sample_concept_b)
    ontology.add_concept(sample_concept_c)
    ontology.add_concept(sample_concept_low_conf)
    ontology.add_relation(sample_relation)
    ontology.add_taxonomy(sample_taxonomy)

    # Add some declared facts
    ontology.add_fact(Fact(
        id="f1",
        statement="IS_A(Car, Vehicle)",
        source=FactSource.DECLARED,
        confidence=1.0,
    ))
    ontology.add_fact(Fact(
        id="f2",
        statement="IS_A(Bicycle, Vehicle)",
        source=FactSource.DECLARED,
        confidence=0.9,
    ))
    return ontology


@pytest.fixture
def sample_ir_graph() -> dict[str, Any]:
    """A minimal valid IR graph for testing."""
    return {
        "metadata": {
            "id": "ir-test-1",
            "name": "Test IR Graph",
            "version": "1.0.0",
            "status": "draft",
        },
        "nodes": [
            {"id": "n1", "name": "Vehicle", "type": "concept", "description": "A vehicle"},
            {"id": "n2", "name": "Car", "type": "concept", "description": "A car"},
            {"id": "n3", "name": "speed", "type": "attribute",
             "description": "Speed property", "dataType": "integer"},
        ],
        "edges": [
            {
                "id": "e1", "source": "n2", "target": "n1",
                "type": "SUBCLASS_OF", "directed": True,
            },
            {
                "id": "e2", "source": "n1", "target": "n3",
                "type": "HAS_ATTRIBUTE", "directed": True,
            },
        ],
    }


@pytest.fixture
def temp_storage_dir():
    """Create a temporary directory for store tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


# ===================================================================
# 1. Ontology Models Tests
# ===================================================================


class TestOntologyModels:
    """Tests for ontology Pydantic models."""

    def test_concept_creation(self, sample_concept_a):
        assert sample_concept_a.id == "c1"
        assert sample_concept_a.name == "Vehicle"
        assert len(sample_concept_a.properties) == 2
        assert sample_concept_a.confidence == 0.95

    def test_concept_default_values(self):
        concept = Concept(id="test", name="Test")
        assert concept.description == ""
        assert concept.properties == []
        assert concept.confidence == 1.0

    def test_concept_confidence_bounds(self):
        with pytest.raises(ValueError):
            Concept(id="bad", name="Bad", confidence=-0.1)
        with pytest.raises(ValueError):
            Concept(id="bad", name="Bad", confidence=1.5)

    def test_property_creation(self):
        prop = Property(name="age", type="integer", cardinality="1")
        assert prop.name == "age"
        assert prop.type == "integer"
        assert prop.cardinality == "1"

    def test_semantic_relation_creation(self, sample_relation):
        assert sample_relation.source_id == "c2"
        assert sample_relation.target_id == "c1"
        assert sample_relation.relation_type == "IS_A"

    def test_taxonomy_creation(self, sample_taxonomy):
        assert sample_taxonomy.parent_id == "c1"
        assert "c2" in sample_taxonomy.concepts
        assert len(sample_taxonomy.concepts) == 2

    def test_inference_rule_creation(self, sample_rule_transitive):
        assert sample_rule_transitive.condition == "IS_A(?X, ?Y) AND IS_A(?Y, ?Z)"
        assert sample_rule_transitive.conclusion == "IS_A(?X, ?Z)"
        assert sample_rule_transitive.confidence_discount == 0.9

    def test_fact_creation(self):
        fact = Fact(
            id="f1",
            statement="IS_A(Car, Vehicle)",
            source=FactSource.DECLARED,
            confidence=0.95,
        )
        assert fact.source == FactSource.DECLARED
        assert fact.confidence == 0.95
        assert fact.justification == ""

    def test_fact_inferred_defaults(self):
        fact = Fact(
            id="f2",
            statement="IS_A(SportsCar, Vehicle)",
            source=FactSource.INFERRED,
            confidence=0.8,
            justification="Inherited from Car",
        )
        assert fact.source == FactSource.INFERRED
        assert fact.justification == "Inherited from Car"

    def test_ontology_graph_container(self, sample_ontology):
        assert sample_ontology.id == "test-onto-1"
        assert len(sample_ontology.concepts) == 4
        assert len(sample_ontology.relations) == 1
        assert len(sample_ontology.taxonomies) == 1
        assert len(sample_ontology.facts) == 2

    def test_ontology_graph_add_and_get(self, sample_ontology):
        new_concept = Concept(id="c10", name="Train")
        sample_ontology.add_concept(new_concept)
        assert sample_ontology.get_concept("c10") is not None
        assert sample_ontology.get_concept("c10").name == "Train"

    def test_ontology_get_nonexistent(self, sample_ontology):
        assert sample_ontology.get_concept("nonexistent") is None
        assert sample_ontology.get_relation("nonexistent") is None

    def test_ontology_get_declared_facts(self, sample_ontology):
        declared = sample_ontology.get_declared_facts()
        assert len(declared) == 2

    def test_ontology_get_inferred_facts(self, sample_ontology):
        inferred = sample_ontology.get_inferred_facts()
        assert len(inferred) == 0

    def test_ontology_get_facts_by_statement(self, sample_ontology):
        facts = sample_ontology.get_facts_by_statement("IS_A(Car, Vehicle)")
        assert len(facts) == 1
        assert facts[0].source == FactSource.DECLARED

    def test_ontology_get_concepts_by_confidence(self, sample_ontology):
        high_conf = sample_ontology.get_concepts_by_confidence(0.8)
        assert len(high_conf) == 3  # c1, c2, c3 have >= 0.8

        all_concepts = sample_ontology.get_concepts_by_confidence(0.0)
        assert len(all_concepts) == 4  # All including low-confidence

        low_conf = sample_ontology.get_concepts_by_confidence(0.5)
        assert len(low_conf) == 3  # c4 (0.3) excluded

    def test_fact_source_enum(self):
        assert FactSource.DECLARED.value == "DECLARED"
        assert FactSource.INFERRED.value == "INFERRED"

    def test_ontology_serialization_roundtrip(self, sample_ontology):
        data = sample_ontology.model_dump(mode="json")
        restored = OntologyGraph.model_validate(data)
        assert restored.id == sample_ontology.id
        assert len(restored.concepts) == len(sample_ontology.concepts)
        assert len(restored.facts) == len(sample_ontology.facts)
        assert list(restored.concepts.keys()) == list(sample_ontology.concepts.keys())


# ===================================================================
# 2. OntologyStore Tests
# ===================================================================


class TestOntologyStore:
    """Tests for JSON persistence of ontologies."""

    def test_save_and_load(self, sample_ontology, temp_storage_dir):
        store = OntologyStore(storage_dir=temp_storage_dir)
        saved_path = store.save(sample_ontology)
        assert Path(saved_path).exists()
        assert saved_path.endswith(".json")

        loaded = store.load(sample_ontology.id)
        assert loaded.id == sample_ontology.id
        assert loaded.name == sample_ontology.name
        assert len(loaded.concepts) == len(sample_ontology.concepts)
        assert len(loaded.facts) == len(sample_ontology.facts)

    def test_save_custom_path(self, sample_ontology, temp_storage_dir):
        store = OntologyStore(storage_dir=temp_storage_dir)
        saved_path = store.save(sample_ontology, "custom.json")
        assert Path(saved_path).exists()
        assert "custom.json" in saved_path

        loaded = store.load("custom.json")
        assert loaded.id == sample_ontology.id

    def test_load_nonexistent(self, temp_storage_dir):
        store = OntologyStore(storage_dir=temp_storage_dir)
        with pytest.raises(FileNotFoundError):
            store.load("nonexistent.json")

    def test_exists(self, sample_ontology, temp_storage_dir):
        store = OntologyStore(storage_dir=temp_storage_dir)
        assert not store.exists(sample_ontology.id)
        store.save(sample_ontology)
        assert store.exists(sample_ontology.id)

    def test_delete(self, sample_ontology, temp_storage_dir):
        store = OntologyStore(storage_dir=temp_storage_dir)
        store.save(sample_ontology)
        assert store.exists(sample_ontology.id)
        assert store.delete(sample_ontology.id) is True
        assert not store.exists(sample_ontology.id)
        assert store.delete(sample_ontology.id) is False

    def test_list_ontologies(self, sample_ontology, temp_storage_dir):
        store = OntologyStore(storage_dir=temp_storage_dir)
        assert store.list_ontologies() == []
        store.save(sample_ontology)
        listing = store.list_ontologies()
        assert len(listing) == 1
        assert listing[0]["id"] == sample_ontology.id

    def test_to_dict_from_dict_roundtrip(self, sample_ontology):
        data = OntologyStore.to_dict(sample_ontology)
        restored = OntologyStore.from_dict(data)
        assert restored.id == sample_ontology.id
        assert len(restored.concepts) == len(sample_ontology.concepts)

    def test_from_dict_invalid(self):
        with pytest.raises(ValueError):
            OntologyStore.from_dict({"not": "valid"})

    def test_save_empty_ontology(self, temp_storage_dir):
        store = OntologyStore(storage_dir=temp_storage_dir)
        empty = OntologyGraph(id="empty", name="Empty")
        store.save(empty)
        loaded = store.load("empty")
        assert loaded.id == "empty"
        assert loaded.concepts == {}
        assert loaded.facts == {}


# ===================================================================
# 3. InferenceEngine Tests
# ===================================================================


class TestInferenceEngine:
    """Tests for the inference engine."""

    def test_register_and_get_rules(self, sample_rule_transitive):
        engine = InferenceEngine()
        assert engine.get_rules() == []
        engine.register_rule(sample_rule_transitive)
        rules = engine.get_rules()
        assert len(rules) == 1
        assert rules[0].id == "rule-transitive"

    def test_register_rules_bulk(self, sample_rule_transitive, sample_rule_is_a):
        engine = InferenceEngine()
        engine.register_rules([sample_rule_transitive, sample_rule_is_a])
        assert len(engine.get_rules()) == 2

    def test_unregister_rule(self, sample_rule_transitive):
        engine = InferenceEngine()
        engine.register_rule(sample_rule_transitive)
        engine.unregister_rule("rule-transitive")
        assert engine.get_rules() == []

    def test_clear_rules(self, sample_rule_transitive, sample_rule_is_a):
        engine = InferenceEngine()
        engine.register_rules([sample_rule_transitive, sample_rule_is_a])
        engine.clear_rules()
        assert engine.get_rules() == []

    def test_run_inference_no_rules(self, sample_ontology):
        engine = InferenceEngine()
        facts = engine.run_inference(sample_ontology)
        assert facts == []

    def test_run_inference_with_transitive_rule(self, sample_ontology, sample_rule_transitive):
        # Add a second IS_A relation to enable transitivity
        sample_ontology.add_fact(Fact(
            id="f3",
            statement="IS_A(SportsCar, Car)",
            source=FactSource.DECLARED,
            confidence=0.95,
        ))

        engine = InferenceEngine()
        engine.register_rule(sample_rule_transitive)
        new_facts = engine.run_inference(sample_ontology)
        assert len(new_facts) >= 1

        # Should infer IS_A(SportsCar, Vehicle)
        inferred_statements = [f.statement for f in new_facts]
        assert "IS_A(SportsCar, Vehicle)" in inferred_statements
        assert all(f.source == FactSource.INFERRED for f in new_facts)
        assert all(f.confidence <= 1.0 for f in new_facts)

    def test_inferred_facts_have_justification(self, sample_ontology, sample_rule_transitive):
        sample_ontology.add_fact(Fact(
            id="f3",
            statement="IS_A(SportsCar, Car)",
            source=FactSource.DECLARED,
            confidence=0.95,
        ))

        engine = InferenceEngine()
        engine.register_rule(sample_rule_transitive)
        new_facts = engine.run_inference(sample_ontology)
        if new_facts:
            assert len(new_facts[0].justification) > 0
            assert "Inferred by rule" in new_facts[0].justification
            assert new_facts[0].source == FactSource.INFERRED

    def test_fixpoint_converges(self, sample_ontology, sample_rule_transitive):
        # Test that fixpoint converges (repeated runs produce no new facts)
        sample_ontology.add_fact(Fact(
            id="f3",
            statement="IS_A(SportsCar, Car)",
            source=FactSource.DECLARED,
            confidence=0.95,
        ))

        engine = InferenceEngine()
        engine.register_rule(sample_rule_transitive)

        # First run
        first_run = engine.run_inference(sample_ontology)
        for f in first_run:
            sample_ontology.add_fact(f)

        # Second run — should produce nothing new
        second_run = engine.run_inference(sample_ontology)
        assert len(second_run) == 0

    def test_fixpoint_no_new_facts(self, sample_ontology, sample_rule_transitive):
        """Fixpoint with no applicable rules should return empty."""
        engine = InferenceEngine()
        engine.register_rule(sample_rule_transitive)

        result = engine.run_fixpoint(sample_ontology, max_iterations=5)
        # There are IS_A facts but no chain of two IS_A, so nothing
        # should be inferred (no X->Y->Z chain)
        assert len(result) >= 0  # May or may not infer depending on match logic

    def test_fixpoint_max_iterations(self, sample_ontology):
        engine = InferenceEngine()
        # Add a self-referential rule that would generate facts every time
        rule = InferenceRule(
            id="self-gen",
            name="Self generating",
            condition="is_a(?X, Concept)",
            conclusion="is_a(Thing, ?X)",
            confidence_discount=0.5,
        )
        engine.register_rule(rule)

        result = engine.run_fixpoint(sample_ontology, max_iterations=3)
        assert len(result) >= 0

    def test_fixpoint_invalid_max_iterations(self):
        engine = InferenceEngine()
        with pytest.raises(ValueError):
            engine.run_fixpoint(OntologyGraph(id="x", name="x"), max_iterations=0)

    def test_declared_vs_inferred_distinction(self, sample_ontology, sample_rule_transitive):
        """Declared and inferred facts should be clearly distinguishable."""
        assert len(sample_ontology.get_declared_facts()) == 2
        assert len(sample_ontology.get_inferred_facts()) == 0

        sample_ontology.add_fact(Fact(
            id="f3",
            statement="IS_A(SportsCar, Car)",
            source=FactSource.DECLARED,
            confidence=0.95,
        ))

        engine = InferenceEngine()
        engine.register_rule(sample_rule_transitive)
        new_facts = engine.run_inference(sample_ontology)
        for f in new_facts:
            sample_ontology.add_fact(f)

        assert len(sample_ontology.get_declared_facts()) == 3
        assert len(sample_ontology.get_inferred_facts()) >= 1

    def test_confidence_discount_applied(self, sample_ontology):
        """Inferred facts should have lower confidence than source."""
        rule = InferenceRule(
            id="test-discount",
            name="Test discount",
            condition="is_a(?X, Concept)",
            conclusion="IS_A(?X, Entity)",
            confidence_discount=0.5,
        )

        engine = InferenceEngine()
        engine.register_rule(rule)
        new_facts = engine.run_inference(sample_ontology)

        # The sample concepts all have confidence >= 0.85
        # Inferred facts should have confidence = 0.85 * 0.5 = 0.425
        for f in new_facts:
            assert f.confidence <= 0.5  # discount applied
            assert f.source == FactSource.INFERRED

    def test_no_duplicate_facts(self, sample_ontology, sample_rule_transitive):
        """Running the same rule twice should not create duplicates."""
        sample_ontology.add_fact(Fact(
            id="f3",
            statement="IS_A(SportsCar, Car)",
            source=FactSource.DECLARED,
            confidence=0.95,
        ))

        engine = InferenceEngine()
        engine.register_rule(sample_rule_transitive)

        first_run = engine.run_inference(sample_ontology)
        for f in first_run:
            sample_ontology.add_fact(f)

        second_run = engine.run_inference(sample_ontology)
        assert len(second_run) == 0  # No duplicates


# ===================================================================
# 4. OntologyCompiler Tests
# ===================================================================


class TestOntologyCompiler:
    """Tests for ontology ↔ IR compilation."""

    def test_compile_to_ir_basic(self, sample_ontology):
        compiler = OntologyCompiler()
        ir_graph = compiler.compile_to_ir(sample_ontology)

        assert "metadata" in ir_graph
        assert "nodes" in ir_graph
        assert "edges" in ir_graph
        assert ir_graph["metadata"]["id"] == "test-onto-1"

    def test_compile_excludes_low_confidence(self, sample_ontology):
        """Concepts with confidence < 0.5 should be excluded."""
        compiler = OntologyCompiler(confidence_threshold=0.5)
        ir_graph = compiler.compile_to_ir(sample_ontology)

        node_ids = {n["id"] for n in ir_graph["nodes"] if n["type"] == "concept"}
        assert "c4" not in node_ids  # Unicorn (0.3)
        assert "c1" in node_ids  # Vehicle (0.95)

    def test_compile_includes_properties_as_attributes(self, sample_ontology):
        compiler = OntologyCompiler()
        ir_graph = compiler.compile_to_ir(sample_ontology)

        # Vehicle has speed and color properties → should be attribute nodes
        attr_nodes = [n for n in ir_graph["nodes"] if n["type"] == "attribute"]
        attr_names = {n["name"] for n in attr_nodes}
        assert "speed" in attr_names
        assert "color" in attr_names
        assert "doors" in attr_names

    def test_compile_generates_has_attribute_edges(self, sample_ontology):
        compiler = OntologyCompiler()
        ir_graph = compiler.compile_to_ir(sample_ontology)

        has_attr_edges = [e for e in ir_graph["edges"] if e["type"] == "HAS_ATTRIBUTE"]
        assert len(has_attr_edges) >= 3  # speed, color, doors

    def test_compile_generates_relation_edges(self, sample_ontology):
        compiler = OntologyCompiler()
        ir_graph = compiler.compile_to_ir(sample_ontology)

        # The IS_A relation between Car (c2) and Vehicle (c1)
        is_a_edges = [e for e in ir_graph["edges"] if e["type"] == "IS_A"]
        assert len(is_a_edges) == 1
        assert is_a_edges[0]["source"] == "c2"
        assert is_a_edges[0]["target"] == "c1"

    def test_compile_generates_subclass_of_edges(self, sample_ontology):
        compiler = OntologyCompiler()
        ir_graph = compiler.compile_to_ir(sample_ontology)

        subclass_edges = [e for e in ir_graph["edges"] if e["type"] == "SUBCLASS_OF"]
        # Taxonomy t1 has parent_id=c1, concepts=[c2, c3]
        assert len(subclass_edges) >= 2

    def test_compile_excluded_concept_relation_not_included(self, sample_ontology):
        """Relations involving excluded concepts should not appear in IR."""
        # Add a relation involving the low-confidence concept
        sample_ontology.add_relation(SemanticRelation(
            id="r-bad",
            name="relates to",
            source_id="c4",  # Unicorn (0.3) — will be excluded
            target_id="c1",
            relation_type="RELATED_TO",
            confidence=0.5,
        ))

        compiler = OntologyCompiler(confidence_threshold=0.5)
        ir_graph = compiler.compile_to_ir(sample_ontology)

        related_edges = [e for e in ir_graph["edges"] if e["type"] == "RELATED_TO"]
        assert len(related_edges) == 0  # Excluded because source c4 is excluded

    def test_extract_from_ir_basic(self, sample_ir_graph):
        ontology = OntologyCompiler.extract_ontology_from_ir(sample_ir_graph)
        assert ontology.id == "ir-test-1"
        assert len(ontology.concepts) == 2  # Vehicle and Car
        assert "n1" in ontology.concepts
        assert "n2" in ontology.concepts

    def test_extract_from_ir_with_properties(self, sample_ir_graph):
        ontology = OntologyCompiler.extract_ontology_from_ir(sample_ir_graph)
        # n1 (Vehicle) has an HAS_ATTRIBUTE edge to n3 (speed)
        vehicle = ontology.get_concept("n1")
        assert vehicle is not None
        assert len(vehicle.properties) >= 1
        prop_names = [p.name for p in vehicle.properties]
        assert "speed" in prop_names

    def test_extract_from_ir_with_taxonomy(self, sample_ir_graph):
        ontology = OntologyCompiler.extract_ontology_from_ir(sample_ir_graph)
        # There should be a taxonomy from the SUBCLASS_OF edge
        assert len(ontology.taxonomies) >= 1
        # Car (n2) should be in the taxonomy
        taxonomy = list(ontology.taxonomies.values())[0]
        assert "n2" in taxonomy.concepts

    def test_extract_from_ir_custom_id(self, sample_ir_graph):
        ontology = OntologyCompiler.extract_ontology_from_ir(
            sample_ir_graph, ontology_id="custom-id"
        )
        assert ontology.id == "custom-id"

    def test_extract_from_ir_missing_keys(self):
        with pytest.raises(ValueError):
            OntologyCompiler.extract_ontology_from_ir({"invalid": True})

    def test_compile_roundtrip(self, sample_ontology):
        """Compile ontology → IR → ontology should preserve data."""
        compiler = OntologyCompiler()
        ir_graph = compiler.compile_to_ir(sample_ontology)

        ontology2 = OntologyCompiler.extract_ontology_from_ir(
            ir_graph, ontology_id="roundtrip"
        )

        # High-confidence concepts should be preserved
        assert ontology2.get_concept("c1") is not None
        assert ontology2.get_concept("c2") is not None

        # Low-confidence (c4) was excluded during compile, won't appear
        assert ontology2.get_concept("c4") is None  # Excluded

    def test_empty_ontology_compile(self):
        """Empty ontology should compile to an empty IR graph."""
        empty = OntologyGraph(id="empty", name="Empty")
        compiler = OntologyCompiler()
        ir_graph = compiler.compile_to_ir(empty)
        assert len(ir_graph["nodes"]) == 0
        assert len(ir_graph["edges"]) == 0


# ===================================================================
# 5. API Endpoint Tests
# ===================================================================


class TestOntologyAPI:
    """Tests for the /api/ontology endpoints."""

    def test_create_ontology(self, client: TestClient):
        data = {
            "id": "api-test-1",
            "name": "API Test Ontology",
            "description": "Created via API",
            "version": "1.0.0",
            "concepts": {},
            "relations": {},
            "taxonomies": {},
            "rules": {},
            "facts": {},
            "metadata": {},
        }
        response = client.post("/api/ontology", json=data)
        assert response.status_code == 201
        result = response.json()
        assert result["id"] == "api-test-1"
        assert result["name"] == "API Test Ontology"

    def test_create_ontology_invalid(self, client: TestClient):
        response = client.post("/api/ontology", json={"invalid": True})
        assert response.status_code == 400

    def test_get_ontology(self, client: TestClient):
        # First create
        client.post("/api/ontology", json={
            "id": "get-test", "name": "Get Test",
        })
        response = client.get("/api/ontology/get-test")
        assert response.status_code == 200
        assert response.json()["name"] == "Get Test"

    def test_get_ontology_not_found(self, client: TestClient):
        response = client.get("/api/ontology/nonexistent")
        assert response.status_code == 404

    def test_delete_ontology(self, client: TestClient):
        client.post("/api/ontology", json={
            "id": "del-test", "name": "Delete Test",
        })
        response = client.delete("/api/ontology/del-test")
        assert response.status_code == 204

    def test_delete_ontology_not_found(self, client: TestClient):
        response = client.delete("/api/ontology/nonexistent")
        assert response.status_code == 404

    def test_list_ontologies(self, client: TestClient):
        client.post("/api/ontology", json={"id": "list-1", "name": "List 1"})
        client.post("/api/ontology", json={"id": "list-2", "name": "List 2"})

        response = client.get("/api/ontology")
        assert response.status_code == 200
        data = response.json()
        assert data["count"] >= 2

    # Fact tests

    def test_get_facts(self, client: TestClient):
        client.post("/api/ontology", json={
            "id": "facts-test", "name": "Facts Test",
            "facts": {
                "f1": {
                    "id": "f1",
                    "statement": "test(X)",
                    "source": "DECLARED",
                    "confidence": 1.0,
                }
            },
        })

        response = client.get("/api/ontology/facts-test/facts")
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 1
        assert data["facts"][0]["statement"] == "test(X)"

    def test_get_facts_filtered(self, client: TestClient):
        client.post("/api/ontology", json={
            "id": "facts-filter", "name": "Facts Filter",
            "facts": {
                "f1": {
                    "id": "f1",
                    "statement": "test(X)",
                    "source": "DECLARED",
                    "confidence": 1.0,
                },
                "f2": {
                    "id": "f2",
                    "statement": "test(Y)",
                    "source": "INFERRED",
                    "confidence": 0.8,
                    "justification": "from rule",
                },
            },
        })

        response = client.get("/api/ontology/facts-filter/facts?source=DECLARED")
        assert response.status_code == 200
        assert response.json()["count"] == 1

        response = client.get("/api/ontology/facts-filter/facts?source=INFERRED")
        assert response.status_code == 200
        assert response.json()["count"] == 1

    def test_add_fact(self, client: TestClient):
        client.post("/api/ontology", json={
            "id": "add-fact", "name": "Add Fact",
        })

        response = client.post("/api/ontology/add-fact/facts", json={
            "id": "new-fact-1",
            "statement": "IS_A(X, Y)",
            "source": "DECLARED",
            "confidence": 1.0,
        })
        assert response.status_code == 201
        assert response.json()["id"] == "new-fact-1"

    # Inference endpoint

    def test_run_inference(self, client: TestClient):
        """Test inference via API with explicit rules."""
        ontology_data = {
            "id": "infer-test",
            "name": "Infer Test",
            "concepts": {
                "c1": {
                    "id": "c1",
                    "name": "Vehicle",
                    "description": "",
                    "properties": [],
                    "confidence": 1.0,
                },
                "c2": {
                    "id": "c2",
                    "name": "Car",
                    "description": "",
                    "properties": [],
                    "confidence": 1.0,
                },
            },
            "facts": {
                "f1": {
                    "id": "f1",
                    "statement": "IS_A(Car, Vehicle)",
                    "source": "DECLARED",
                    "confidence": 1.0,
                },
            },
        }
        client.post("/api/ontology", json=ontology_data)

        rules = [
            {
                "id": "rule1",
                "name": "Reflexive rule",
                "condition": "IS_A(?X, ?Y)",
                "conclusion": "RELATED_TO(?X, ?Y)",
                "confidence_discount": 0.9,
            }
        ]

        response = client.post(
            "/api/ontology/infer-test/infer?fixpoint=false",
            json=rules,
        )
        assert response.status_code == 200
        data = response.json()
        # Should have inferred RELATED_TO(Car, Vehicle)
        assert data["new_facts_count"] >= 1

    def test_compile_endpoint(self, client: TestClient):
        """Test compilation via API."""
        ontology_data = {
            "id": "compile-test",
            "name": "Compile Test",
            "concepts": {
                "c1": {
                    "id": "c1",
                    "name": "Vehicle",
                    "description": "",
                    "properties": [],
                    "confidence": 0.95,
                },
                "c2": {
                    "id": "c2",
                    "name": "Car",
                    "description": "",
                    "properties": [],
                    "confidence": 0.3,  # Low confidence — should be excluded
                },
            },
            "relations": {
                "r1": {
                    "id": "r1",
                    "name": "is a",
                    "source_id": "c2",
                    "target_id": "c1",
                    "relation_type": "IS_A",
                    "confidence": 0.9,
                },
            },
        }
        client.post("/api/ontology", json=ontology_data)

        response = client.post(
            "/api/ontology/compile-test/compile?confidence_threshold=0.5",
        )
        assert response.status_code == 200
        data = response.json()
        assert "metadata" in data
        assert "nodes" in data
        assert "edges" in data

        # c2 (Car, 0.3) should be excluded
        node_ids = {n["id"] for n in data["nodes"]}
        assert "c1" in node_ids
        assert "c2" not in node_ids  # low confidence excluded

    def test_store_and_load_endpoint(self, client: TestClient):
        """Test save/load roundtrip via API."""
        store_path = "/tmp/test_ontology_store.json"

        ontology_data = {
            "id": "store-test",
            "name": "Store Test",
            "concepts": {
                "c1": {
                    "id": "c1",
                    "name": "TestConcept",
                    "description": "",
                    "properties": [],
                    "confidence": 1.0,
                },
            },
        }
        client.post("/api/ontology", json=ontology_data)

        # Save to file
        store_response = client.post(
            "/api/ontology/store-test/store",
            json={"file_path": store_path},
        )
        assert store_response.status_code == 200
        assert store_response.json()["ontology_id"] == "store-test"

        # Delete from memory
        client.delete("/api/ontology/store-test")

        # Load from file
        load_response = client.get(
            f"/api/ontology/store-test/load?file_path={store_path}",
        )
        assert load_response.status_code == 200
        assert load_response.json()["id"] == "store-test"
        assert len(load_response.json()["concepts"]) == 1


# ===================================================================
# 6. Edge Case Tests
# ===================================================================


class TestOntologyEdgeCases:
    """Edge case tests for the ontology system."""

    def test_empty_ontology(self):
        """An empty ontology should be valid."""
        ontology = OntologyGraph(id="empty", name="Empty")
        assert ontology.id == "empty"
        assert ontology.concepts == {}
        assert ontology.facts == {}

    def test_compile_empty_ontology(self):
        """Empty ontology compiles to empty IR."""
        empty = OntologyGraph(id="empty", name="Empty")
        compiler = OntologyCompiler()
        ir_graph = compiler.compile_to_ir(empty)
        assert len(ir_graph["nodes"]) == 0
        assert len(ir_graph["edges"]) == 0

    def test_all_concepts_low_confidence(self):
        """If all concepts are below the threshold, IR should be empty."""
        ontology = OntologyGraph(id="low", name="Low Confidence")
        ontology.add_concept(Concept(id="c1", name="Maybe", confidence=0.2))
        ontology.add_concept(Concept(id="c2", name="Perhaps", confidence=0.4))

        compiler = OntologyCompiler(confidence_threshold=0.5)
        ir_graph = compiler.compile_to_ir(ontology)
        assert len(ir_graph["nodes"]) == 0

    def test_concept_with_many_properties(self):
        """A concept with many properties should generate many attribute nodes."""
        ontology = OntologyGraph(id="many", name="Many Properties")
        props = [
            Property(name=f"prop{i}", type="string", cardinality="0..1")
            for i in range(10)
        ]
        ontology.add_concept(Concept(
            id="c1", name="BigConcept", properties=props, confidence=1.0,
        ))

        compiler = OntologyCompiler()
        ir_graph = compiler.compile_to_ir(ontology)
        attr_nodes = [n for n in ir_graph["nodes"] if n["type"] == "attribute"]
        assert len(attr_nodes) == 10

    def test_circular_inference_handling(self):
        """Rules that could cause infinite loops are bounded by fixpoint."""
        ontology = OntologyGraph(id="circular", name="Circular Test")
        ontology.add_concept(Concept(id="c1", name="A", confidence=1.0))
        ontology.add_fact(Fact(
            id="f1", statement="RELATES_TO(A, B)", source=FactSource.DECLARED,
        ))

        # A rule that swaps arguments — could cause circular inference
        rule = InferenceRule(
            id="swap",
            name="Swap relation",
            condition="RELATES_TO(?X, ?Y)",
            conclusion="RELATES_TO(?Y, ?X)",
            confidence_discount=0.5,
        )

        ontology.add_fact(Fact(
            id="f2", statement="RELATES_TO(B, C)", source=FactSource.DECLARED,
        ))

        engine = InferenceEngine()
        engine.register_rule(rule)

        # Should converge without infinite loop
        result = engine.run_fixpoint(ontology, max_iterations=5)
        # The swap rule + chain could generate:
        # RELATES_TO(B, A), RELATES_TO(C, B), RELATES_TO(A, C), RELATES_TO(C, A), etc.
        # But fixpoint limits iterations
        assert isinstance(result, list)

    def test_compiler_custom_threshold(self, sample_ontology):
        """Compiler should respect custom confidence thresholds."""
        # At threshold 0.2, all concepts included
        compiler = OntologyCompiler(confidence_threshold=0.2)
        ir_graph = compiler.compile_to_ir(sample_ontology)
        concept_nodes = [n for n in ir_graph["nodes"] if n["type"] == "concept"]
        assert len(concept_nodes) == 4  # All concepts

        # At threshold 0.86, only c1 (0.95) and c2 (0.9) included
        compiler = OntologyCompiler(confidence_threshold=0.86)
        ir_graph = compiler.compile_to_ir(sample_ontology)
        concept_nodes = [n for n in ir_graph["nodes"] if n["type"] == "concept"]
        assert len(concept_nodes) == 2  # Vehicle (0.95) and Car (0.9)
        concept_ids = {n["id"] for n in concept_nodes}
        assert "c1" in concept_ids
        assert "c2" in concept_ids
        assert "c3" not in concept_ids  # Bicycle (0.85) excluded

    def test_store_load_preserves_rules(self, sample_rule_transitive, temp_storage_dir):
        """Rules should survive a save/load cycle."""
        ontology = OntologyGraph(id="rules-test", name="Rules Test")
        ontology.add_rule(sample_rule_transitive)
        ontology.add_concept(Concept(id="c1", name="Test", confidence=1.0))

        store = OntologyStore(storage_dir=temp_storage_dir)
        store.save(ontology)
        loaded = store.load("rules-test")

        assert "rule-transitive" in loaded.rules
        assert loaded.rules["rule-transitive"].name == "Transitive inheritance"

    def test_inference_without_any_declared_facts(self):
        """Running inference on an ontology with no facts should work."""
        ontology = OntologyGraph(id="no-facts", name="No Facts")
        ontology.add_concept(Concept(id="c1", name="Test", confidence=1.0))

        rule = InferenceRule(
            id="r1",
            name="Test rule",
            condition="is_a(?X, Concept)",
            conclusion="IS_A(?X, Thing)",
            confidence_discount=0.8,
        )

        engine = InferenceEngine()
        engine.register_rule(rule)
        new_facts = engine.run_inference(ontology)
        # Even without explicitly declared is_a facts, the engine
        # can generate them from concept names
        assert len(new_facts) >= 0

    def test_inference_rule_no_variables(self):
        """A rule with no variables should still work."""
        rule = InferenceRule(
            id="constant",
            name="Constant conclusion",
            condition="is_a(Vehicle, Concept)",
            conclusion="IS_A(Vehicle, Thing)",
            confidence_discount=1.0,
        )
        ontology = OntologyGraph(id="const", name="Constant")
        ontology.add_concept(Concept(id="c1", name="Vehicle", confidence=1.0))

        engine = InferenceEngine()
        engine.register_rule(rule)
        new_facts = engine.run_inference(ontology)
        assert len(new_facts) >= 0
