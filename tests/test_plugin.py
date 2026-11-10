"""Unit tests for the LogicTemplate plugin.

These tests run without a running OBS instance — conftest.py stubs out the
OBS plugin API so the plugin module can be imported standalone.
"""

from __future__ import annotations

import importlib
import sys

sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent.parent / "plugins"))
plugin_mod = importlib.import_module("obs_plugin_logic_template")
LogicTemplate = plugin_mod.LogicTemplate


# ── node_type_def ─────────────────────────────────────────────────────────────


def test_type_name():
    assert LogicTemplate.type_name == "logic_template"


def test_node_type_def_ports():
    td = LogicTemplate.node_type_def()
    assert {p.id for p in td.inputs} == {"in1", "in2"}
    assert {p.id for p in td.outputs} == {"result"}


def test_node_type_def_config_schema():
    td = LogicTemplate.node_type_def()
    assert "multiplier" in td.config_schema


# ── evaluate ──────────────────────────────────────────────────────────────────


def _eval(inputs=None, config=None, state=None):
    return LogicTemplate.evaluate(
        node_id="test",
        inputs=inputs or {},
        config=config or {},
        state=state or {},
    )


def test_evaluate_sums_inputs():
    outputs, _ = _eval(inputs={"in1": 3, "in2": 4})
    assert outputs["result"] == 7.0


def test_evaluate_applies_multiplier():
    outputs, _ = _eval(inputs={"in1": 3, "in2": 4}, config={"multiplier": 2})
    assert outputs["result"] == 14.0


def test_none_inputs_default_to_zero():
    outputs, _ = _eval(inputs={"in1": None, "in2": None})
    assert outputs["result"] == 0.0


def test_string_inputs_are_coerced():
    outputs, _ = _eval(inputs={"in1": "5", "in2": "3"})
    assert outputs["result"] == 8.0


def test_state_passed_through_unchanged():
    state = {"counter": 42}
    _, returned_state = _eval(state=state)
    assert returned_state["counter"] == 42
