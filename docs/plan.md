# Milestones and decision log

- [x] Clone and inspect empty repository. Verified `git ls-remote`, `git clone`, and `git status --short --branch`; the clone had no commits. Next: obtain and verify Task01.
- [x] Verify Task01 MD5, extract, assert metadata, commit the patient split. Verification: `.venv/bin/python scripts/prepare_data.py --archive ../brain-tumor-data/Task01_BrainTumour.tar --out ../brain-tumor-data --delete-archive` printed MD5 `240a19d752f0d9e9101544901065d872`, 484 labelled cases, FLAIR channel 0, expected labels, and split counts 339/73/72. The verified archive was removed. Next: tests and MPS smoke run.
- [ ] Run tests and MPS smoke benchmark. Verification: `pytest -q` and `python -m brain_tumor.train ... --smoke`; record elapsed time. Next: full baseline training.
- [ ] Train baseline with validation early stopping. Verification: training log and checkpoint metadata; record checkpoint SHA. Next: benchmark SAM.
- [ ] Benchmark official frozen SAM ViT-B. Verification: `scripts/benchmark_sam.py`; record projected runtime and device memory. Next: validation selection.
- [ ] Lock validation choices. Verification: `python -m brain_tumor.evaluate tune ...` and `configs/selection.json`; record its SHA. Next: untouched test evaluation.
- [ ] Evaluate all 72 test patients and write `docs/results.md`. Verification: `python -m brain_tumor.evaluate test ...`; verify per-patient count, mask shape and affine. Next: review.

## Decisions

- 2026-10-21: Use one FLAIR channel, all nonzero tumour labels, axial 2D slices, and 128×128 working resolution. Keep full source metadata for reconstruction.
- 2026-10-21: Normalize each FLAIR volume using positive finite voxels' 1st and 99th percentiles; set background to zero. The same rule applies to every split.
- 2026-10-21: Shuffle patients and slices within each patient during training so each compressed volume is loaded once per epoch without a slice cache.
- 2026-10-21: Choose SAM's highest predicted IoU mask for each U-Net-derived component box. Empty predictions produce empty SAM outputs. Tune padding on fixed validation patients only.
