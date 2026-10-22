import numpy as np

from brain_tumor.data import check_split, make_split, normalize, restore_mask, save_mask
from brain_tumor.inference import sam_padding_grid, sam_refine, unet_probability
from brain_tumor.metrics import boxes_from_mask, cleanup, patient_metrics
from brain_tumor.model import UNet


def test_split_is_complete_disjoint_and_repeatable():
    cases = {f"case_{i:03d}": None for i in range(484)}
    a = make_split(cases)
    assert a == make_split(cases)
    assert [len(a[k]) for k in ("train", "val", "test")] == [339, 73, 72]
    check_split(a, cases)


def test_empty_prompt_and_cleanup():
    empty = np.zeros((16, 16), bool)
    assert boxes_from_mask(empty) == []
    assert not cleanup(empty).any()
    mask = empty.copy(); mask[1:5, 2:7] = True; mask[10, 10] = True
    assert len(boxes_from_mask(cleanup(mask, 3))) == 1


def test_reconstruction_and_physical_metrics():
    mask = np.ones((3, 8, 8), bool)
    restored = restore_mask(mask, (16, 20, 3))
    assert restored.shape == (16, 20, 3)
    affine = np.diag([2., 2., 5., 1.])
    result = patient_metrics(restored, restored, affine)
    assert result["dice"] == 1 and result["recall"] == 1
    assert result["false_positive_ml"] == 0
    assert np.isclose(result["truth_ml"], 16*20*3*20/1000)


def test_normalization_and_model_shape():
    import torch
    image = np.array([0., 10., 20., 30.], dtype=np.float32)
    norm = normalize(image)
    assert norm[0] == 0 and norm.min() >= 0 and norm.max() <= 1
    assert UNet(16)(torch.zeros(2, 1, 128, 128)).shape == (2, 1, 128, 128)


def test_inference_requires_no_ground_truth_and_preserves_nifti_grid(tmp_path):
    import nibabel as nib
    import torch
    image = np.zeros((16, 20, 3), np.float32)
    image[4:12, 5:15, :] = 10
    model = UNet(16).eval()
    prob, _ = unet_probability(model, image, 32, "cpu", 2)
    assert prob.shape == (3, 32, 32)
    restored = restore_mask(prob > .5, image.shape)
    affine = np.array([[2, 0, 0, -40], [0, 2, 0, -50], [0, 0, 5, 10], [0, 0, 0, 1]], float)
    path = tmp_path / "mask.nii.gz"
    save_mask(restored, affine, nib.Nifti1Header(), path)
    saved = nib.load(str(path))
    assert saved.shape == image.shape
    assert np.allclose(saved.affine, affine)


def test_sam_empty_candidates_skip_model_calls():
    class FailPredictor:
        def set_image(self, image):
            raise AssertionError("SAM should not run without a candidate")
    pred, times = sam_refine(np.zeros((2, 16, 16)), np.zeros((16, 16, 2)),
                             FailPredictor(), .5, 0, 4)
    assert not pred.any() and times == []


def test_padding_grid_reuses_one_image_encoding():
    class Predictor:
        def __init__(self):
            self.images = 0
            self.shape = None
        def set_image(self, image):
            self.images += 1
            self.shape = image.shape[:2]
        def predict(self, box, multimask_output):
            mask = np.zeros(self.shape, bool)
            x1, y1, x2, y2 = box
            mask[y1:y2+1, x1:x2+1] = True
            return np.stack([mask, np.zeros_like(mask)]), np.array([.9, .1]), None
    prob = np.zeros((2, 16, 16))
    prob[0, 4:8, 5:9] = 1
    predictor = Predictor()
    outputs = sam_padding_grid(prob, np.ones((16, 16, 2)), predictor, .5, 0, [0, 2])
    assert predictor.images == 1
    assert outputs[0][0].sum() == 16
    assert outputs[2][0].sum() > outputs[0][0].sum()
    assert not outputs[0][1].any()
