"""Label-free, single-volume inference with the locked experiment settings."""
import argparse
import hashlib
import json
import platform
import time
from pathlib import Path

import nibabel as nib
import numpy as np
import torch

from .data import restore_mask, save_mask
from .evaluate import load_model, sam_predictor
from .inference import sam_refine, threshold_probability, unet_probability


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_flair(path, channel=None):
    source = nib.load(str(path))
    shape = source.shape
    if len(shape) == 3:
        if channel is not None:
            raise ValueError("--flair-channel is only valid for a 4D input")
        data = source.dataobj
    elif len(shape) == 4:
        if channel is None:
            raise ValueError("4D input requires an explicit --flair-channel")
        if not 0 <= channel < shape[3]:
            raise ValueError(f"FLAIR channel {channel} is outside 0..{shape[3] - 1}")
        data = source.dataobj[..., channel]
    else:
        raise ValueError(f"Expected a 3D or 4D NIfTI image, got shape {shape}")
    image = np.asarray(data, dtype=np.float32)
    if not all(d > 0 for d in image.shape) or not np.isfinite(image).all():
        raise ValueError("FLAIR volume must be nonempty and contain only finite values")
    return image, source.affine.copy(), source.header.copy()


def synchronize(device):
    if device == "mps":
        torch.mps.synchronize()
    elif device == "cuda":
        torch.cuda.synchronize()


def run_prediction(input_path, output_dir, checkpoint, config_path, selection_path,
                   sam_checkpoint=None, flair_channel=None, device="auto"):
    config = json.loads(Path(config_path).read_text())
    selection = json.loads(Path(selection_path).read_text())
    config_sha = sha256(config_path)
    if selection["config_sha256"] != config_sha:
        raise ValueError("Selection and experiment configuration hashes differ")
    if selection["sam_mask_rule"] != "highest_predicted_iou":
        raise ValueError("Unsupported SAM mask-selection rule")
    if device == "auto":
        device = "mps" if torch.backends.mps.is_available() else "cuda" if torch.cuda.is_available() else "cpu"
    image, affine, header = load_flair(input_path, flair_channel)
    model, checkpoint_metadata = load_model(checkpoint, config, device)
    if checkpoint_metadata["config_sha256"] != config_sha:
        raise ValueError("U-Net checkpoint and experiment configuration hashes differ")
    if checkpoint_metadata["split_sha256"] != selection["split_sha256"]:
        raise ValueError("U-Net checkpoint and selected patient split hashes differ")

    started = time.perf_counter()
    prob, normalized = unet_probability(model, image, config["image_size"], device,
                                        config["batch_size"])
    synchronize(device)
    unet_seconds = time.perf_counter() - started
    raw = np.stack([sl >= selection["unet_raw_threshold"] for sl in prob])
    cleaned = threshold_probability(prob, selection["unet_threshold"],
                                    selection["minimum_component_pixels"],
                                    config["max_boxes_per_slice"])
    masks = {"unet": raw, "unet_cleaned": cleaned}
    sam_seconds = None
    prompted_slices = 0
    if sam_checkpoint is not None:
        predictor = sam_predictor(sam_checkpoint, device)
        started = time.perf_counter()
        sam, times = sam_refine(prob, normalized, predictor, selection["unet_threshold"],
                                selection["minimum_component_pixels"],
                                selection["box_padding_pixels"],
                                config["max_boxes_per_slice"])
        synchronize(device)
        sam_seconds = time.perf_counter() - started
        prompted_slices = len(times)
        masks["unet_sam"] = sam

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    for name, mask in masks.items():
        save_mask(restore_mask(mask, image.shape), affine, header, output_dir / f"{name}.nii.gz")
    source_dir = Path(__file__).parent
    code_hashes = {name: sha256(source_dir / f"{name}.py")
                   for name in ("predict", "data", "evaluate", "inference", "metrics", "model")}
    record = {"input": str(Path(input_path).resolve()), "input_sha256": sha256(input_path),
              "source_shape": list(image.shape), "source_affine": affine.tolist(),
              "flair_channel": flair_channel, "code_sha256": code_hashes,
              "config_sha256": config_sha, "selection_sha256": sha256(selection_path),
              "split_sha256": selection["split_sha256"],
              "unet_checkpoint_sha256": sha256(checkpoint),
              "sam_checkpoint_sha256": sha256(sam_checkpoint) if sam_checkpoint else None,
              "training_commit": checkpoint_metadata["commit"],
              "device": device, "hardware": platform.platform(),
              "unet_seconds": unet_seconds, "sam_seconds": sam_seconds,
              "sam_prompted_slices": prompted_slices,
              "outputs": sorted(masks)}
    (output_dir / "run.json").write_text(json.dumps(record, indent=2) + "\n")
    return record


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True, help="3D FLAIR or 4D MRI NIfTI")
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--flair-channel", type=int, help="required for a 4D input; Task01 uses 0")
    parser.add_argument("--checkpoint", type=Path, default=Path("artifacts/baseline.pt"))
    parser.add_argument("--sam-checkpoint", type=Path,
                        help="optional official ViT-B checkpoint; omit for U-Net only")
    parser.add_argument("--config", type=Path, default=Path("configs/experiment.json"))
    parser.add_argument("--selection", type=Path, default=Path("configs/selection.json"))
    parser.add_argument("--device", choices=("auto", "cpu", "mps", "cuda"), default="auto")
    args = parser.parse_args()
    record = run_prediction(args.input, args.output_dir, args.checkpoint, args.config,
                            args.selection, args.sam_checkpoint, args.flair_channel, args.device)
    print(json.dumps(record, indent=2))


if __name__ == "__main__":
    main()
