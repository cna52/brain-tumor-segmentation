"""Exploratory anatomy and prompt-coverage analysis of the locked test outputs."""
import argparse
import hashlib
import html
import json
import os
from pathlib import Path

import nibabel as nib
import numpy as np
import torch
from scipy.stats import spearmanr

from brain_tumor.data import check_split, load_volume, read_cases, restore_mask
from brain_tumor.evaluate import load_model
from brain_tumor.inference import threshold_probability, unet_probability
from brain_tumor.metrics import boxes_from_mask


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def box_coverage(prob, truth, image_shape, selection, max_boxes):
    cleaned = threshold_probability(prob, selection["unet_threshold"],
                                    selection["minimum_component_pixels"], max_boxes)
    boxes_union = np.zeros_like(cleaned, bool)
    prompted = 0
    for z, mask in enumerate(cleaned):
        boxes = boxes_from_mask(mask, selection["box_padding_pixels"], max_boxes)
        prompted += bool(boxes)
        for x1, y1, x2, y2 in boxes:
            boxes_union[z, y1:y2 + 1, x1:x2 + 1] = True
    source_boxes = restore_mask(boxes_union, image_shape).astype(bool)
    tumor_slices = np.any(truth, axis=(0, 1))
    no_prompt_indices = [z for z in range(len(tumor_slices))
                         if tumor_slices[z] and not boxes_union[z].any()]
    missed_voxel_fraction = (np.count_nonzero(truth[:, :, no_prompt_indices]) /
                             np.count_nonzero(truth))
    return (float(np.count_nonzero(source_boxes & truth) / np.count_nonzero(truth)),
            int(prompted), len(no_prompt_indices), float(missed_voxel_fraction), cleaned)


def write_scatter(rows, path):
    """Self-contained, patient-level SVG with hoverable case IDs."""
    width, height = 1000, 430
    panels = (("candidate_recall", "U-Net candidate recall", 0.0, 1.0),
              ("sam_added_false_positive_ml", "SAM added false-positive mL", None, None))
    pieces = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" role="img" aria-label="Patient-level associations with SAM Dice change">',
              '<rect width="100%" height="100%" fill="white"/>',
              '<style>text{font-family:Arial,sans-serif;fill:#142333}.axis{stroke:#64748b;stroke-width:1}.zero{stroke:#c96b22;stroke-dasharray:5 4}.point{opacity:.75}</style>',
              '<text x="24" y="28" font-size="18" font-weight="bold">Exploratory patient-level relationships (n=72)</text>']
    y_values = [row["sam_minus_cleaned_dice"] for row in rows]
    y_min, y_max = min(y_values) - .015, max(y_values) + .015
    for panel_index, (key, title, fixed_min, fixed_max) in enumerate(panels):
        left = 70 + panel_index * 500
        top, plot_width, plot_height = 78, 400, 275
        x_values = [row[key] for row in rows]
        x_min = min(x_values) if fixed_min is None else fixed_min
        x_max = max(x_values) if fixed_max is None else fixed_max
        if x_max == x_min:
            x_max = x_min + 1
        sx = lambda value: left + (value - x_min) / (x_max - x_min) * plot_width
        sy = lambda value: top + (y_max - value) / (y_max - y_min) * plot_height
        pieces += [f'<text x="{left}" y="58" font-size="14" font-weight="bold">{html.escape(title)}</text>',
                   f'<line class="axis" x1="{left}" y1="{top}" x2="{left}" y2="{top + plot_height}"/>',
                   f'<line class="axis" x1="{left}" y1="{top + plot_height}" x2="{left + plot_width}" y2="{top + plot_height}"/>',
                   f'<line class="zero" x1="{left}" y1="{sy(0):.1f}" x2="{left + plot_width}" y2="{sy(0):.1f}"/>',
                   f'<text x="{left}" y="{top + plot_height + 24}" font-size="12">{x_min:.2f}</text>',
                   f'<text x="{left + plot_width - 35}" y="{top + plot_height + 24}" font-size="12">{x_max:.2f}</text>',
                   f'<text x="{left}" y="{top + plot_height + 43}" font-size="12">{html.escape(title)}</text>',
                   f'<text x="{left + 6}" y="{top + 13}" font-size="11">Dice change</text>']
        for tick in (-0.1, 0.0, 0.1):
            if y_min <= tick <= y_max:
                tick_y = sy(tick)
                pieces.append(f'<text x="{left - 43}" y="{tick_y + 4:.1f}" font-size="11">{tick:+.1f}</text>')
        for row in rows:
            x, y = sx(row[key]), sy(row["sam_minus_cleaned_dice"])
            color = "#146b85" if row["sam_minus_cleaned_dice"] >= 0 else "#b84751"
            tip = (f"{row['patient']}: {key}={row[key]:.3f}; "
                   f"SAM minus U-Net Dice={row['sam_minus_cleaned_dice']:+.3f}")
            pieces.append(f'<circle class="point" cx="{x:.1f}" cy="{y:.1f}" r="4" fill="{color}"><title>{html.escape(tip)}</title></circle>')
    pieces += ['<text x="24" y="416" font-size="12">Blue: SAM improved Dice; red: SAM worsened Dice. Existing test set; descriptive only.</text>', '</svg>']
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(pieces) + "\n")


def analyze(data_root, predictions, results_path, checkpoint, config_path,
            selection_path, split_path, output_path, report_path, figure_path, device):
    cases, _ = read_cases(data_root)
    split = json.loads(Path(split_path).read_text())
    check_split(split, cases)
    results = json.loads(Path(results_path).read_text())
    config = json.loads(Path(config_path).read_text())
    selection = json.loads(Path(selection_path).read_text())
    if results["split_sha256"] != sha256(split_path) or results["selection_sha256"] != sha256(selection_path):
        raise ValueError("Locked results do not match split or selection")
    if selection["config_sha256"] != sha256(config_path):
        raise ValueError("Selection does not match configuration")
    if results["checkpoint_sha256"] != sha256(checkpoint):
        raise ValueError("Checkpoint does not match locked results")
    if device == "auto":
        device = "mps" if torch.backends.mps.is_available() else "cuda" if torch.cuda.is_available() else "cpu"
    model, _ = load_model(checkpoint, config, device)
    published = {row["patient"]: row for row in results["patients"]}
    if set(published) != set(split["test"]):
        raise ValueError("Published results do not cover the test split exactly")
    rows = []
    for index, case_id in enumerate(split["test"], 1):
        image, truth, affine, _ = load_volume(cases[case_id])
        prob, _ = unet_probability(model, image, config["image_size"], device, config["batch_size"])
        coverage, prompted, missed_slices, missed_fraction, cleaned = box_coverage(
            prob, truth, image.shape, selection, config["max_boxes_per_slice"])
        saved = nib.load(str(Path(predictions) / "unet_cleaned" / f"{case_id}.nii.gz"))
        if saved.shape != truth.shape or not np.allclose(saved.affine, affine):
            raise ValueError(f"Prediction grid mismatch: {case_id}")
        restored = restore_mask(cleaned, image.shape)
        if not np.array_equal(restored, np.asarray(saved.dataobj)):
            raise ValueError(f"Recomputed candidates differ from locked prediction: {case_id}")
        published_row = published[case_id]
        if prompted != published_row["sam_prompted_slices"]:
            raise ValueError(f"Prompted-slice count differs from locked result: {case_id}")
        metrics = published_row["metrics"]
        cleaned_metrics, sam_metrics = metrics["unet_cleaned"], metrics["unet_sam"]
        rows.append({"patient": case_id,
                     "truth_ml": cleaned_metrics["truth_ml"],
                     "candidate_recall": cleaned_metrics["recall"],
                     "box_coverage": coverage,
                     "tumor_slices_without_prompt": missed_slices,
                     "tumor_voxel_fraction_on_unprompted_slices": missed_fraction,
                     "prompted_slices": prompted,
                     "slice_count": published_row["slice_count"],
                     "sam_minus_cleaned_dice": sam_metrics["dice"] - cleaned_metrics["dice"],
                     "sam_added_false_positive_ml": sam_metrics["false_positive_ml"] - cleaned_metrics["false_positive_ml"],
                     "sam_minus_cleaned_recall": sam_metrics["recall"] - cleaned_metrics["recall"]})
        print(f"Analyzed {index}/{len(split['test'])} {case_id}", flush=True)

    delta = np.array([row["sam_minus_cleaned_dice"] for row in rows])
    variables = ("truth_ml", "candidate_recall", "box_coverage",
                 "tumor_slices_without_prompt", "sam_added_false_positive_ml")
    labels = {"truth_ml": "Tumour volume (mL)",
              "candidate_recall": "U-Net candidate tumour recall",
              "box_coverage": "U-Net box tumour coverage",
              "tumor_slices_without_prompt": "Tumour slices without a prompt",
              "sam_added_false_positive_ml": "SAM added false-positive volume (mL)"}
    correlations = {}
    for name in variables:
        result = spearmanr([row[name] for row in rows], delta)
        correlations[name] = {"spearman_rho": float(result.statistic),
                              "p_value_exploratory": float(result.pvalue)}
    output = {"status": "retrospective exploratory; no model selection or new held-out claim",
              "analysis_script_sha256": sha256(__file__), "device": device,
              "results_sha256": sha256(results_path), "split_sha256": sha256(split_path),
              "selection_sha256": sha256(selection_path), "checkpoint_sha256": sha256(checkpoint),
              "n_patients": len(rows), "correlations_with_sam_dice_change": correlations,
              "patients": rows}
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(output, indent=2) + "\n")
    write_scatter(rows, figure_path)
    report = ["# Exploratory failure analysis", "",
              "This retrospective analysis uses the already inspected 72-patient test set. It does not select a new method or establish a fresh held-out result. Ground truth is used only to measure coverage and error, never to make prompts.", "",
              f"Locked results SHA-256: `{output['results_sha256']}`. Split SHA-256: `{output['split_sha256']}`. Selection SHA-256: `{output['selection_sha256']}`.", "",
              "## Associations with SAM minus cleaned U-Net Dice", "",
              "Spearman correlations across patients are descriptive. P values are exploratory and unadjusted; these relationships are not causal.", "",
              "| Patient measure | Spearman rho | Exploratory p |", "|---|---:|---:|"]
    for name in variables:
        value = correlations[name]
        report.append(f"| {labels[name]} | {value['spearman_rho']:+.3f} | {value['p_value_exploratory']:.3g} |")
    report.extend(["", f"![Exploratory patient-level scatter plots]({os.path.relpath(figure_path, Path(report_path).parent)})", "",
                   "## Counts and examples", "",
                   f"Patients with at least one tumour-bearing slice without a U-Net prompt: {sum(row['tumor_slices_without_prompt'] > 0 for row in rows)}/{len(rows)}.",
                   f"Median unprompted tumour-bearing slices per patient: {np.median([row['tumor_slices_without_prompt'] for row in rows]):.0f}; median fraction of tumour voxels on those slices: {np.median([row['tumor_voxel_fraction_on_unprompted_slices'] for row in rows]):.3%}.",
                   f"Patients where SAM added false-positive volume: {sum(row['sam_added_false_positive_ml'] > 0 for row in rows)}/{len(rows)}; median added volume {np.median([row['sam_added_false_positive_ml'] for row in rows]):+.2f} mL.",
                   f"Median candidate recall was {np.median([row['candidate_recall'] for row in rows]):.3f}, and median box coverage was {np.median([row['box_coverage'] for row in rows]):.3f}. Patients with higher candidate recall tended to have a more negative SAM Dice change (rho {correlations['candidate_recall']['spearman_rho']:+.3f}); this is a descriptive association, not a causal finding.", ""])
    for row in (min(rows, key=lambda x: x["sam_minus_cleaned_dice"]),
                max(rows, key=lambda x: x["sam_minus_cleaned_dice"])):
        report.append(f"- `{row['patient']}`: Dice change {row['sam_minus_cleaned_dice']:+.4f}; "
                      f"added false positives {row['sam_added_false_positive_ml']:+.2f} mL; "
                      f"candidate recall {row['candidate_recall']:.3f}; box coverage {row['box_coverage']:.3f}; "
                      f"tumour slices without a prompt {row['tumor_slices_without_prompt']}.")
    report.extend(["", "## Interpretation limits", "",
                   "Candidate coverage and box coverage are related by construction, and added false positives are mathematically related to Dice. Associations can explain where the observed errors occur but cannot prove a mechanism. The input is FLAIR-only, one dataset split, and a frozen natural-image SAM model.", "",
                   f"Machine-readable patient values: `{output_path}`.", ""])
    report_path = Path(report_path)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(report))
    print(f"Wrote {output_path} and {report_path}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, required=True)
    parser.add_argument("--predictions", type=Path, default=Path("artifacts/predictions"))
    parser.add_argument("--results", type=Path, default=Path("metrics/results.json"))
    parser.add_argument("--checkpoint", type=Path, default=Path("artifacts/baseline.pt"))
    parser.add_argument("--config", type=Path, default=Path("configs/experiment.json"))
    parser.add_argument("--selection", type=Path, default=Path("configs/selection.json"))
    parser.add_argument("--split", type=Path, default=Path("splits/patients.json"))
    parser.add_argument("--output", type=Path, default=Path("metrics/failure_analysis.json"))
    parser.add_argument("--report", type=Path, default=Path("docs/failure_analysis.md"))
    parser.add_argument("--figure", type=Path, default=Path("docs/figures/failure_scatter.svg"))
    parser.add_argument("--device", choices=("auto", "cpu", "mps", "cuda"), default="auto")
    args = parser.parse_args()
    analyze(args.data, args.predictions, args.results, args.checkpoint, args.config,
            args.selection, args.split, args.output, args.report, args.figure, args.device)


if __name__ == "__main__":
    main()
