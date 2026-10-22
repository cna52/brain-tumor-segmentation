"""Prediction and frozen SAM refinement, independent of labels."""
import time

import numpy as np
import torch

from .data import normalize, resize_slice, restore_mask
from .metrics import boxes_from_mask, cleanup


@torch.inference_mode()
def unet_probability(model, image, size, device, batch_size=16):
    image = normalize(image)
    depth = image.shape[2]
    output = []
    model.eval()
    for start in range(0, depth, batch_size):
        batch = torch.stack([resize_slice(image[:, :, z], size) for z in range(start, min(depth, start+batch_size))])[:, None]
        logits = model(batch.to(device))
        output.append(logits.sigmoid().cpu().numpy()[:, 0])
    return np.concatenate(output), image


def threshold_probability(prob, threshold, min_pixels=0, max_components=5):
    return np.stack([cleanup(x >= threshold, min_pixels, max_components) for x in prob])


def sam_refine(prob, image, predictor, threshold, min_pixels, padding, max_components=5):
    """One FLAIR slice encoding per nonempty slice; highest SAM quality per box."""
    size = prob.shape[-1]
    result = np.zeros_like(prob, dtype=bool)
    times = []
    for z in range(len(prob)):
        candidates = cleanup(prob[z] >= threshold, min_pixels, max_components)
        boxes = boxes_from_mask(candidates, padding, max_components)
        if not boxes:
            continue
        start = time.perf_counter()
        gray = resize_slice(image[:, :, z], size).numpy()
        rgb = np.repeat((np.clip(gray, 0, 1)*255).astype(np.uint8)[:, :, None], 3, axis=2)
        predictor.set_image(rgb)
        for box in boxes:
            masks, scores, _ = predictor.predict(box=np.array(box), multimask_output=True)
            result[z] |= masks[int(np.argmax(scores))]
        times.append(time.perf_counter()-start)
    return result, times


def restore_prediction(pred, source_shape):
    return restore_mask(pred, source_shape)
