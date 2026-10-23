import hashlib
import json

import nibabel as nib
import numpy as np
import pytest
import torch

from brain_tumor.model import UNet
from brain_tumor.predict import load_flair, run_prediction


def test_load_flair_requires_explicit_4d_channel(tmp_path):
    image = np.zeros((32, 40, 2, 4), np.float32)
    image[..., 0] = 3
    image[..., 1] = 100
    path = tmp_path / "four_channels.nii.gz"
    nib.save(nib.Nifti1Image(image, np.eye(4)), path)
    with pytest.raises(ValueError, match="explicit"):
        load_flair(path)
    flair, _, _ = load_flair(path, 0)
    assert flair.shape == (32, 40, 2)
    assert np.all(flair == 3)
    with pytest.raises(ValueError, match="outside"):
        load_flair(path, 4)


def test_label_free_prediction_exports_source_grid_and_provenance(tmp_path):
    image = np.zeros((32, 40, 2), np.float32)
    image[8:24, 10:30, :] = 10
    affine = np.array([[2, 0, 0, -40], [0, 2, 0, -50],
                       [0, 0, 5, 10], [0, 0, 0, 1]], float)
    input_path = tmp_path / "flair.nii.gz"
    nib.save(nib.Nifti1Image(image, affine), input_path)

    config = {"image_size": 32, "batch_size": 2, "base_channels": 16,
              "max_boxes_per_slice": 5}
    config_path = tmp_path / "config.json"
    config_path.write_text(json.dumps(config))
    config_sha = hashlib.sha256(config_path.read_bytes()).hexdigest()
    selection = {"config_sha256": config_sha, "split_sha256": "test-split",
                 "sam_mask_rule": "highest_predicted_iou",
                 "unet_raw_threshold": 0.25, "unet_threshold": 0.25,
                 "minimum_component_pixels": 16, "box_padding_pixels": 0}
    selection_path = tmp_path / "selection.json"
    selection_path.write_text(json.dumps(selection))
    checkpoint = tmp_path / "model.pt"
    torch.save({"model": UNet(16).state_dict(),
                "metadata": {"smoke": False, "config_sha256": config_sha,
                             "split_sha256": "test-split", "commit": "test-commit"}}, checkpoint)

    output_dir = tmp_path / "outputs"
    record = run_prediction(input_path, output_dir, checkpoint, config_path,
                            selection_path, device="cpu")
    assert record["outputs"] == ["unet", "unet_cleaned"]
    assert record["sam_seconds"] is None
    assert json.loads((output_dir / "run.json").read_text()) == record
    for name in record["outputs"]:
        saved = nib.load(str(output_dir / f"{name}.nii.gz"))
        assert saved.shape == image.shape
        assert np.allclose(saved.affine, affine)
        assert set(np.unique(np.asarray(saved.dataobj))).issubset({0, 1})
