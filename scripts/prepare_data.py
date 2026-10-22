"""Verify MONAI's archive checksum, safely extract, and lock patient split."""
import argparse
import hashlib
import json
import tarfile
from pathlib import Path

from brain_tumor.data import make_split, read_cases

URL = "https://msd-for-monai.s3-us-west-2.amazonaws.com/Task01_BrainTumour.tar"
MD5 = "240a19d752f0d9e9101544901065d872"


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--archive", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--split", type=Path, default=Path("splits/patients.json"))
    p.add_argument("--delete-archive", action="store_true")
    args = p.parse_args()
    digest = hashlib.md5()
    with args.archive.open("rb") as f:
        for block in iter(lambda: f.read(8*1024*1024), b""):
            digest.update(block)
    assert digest.hexdigest() == MD5, f"MD5 mismatch: {digest.hexdigest()}"
    print(f"Verified MD5 {MD5}", flush=True)
    args.out.mkdir(parents=True, exist_ok=True)
    with tarfile.open(args.archive) as tar:
        for member in tar:
            destination = (args.out / member.name).resolve()
            assert destination.is_relative_to(args.out.resolve()), member.name
            assert member.isfile() or member.isdir(), member.name
        tar.extractall(args.out)
    root = args.out / "Task01_BrainTumour"
    cases, meta = read_cases(root)
    print(json.dumps({"cases": len(cases), "modality": meta["modality"],
                      "labels": meta["labels"], "licence": meta.get("licence"),
                      "numTest": meta.get("numTest")}, indent=2), flush=True)
    split = make_split(cases)
    args.split.parent.mkdir(parents=True, exist_ok=True)
    args.split.write_text(json.dumps(split, indent=2) + "\n")
    print(f"Wrote {args.split}: train={len(split['train'])}, val={len(split['val'])}, test={len(split['test'])}")
    if args.delete_archive:
        args.archive.unlink()
        print("Removed verified archive after extraction")


if __name__ == "__main__":
    main()
