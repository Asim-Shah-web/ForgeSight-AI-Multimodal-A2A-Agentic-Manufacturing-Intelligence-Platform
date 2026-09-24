"""
Non-interactive CLI for training the ForgeSight fixture YOLOv8 checkpoint.

This is the SAME training logic the notebook
(notebooks/finetune_yolov8_forgesight.ipynb) calls interactively — refactored
into a plain function here so there is one source of truth, callable either
from a human's notebook session or a script. CI does NOT call this script;
per the Phase 13 decision, checkpoint production is a manual, human-run step
(via the notebook), and CI only ever consumes an already-produced checkpoint.

This script exists so that IF you ever want a scriptable path (e.g. for your
own local automation, not for CI), it's available and stays in sync with the
notebook rather than drifting into two different training implementations.

Usage:
    python scripts/train_fixture_vision_model.py --epochs 5
"""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path

from ultralytics import YOLO

from forgesight.config.logging import get_logger
from forgesight.config.settings import settings

logger = get_logger(__name__)

REPO_ROOT = Path(__file__).resolve().parent.parent


def train_fixture_model(
    dataset_yaml_path: Path,
    epochs: int,
    image_size: int,
    batch_size: int,
    output_checkpoint_path: Path,
    device: str = "cpu",
) -> Path:
    """
    Fine-tunes yolov8n.pt on the given dataset and copies the best checkpoint
    to output_checkpoint_path. Returns that path.

    This is the single shared implementation the notebook's Section 4 also
    calls — do not duplicate this logic elsewhere.
    """
    if not dataset_yaml_path.exists():
        raise FileNotFoundError(
            f"Dataset YAML not found at {dataset_yaml_path}. Run "
            f"scripts/generate_synthetic_vision_dataset.py first, or point at a real dataset."
        )

    model = YOLO("yolov8n.pt")
    runs_dir = REPO_ROOT / "runs" / "vision"

    model.train(
        data=str(dataset_yaml_path),
        epochs=epochs,
        imgsz=image_size,
        batch=batch_size,
        patience=20,
        device=device,
        project=str(runs_dir),
        name="forgesight_yolov8n_finetune",
        exist_ok=True,
        verbose=True,
    )

    best_checkpoint = runs_dir / "forgesight_yolov8n_finetune" / "weights" / "best.pt"
    if not best_checkpoint.exists():
        raise RuntimeError(f"Training completed but no checkpoint found at {best_checkpoint}.")

    output_checkpoint_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(best_checkpoint, output_checkpoint_path)
    logger.info(
        "fixture_model_trained",
        extra={"epochs": epochs, "output_path": str(output_checkpoint_path)},
    )
    return output_checkpoint_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Train the ForgeSight fixture YOLOv8 checkpoint.")
    parser.add_argument("--epochs", type=int, default=5)
    parser.add_argument("--image-size", type=int, default=settings.cv_image_size)
    parser.add_argument("--batch-size", type=int, default=16)
    parser.add_argument(
        "--dataset-yaml",
        type=str,
        default=str(REPO_ROOT / "data" / "vision" / "synthetic_dataset" / "data.yaml"),
    )
    parser.add_argument("--output-path", type=str, default=settings.cv_model_path)
    parser.add_argument("--device", type=str, default="cpu")
    args = parser.parse_args()

    output_path = train_fixture_model(
        dataset_yaml_path=Path(args.dataset_yaml),
        epochs=args.epochs,
        image_size=args.image_size,
        batch_size=args.batch_size,
        output_checkpoint_path=Path(args.output_path),
        device=args.device,
    )
    print(f"Checkpoint written to: {output_path}")


if __name__ == "__main__":
    main()