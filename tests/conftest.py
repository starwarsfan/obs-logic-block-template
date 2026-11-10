"""Minimal OBS plugin API stubs so tests run without OBS installed."""

from __future__ import annotations

import sys
from dataclasses import dataclass, field
from typing import Any


@dataclass
class NodeTypePort:
    id: str
    label: str
    type: str = "value"


@dataclass
class NodeTypeDef:
    type: str
    label: str
    category: str
    description: str = ""
    inputs: list = field(default_factory=list)
    outputs: list = field(default_factory=list)
    config_schema: dict = field(default_factory=dict)
    color: str = "#475569"


def register_node_type(cls):
    return cls


class LogicNodePlugin:
    type_name: str


# Inject stubs before the plugin module is imported so the `from obs.logic.plugin_api import …`
# line resolves without a real OBS installation.
_api_stub = type(sys)("obs.logic.plugin_api")
_api_stub.LogicNodePlugin = LogicNodePlugin
_api_stub.NodeTypeDef = NodeTypeDef
_api_stub.NodeTypePort = NodeTypePort
_api_stub.register_node_type = register_node_type

sys.modules.setdefault("obs", type(sys)("obs"))
sys.modules.setdefault("obs.logic", type(sys)("obs.logic"))
sys.modules["obs.logic.plugin_api"] = _api_stub
