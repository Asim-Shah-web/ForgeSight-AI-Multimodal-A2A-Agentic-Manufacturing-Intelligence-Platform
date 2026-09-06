"""
YOLOv8 inference service (Phase 3 ADR-004, Phase 9 implementation).

Loads the checkpoint at settings.cv_model_path once as a process-wide
singleton. Every detection below settings.cv_confidence_threshold is
filtered out here, structurally, before any result leaves this module —
callers never receive and can never accidentally persist a sub-threshold
finding.
"""

from __future__ import annotations

import asyncio
from functools import lru_cache
from pathlib import Path

import cv2
import numpy as np
from pydantic import BaseModel
from ultralytics import YOLO

from forgesight.config.logging import get_logger
from forgesight.config.settings import settings

logger = get_logger(__name__)


class InvalidImageError(Exception):
    """Raised when a file cannot be decoded as an image."""


class ModelCheckpointNotFoundError(Exception):
    """Raised when settings.cv_model_path does not point to an existing file."""


class Detection(BaseModel):
    """A single above-threshold detection, prior to CvFinding persistence."""

    defect_type: str
    confidence: float
    bounding_box: list[int]  # [x, y, w, h] in pixel coordinates


@lru_cache(maxsize=1)
def _get_vision_model() -> YOLO:
    """Load and cache the YOLOv8 model as a process-wide singleton."""
    checkpoint_path = Path(settings.cv_model_path)
    if not checkpoint_path.exists():
        raise ModelCheckpointNotFoundError(
            f"No CV model checkpoint found at '{checkpoint_path}'. Train or copy a "
            f"checkpoint to this path (see notebooks/finetune_yolov8_forgesight.ipynb) "
            f"before running inference."
        )

    logger.info(
        "vision_model_loading",
        extra={"checkpoint_path": str(checkpoint_path), "device": settings.cv_device},
    )
    model = YOLO(str(checkpoint_path))
    logger.info("vision_model_loaded", extra={"checkpoint_path": str(checkpoint_path)})
    return model


def _load_image_array(image_path: str) -> np.ndarray:
    image_array = cv2.imread(image_path)
    if image_array is None:
        raise InvalidImageError(f"Could not decode image at '{image_path}' as a valid image file.")
    return image_array


def _map_class_index_to_defect_type(class_idx: int) -> str:
    defect_classes = settings.cv_defect_classes
    if 0 <= class_idx < len(defect_classes):
        return defect_classes[class_idx]
    logger.warning("unmapped_class_index", extra={"class_idx": class_idx})
    return f"unknown_class_{class_idx}"


def _run_inference_sync(image_path: str) -> list[Detection]:
    model = _get_vision_model()
    image_array = _load_image_array(image_path)

    results = model.predict(
        source=image_array,
        imgsz=settings.cv_image_size,
        iou=settings.cv_iou_threshold,
        conf=0.0,  # do NOT let ultralytics pre-filter; we filter explicitly below
        device=settings.cv_device,
        verbose=False,
    )

    detections: list[Detection] = []
    if not results:
        return detections

    boxes = results[0].boxes
    if boxes is None:
        return detections

    for box in boxes:
        confidence = float(box.conf.item())
        if confidence < settings.cv_confidence_threshold:
            continue

        class_idx = int(box.cls.item())
        x_min, y_min, x_max, y_max = box.xyxy[0].tolist()
        bounding_box = [int(x_min), int(y_min), int(x_max - x_min), int(y_max - y_min)]

        detections.append(
            Detection(
                defect_type=_map_class_index_to_defect_type(class_idx),
                confidence=confidence,
                bounding_box=bounding_box,
            )
        )

    detections.sort(key=lambda d: d.confidence, reverse=True)
    return detections[: settings.cv_max_detections_per_image]


async def run_inference(image_path: str) -> list[Detection]:
    """Run YOLOv8 inference on the image at image_path, offloaded to a worker
    thread so the blocking forward pass never stalls the event loop."""
    return await asyncio.to_thread(_run_inference_sync, image_path)