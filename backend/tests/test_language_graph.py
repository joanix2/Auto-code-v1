"""Tests for the language graph model (NodeKind, LangNode, LangGraph, …)."""

from src.models.language import EdgeKind, LangEdge, LangGraph, LangNode, NodeKind


class TestLangGraph:
    def test_empty(self):
        g = LangGraph()
        assert g.nodes == []
        assert g.edges == []

    def test_add_node(self):
        g = LangGraph()
        n = g.add_node(NodeKind.SORT, "string", "A string type")
        assert n.kind == NodeKind.SORT
        assert n.name == "string"
        assert n.description == "A string type"

    def test_add_node_with_props(self):
        g = LangGraph()
        n = g.add_node(NodeKind.SORT, "widget", label="Widget")
        assert n.properties["label"] == "Widget"

    def test_add_edge(self):
        g = LangGraph()
        a = g.add_node(NodeKind.SORT, "a")
        b = g.add_node(NodeKind.SORT, "b")
        e = g.add_edge(EdgeKind.SUBSORT, a.id, b.id)
        assert e.kind == EdgeKind.SUBSORT
        assert e.source_id == a.id
        assert e.target_id == b.id

    def test_nodes_by_kind(self):
        g = LangGraph()
        g.add_node(NodeKind.SORT, "s1")
        g.add_node(NodeKind.SORT, "s2")
        g.add_node(NodeKind.OP, "o1")
        assert len(g.nodes_by_kind(NodeKind.SORT)) == 2
        assert len(g.nodes_by_kind(NodeKind.OP)) == 1

    def test_get_node(self):
        g = LangGraph()
        g.add_node(NodeKind.SORT, "foo")
        assert g.get_node("foo", NodeKind.SORT) is not None
        assert g.get_node("foo") is not None
        assert g.get_node("foo", NodeKind.OP) is None

    def test_sub_sorts(self):
        g = LangGraph()
        p = g.add_node(NodeKind.SORT, "parent")
        c = g.add_node(NodeKind.SORT, "child")
        g.add_edge(EdgeKind.SUBSORT, c.id, p.id)
        assert g.sub_sorts("parent")[0].name == "child"
        assert g.sub_sorts("nope") == []

    def test_op_result_sort(self):
        g = LangGraph()
        s = g.add_node(NodeKind.SORT, "result")
        op = g.add_node(NodeKind.OP, "make")
        g.add_edge(EdgeKind.HAS_SORT, op.id, s.id)
        assert g.op_result_sort(op.id).name == "result"

    def test_op_params(self):
        g = LangGraph()
        s1 = g.add_node(NodeKind.SORT, "string")
        s2 = g.add_node(NodeKind.SORT, "int")
        op = g.add_node(NodeKind.OP, "pair")
        g.add_edge(EdgeKind.HAS_PARAM, op.id, s1.id)
        g.add_edge(EdgeKind.HAS_PARAM, op.id, s2.id)
        assert len(g.op_params(op.id)) == 2

    def test_edge_constraints(self):
        g = LangGraph()
        a = g.add_node(NodeKind.SORT, "src")
        b = g.add_node(NodeKind.SORT, "tgt")
        g.add_edge(EdgeKind.EDGE_CONSTRAINT, a.id, b.id, label="MY_EDGE")
        cs = g.edge_constraints()
        assert cs[0]["sourceNodeKind"] == "src"
        assert cs[0]["targetNodeKind"] == "tgt"

    def test_all_kinds(self):
        assert NodeKind.SORT.value == "Sort"
        assert NodeKind.OP.value == "Op"
        assert NodeKind.EQUATION.value == "Equation"
        assert NodeKind.RULE.value == "Rule"
        assert NodeKind.CONDITIONAL_RULE.value == "ConditionalRule"
        assert NodeKind.STRATEGY.value == "Strategy"
        assert NodeKind.INVARIANT.value == "Invariant"

    def test_all_edge_kinds(self):
        assert EdgeKind.HAS_SORT.value == "has_sort"
        assert EdgeKind.HAS_PARAM.value == "has_param"
        assert EdgeKind.SUBSORT.value == "subsort"
        assert EdgeKind.EDGE_CONSTRAINT.value == "edge_constraint"


class TestLanguageManager:
    def test_create_and_list(self):
        from src.services.language_manager import LanguageManager

        LanguageManager._reset()
        mgr = LanguageManager()
        assert len(mgr.list()) == 1  # default
        mgr.create("test-lang")
        assert len(mgr.list()) == 2

    def test_add_nodes(self):
        from src.services.language_manager import LanguageManager

        LanguageManager._reset()
        mgr = LanguageManager()
        lang = mgr.create("math")
        mgr.add_sort(lang.id, "int")
        mgr.add_sort(lang.id, "float")
        mgr.add_op(lang.id, "add", "int", ["int", "int"])
        assert len(mgr.get_sorts(lang.id)) == 2
        assert len(mgr.get_ops(lang.id)) == 1
        LanguageManager._reset()


class TestLangModels:
    def test_node_defaults(self):
        n = LangNode(kind=NodeKind.SORT, name="t")
        assert n.description == ""
        assert n.properties == {}

    def test_edge_defaults(self):
        e = LangEdge(kind=EdgeKind.SUBSORT, source_id="a", target_id="b")
        assert e.properties == {}
