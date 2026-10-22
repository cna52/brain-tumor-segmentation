"""Metadata-checked MSD Task01 loading and reversible in-plane resize."""
from __future__ import annotations

import json
import random
from functools import lru_cache
from pathlib import Path

import nibabel as nib
import numpy as np
import torch
import torch.nn.functional as F
from torch.utils.data import Dataset, Sampler

EXPECTED_MODALITY = {"0": "FLAIR", "1": "T1w", "2": "t1gd", "3": "T2w"}
EXPECTED_LABELS = {"0": "background", "1": "edema", "2": "non-enhancing tumor", "3": "enhancing tumour"}


def read_cases(root: Path):
    root = Path(root)
    meta = json.loads((root / "dataset.json").read_text())
    modality = {str(k): str(v) for k, v in meta["modality"].items()}
    labels = {str(k): str(v) for k, v in meta["labels"].items()}
    assert modality == EXPECTED_MODALITY, f"Unexpected modality mapping: {modality}"
    assert labels == EXPECTED_LABELS, f"Unexpected label mapping: {labels}"
    assert meta["numTraining"] == 484 and len(meta["training"]) == 484
    cases = {}
    for item in meta["training"]:
        image = root / item["image"].removeprefix("./")
        label = root / item["label"].removeprefix("./")
        case_id = image.name.removesuffix(".nii.gz")
        assert case_id not in cases
        assert image.is_file() and label.is_file(), (image, label)
        cases[case_id] = {"image": image, "label": label}
    assert len(cases) == 484
    return cases, meta


def make_split(cases, seed=20261021):
    ids = sorted(cases)
    random.Random(seed).shuffle(ids)
    n = len(ids)
    n_train, n_val = round(n * .70), round(n * .15)
    split = {"seed": seed, "train": sorted(ids[:n_train]),
             "val": sorted(ids[n_train:n_train+n_val]), "test": sorted(ids[n_train+n_val:])}
    check_split(split, cases)
    return split


def check_split(split, cases):
    groups = [set(split[k]) for k in ("train", "val", "test")]
    assert all(not groups[i] & groups[j] for i in range(3) for j in range(i+1, 3))
    assert set.union(*groups) == set(cases)
    assert [len(x) for x in groups] == [339, 73, 72]


def load_volume(case, with_label=True):
    img_nii = nib.load(str(case["image"]), mmap=True)
    assert len(img_nii.shape) == 4 and img_nii.shape[3] == 4
    image = np.asarray(img_nii.dataobj[..., 0], dtype=np.float32)
    label = None
    if with_label:
        label_nii = nib.load(str(case["label"]), mmap=True)
        assert label_nii.shape == image.shape
        assert np.allclose(img_nii.affine, label_nii.affine)
        raw = np.asarray(label_nii.dataobj)
        assert set(np.unique(raw)).issubset({0, 1, 2, 3})
        label = raw > 0
    return image, label, img_nii.affine.copy(), img_nii.header.copy()


def normalize(image):
    """Clip nonzero FLAIR to its 1st/99th percentiles, then map to [0,1]."""
    out = np.zeros_like(image, dtype=np.float32)
    nonzero = np.isfinite(image) & (image > 0)
    if nonzero.any():
        lo, hi = np.percentile(image[nonzero], [1, 99])
        if hi > lo:
            out[nonzero] = np.clip((image[nonzero] - lo) / (hi - lo), 0, 1)
    return out


def resize_slice(array, size, is_mask=False):
    tensor = torch.as_tensor(np.ascontiguousarray(array), dtype=torch.float32)[None, None]
    mode = "nearest" if is_mask else "bilinear"
    result = F.interpolate(tensor, size=(size, size), mode=mode,
                           **({} if is_mask else {"align_corners": False}))
    return result[0, 0]


def restore_mask(mask, shape):
    """Restore all axial slices to source (X,Y,Z) grid, preserving slice count."""
    x, y, z = shape
    tensor = torch.as_tensor(mask, dtype=torch.float32)[:, None]
    assert tensor.shape[0] == z
    out = F.interpolate(tensor, size=(x, y), mode="nearest")[:, 0]
    return out.numpy().transpose(1, 2, 0).astype(np.uint8)


def save_mask(mask, affine, header, path):
    header = header.copy()
    header.set_data_dtype(np.uint8)
    nib.save(nib.Nifti1Image(mask.astype(np.uint8), affine, header), str(path))


class SliceDataset(Dataset):
    def __init__(self, cases, ids, size=128, augment=False):
        self.cases, self.ids, self.size, self.augment = cases, ids, size, augment
        self.index = []
        for patient_index, case_id in enumerate(ids):
            shape = nib.load(str(cases[case_id]["image"])).shape
            assert len(shape) == 4 and shape[-1] == 4
            self.index.extend((patient_index, z) for z in range(shape[2]))

    def __len__(self):
        return len(self.index)

    @lru_cache(maxsize=1)
    def _patient(self, patient_index):
        image, label, _, _ = load_volume(self.cases[self.ids[patient_index]])
        return normalize(image), label

    def __getitem__(self, index):
        patient_index, z = self.index[index]
        image, label = self._patient(patient_index)
        x = resize_slice(image[:, :, z], self.size)
        y = resize_slice(label[:, :, z], self.size, True)
        if self.augment:
            if random.random() < .5:
                x, y = x.flip(0), y.flip(0)
            if random.random() < .5:
                x, y = x.flip(1), y.flip(1)
            k = random.randrange(4)
            x, y = x.rot90(k), y.rot90(k)
        return x.unsqueeze(0), y.unsqueeze(0)


class PatientBatchSampler(Sampler):
    """Shuffle patients, then slices within each patient; load each volume once."""
    def __init__(self, dataset, batch_size, shuffle=True):
        self.dataset, self.batch_size, self.shuffle = dataset, batch_size, shuffle
        self.groups = [[] for _ in dataset.ids]
        for i, (patient_index, _) in enumerate(dataset.index):
            self.groups[patient_index].append(i)

    def __iter__(self):
        patients = list(range(len(self.groups)))
        if self.shuffle:
            random.shuffle(patients)
        for patient in patients:
            indices = self.groups[patient].copy()
            if self.shuffle:
                random.shuffle(indices)
            for start in range(0, len(indices), self.batch_size):
                yield indices[start:start+self.batch_size]

    def __len__(self):
        return sum((len(g) + self.batch_size - 1) // self.batch_size for g in self.groups)
