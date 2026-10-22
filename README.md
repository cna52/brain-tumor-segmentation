# FLAIR whole-tumour segmentation: U-Net and SAM

Research-only experiment on [Medical Segmentation Decathlon](https://medicaldecathlon.com/) Task01 BrainTumour. A single-channel 2D U-Net predicts whole tumour (all nonzero label classes) from FLAIR MRI. Its connected components generate bounded box prompts for frozen [Segment Anything](https://github.com/facebookresearch/segment-anything) ViT-B. The locked held-out comparison includes a simple FLAIR threshold, raw U-Net, U-Net with the same candidate cleanup, and U-Net plus SAM. SAM is retained in the report even if it makes the result worse. This is **not for clinical use**.

The idea builds on a course team's conceptual exploration of brain-tumour segmentation. This repository uses a new implementation and public MSD data; it contains none of that team's code, data, checkpoints, images, or unverified metrics. Team member names can be added with their consent.

## Data and licence

MSD lists its data under [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/) and asks users to cite the challenge. Cite: Antonelli et al., *The Medical Segmentation Decathlon*, Nature Communications 13, 4128 (2022), https://doi.org/10.1038/s41467-022-30695-9. The 484 labelled training cases support this study; the separate 266 unlabelled test cases do not. The pipeline asserts the FLAIR channel and tumour label definitions in `dataset.json` before use. [MONAI publishes](https://github.com/Project-MONAI/MONAI/blob/dev/monai/apps/datasets.py) the archive URL and MD5 `240a19d752f0d9e9101544901065d872`.

## Setup and reproduction

The commands below run from the repository root on Python 3.11. Keep data and model checkpoints outside Git. The working directory examples put the dataset beside the repository.

```bash
python3.11 -m venv .venv
.venv/bin/python -m pip install -e '.[test]'
.venv/bin/python -m pip list --format=freeze | grep -v '^brain-tumor-segmentation==' > requirements.lock.txt
mkdir -p ../brain-tumor-data
curl -L --fail --continue-at - -o ../brain-tumor-data/Task01_BrainTumour.tar https://msd-for-monai.s3-us-west-2.amazonaws.com/Task01_BrainTumour.tar
.venv/bin/python scripts/prepare_data.py --archive ../brain-tumor-data/Task01_BrainTumour.tar --out ../brain-tumor-data --delete-archive
.venv/bin/python -m pytest -q
.venv/bin/python -m brain_tumor.train --data ../brain-tumor-data/Task01_BrainTumour --smoke --output artifacts/smoke.pt
.venv/bin/python -m brain_tumor.train --data ../brain-tumor-data/Task01_BrainTumour
curl -L --fail -o artifacts/sam_vit_b_01ec64.pth https://dl.fbaipublicfiles.com/segment_anything/sam_vit_b_01ec64.pth
.venv/bin/python scripts/benchmark_sam.py --data ../brain-tumor-data/Task01_BrainTumour
.venv/bin/python -m brain_tumor.evaluate tune --data ../brain-tumor-data/Task01_BrainTumour
.venv/bin/python -m brain_tumor.evaluate test --data ../brain-tumor-data/Task01_BrainTumour --export-dir artifacts/predictions
```

The split is fixed in `splits/patients.json`. Training includes every axial training slice, including empty slices. Validation patients select the checkpoint, thresholds, connected-component size, and box padding. Test labels are loaded only by the final `test` command for metrics. Inference functions use no labels. The output masks restore source shape and affine. `artifacts/` and NIfTI files are ignored by Git.

See [plan](docs/plan.md) and [results](docs/results.md) for recorded execution status and findings.
