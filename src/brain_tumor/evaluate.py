"""Validation tuning and once-only held-out evaluation."""
import argparse
import hashlib
import json
import platform
import subprocess
import time
from pathlib import Path

import numpy as np
import torch

from .data import check_split, load_volume, read_cases, resize_slice, restore_mask, save_mask
from .inference import sam_refine, threshold_probability, unet_probability
from .metrics import patient_metrics
from .model import UNet


def load_model(path, config, device):
    checkpoint = torch.load(path, map_location="cpu", weights_only=False)
    assert not checkpoint["metadata"]["smoke"]
    model = UNet(config["base_channels"])
    model.load_state_dict(checkpoint["model"])
    return model.to(device).eval(), checkpoint["metadata"]


def sam_predictor(checkpoint, device):
    from segment_anything import SamPredictor, sam_model_registry
    sam = sam_model_registry["vit_b"](checkpoint=str(checkpoint))
    sam.to(device).eval()
    for parameter in sam.parameters():
        parameter.requires_grad_(False)
    return SamPredictor(sam)


def mean_dice(rows):
    return float(np.mean([r["dice"] for r in rows]))


def score(pred, truth, affine):
    return patient_metrics(restore_mask(pred, truth.shape), truth, affine)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("mode", choices=["tune", "test"])
    p.add_argument("--data", type=Path, required=True)
    p.add_argument("--split", type=Path, default=Path("splits/patients.json"))
    p.add_argument("--config", type=Path, default=Path("configs/experiment.json"))
    p.add_argument("--checkpoint", type=Path, default=Path("artifacts/baseline.pt"))
    p.add_argument("--sam-checkpoint", type=Path, default=Path("artifacts/sam_vit_b_01ec64.pth"))
    p.add_argument("--selection", type=Path, default=Path("configs/selection.json"))
    p.add_argument("--output", type=Path, default=Path("artifacts/results.json"))
    p.add_argument("--export-dir", type=Path)
    args = p.parse_args()
    cfg = json.loads(args.config.read_text())
    split = json.loads(args.split.read_text())
    cases, _ = read_cases(args.data)
    check_split(split, cases)
    device = "mps" if torch.backends.mps.is_available() else "cuda" if torch.cuda.is_available() else "cpu"
    model, metadata = load_model(args.checkpoint, cfg, device)
    assert metadata["split_sha256"] == hashlib.sha256(args.split.read_bytes()).hexdigest()
    assert metadata["config_sha256"] == hashlib.sha256(args.config.read_bytes()).hexdigest()
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    ids = split["val"] if args.mode == "tune" else split["test"]

    if args.mode == "tune":
        records = []
        for i, case_id in enumerate(ids, 1):
            image, truth, affine, _ = load_volume(cases[case_id])
            prob, norm = unet_probability(model, image, cfg["image_size"], device, cfg["batch_size"])
            records.append((case_id, prob, norm, truth, affine))
            print(f"Loaded validation {i}/{len(ids)} {case_id}", flush=True)
        candidates = []
        raw_candidates = []
        for threshold in cfg["threshold_candidates"]:
            raw_rows = [score(np.stack([sl >= threshold for sl in prob]), truth, affine)
                        for _, prob, _, truth, affine in records]
            raw_candidates.append((mean_dice(raw_rows), threshold))
            for min_pixels in cfg["minimum_component_pixels"]:
                rows = [score(threshold_probability(prob, threshold, min_pixels), truth, affine)
                        for _, prob, _, truth, affine in records]
                candidates.append((mean_dice(rows), threshold, min_pixels))
        _, threshold, min_pixels = max(candidates)
        _, raw_threshold = max(raw_candidates)
        flair_candidates = []
        for threshold_flair in np.arange(.2, .81, .1):
            rows = [score(np.stack([resize_slice(norm[:, :, z], cfg["image_size"]).numpy() >= threshold_flair
                                    for z in range(norm.shape[2])]), truth, affine)
                    for _, _, norm, truth, affine in records]
            flair_candidates.append((mean_dice(rows), float(threshold_flair)))
        _, flair_threshold = max(flair_candidates)
        predictor = sam_predictor(args.sam_checkpoint, device)
        # Tune box padding on twelve fixed validation patients; full volumes, never test patients.
        subset = records[:12]
        padding_scores = []
        for padding in cfg["box_padding_pixels"]:
            rows = []
            for case_id, prob, norm, truth, affine in subset:
                pred, _ = sam_refine(prob, norm, predictor, threshold, min_pixels, padding,
                                     cfg["max_boxes_per_slice"])
                rows.append(score(pred, truth, affine))
            padding_scores.append((mean_dice(rows), padding))
            print(f"Validation SAM padding={padding}: Dice={padding_scores[-1][0]:.4f}", flush=True)
        _, padding = max(padding_scores)
        selection = {"unet_threshold": threshold, "unet_raw_threshold": raw_threshold,
                     "minimum_component_pixels": min_pixels,
                     "flair_threshold": flair_threshold, "box_padding_pixels": padding,
                     "sam_mask_rule": cfg["sam_mask_rule"], "sam_tuning_patients": [r[0] for r in subset],
                     "validation_unet_grid": candidates, "validation_unet_raw_grid": raw_candidates,
                     "validation_flair_grid": flair_candidates,
                     "validation_sam_padding_grid": padding_scores,
                     "split_sha256": hashlib.sha256(args.split.read_bytes()).hexdigest(),
                     "config_sha256": hashlib.sha256(args.config.read_bytes()).hexdigest(),
                     "checkpoint_epoch": metadata["epoch"], "checkpoint_commit": metadata["commit"],
                     "selection_commit": commit}
        args.selection.parent.mkdir(parents=True, exist_ok=True)
        args.selection.write_text(json.dumps(selection, indent=2) + "\n")
        print(f"Locked selection in {args.selection}", flush=True)
        return

    selection = json.loads(args.selection.read_text())
    assert selection["split_sha256"] == hashlib.sha256(args.split.read_bytes()).hexdigest()
    assert selection["config_sha256"] == hashlib.sha256(args.config.read_bytes()).hexdigest()
    assert selection["sam_mask_rule"] == "highest_predicted_iou"
    predictor = sam_predictor(args.sam_checkpoint, device)
    results = []
    for i, case_id in enumerate(ids, 1):
        image, truth, affine, header = load_volume(cases[case_id])
        prob, norm = unet_probability(model, image, cfg["image_size"], device, cfg["batch_size"])
        raw = np.stack([sl >= selection["unet_raw_threshold"] for sl in prob])
        cleaned = threshold_probability(prob, selection["unet_threshold"], selection["minimum_component_pixels"])
        flair = np.stack([resize_slice(norm[:, :, z], cfg["image_size"]).numpy() >= selection["flair_threshold"]
                          for z in range(norm.shape[2])])
        sam, sam_times = sam_refine(prob, norm, predictor, selection["unet_threshold"],
                                    selection["minimum_component_pixels"], selection["box_padding_pixels"],
                                    cfg["max_boxes_per_slice"])
        masks = {"flair": flair, "unet": raw, "unet_cleaned": cleaned, "unet_sam": sam}
        row = {"patient": case_id, "slice_count": image.shape[2], "sam_prompted_slices": len(sam_times),
               "sam_seconds": sum(sam_times), "metrics": {}}
        for name, mask in masks.items():
            restored = restore_mask(mask, image.shape)
            row["metrics"][name] = patient_metrics(restored, truth, affine)
            if args.export_dir:
                out = args.export_dir / name
                out.mkdir(parents=True, exist_ok=True)
                save_mask(restored, affine, header, out / f"{case_id}.nii.gz")
        results.append(row)
        print(f"Test {i}/{len(ids)} {case_id}: U-Net={row['metrics']['unet']['dice']:.4f}, SAM={row['metrics']['unet_sam']['dice']:.4f}", flush=True)
    names = ("flair", "unet", "unet_cleaned", "unet_sam")
    aggregate = {name: {metric: float(np.mean([r["metrics"][name][metric] for r in results]))
                        for metric in ("dice", "recall", "false_positive_ml")}
                 for name in names}
    paired = {"sam_minus_unet_dice": float(np.mean([r["metrics"]["unet_sam"]["dice"]-r["metrics"]["unet"]["dice"] for r in results])),
              "sam_minus_cleaned_dice": float(np.mean([r["metrics"]["unet_sam"]["dice"]-r["metrics"]["unet_cleaned"]["dice"] for r in results]))}
    output = {"split_sha256": hashlib.sha256(args.split.read_bytes()).hexdigest(),
              "config_sha256": hashlib.sha256(args.config.read_bytes()).hexdigest(),
              "selection_sha256": hashlib.sha256(args.selection.read_bytes()).hexdigest(),
              "checkpoint_sha256": hashlib.sha256(args.checkpoint.read_bytes()).hexdigest(),
              "sam_checkpoint_sha256": hashlib.sha256(args.sam_checkpoint.read_bytes()).hexdigest(),
              "code_commit": commit, "training_metadata": metadata, "hardware": platform.platform(),
              "device": device, "n_test": len(ids), "aggregate": aggregate, "paired": paired,
              "patients": results}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, indent=2) + "\n")
    print(json.dumps({"aggregate": aggregate, "paired": paired}, indent=2))


if __name__ == "__main__":
    main()
