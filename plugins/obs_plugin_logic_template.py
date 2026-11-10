"""Logic Template — replace this docstring with your block's description.

Edit this file to implement your custom logic block.
Save — OBS reloads it automatically (no restart needed).

Run `python init.py` once after cloning to rename all template placeholders.
"""

from __future__ import annotations

from typing import Any

from obs.logic.plugin_api import LogicNodePlugin, NodeTypeDef, NodeTypePort, register_node_type


@register_node_type
class LogicTemplate(LogicNodePlugin):
    type_name = "logic_template"

    @classmethod
    def node_type_def(cls) -> NodeTypeDef:
        return NodeTypeDef(
            type="logic_template",
            label="Logic Template",
            category="integration",
            description="Replace this description with your block's purpose.",
            inputs=[
                NodeTypePort(id="in1", label="Input 1"),
                NodeTypePort(id="in2", label="Input 2"),
            ],
            outputs=[
                NodeTypePort(id="result", label="Result"),
            ],
            config_schema={
                "multiplier": {
                    "type": "number",
                    "default": 1,
                    "label": "Multiplier",
                },
            },
            color="#6366f1",
        )

    @classmethod
    def evaluate(
        cls,
        node_id: str,
        inputs: dict[str, Any],
        config: dict[str, Any],
        state: dict[str, Any],
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        a = _to_num(inputs.get("in1"))
        b = _to_num(inputs.get("in2"))
        multiplier = float(config.get("multiplier") or 1)
        result = (a + b) * multiplier
        return {"result": round(result, 4)}, state


# ── Helpers — copy and adapt as needed ────────────────────────────────────────


def _to_num(v: Any, default: float = 0.0) -> float:
    if v is None:
        return default
    if isinstance(v, bool):
        return 1.0 if v else 0.0
    try:
        return float(v)
    except (TypeError, ValueError):
        return default


def _to_bool(v: Any) -> bool:
    if v is None:
        return False
    if isinstance(v, str):
        return v.strip().lower() not in ("0", "false", "no", "off", "")
    return bool(v)
