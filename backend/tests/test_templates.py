"""Tests for Template Registry, Renderer, Generation Plan, and Executor.

Tests cover:
1. TemplateRegistry (register, list, load, get, remove, kind mapping)
2. TemplateRenderer (render, filters, error handling, entity-based rendering)
3. Custom Jinja2 filters (snake_case, camel_case, PascalCase, pluralize, capitalize_first)
4. GenerationPlan & GenerationStep model validation
5. Topological sort (ordering, cycle detection, missing deps)
6. PlanExecutor (sequential execution, hooks, retry, error strategies)
7. Example templates render correctly
8. API endpoints
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from jinja2 import Template

from src.services.templates import (
    ExecutionResult,
    GenerationPlan,
    GenerationStep,
    PlanExecutor,
    StepResult,
    TemplateRegistry,
    TemplateRenderer,
    topological_sort,
    validate_plan,
)
from src.services.templates.generation_plan import (
    ErrorStrategy,
    ExecutionMode,
    RetryPolicy,
)
from src.services.templates.template_renderer import (
    TemplateRenderError,
    filter_camel_case,
    filter_capitalize_first,
    filter_pascal_case,
    filter_pluralize,
    filter_snake_case,
)

# ======================================================================
# Filter Tests
# ======================================================================


class TestSnakeCaseFilter:
    """Tests for the snake_case filter."""

    def test_camel_case_to_snake(self):
        assert filter_snake_case("firstName") == "first_name"

    def test_pascal_case_to_snake(self):
        assert filter_snake_case("MyClass") == "my_class"

    def test_spaced_to_snake(self):
        assert filter_snake_case("  spaced  name ") == "spaced_name"

    def test_hyphenated_to_snake(self):
        assert filter_snake_case("user-id") == "user_id"

    def test_already_snake(self):
        assert filter_snake_case("already_snake") == "already_snake"

    def test_consecutive_uppercase(self):
        assert filter_snake_case("HTTPResponse") == "http_response"

    def test_empty_string(self):
        assert filter_snake_case("") == ""

    def test_non_string_input(self):
        assert filter_snake_case(123) == "123"

    def test_single_word(self):
        assert filter_snake_case("hello") == "hello"


class TestCamelCaseFilter:
    """Tests for the camelCase filter."""

    def test_snake_to_camel(self):
        assert filter_camel_case("my_class") == "myClass"

    def test_pascal_to_camel(self):
        assert filter_camel_case("MyClass") == "myClass"

    def test_already_camel(self):
        assert filter_camel_case("firstName") == "firstName"

    def test_single_word(self):
        assert filter_camel_case("hello") == "hello"

    def test_hyphenated(self):
        assert filter_camel_case("user-id") == "userId"

    def test_empty_string(self):
        assert filter_camel_case("") == ""


class TestPascalCaseFilter:
    """Tests for the PascalCase filter."""

    def test_snake_to_pascal(self):
        assert filter_pascal_case("my_class") == "MyClass"

    def test_camel_to_pascal(self):
        assert filter_pascal_case("firstName") == "FirstName"

    def test_already_pascal(self):
        assert filter_pascal_case("MyClass") == "MyClass"

    def test_single_word(self):
        assert filter_pascal_case("hello") == "Hello"

    def test_empty_string(self):
        assert filter_pascal_case("") == ""


class TestPluralizeFilter:
    """Tests for the pluralize filter."""

    def test_regular_s(self):
        assert filter_pluralize("user") == "users"

    def test_ending_in_y(self):
        assert filter_pluralize("category") == "categories"

    def test_ending_in_y_vowel(self):
        assert filter_pluralize("key") == "keys"

    def test_ending_in_s(self):
        assert filter_pluralize("class") == "classes"

    def test_ending_in_sh(self):
        assert filter_pluralize("brush") == "brushes"

    def test_ending_in_ch(self):
        assert filter_pluralize("match") == "matches"

    def test_ending_in_x(self):
        assert filter_pluralize("box") == "boxes"

    def test_ending_in_z(self):
        assert filter_pluralize("buzz") == "buzzes"

    def test_irregular_person(self):
        assert filter_pluralize("person") == "people"

    def test_irregular_child(self):
        assert filter_pluralize("child") == "children"

    def test_irregular_sheep(self):
        assert filter_pluralize("sheep") == "sheep"

    def test_irregular_fish(self):
        assert filter_pluralize("fish") == "fish"

    def test_irregular_preserves_casing(self):
        assert filter_pluralize("Person") == "People"

    def test_empty_string(self):
        assert filter_pluralize("") == ""


class TestCapitalizeFirstFilter:
    """Tests for the capitalize_first filter."""

    def test_lowercase(self):
        assert filter_capitalize_first("hello") == "Hello"

    def test_already_capitalized(self):
        assert filter_capitalize_first("Hello") == "Hello"

    def test_single_char(self):
        assert filter_capitalize_first("a") == "A"

    def test_empty_string(self):
        assert filter_capitalize_first("") == ""

    def test_non_string(self):
        assert filter_capitalize_first(123) == 123


# ======================================================================
# TemplateRegistry Tests
# ======================================================================


class TestTemplateRegistry:
    """Tests for TemplateRegistry."""

    def test_register_and_get(self):
        """Should register a template from string and retrieve it."""
        registry = TemplateRegistry()
        registry.register_template("hello", "Hello {{ name }}!")
        tmpl = registry.get_template("hello")
        assert isinstance(tmpl, Template)
        assert tmpl.render({"name": "World"}) == "Hello World!"

    def test_register_duplicate_raises(self):
        """Should raise ValueError for duplicate template names."""
        registry = TemplateRegistry()
        registry.register_template("test", "content")
        with pytest.raises(ValueError, match="already registered"):
            registry.register_template("test", "other")

    def test_get_missing_raises(self):
        """Should raise ValueError for unknown template."""
        registry = TemplateRegistry()
        with pytest.raises(ValueError, match="not found"):
            registry.get_template("nonexistent")

    def test_list_templates(self):
        """Should return sorted list of registered template names."""
        registry = TemplateRegistry()
        registry.register_template("z_template", "z")
        registry.register_template("a_template", "a")
        registry.register_template("m_template", "m")
        assert registry.list_templates() == [
            "a_template", "m_template", "z_template"
        ]

    def test_register_with_kind(self):
        """Should map templates to node kinds."""
        registry = TemplateRegistry()
        registry.register_template("py_model", "model", kind="concept")
        registry.register_template("py_attr", "attr", kind="attribute")
        assert registry.get_templates_by_kind("concept") == ["py_model"]
        assert registry.get_templates_by_kind("attribute") == ["py_attr"]
        assert registry.get_templates_by_kind("relation") == []

    def test_register_with_metadata(self):
        """Should store metadata with template."""
        registry = TemplateRegistry()
        meta = {"author": "test", "version": 1}
        registry.register_template("test", "content", metadata=meta)
        assert registry.get_metadata("test") == meta

    def test_has_template(self):
        """Should correctly check template existence."""
        registry = TemplateRegistry()
        assert not registry.has_template("test")
        registry.register_template("test", "content")
        assert registry.has_template("test")

    def test_remove_template(self):
        """Should remove a template and its kind mapping."""
        registry = TemplateRegistry()
        registry.register_template("test", "content", kind="concept")
        registry.remove_template("test")
        assert not registry.has_template("test")
        assert "test" not in registry.get_templates_by_kind("concept")

    def test_remove_missing_raises(self):
        """Should raise ValueError when removing nonexistent template."""
        registry = TemplateRegistry()
        with pytest.raises(ValueError, match="not found"):
            registry.remove_template("nonexistent")

    def test_clear(self):
        """Should remove all templates."""
        registry = TemplateRegistry()
        registry.register_template("a", "a")
        registry.register_template("b", "b", kind="concept")
        registry.clear()
        assert registry.list_templates() == []
        assert registry.get_templates_by_kind("concept") == []

    def test_load_from_directory(self):
        """Should load .j2 files from a directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create template files
            Path(tmpdir, "hello.j2").write_text("Hello {{ name }}!")
            Path(tmpdir, "bye.j2").write_text("Bye {{ name }}!")
            # Create a non-template file (should be ignored)
            Path(tmpdir, "readme.txt").write_text("Not a template")

            registry = TemplateRegistry()
            names = registry.load_from_directory(tmpdir)

            assert "hello" in names
            assert "bye" in names
            assert len(names) == 2

            tmpl = registry.get_template("hello")
            assert tmpl.render({"name": "World"}) == "Hello World!"

    def test_load_from_directory_not_found(self):
        """Should raise FileNotFoundError for invalid directory."""
        registry = TemplateRegistry()
        with pytest.raises(FileNotFoundError):
            registry.load_from_directory("/nonexistent/path")

    def test_register_from_file(self):
        """Should register a single file and return its name."""
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir, "mytemplate.j2")
            filepath.write_text("Hello {{ name }}!")

            registry = TemplateRegistry()
            name = registry.register_template_from_file(str(filepath))
            assert name == "mytemplate"

            tmpl = registry.get_template("mytemplate")
            assert tmpl.render({"name": "Test"}) == "Hello Test!"

    def test_register_from_file_not_found(self):
        """Should raise FileNotFoundError for missing file."""
        registry = TemplateRegistry()
        with pytest.raises(FileNotFoundError):
            registry.register_template_from_file("/nonexistent/file.j2")


# ======================================================================
# TemplateRenderer Tests
# ======================================================================


class TestTemplateRenderer:
    """Tests for TemplateRenderer."""

    @pytest.fixture
    def renderer(self):
        return TemplateRenderer()

    def test_render_registered_template(self, renderer):
        """Should render a template registered in the registry."""
        registry = TemplateRegistry()
        registry.register_template("greet", "Hello {{ name }}!")
        renderer = TemplateRenderer(registry)
        output = renderer.render_template("greet", {"name": "World"})
        assert output == "Hello World!"

    def test_render_missing_template_raises(self):
        """Should raise ValueError for unregistered template."""
        renderer = TemplateRenderer()
        with pytest.raises(ValueError, match="not found"):
            renderer.render_template("nonexistent", {})

    def test_render_from_string(self, renderer):
        """Should render inline template string."""
        output = renderer.render_from_string(
            "Hello {{ name }}! Today is {{ day }}.",
            {"name": "Test", "day": "Monday"},
        )
        assert output == "Hello Test! Today is Monday."

    def test_render_from_string_missing_var(self, renderer):
        """Should raise TemplateRenderError on missing variable."""
        with pytest.raises(TemplateRenderError, match="Missing variable"):
            renderer.render_from_string("Hello {{ name }}!", {})

    def test_render_from_entity(self, renderer):
        """Should render template using entity tree."""
        renderer.registry.register_template(
            "entity_model",
            "Entity: {{ entity.name }}\n"
            "Fields: {% for f in fields %}{{ f.entity.name }},{% endfor %}",
        )

        entity_tree = {
            "entity": {"id": "c1", "name": "Person", "_kind": "concept"},
            "fields": [
                {"entity": {"id": "a1", "name": "firstName", "type": "string"}},
                {"entity": {"id": "a2", "name": "lastName", "type": "string"}},
            ],
            "relations": [],
        }

        output = renderer.render_from_entity(entity_tree, "entity_model")
        assert "Entity: Person" in output
        assert "firstName" in output
        assert "lastName" in output

    def test_render_with_custom_filters(self, renderer):
        """Should use custom filters in templates."""
        output = renderer.render_from_string(
            "{{ 'my_class' | PascalCase }}",
            {},
        )
        assert output == "MyClass"

    def test_render_with_snake_case_filter(self, renderer):
        output = renderer.render_from_string(
            "{{ 'MyClass' | snake_case }}", {}
        )
        assert output == "my_class"

    def test_render_with_camel_case_filter(self, renderer):
        output = renderer.render_from_string(
            "{{ 'my_class' | camel_case }}", {}
        )
        assert output == "myClass"

    def test_render_with_pluralize_filter(self, renderer):
        output = renderer.render_from_string(
            "{{ 'category' | pluralize }}", {}
        )
        assert output == "categories"

    def test_render_with_capitalize_first_filter(self, renderer):
        output = renderer.render_from_string(
            "{{ 'hello' | capitalize_first }}", {}
        )
        assert output == "Hello"

    def test_render_complex_template(self, renderer):
        """Should render template with control flow."""
        template = (
            "{% if items %}Items:\n"
            "{% for item in items %}"
            "  - {{ item | snake_case }}\n"
            "{% endfor %}"
            "{% else %}No items{% endif %}"
        )
        output = renderer.render_from_string(template, {"items": ["FooBar", "baz_qux"]})
        assert "foo_bar" in output
        assert "baz_qux" in output


# ======================================================================
# GenerationStep & GenerationPlan Model Tests
# ======================================================================


class TestGenerationStep:
    """Tests for GenerationStep Pydantic model."""

    def test_valid_step(self):
        """Should create a valid step."""
        step = GenerationStep(name="test", template_name="hello")
        assert step.name == "test"
        assert step.template_name == "hello"
        assert step.depends_on == []
        assert step.output_path is None

    def test_step_with_all_fields(self):
        """Should create a step with all fields."""
        step = GenerationStep(
            name="full",
            template_name="tmpl",
            entity_id="e1",
            depends_on=["prev"],
            output_path="out.py",
            context_overrides={"extra": "value"},
            metadata={"tags": ["test"]},
        )
        assert step.entity_id == "e1"
        assert step.depends_on == ["prev"]
        assert step.output_path == "out.py"
        assert step.context_overrides == {"extra": "value"}

    def test_empty_name_raises(self):
        """Should raise validation error for empty name."""
        with pytest.raises(ValueError):
            GenerationStep(name="  ", template_name="t")

    def test_self_dependency_raises(self):
        """Should raise validation error for self-dependency."""
        with pytest.raises(ValueError, match="cannot depend on itself"):
            GenerationStep(name="self", template_name="t", depends_on=["self"])


class TestGenerationPlan:
    """Tests for GenerationPlan Pydantic model."""

    def test_valid_plan(self):
        """Should create a valid plan."""
        plan = GenerationPlan(
            name="test-plan",
            steps=[
                GenerationStep(name="s1", template_name="t1"),
                GenerationStep(name="s2", template_name="t2", depends_on=["s1"]),
            ],
        )
        assert plan.name == "test-plan"
        assert len(plan.steps) == 2
        assert plan.execution_mode == ExecutionMode.SEQUENTIAL

    def test_plan_default_values(self):
        """Should have sensible defaults."""
        plan = GenerationPlan(name="defaults")
        assert plan.steps == []
        assert plan.execution_mode == ExecutionMode.SEQUENTIAL
        assert plan.error_strategy == ErrorStrategy.ABORT


# ======================================================================
# Topological Sort Tests
# ======================================================================


class TestTopologicalSort:
    """Tests for topological_sort function."""

    def test_empty_list(self):
        """Should return empty list for no steps."""
        assert topological_sort([]) == []

    def test_single_step(self):
        """Should return the single step."""
        step = GenerationStep(name="only", template_name="t")
        result = topological_sort([step])
        assert result == [step]

    def test_independent_steps(self):
        """Should maintain order for independent steps."""
        s1 = GenerationStep(name="a", template_name="t")
        s2 = GenerationStep(name="b", template_name="t")
        s3 = GenerationStep(name="c", template_name="t")
        result = topological_sort([s1, s2, s3])
        assert [r.name for r in result] == ["a", "b", "c"]

    def test_linear_dependency(self):
        """Should order steps respecting linear deps."""
        s1 = GenerationStep(name="a", template_name="t")
        s2 = GenerationStep(name="b", template_name="t", depends_on=["a"])
        s3 = GenerationStep(name="c", template_name="t", depends_on=["b"])
        result = topological_sort([s3, s1, s2])
        names = [r.name for r in result]
        assert names.index("a") < names.index("b")
        assert names.index("b") < names.index("c")

    def test_diamond_dependency(self):
        """Should handle diamond-shaped dependencies."""
        s1 = GenerationStep(name="root", template_name="t")
        s2 = GenerationStep(name="left", template_name="t", depends_on=["root"])
        s3 = GenerationStep(name="right", template_name="t", depends_on=["root"])
        s4 = GenerationStep(name="leaf", template_name="t", depends_on=["left", "right"])
        result = topological_sort([s1, s2, s3, s4])
        names = [r.name for r in result]
        assert names.index("root") < names.index("left")
        assert names.index("root") < names.index("right")
        assert names.index("left") < names.index("leaf")
        assert names.index("right") < names.index("leaf")

    def test_cycle_detection(self):
        """Should raise ValueError for circular dependency."""
        s1 = GenerationStep(name="a", template_name="t", depends_on=["b"])
        s2 = GenerationStep(name="b", template_name="t", depends_on=["a"])
        with pytest.raises(ValueError, match="Circular dependency"):
            topological_sort([s1, s2])

    def test_self_reference_cycle(self):
        """Should raise ValueError for self-referencing dependency (caught by model validation)."""
        with pytest.raises(ValueError, match="cannot depend on itself"):
            GenerationStep(name="a", template_name="t", depends_on=["a"])

    def test_missing_dependency(self):
        """Should raise ValueError for missing dependency."""
        s1 = GenerationStep(name="a", template_name="t", depends_on=["missing"])
        with pytest.raises(ValueError, match="depends on unknown step"):
            topological_sort([s1])


# ======================================================================
# validate_plan Tests
# ======================================================================


class TestValidatePlan:
    """Tests for validate_plan function."""

    def test_valid_plan(self):
        """Should return empty errors for valid plan."""
        plan = GenerationPlan(
            name="valid",
            steps=[
                GenerationStep(name="s1", template_name="t1"),
                GenerationStep(name="s2", template_name="t2", depends_on=["s1"]),
            ],
        )
        errors = validate_plan(plan)
        assert errors == []

    def test_empty_steps(self):
        """Should return error for empty steps."""
        plan = GenerationPlan(name="empty")
        errors = validate_plan(plan)
        assert len(errors) == 1
        assert "at least one step" in errors[0]

    def test_duplicate_names(self):
        """Should detect duplicate step names."""
        plan = GenerationPlan(
            name="dupes",
            steps=[
                GenerationStep(name="dup", template_name="t1"),
                GenerationStep(name="dup", template_name="t2"),
            ],
        )
        errors = validate_plan(plan)
        assert any("Duplicate" in e for e in errors)

    def test_missing_dependency(self):
        """Should detect unknown dependency references."""
        plan = GenerationPlan(
            name="missing-dep",
            steps=[
                GenerationStep(name="a", template_name="t", depends_on=["b"]),
            ],
        )
        errors = validate_plan(plan)
        assert any("unknown step" in e for e in errors)

    def test_cycle_detection_in_validation(self):
        """Should detect circular dependencies."""
        plan = GenerationPlan(
            name="cycle",
            steps=[
                GenerationStep(name="a", template_name="t", depends_on=["b"]),
                GenerationStep(name="b", template_name="t", depends_on=["a"]),
            ],
        )
        errors = validate_plan(plan)
        assert any("Circular" in e for e in errors)


# ======================================================================
# PlanExecutor Tests
# ======================================================================


class FakeRenderer:
    """A fake renderer that returns predictable output for testing."""

    def __init__(self, fail_on: list[str] | None = None):
        self.registry = None
        self.fail_on = fail_on or []
        self.rendered: list[str] = []

    def render_template(self, template_name: str, context: dict[str, Any]) -> str:
        self.rendered.append(template_name)
        if template_name in self.fail_on:
            raise TemplateRenderError(
                template_name=template_name,
                message="Simulated failure",
            )
        return f"Rendered({template_name})"

    def render_from_string(self, template_string: str, context: dict[str, Any]) -> str:
        return f"Rendered(inline)"


class FakeQueryService:
    """A fake query service that returns controlled entity trees."""

    def __init__(self):
        self.trees: dict[str, dict[str, Any]] = {}

    def get_entity_tree(self, root_id: str, **kwargs) -> dict[str, Any] | None:
        return self.trees.get(root_id)

    def add_tree(self, root_id: str, tree: dict[str, Any]):
        self.trees[root_id] = tree


class TestPlanExecutor:
    """Tests for PlanExecutor."""

    def test_execute_single_step(self):
        """Should execute a single step successfully."""
        renderer = FakeRenderer()
        executor = PlanExecutor(renderer=renderer)
        plan = GenerationPlan(
            name="single",
            steps=[GenerationStep(name="step1", template_name="hello")],
        )
        result = executor.execute_plan(plan, query_service=FakeQueryService())
        assert result.success is True
        assert len(result.step_results) == 1
        assert result.step_results[0].success is True
        assert result.step_results[0].output == "Rendered(hello)"
        assert len(result.successful_steps) == 1
        assert len(result.failed_steps) == 0

    def test_execute_sequential_steps(self):
        """Should execute steps in order respecting dependencies."""
        renderer = FakeRenderer()
        executor = PlanExecutor(renderer=renderer)
        plan = GenerationPlan(
            name="sequential",
            steps=[
                GenerationStep(name="first", template_name="t1"),
                GenerationStep(name="second", template_name="t2", depends_on=["first"]),
                GenerationStep(name="third", template_name="t3", depends_on=["second"]),
            ],
        )
        result = executor.execute_plan(plan, query_service=FakeQueryService())
        assert result.success is True
        assert len(result.step_results) == 3
        assert renderer.rendered == ["t1", "t2", "t3"]

    def test_execute_with_entity(self):
        """Should fetch entity tree and pass to template."""
        qs = FakeQueryService()
        qs.add_tree("e1", {
            "entity": {"id": "e1", "name": "Person"},
            "fields": [],
            "relations": [],
        })

        renderer = FakeRenderer()
        executor = PlanExecutor(renderer=renderer)
        plan = GenerationPlan(
            name="entity-plan",
            steps=[GenerationStep(
                name="gen", template_name="tmpl", entity_id="e1"
            )],
        )
        result = executor.execute_plan(plan, query_service=qs)
        assert result.success is True
        assert renderer.rendered == ["tmpl"]

    def test_entity_not_found(self):
        """Should fail gracefully when entity is not found."""
        qs = FakeQueryService()  # No trees added
        renderer = FakeRenderer()
        executor = PlanExecutor(renderer=renderer)
        plan = GenerationPlan(
            name="missing-entity",
            steps=[GenerationStep(
                name="gen", template_name="tmpl", entity_id="nonexistent"
            )],
        )
        result = executor.execute_plan(plan, query_service=qs)
        assert result.success is False
        assert len(result.failed_steps) == 1
        assert "not found" in result.failed_steps[0].error

    def test_error_strategy_abort(self):
        """Should abort on first error with ABORT strategy."""
        renderer = FakeRenderer(fail_on=["t2"])
        executor = PlanExecutor(renderer=renderer)
        plan = GenerationPlan(
            name="abort",
            steps=[
                GenerationStep(name="a", template_name="t1"),
                GenerationStep(name="b", template_name="t2"),  # will fail
                GenerationStep(name="c", template_name="t3"),  # should be skipped
            ],
            error_strategy=ErrorStrategy.ABORT,
        )
        result = executor.execute_plan(plan, query_service=FakeQueryService())
        assert result.success is False
        assert len(result.step_results) == 3
        assert result.step_results[0].success is True  # t1
        assert result.step_results[1].success is False  # t2 failed
        assert result.step_results[2].success is False  # t3 skipped

    def test_error_strategy_skip(self):
        """Should skip failed steps with SKIP strategy."""
        renderer = FakeRenderer(fail_on=["t2"])
        executor = PlanExecutor(renderer=renderer)
        plan = GenerationPlan(
            name="skip",
            steps=[
                GenerationStep(name="a", template_name="t1"),
                GenerationStep(name="b", template_name="t2"),  # will fail
                GenerationStep(name="c", template_name="t3"),  # should still run
            ],
            error_strategy=ErrorStrategy.SKIP,
        )
        result = executor.execute_plan(plan, query_service=FakeQueryService())
        assert result.success is False
        assert result.step_results[0].success is True
        assert result.step_results[1].success is False
        # With SKIP, subsequent steps still run but since ABORT is default in executor logic:
        # Actually, looking at the code: skip strategy doesn't set abort=True,
        # so step c should run. Let me check the executor code.
        # In _execute_step, it just returns a StepResult with success=False.
        # Then in execute_plan, if not result.success and error_strategy == ABORT, abort=True.
        # For SKIP, abort is never set, so step c should execute.
        # But wait, the current code sets abort based on error_strategy != SKIP.
        # Actually looking at code: after _execute_step, if not result.success:
        #   if plan.error_strategy == ErrorStrategy.ABORT: abort = True
        # So for SKIP, abort is never set, and step c will run.
        assert result.step_results[2].success is True

    def test_retry_policy(self):
        """Should retry failed steps with RETRY strategy."""
        call_count = [0]

        class FailingThenSucceedingRenderer:
            registry = None
            def render_template(self, template_name, context):
                call_count[0] += 1
                if call_count[0] < 3:  # Fail first 2 times
                    raise TemplateRenderError(
                        template_name=template_name,
                        message="Simulated failure",
                    )
                return "Success after retry"

        executor = PlanExecutor(renderer=FailingThenSucceedingRenderer())
        plan = GenerationPlan(
            name="retry-test",
            steps=[GenerationStep(name="step", template_name="t")],
            error_strategy=ErrorStrategy.RETRY,
            retry_policy=RetryPolicy(max_retries=3, delay_seconds=0),
        )
        result = executor.execute_plan(plan, query_service=FakeQueryService())
        assert result.success is True
        assert call_count[0] == 3  # 2 failures + 1 success

    def test_before_step_hook(self):
        """Should call before_step hook."""
        renderer = FakeRenderer()
        executor = PlanExecutor(renderer=renderer)
        hook_calls = []

        def hook(step, ctx):
            hook_calls.append(step.name)

        executor.before_step = hook
        plan = GenerationPlan(
            name="hooks",
            steps=[
                GenerationStep(name="a", template_name="t1"),
                GenerationStep(name="b", template_name="t2"),
            ],
        )
        executor.execute_plan(plan, query_service=FakeQueryService())
        assert hook_calls == ["a", "b"]

    def test_after_step_hook(self):
        """Should call after_step hook."""
        renderer = FakeRenderer()
        executor = PlanExecutor(renderer=renderer)
        hook_calls = []

        def hook(step, ctx):
            hook_calls.append(step.name)

        executor.after_step = hook
        plan = GenerationPlan(
            name="after-hooks",
            steps=[GenerationStep(name="a", template_name="t1")],
        )
        executor.execute_plan(plan, query_service=FakeQueryService())
        assert hook_calls == ["a"]

    def test_on_error_hook(self):
        """Should call on_error hook when step fails."""
        renderer = FakeRenderer(fail_on=["t1"])
        executor = PlanExecutor(renderer=renderer)
        hook_calls = []

        def hook(step, error):
            hook_calls.append((step.name, str(error)))

        executor.on_error = hook
        plan = GenerationPlan(
            name="error-hook",
            steps=[GenerationStep(name="a", template_name="t1")],
        )
        executor.execute_plan(plan, query_service=FakeQueryService())
        assert len(hook_calls) == 1
        assert hook_calls[0][0] == "a"

    def test_no_query_service_raises(self):
        """Should raise ValueError when no QueryService is available."""
        executor = PlanExecutor(renderer=FakeRenderer())
        plan = GenerationPlan(
            name="no-qs",
            steps=[GenerationStep(name="a", template_name="t")],
        )
        with pytest.raises(ValueError, match="No QueryService"):
            executor.execute_plan(plan, query_service=None)

    def test_execution_result_properties(self):
        """Should correctly report failed and successful steps."""
        result = ExecutionResult(
            plan_name="test",
            success=True,
            step_results=[
                StepResult("a", True, output="ok"),
                StepResult("b", False, error="fail"),
                StepResult("c", True, output="ok"),
            ],
        )
        assert len(result.successful_steps) == 2
        assert len(result.failed_steps) == 1
        assert result.failed_steps[0].step_name == "b"

    def test_parallel_execution(self):
        """Should execute independent steps in parallel."""
        renderer = FakeRenderer()
        executor = PlanExecutor(renderer=renderer)
        plan = GenerationPlan(
            name="parallel",
            steps=[
                GenerationStep(name="a", template_name="t1"),
                GenerationStep(name="b", template_name="t2"),
                GenerationStep(name="c", template_name="t3"),
            ],
            execution_mode=ExecutionMode.PARALLEL,
        )
        result = executor.execute_plan(plan, query_service=FakeQueryService())
        assert result.success is True
        assert len(result.step_results) == 3


# ======================================================================
# Example Template Tests
# ======================================================================


class TestExampleTemplates:
    """Tests that example templates render correctly."""

    @pytest.fixture
    def renderer(self):
        # Use a renderer with custom filters for loading example templates
        rend = TemplateRenderer()
        # Load example templates from backend/templates/
        templates_dir = Path(__file__).parent.parent / "templates"
        if templates_dir.exists():
            rend.registry.load_from_directory(str(templates_dir))
        return rend

    @pytest.fixture
    def entity_tree(self):
        return {
            "entity": {
                "id": "concept-user",
                "name": "User",
                "description": "A system user",
                "_kind": "concept",
            },
            "fields": [
                {
                    "entity": {
                        "id": "attr-1",
                        "name": "email",
                        "type": "string",
                        "is_required": True,
                        "is_unique": True,
                    },
                    "edge_type": "HAS_ATTRIBUTE",
                    "direction": "outgoing",
                },
                {
                    "entity": {
                        "id": "attr-2",
                        "name": "age",
                        "type": "integer",
                        "is_required": False,
                        "is_unique": False,
                    },
                    "edge_type": "HAS_ATTRIBUTE",
                    "direction": "outgoing",
                },
            ],
            "relations": [
                {
                    "entity": {
                        "id": "rel-1",
                        "name": "Profile",
                        "description": "User profile",
                        "_kind": "relation",
                    },
                    "fields": [],
                    "relations": [],
                    "_edge_type": "HAS_RELATION",
                    "_direction": "outgoing",
                }
            ],
        }

    def test_python_model_template(self, renderer, entity_tree):
        """Should render Python Pydantic model template."""
        if not renderer.registry.has_template("python_model"):
            pytest.skip("python_model.j2 not found")
        output = renderer.render_from_entity(entity_tree, "python_model")
        assert "class User(BaseModel)" in output
        assert "email" in output
        assert "age" in output
        assert "Profile" in output

    def test_typescript_interface_template(self, renderer, entity_tree):
        """Should render TypeScript interface template."""
        if not renderer.registry.has_template("typescript_interface"):
            pytest.skip("typescript_interface.j2 not found")
        output = renderer.render_from_entity(entity_tree, "typescript_interface")
        assert "export interface User" in output
        assert "email" in output
        assert "age" in output

    def test_sql_create_table_template(self, renderer, entity_tree):
        """Should render SQL CREATE TABLE template."""
        if not renderer.registry.has_template("sql_create_table"):
            pytest.skip("sql_create_table.j2 not found")
        output = renderer.render_from_entity(entity_tree, "sql_create_table")
        assert "CREATE TABLE" in output
        assert "VARCHAR" in output
        assert "PRIMARY KEY" in output

    def test_fastapi_router_template(self, renderer, entity_tree):
        """Should render FastAPI router template."""
        if not renderer.registry.has_template("python_fastapi_router"):
            pytest.skip("python_fastapi_router.j2 not found")
        output = renderer.render_from_entity(entity_tree, "python_fastapi_router")
        assert "router = APIRouter" in output
        assert "list_users" in output or "list_user" in output
        assert "create_user" in output


# ======================================================================
# API Endpoint Tests
# ======================================================================


class TestTemplateAPI:
    """Tests for template API endpoints."""

    def test_list_templates_empty(self, client: TestClient):
        """GET /api/templates should return empty list initially."""
        resp = client.get("/api/templates")
        assert resp.status_code == 200
        data = resp.json()
        assert data["count"] == 0
        assert data["templates"] == []

    def test_register_template(self, client: TestClient):
        """POST /api/templates should register a new template."""
        resp = client.post("/api/templates", json={
            "name": "helloworld",
            "template": "Hello {{ name }}!",
        })
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "helloworld"

    def test_register_duplicate(self, client: TestClient):
        """POST /api/templates with duplicate name should return 409."""
        client.post("/api/templates", json={
            "name": "dup", "template": "first",
        })
        resp = client.post("/api/templates", json={
            "name": "dup", "template": "second",
        })
        assert resp.status_code == 409

    def test_register_missing_fields(self, client: TestClient):
        """POST /api/templates without name/template should return 400."""
        resp = client.post("/api/templates", json={"name": "only-name"})
        assert resp.status_code == 400

    def test_render_template_endpoint(self, client: TestClient):
        """POST /api/templates/render should render a template."""
        # Register first
        client.post("/api/templates", json={
            "name": "greet", "template": "Hi {{ person }}!",
        })
        resp = client.post("/api/templates/render", json={
            "template_name": "greet",
            "context": {"person": "Alice"},
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["output"] == "Hi Alice!"

    def test_render_inline_template(self, client: TestClient):
        """POST /api/templates/render should handle inline templates."""
        resp = client.post("/api/templates/render", json={
            "template_string": "Hello {{ name }}!",
            "context": {"name": "World"},
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["output"] == "Hello World!"

    def test_render_nonexistent_template(self, client: TestClient):
        """POST /api/templates/render with bad name should return 404."""
        resp = client.post("/api/templates/render", json={
            "template_name": "nonexistent",
            "context": {},
        })
        assert resp.status_code == 404

    def test_render_missing_variable(self, client: TestClient):
        """POST /api/templates/render with missing var should return 422."""
        resp = client.post("/api/templates/render", json={
            "template_string": "Hi {{ name }}!",
            "context": {},  # missing 'name'
        })
        assert resp.status_code == 422

    def test_get_template_info(self, client: TestClient):
        """GET /api/templates/{name} should return template info."""
        client.post("/api/templates", json={
            "name": "test_tmpl",
            "template": "content",
            "metadata": {"version": 1},
        })
        resp = client.get("/api/templates/test_tmpl")
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == "test_tmpl"

    def test_get_template_info_not_found(self, client: TestClient):
        """GET /api/templates/{name} for missing template should return 404."""
        resp = client.get("/api/templates/nonexistent")
        assert resp.status_code == 404

    def test_delete_template(self, client: TestClient):
        """DELETE /api/templates/{name} should remove template."""
        client.post("/api/templates", json={
            "name": "delete_me", "template": "content",
        })
        resp = client.delete("/api/templates/delete_me")
        assert resp.status_code == 200
        # Verify it's gone
        resp = client.get("/api/templates")
        names = [t["name"] for t in resp.json()["templates"]]
        assert "delete_me" not in names

    def test_delete_nonexistent_template(self, client: TestClient):
        """DELETE /api/templates/{name} for missing template should return 404."""
        resp = client.delete("/api/templates/nonexistent")
        assert resp.status_code == 404

    def test_create_plan_endpoint(self, client: TestClient):
        """POST /api/templates/plan should create and validate a plan."""
        resp = client.post("/api/templates/plan", json={
            "name": "test-plan",
            "steps": [
                {"name": "step1", "template_name": "t1"},
                {"name": "step2", "template_name": "t2", "depends_on": ["step1"]},
            ],
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["valid"] is True
        assert data["step_count"] == 2
        assert data["execution_order"] == ["step1", "step2"]

    def test_create_plan_with_cycle(self, client: TestClient):
        """POST /api/templates/plan should reject cyclic plans."""
        resp = client.post("/api/templates/plan", json={
            "name": "bad-plan",
            "steps": [
                {"name": "a", "template_name": "t", "depends_on": ["b"]},
                {"name": "b", "template_name": "t", "depends_on": ["a"]},
            ],
        })
        assert resp.status_code == 422

    def test_execute_plan_endpoint(self, client: TestClient):
        """POST /api/templates/execute should execute a plan."""
        # Register a template first
        client.post("/api/templates", json={
            "name": "say_hi",
            "template": "Hello {{ step_name }}!",
        })

        resp = client.post("/api/templates/execute", json={
            "plan": {
                "name": "exec-test",
                "steps": [
                    {"name": "greeting", "template_name": "say_hi"},
                ],
            }
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["step_count"] == 1

    def test_execute_plan_with_missing_template(self, client: TestClient):
        """POST /api/templates/execute should fail gracefully on bad template."""
        resp = client.post("/api/templates/execute", json={
            "plan": {
                "name": "bad-exec",
                "steps": [
                    {"name": "fail", "template_name": "nonexistent_template"},
                ],
            }
        })
        # Step failure is reported in the response, not as HTTP error
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is False
        assert data["failed_count"] == 1

    def test_render_entity_not_found(self, client: TestClient):
        """POST /api/templates/render-entity/{id} should 404 on bad entity."""
        resp = client.post("/api/templates/render-entity/nonexistent", json={
            "template_string": "test",
        })
        assert resp.status_code == 404
