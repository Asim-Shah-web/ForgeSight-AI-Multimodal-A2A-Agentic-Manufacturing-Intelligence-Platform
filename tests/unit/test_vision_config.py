"""Unit tests for the declarative vision config loading layer (Step 9.0)."""

from __future__ import annotations

import pytest

from forgesight.config.settings import get_settings


def test_vision_yaml_loads_into_nested_settings() -> None:
    get_settings.cache_clear()
    settings = get_settings()

    assert settings.vision.model.model_name == settings.cv_model_name
    assert settings.vision.model.checkpoint_path == settings.cv_model_path
    assert settings.vision.inference.confidence_threshold == settings.cv_confidence_threshold
    assert settings.vision.upload.max_file_size_mb == settings.cv_upload_max_size_mb


def test_vision_env_var_overrides_yaml_default(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CV_CONFIDENCE_THRESHOLD", "0.75")
    monkeypatch.setenv("CV_MODEL_VERSION", "test-override-v9")
    get_settings.cache_clear()

    overridden = get_settings()

    assert overridden.cv_confidence_threshold == 0.75
    assert overridden.vision.inference.confidence_threshold == 0.75
    assert overridden.cv_model_version == "test-override-v9"
    assert overridden.vision.model.model_version == "test-override-v9"

    get_settings.cache_clear()


def test_defect_classes_contains_exactly_thirteen_phase1_classes() -> None:
    get_settings.cache_clear()
    settings = get_settings()

    expected = {
        "insufficient_solder_paste",
        "excessive_solder_paste",
        "solder_paste_bridging",
        "component_misalignment",
        "missing_component",
        "tombstoning",
        "polarity_inversion",
        "wrong_component",
        "cold_solder_joint",
        "solder_bridging",
        "solder_balling",
        "solder_voids",
        "head_in_pillow",
    }
    assert set(settings.cv_defect_classes) == expected
    assert len(settings.cv_defect_classes) == 13