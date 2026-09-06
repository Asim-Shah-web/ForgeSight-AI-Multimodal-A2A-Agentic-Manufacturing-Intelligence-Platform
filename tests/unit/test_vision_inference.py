"""Unit tests for the vision inference service."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from forgesight.config.settings import settings
from forgesight.vision.inference import (
    Detection,
    InvalidImageError,
    _load_image_array,
    _map_class_index_to_defect_type,
    _run_inference_sync,
)


def _make_fake_box(class_idx: int, confidence: float, xyxy: list[float]) -> MagicMock:
    box = MagicMock()
    box.conf.item.return_value = confidence
    box.cls.item.return_value = class_idx
    box.xyxy = [MagicMock(tolist=MagicMock(return_value=xyxy))]
    return box


def test_sub_threshold_detections_are_filtered_out(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    fake_image_path = tmp_path / "fake.jpg"
    fake_image_path.write_bytes(b"not a real jpeg but path just needs to exist for the mock")

    above_threshold_box = _make_fake_box(0, settings.cv_confidence_threshold + 0.2, [10, 10, 50, 50])
    below_threshold_box = _make_fake_box(1, settings.cv_confidence_threshold - 0.2, [60, 60, 90, 90])

    fake_result = MagicMock()
    fake_result.boxes = [above_threshold_box, below_threshold_box]

    fake_model = MagicMock()
    fake_model.predict.return_value = [fake_result]

    monkeypatch.setattr("forgesight.vision.inference._get_vision_model", lambda: fake_model)
    monkeypatch.setattr(
        "forgesight.vision.inference._load_image_array", lambda path: np.zeros((640, 640, 3), dtype=np.uint8)
    )

    detections = _run_inference_sync(str(fake_image_path))

    assert len(detections) == 1
    assert detections[0].confidence >= settings.cv_confidence_threshold


def test_detections_capped_at_max_detections_per_image(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    fake_image_path = tmp_path / "fake.jpg"
    fake_image_path.write_bytes(b"placeholder")

    boxes = [
        _make_fake_box(0, settings.cv_confidence_threshold + 0.1, [i, i, i + 10, i + 10])
        for i in range(settings.cv_max_detections_per_image + 10)
    ]
    fake_result = MagicMock()
    fake_result.boxes = boxes

    fake_model = MagicMock()
    fake_model.predict.return_value = [fake_result]

    monkeypatch.setattr("forgesight.vision.inference._get_vision_model", lambda: fake_model)
    monkeypatch.setattr(
        "forgesight.vision.inference._load_image_array", lambda path: np.zeros((640, 640, 3), dtype=np.uint8)
    )

    detections = _run_inference_sync(str(fake_image_path))
    assert len(detections) == settings.cv_max_detections_per_image


def test_unreadable_file_raises_invalid_image_error(tmp_path) -> None:
    corrupt_file = tmp_path / "corrupt.jpg"
    corrupt_file.write_bytes(b"this is definitely not a valid image file")

    with pytest.raises(InvalidImageError):
        _load_image_array(str(corrupt_file))


def test_class_index_out_of_range_maps_to_unknown() -> None:
    result = _map_class_index_to_defect_type(9999)
    assert result == "unknown_class_9999"


def test_class_index_in_range_maps_to_configured_class() -> None:
    result = _map_class_index_to_defect_type(0)
    assert result == settings.cv_defect_classes[0]