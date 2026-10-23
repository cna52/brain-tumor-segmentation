# Case-study image attribution

`case_study.png` is an adapted visualization of FLAIR images and whole-tumour labels from Medical Segmentation Decathlon Task01 BrainTumour, cases `BRATS_073` and `BRATS_198`. The figure generator overlays this project's U-Net and SAM predictions and adds titles, colours, and metrics. It is provided under [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/) in accordance with the [MSD dataset terms](https://medicaldecathlon.com/). The source MRI volumes and labels are not included in this repository.

Please cite Antonelli et al., *The Medical Segmentation Decathlon*, Nature Communications 13, 4128 (2022), https://doi.org/10.1038/s41467-022-30695-9. The figure is for research illustration only, not clinical use. Rebuild it with `scripts/render_case_study.py` and the verified Task01 dataset.
