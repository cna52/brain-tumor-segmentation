"""Benchmark official frozen ViT-B on a bounded set of real validation slices."""
import argparse
import json
import platform
import time
from pathlib import Path

import numpy as np
import torch

from brain_tumor.data import load_volume, normalize, read_cases, resize_slice
from brain_tumor.evaluate import sam_predictor


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--data", type=Path, required=True)
    p.add_argument("--split", type=Path, default=Path("splits/patients.json"))
    p.add_argument("--checkpoint", type=Path, default=Path("artifacts/sam_vit_b_01ec64.pth"))
    p.add_argument("--output", type=Path, default=Path("artifacts/sam_benchmark.json"))
    p.add_argument("--n", type=int, default=8)
    args = p.parse_args()
    cases, _ = read_cases(args.data)
    split = json.loads(args.split.read_text())
    device = "mps" if torch.backends.mps.is_available() else "cuda" if torch.cuda.is_available() else "cpu"
    predictor = sam_predictor(args.checkpoint, device)
    times = []
    allocations = []
    for case_id in split["val"][:2]:
        image, _, _, _ = load_volume(cases[case_id], with_label=False)
        image = normalize(image)
        for z in np.linspace(image.shape[2]//4, image.shape[2]*3//4, args.n//2, dtype=int):
            gray = resize_slice(image[:, :, z], 128).numpy()
            gray = (255*np.clip(gray, 0, 1)).astype(np.uint8)
            rgb = np.repeat(gray[:, :, None], 3, axis=2)
            start = time.perf_counter()
            predictor.set_image(rgb)
            predictor.predict(box=np.array([32, 32, 96, 96]), multimask_output=True)
            if device == "mps":
                torch.mps.synchronize()
            elif device == "cuda":
                torch.cuda.synchronize()
            times.append(time.perf_counter()-start)
            allocations.append(torch.mps.driver_allocated_memory() if device == "mps" else
                               torch.cuda.max_memory_allocated() if device == "cuda" else None)
    peak = max((x for x in allocations if x is not None), default=None)
    result = {"hardware": platform.platform(), "device": device, "n": len(times),
              "seconds_per_slice_median": float(np.median(times)),
              "seconds_per_slice_mean": float(np.mean(times)),
              "first_call_seconds": times[0],
              "steady_seconds_per_slice_mean": float(np.mean(times[1:])),
              "max_observed_device_allocated_bytes": peak,
              "projected_72_patients_155_slices_hours": float(np.mean(times)*72*155/3600),
              "projected_steady_all_slices_hours": float(np.mean(times[1:])*72*155/3600),
              "times": times}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
