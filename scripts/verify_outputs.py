"""Audit the locked test output against the manifest and source image grids."""
import argparse
import hashlib
import json
from pathlib import Path

import nibabel as nib
import numpy as np

from brain_tumor.data import check_split, read_cases


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--data", type=Path, required=True)
    p.add_argument("--split", type=Path, default=Path("splits/patients.json"))
    p.add_argument("--results", type=Path, default=Path("artifacts/results.json"))
    p.add_argument("--predictions", type=Path, default=Path("artifacts/predictions"))
    args = p.parse_args()
    cases, _ = read_cases(args.data)
    split = json.loads(args.split.read_text())
    check_split(split, cases)
    results = json.loads(args.results.read_text())
    assert results["split_sha256"] == hashlib.sha256(args.split.read_bytes()).hexdigest()
    assert results["n_test"] == len(split["test"]) == 72
    assert {r["patient"] for r in results["patients"]} == set(split["test"])
    count = 0
    for case_id in split["test"]:
        source = nib.load(str(cases[case_id]["image"]))
        for method in ("flair", "unet", "unet_cleaned", "unet_sam"):
            mask = nib.load(str(args.predictions / method / f"{case_id}.nii.gz"))
            assert mask.shape == source.shape[:3], (case_id, method, mask.shape)
            assert np.allclose(mask.affine, source.affine), (case_id, method)
            values = np.unique(np.asarray(mask.dataobj))
            assert set(values).issubset({0, 1}), (case_id, method, values)
            count += 1
    print(f"Verified {len(split['test'])} distinct test patients and {count} masks with source shape, affine, and binary values")


if __name__ == "__main__":
    main()
