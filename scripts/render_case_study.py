"""Render two retrospective Task01 examples from already locked predictions."""
import argparse
import json
from pathlib import Path

import nibabel as nib
import numpy as np
from PIL import Image, ImageDraw

from brain_tumor.data import load_volume, normalize, read_cases


EXAMPLES = (("BRATS_073", "More false positives"),
            ("BRATS_198", "SAM improvement"))


def slice_dice(pred, truth):
    total = np.count_nonzero(pred) + np.count_nonzero(truth)
    return 2 * np.count_nonzero(pred & truth) / total if total else 1.0


def choose_slice(truth, cleaned, sam, failure):
    scored = []
    for z in range(truth.shape[2]):
        if np.count_nonzero(truth[:, :, z]) < 10:
            continue
        if failure:
            score = np.count_nonzero(sam[:, :, z] & ~truth[:, :, z]) - np.count_nonzero(cleaned[:, :, z] & ~truth[:, :, z])
        else:
            score = slice_dice(sam[:, :, z], truth[:, :, z]) - slice_dice(cleaned[:, :, z], truth[:, :, z])
        scored.append((score, z))
    if not scored:
        raise ValueError("No tumour-bearing slice available for case study")
    return max(scored)[1]


def overlay(gray, truth, pred):
    rgb = np.repeat(gray[:, :, None], 3, axis=2).astype(np.float32)
    colors = ((truth & pred, [40, 220, 100]),
              (~truth & pred, [240, 60, 110]),
              (truth & ~pred, [70, 150, 255]))
    for mask, color in colors:
        rgb[mask] = 0.45 * rgb[mask] + 0.55 * np.array(color)
    return Image.fromarray(rgb.astype(np.uint8), "RGB")


def render(data_root, predictions, results_path, output):
    cases, _ = read_cases(data_root)
    rows = {row["patient"]: row for row in json.loads(Path(results_path).read_text())["patients"]}
    panels = []
    for case_id, label in EXAMPLES:
        image, truth, affine, _ = load_volume(cases[case_id])
        masks = {}
        for name in ("unet_cleaned", "unet_sam"):
            saved = nib.load(str(Path(predictions) / name / f"{case_id}.nii.gz"))
            if saved.shape != truth.shape or not np.allclose(saved.affine, affine):
                raise ValueError(f"Prediction grid mismatch for {case_id} {name}")
            masks[name] = np.asarray(saved.dataobj).astype(bool)
        cleaned, sam = masks["unet_cleaned"], masks["unet_sam"]
        z = choose_slice(truth, cleaned, sam, failure=case_id == "BRATS_073")
        gray = (255 * normalize(image)[:, :, z]).astype(np.uint8)
        base = Image.fromarray(gray, "L").convert("RGB")
        truth_panel = overlay(gray, truth[:, :, z], truth[:, :, z])
        unet_panel = overlay(gray, truth[:, :, z], cleaned[:, :, z])
        sam_panel = overlay(gray, truth[:, :, z], sam[:, :, z])
        metrics = rows[case_id]["metrics"]
        title = (f"{case_id} | {label} | axial slice {z} | whole-volume Dice: "
                 f"U-Net {metrics['unet_cleaned']['dice']:.3f}, SAM {metrics['unet_sam']['dice']:.3f}")
        panels.append((title, (base, truth_panel, unet_panel, sam_panel)))

    width, height = panels[0][1][0].size
    margin, label_height, gap = 12, 42, 18
    canvas = Image.new("RGB", (4 * width + 2 * margin + 3 * gap,
                               2 * (height + label_height + 22) + 55), "white")
    draw = ImageDraw.Draw(canvas)
    headings = ("FLAIR", "Ground truth", "U-Net + cleanup", "U-Net + SAM")
    for row_index, (title, images) in enumerate(panels):
        y = row_index * (height + label_height + 22) + margin
        draw.text((margin, y), title, fill="black")
        for col, panel in enumerate(images):
            x = margin + col * (width + gap)
            draw.text((x, y + 20), headings[col], fill="black")
            canvas.paste(panel, (x, y + label_height))
    footer_y = 2 * (height + label_height + 22) + margin
    draw.text((margin, footer_y), "Overlay: green = true positive; pink = false positive; blue = false negative.", fill="black")
    draw.text((margin, footer_y + 16), "MSD Task01 images adapted under CC BY-SA 4.0; research only, not for clinical use.", fill="black")
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    canvas.resize((canvas.width * 2, canvas.height * 2), Image.Resampling.NEAREST).save(output)
    print(f"Wrote {output}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, required=True)
    parser.add_argument("--predictions", type=Path, default=Path("artifacts/predictions"))
    parser.add_argument("--results", type=Path, default=Path("metrics/results.json"))
    parser.add_argument("--output", type=Path, default=Path("docs/figures/case_study.png"))
    args = parser.parse_args()
    render(args.data, args.predictions, args.results, args.output)


if __name__ == "__main__":
    main()
