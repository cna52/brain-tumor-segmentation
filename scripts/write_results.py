"""Render machine-readable held-out metrics into a compact public report."""
import argparse
import json
from pathlib import Path


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--results", type=Path, default=Path("artifacts/results.json"))
    p.add_argument("--benchmark", type=Path, default=Path("artifacts/sam_benchmark.json"))
    p.add_argument("--output", type=Path, default=Path("docs/results.md"))
    args = p.parse_args()
    result = json.loads(args.results.read_text())
    assert result["n_test"] == 72 and len(result["patients"]) == 72
    bench = json.loads(args.benchmark.read_text())
    names = [("flair", "FLAIR threshold"), ("unet", "U-Net"),
             ("unet_cleaned", "U-Net + cleanup"), ("unet_sam", "U-Net + SAM")]
    lines = ["# Held-out results", "", "Research only; not for clinical use.", "",
             f"Code commit: `{result['code_commit']}`. Split SHA-256: `{result['split_sha256']}`. ",
             f"Configuration SHA-256: `{result['config_sha256']}`. Selection SHA-256: `{result['selection_sha256']}`. ",
             f"U-Net checkpoint SHA-256: `{result['checkpoint_sha256']}`. SAM checkpoint SHA-256: `{result['sam_checkpoint_sha256']}`.",
             f"The dependency lockfile is `requirements.lock.txt`. Device: {result['device']} on {result['hardware']}.", "",
             "## Aggregate", "", "Mean across all 72 held-out patient volumes. False positives use each source affine's voxel volume.", "",
             "| Method | Dice | Tumour recall | False-positive mL |", "|---|---:|---:|---:|"]
    for key, name in names:
        m = result["aggregate"][key]
        lines.append(f"| {name} | {m['dice']:.4f} | {m['recall']:.4f} | {m['false_positive_ml']:.2f} |")
    paired = result["paired"]
    lines.extend(["", f"Mean paired Dice difference, SAM minus raw U-Net: {paired['sam_minus_unet_dice']:+.4f}; "
                  f"SAM minus cleaned U-Net: {paired['sam_minus_cleaned_dice']:+.4f}.", "",
                  "## Every test patient", "",
                  "All values are whole-volume. FP is false-positive volume in mL.", "",
                  "| Patient | U-Net Dice | Cleaned Dice | SAM Dice | SAM recall | SAM FP mL |", "|---|---:|---:|---:|---:|---:|"])
    for row in result["patients"]:
        m = row["metrics"]
        lines.append(f"| {row['patient']} | {m['unet']['dice']:.4f} | {m['unet_cleaned']['dice']:.4f} | "
                     f"{m['unet_sam']['dice']:.4f} | {m['unet_sam']['recall']:.4f} | {m['unet_sam']['false_positive_ml']:.2f} |")
    failures = sorted(result["patients"], key=lambda row: row["metrics"]["unet_sam"]["dice"]-row["metrics"]["unet_cleaned"]["dice"])[:3]
    lines.extend(["", "## Representative failures", "", "Largest paired SAM declines relative to the cleaned U-Net:", ""])
    for row in failures:
        m = row["metrics"]
        lines.append(f"- `{row['patient']}`: cleaned Dice {m['unet_cleaned']['dice']:.4f}, "
                     f"SAM Dice {m['unet_sam']['dice']:.4f}; SAM recall {m['unet_sam']['recall']:.4f}; "
                     f"SAM FP {m['unet_sam']['false_positive_ml']:.2f} mL. "
                     "This quantifies the failure; visual interpretation requires reviewing the locally exported masks.")
    lines.extend(["", "## Compute and limitations", "",
                  f"The SAM benchmark used {bench['n']} validation slices; mean {bench['seconds_per_slice_mean']:.3f} s/slice, "
                  f"median {bench['seconds_per_slice_median']:.3f} s/slice, reported peak device allocation {bench['peak_device_bytes']} bytes. "
                  f"An all-slice projection was {bench['projected_72_patients_155_slices_hours']:.2f} hours; actual SAM times per patient are in `artifacts/results.json`.",
                  "Only FLAIR is used. This is a 2D model evaluated on a fixed patient split of one public dataset; "+
                  "the original unlabelled MSD test set has no labels for this evaluation. Box prompts are generated from U-Net predictions, " +
                  "so missed tumours cannot be recovered when a slice has no U-Net candidate. SAM was trained on natural images and was used frozen. " +
                  "Validation choices are limited to the documented grids. These findings do not establish clinical performance or external generalization.", "",
                  "## Reproduction", "", "Run the commands in `README.md` in order. `configs/selection.json` locks validation choices. " +
                  "The held-out command was `python -m brain_tumor.evaluate test --data ../brain-tumor-data/Task01_BrainTumour --export-dir artifacts/predictions`. " +
                  "The machine-readable metrics and individual NIfTI predictions remain outside Git under `artifacts/`.", ""])
    args.output.write_text("\n".join(lines))
    print(f"Wrote {args.output}")


if __name__ == "__main__":
    main()
