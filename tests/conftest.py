from __future__ import annotations

import pytest


def pytest_addoption(parser):
    parser.addoption(
        "--desktop",
        action="store_true",
        help="roda também os testes que abrem o Power BI Desktop numa janela (marcados desktop)",
    )


def pytest_collection_modifyitems(config, items):
    if config.getoption("--desktop"):
        return
    pular = pytest.mark.skip(reason="abre o Power BI Desktop numa janela; rode com --desktop")
    for item in items:
        if "desktop" in item.keywords:
            item.add_marker(pular)
