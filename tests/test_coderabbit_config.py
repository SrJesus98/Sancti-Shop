"""Tests for the .coderabbitai.yaml configuration file added in this PR."""

from pathlib import Path

import yaml

CONFIG_PATH = Path(__file__).resolve().parents[1] / ".coderabbitai.yaml"


def _load_config() -> dict:
    return yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8"))


def test_coderabbitai_yaml_existe() -> None:
    assert CONFIG_PATH.is_file()


def test_coderabbitai_yaml_es_yaml_valido() -> None:
    data = _load_config()

    assert isinstance(data, dict)


def test_coderabbitai_yaml_idioma_es_espanol() -> None:
    data = _load_config()

    assert data["language"] == "es-ES"


def test_coderabbitai_yaml_review_status_habilitado() -> None:
    data = _load_config()

    assert data["reviews"]["review_status"] is True


def test_coderabbitai_yaml_path_filters_ignora_locks_y_pyc() -> None:
    data = _load_config()

    path_filters = data["reviews"]["path_filters"]
    assert "!**/*.lock" in path_filters
    assert "!**/*.pyc" in path_filters


def test_coderabbitai_yaml_base_branches_incluye_develop_y_main() -> None:
    data = _load_config()

    base_branches = data["reviews"]["base_branches"]
    assert set(base_branches) == {"develop", "main"}