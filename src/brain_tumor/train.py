import argparse
import hashlib
import json
import random
import subprocess
import time
from pathlib import Path

import numpy as np
import torch
from torch.utils.data import DataLoader

from .data import PatientBatchSampler, SliceDataset, check_split, read_cases
from .model import UNet, loss_fn


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", type=Path, required=True)
    parser.add_argument("--split", type=Path, default=Path("splits/patients.json"))
    parser.add_argument("--config", type=Path, default=Path("configs/experiment.json"))
    parser.add_argument("--output", type=Path, default=Path("artifacts/baseline.pt"))
    parser.add_argument("--smoke", action="store_true")
    args = parser.parse_args()
    cfg = json.loads(args.config.read_text())
    split = json.loads(args.split.read_text())
    cases, _ = read_cases(args.data)
    check_split(split, cases)
    seed = cfg["seed"]
    random.seed(seed); np.random.seed(seed); torch.manual_seed(seed)
    code_commit = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    lock_sha256 = hashlib.sha256(Path("requirements.lock.txt").read_bytes()).hexdigest()
    device = "mps" if torch.backends.mps.is_available() else "cuda" if torch.cuda.is_available() else "cpu"
    train = SliceDataset(cases, split["train"], cfg["image_size"], augment=True)
    val = SliceDataset(cases, split["val"], cfg["image_size"])
    train_loader = DataLoader(train, batch_sampler=PatientBatchSampler(train, cfg["batch_size"]), num_workers=0)
    val_loader = DataLoader(val, batch_sampler=PatientBatchSampler(val, cfg["batch_size"], False), num_workers=0)
    model = UNet(cfg["base_channels"]).to(device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=cfg["learning_rate"], weight_decay=cfg["weight_decay"])
    best = float("inf"); stale = 0
    epochs = 1 if args.smoke else cfg["epochs"]
    for epoch in range(epochs):
        started = time.perf_counter()
        model.train(); train_loss = 0.; batches = 0
        for x, y in train_loader:
            x, y = x.to(device), y.to(device)
            optimizer.zero_grad(set_to_none=True)
            loss = loss_fn(model(x), y)
            loss.backward(); optimizer.step()
            train_loss += loss.item(); batches += 1
            if args.smoke and batches == 2:
                break
        model.eval(); val_loss = 0.; val_batches = 0
        with torch.inference_mode():
            for x, y in val_loader:
                val_loss += loss_fn(model(x.to(device)), y.to(device)).item(); val_batches += 1
                if args.smoke and val_batches == 2:
                    break
        val_loss /= val_batches
        print(json.dumps({"epoch": epoch+1, "train_loss": train_loss/batches,
                          "val_loss": val_loss, "seconds": time.perf_counter()-started,
                          "device": device, "train_batches": batches, "val_batches": val_batches}), flush=True)
        if val_loss < best:
            best, stale = val_loss, 0
            args.output.parent.mkdir(parents=True, exist_ok=True)
            metadata = {"epoch": epoch+1, "val_loss": val_loss, "seed": seed, "device": device,
                        "config_sha256": hashlib.sha256(args.config.read_bytes()).hexdigest(),
                        "split_sha256": hashlib.sha256(args.split.read_bytes()).hexdigest(),
                        "commit": code_commit, "lockfile_sha256": lock_sha256,
                        "torch": torch.__version__, "smoke": args.smoke}
            torch.save({"model": model.state_dict(), "metadata": metadata}, args.output)
        else:
            stale += 1
            if stale >= cfg["patience"]:
                break


if __name__ == "__main__":
    main()
