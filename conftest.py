"""
conftest.py — Root pytest configuration for FinSight.ai monorepo.

Adds all Python package directories to sys.path so tests can import
core_engine, scenario_engine, validation_gateway, and shared_types
without installing them as packages.

This is the MVP approach. In production, each package will have its own
pyproject.toml and be installed with `pip install -e .`.
"""

import os
import sys

_root = os.path.dirname(os.path.abspath(__file__))

# Register all Python packages with the interpreter
_packages = [
    "packages/core-engine",
    "packages/scenario-engine",
    "packages/validation-gateway",
    "packages/shared-types",
    "packages/ai-layer",
    "packages/analytics",
]

for pkg in _packages:
    path = os.path.join(_root, pkg)
    if path not in sys.path:
        sys.path.insert(0, path)
