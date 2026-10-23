# Portfolio extension roadmap

Status: proposed. The completed experiment and its locked 72-patient result remain in [results.md](results.md). These tasks have not been implemented or evaluated.

## Goal and order

Make the existing work easy to run and inspect, then explain why frozen SAM reduced mean whole-volume Dice. Complete milestones 1–3 before committing to the larger model comparison in milestone 4. Keep the original result and configuration unchanged.

## 1. Label-free inference and benchmark clarity

- Add a command that accepts a FLAIR NIfTI volume, the trained U-Net checkpoint, and optionally the official SAM checkpoint. Support a 3D FLAIR input and an explicitly selected FLAIR channel from a 4D input.
- Export full-resolution binary masks with the input shape and affine, plus a small JSON record of model/checkpoint hashes, configuration, device, and per-stage timing. The command must never require or open a label file.
- Validate dimensions and channel selection, handle empty U-Net candidates, and test the command with a synthetic NIfTI and a real unlabelled case. Verify exported masks against the source grid.
- Revisit the SAM memory benchmark. Measure allocation during inference if the available MPS tooling supports a defensible peak; otherwise keep the result labelled as the maximum **observed** allocation and document the sampling method.
- Decide whether the trained checkpoint can be distributed under the applicable data and model terms before offering a public download. Keep checkpoints out of Git unless rights are verified.

**Done when:** a documented command runs without ground truth, its outputs pass shape/affine/binary checks, and the benchmark's memory wording matches the measurement.

## 2. Visual case study

- Build a reproducible figure generator for one SAM improvement and one failure, showing the FLAIR slice, U-Net mask, SAM mask, and false-positive/false-negative overlays. Include the case ID and whole-volume metrics so the images are not mistaken for aggregate evidence.
- Check the source image's publication terms and required attribution before committing any image. If publication is not cleared, publish a synthetic demonstration and keep patient imagery local.
- Add a short README walkthrough that links the figure, the inference command, and the full per-patient results. Do not use material from the earlier course project.

**Done when:** a reviewer can understand the automatic prompt path and the negative result from the README, and every public image has a documented source and publication basis.

## 3. Failure analysis of the existing comparison

- Write down the analysis questions and metrics before producing new plots: tumour volume, U-Net candidate coverage, box coverage, prompted versus unprompted slices, SAM Dice change, and added false-positive volume.
- Compute ground-truth-derived coverage only for retrospective analysis. Inference prompts must continue to come solely from U-Net predictions.
- Show distributions and patient-level relationships, with uncertainty where useful. Explain both cases where SAM helps and cases where it expands false positives or loses tumour recall.
- Treat analysis of the already inspected 72-patient test set as **exploratory**. Do not tune thresholds, select a new method, or make a fresh held-out performance claim from it.

**Done when:** a brief report connects the aggregate Dice decline to measured failure patterns without implying causation or clinical utility.

## 4. Optional new model comparison

- First choose a labelled, FLAIR-compatible cohort with a matching whole-tumour definition. Check access, licence, patient overlap with MSD Task01, available storage, and compute before downloading it. If those checks fail, stop this milestone rather than reuse the original test set as a new holdout.
- Benchmark the official [MedSAM](https://github.com/bowang-lab/MedSAM) implementation and checkpoint. Pin the version and checksum, and compare it with SAM using the same U-Net-generated candidate boxes. Document any preprocessing needed by each model.
- Select mask rules and other settings using validation data only. Freeze the protocol and evaluate the external cohort once, reporting every patient, paired differences, runtime, and failures whether MedSAM helps or hurts.
- A 3D baseline such as [nnU-Net](https://github.com/MIC-DKFZ/nnUNet) is a later, separate experiment if compute and data access justify it.

**Done when:** the new comparison has a documented nonoverlapping evaluation cohort and a locked, reproducible result. Runs on the original 72 test patients may be reported only as exploratory.

## Resume evidence to produce

Milestones 1–2 should provide a runnable demonstration and clear public artifact. Milestone 3 should show evidence-based debugging. Milestone 4 can support a new comparative result only after its evaluation gate passes. Update resume claims only for completed, measured work; describe the original SAM finding accurately.
