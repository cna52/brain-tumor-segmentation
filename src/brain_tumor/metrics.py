import numpy as np
from scipy import ndimage


def cleanup(mask, min_pixels=0, max_components=5):
    """Use the same 2D candidate components for the control and SAM prompts."""
    if not mask.any():
        return mask.astype(bool)
    labels, count = ndimage.label(mask, structure=np.ones((3, 3), bool))
    sizes = np.bincount(labels.ravel())[1:]
    keep = np.argsort(sizes)[::-1][:max_components] + 1
    keep = [i for i in keep if sizes[i-1] >= min_pixels]
    return np.isin(labels, keep)


def boxes_from_mask(mask, padding=0, max_boxes=5):
    labels, count = ndimage.label(mask, structure=np.ones((3, 3), bool))
    if count == 0:
        return []
    sizes = np.bincount(labels.ravel())[1:]
    boxes = []
    h, w = mask.shape
    for label in np.argsort(sizes)[::-1][:max_boxes] + 1:
        ys, xs = np.where(labels == label)
        boxes.append([max(0, int(xs.min())-padding), max(0, int(ys.min())-padding),
                      min(w-1, int(xs.max())+padding), min(h-1, int(ys.max())+padding)])
    return boxes


def patient_metrics(pred, truth, affine):
    pred, truth = pred.astype(bool), truth.astype(bool)
    tp = np.count_nonzero(pred & truth)
    p, t = np.count_nonzero(pred), np.count_nonzero(truth)
    voxel_ml = abs(np.linalg.det(affine[:3, :3])) / 1000
    return {"dice": float(2*tp/(p+t)) if p+t else 1.0,
            "recall": float(tp/t) if t else 1.0,
            "false_positive_ml": float((p-tp)*voxel_ml),
            "predicted_ml": float(p*voxel_ml), "truth_ml": float(t*voxel_ml)}
