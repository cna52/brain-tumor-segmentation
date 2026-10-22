# Held-out results

Research only; not for clinical use.

Code commit: `567bd37c0edde5c87d187f3f9a6926eb05c4ea09`. Split SHA-256: `f47ad61669a733ca531e89ade8499483cc739bedcdf9355e302caf170826697b`.
Configuration SHA-256: `536ed17bff7d48744fcab1e93e673c3251abad9715b91ae6a146045870bc2f76`. Selection SHA-256: `5f3654174d83ab286d63135bb5f01a16d47e09b2868c8c348168fe4b01a73e8a`.
Dependency lockfile SHA-256: `9f1f69cb2b35c52baa45d4b733347af6a8f809bf48981c58b7c03042b52fcf4c`.
U-Net checkpoint SHA-256: `ff291f6f769a9535d504feeb660c1c64b392ab9b905f379a5284c8991de6fdf5`. SAM checkpoint SHA-256: `ec2df62732614e57411cdcf32a23ffdf28910380d03139ee0f4fcbe91eb8c912`.
The dependency lockfile is `requirements.lock.txt`. Device: mps on macOS-26.5-arm64-arm-64bit.

## Aggregate

Mean across all 72 held-out patient volumes. False positives use each source affine's voxel volume.

| Method | Dice | Tumour recall | False-positive mL |
|---|---:|---:|---:|
| FLAIR threshold | 0.5547 | 0.7415 | 138.26 |
| U-Net | 0.7931 | 0.7768 | 12.85 |
| U-Net + cleanup | 0.7931 | 0.7749 | 12.61 |
| U-Net + SAM | 0.7566 | 0.8113 | 31.85 |

Mean paired Dice difference, SAM minus raw U-Net: -0.0365; SAM minus cleaned U-Net: -0.0365. Median paired difference: -0.0405. SAM improved 13 patients and worsened 59. Patient bootstrap 95% interval for the mean difference: [-0.0489, -0.0241] (10,000 resamples, seed 20261021).

## Every test patient

All values are whole-volume. FP is false-positive volume in mL.

| Patient | Method | Dice | Recall | FP mL |
|---|---|---:|---:|---:|
| BRATS_001 | FLAIR threshold | 0.8318 | 0.7620 | 7.84 |
| BRATS_001 | U-Net | 0.8633 | 0.8964 | 20.15 |
| BRATS_001 | U-Net + cleanup | 0.8631 | 0.8961 | 20.14 |
| BRATS_001 | U-Net + SAM | 0.7955 | 0.9387 | 47.08 |
| BRATS_006 | FLAIR threshold | 0.7369 | 0.5998 | 6.08 |
| BRATS_006 | U-Net | 0.7082 | 0.5628 | 5.75 |
| BRATS_006 | U-Net + cleanup | 0.7072 | 0.5615 | 5.75 |
| BRATS_006 | U-Net + SAM | 0.7676 | 0.7291 | 37.09 |
| BRATS_007 | FLAIR threshold | 0.2942 | 0.9244 | 266.37 |
| BRATS_007 | U-Net | 0.8009 | 0.8902 | 20.33 |
| BRATS_007 | U-Net + cleanup | 0.8002 | 0.8876 | 20.21 |
| BRATS_007 | U-Net + SAM | 0.7944 | 0.8707 | 19.64 |
| BRATS_010 | FLAIR threshold | 0.0486 | 0.9950 | 797.44 |
| BRATS_010 | U-Net | 0.7968 | 0.9076 | 7.59 |
| BRATS_010 | U-Net + cleanup | 0.8049 | 0.9076 | 7.12 |
| BRATS_010 | U-Net + SAM | 0.7423 | 0.8772 | 9.96 |
| BRATS_026 | FLAIR threshold | 0.3493 | 0.9323 | 210.28 |
| BRATS_026 | U-Net | 0.8024 | 0.8441 | 16.04 |
| BRATS_026 | U-Net + cleanup | 0.8023 | 0.8431 | 15.97 |
| BRATS_026 | U-Net + SAM | 0.8562 | 0.9083 | 13.17 |
| BRATS_028 | FLAIR threshold | 0.2284 | 0.8584 | 450.51 |
| BRATS_028 | U-Net | 0.5151 | 0.4609 | 26.17 |
| BRATS_028 | U-Net + cleanup | 0.5166 | 0.4600 | 25.54 |
| BRATS_028 | U-Net + SAM | 0.5421 | 0.5701 | 42.47 |
| BRATS_029 | FLAIR threshold | 0.0527 | 0.8399 | 567.37 |
| BRATS_029 | U-Net | 0.2291 | 0.7402 | 89.19 |
| BRATS_029 | U-Net + cleanup | 0.2323 | 0.7402 | 87.48 |
| BRATS_029 | U-Net + SAM | 0.1334 | 0.7223 | 172.02 |
| BRATS_032 | FLAIR threshold | 0.5907 | 0.4195 | 0.22 |
| BRATS_032 | U-Net | 0.8549 | 0.7787 | 9.66 |
| BRATS_032 | U-Net + cleanup | 0.8546 | 0.7778 | 9.54 |
| BRATS_032 | U-Net + SAM | 0.8294 | 0.9051 | 62.34 |
| BRATS_044 | FLAIR threshold | 0.6637 | 0.7372 | 19.51 |
| BRATS_044 | U-Net | 0.8442 | 0.9098 | 9.89 |
| BRATS_044 | U-Net + cleanup | 0.8454 | 0.9072 | 9.63 |
| BRATS_044 | U-Net + SAM | 0.7109 | 0.7437 | 14.04 |
| BRATS_047 | FLAIR threshold | 0.6189 | 0.5169 | 24.08 |
| BRATS_047 | U-Net | 0.8078 | 0.6862 | 2.00 |
| BRATS_047 | U-Net + cleanup | 0.8058 | 0.6833 | 1.99 |
| BRATS_047 | U-Net + SAM | 0.8602 | 0.8554 | 20.90 |
| BRATS_049 | FLAIR threshold | 0.2588 | 0.6225 | 255.98 |
| BRATS_049 | U-Net | 0.3547 | 0.5705 | 132.23 |
| BRATS_049 | U-Net + cleanup | 0.3529 | 0.5662 | 131.89 |
| BRATS_049 | U-Net + SAM | 0.3462 | 0.7640 | 212.82 |
| BRATS_052 | FLAIR threshold | 0.8314 | 0.7188 | 0.97 |
| BRATS_052 | U-Net | 0.9278 | 0.8761 | 1.17 |
| BRATS_052 | U-Net + cleanup | 0.9277 | 0.8760 | 1.17 |
| BRATS_052 | U-Net + SAM | 0.8871 | 0.8273 | 3.56 |
| BRATS_053 | FLAIR threshold | 0.7246 | 0.7450 | 23.13 |
| BRATS_053 | U-Net | 0.8228 | 0.7661 | 7.13 |
| BRATS_053 | U-Net + cleanup | 0.8212 | 0.7615 | 6.92 |
| BRATS_053 | U-Net + SAM | 0.7611 | 0.8181 | 24.64 |
| BRATS_055 | FLAIR threshold | 0.8232 | 0.7416 | 8.74 |
| BRATS_055 | U-Net | 0.9056 | 0.8720 | 7.81 |
| BRATS_055 | U-Net + cleanup | 0.9050 | 0.8707 | 7.79 |
| BRATS_055 | U-Net + SAM | 0.8322 | 0.9304 | 44.44 |
| BRATS_056 | FLAIR threshold | 0.8410 | 0.7875 | 12.63 |
| BRATS_056 | U-Net | 0.9222 | 0.9040 | 8.37 |
| BRATS_056 | U-Net + cleanup | 0.9221 | 0.9034 | 8.31 |
| BRATS_056 | U-Net + SAM | 0.8327 | 0.9564 | 50.44 |
| BRATS_059 | FLAIR threshold | 0.6765 | 0.5279 | 3.27 |
| BRATS_059 | U-Net | 0.9163 | 0.8616 | 1.89 |
| BRATS_059 | U-Net + cleanup | 0.9156 | 0.8603 | 1.88 |
| BRATS_059 | U-Net + SAM | 0.8885 | 0.8658 | 8.27 |
| BRATS_061 | FLAIR threshold | 0.8114 | 0.6868 | 0.51 |
| BRATS_061 | U-Net | 0.9325 | 0.8963 | 2.18 |
| BRATS_061 | U-Net + cleanup | 0.9325 | 0.8963 | 2.18 |
| BRATS_061 | U-Net + SAM | 0.8756 | 0.8212 | 4.57 |
| BRATS_062 | FLAIR threshold | 0.4347 | 0.5173 | 49.38 |
| BRATS_062 | U-Net | 0.5943 | 0.5360 | 15.33 |
| BRATS_062 | U-Net + cleanup | 0.5906 | 0.5258 | 14.58 |
| BRATS_062 | U-Net + SAM | 0.5326 | 0.5067 | 22.68 |
| BRATS_073 | FLAIR threshold | 0.4913 | 0.8622 | 181.13 |
| BRATS_073 | U-Net | 0.8459 | 0.8024 | 10.41 |
| BRATS_073 | U-Net + cleanup | 0.8451 | 0.8002 | 10.27 |
| BRATS_073 | U-Net + SAM | 0.6992 | 0.8245 | 58.68 |
| BRATS_079 | FLAIR threshold | 0.2982 | 0.8909 | 363.99 |
| BRATS_079 | U-Net | 0.8229 | 0.7399 | 5.20 |
| BRATS_079 | U-Net + cleanup | 0.8226 | 0.7367 | 4.85 |
| BRATS_079 | U-Net + SAM | 0.7831 | 0.8374 | 26.84 |
| BRATS_088 | FLAIR threshold | 0.5928 | 0.8277 | 244.77 |
| BRATS_088 | U-Net | 0.6366 | 0.4836 | 9.01 |
| BRATS_088 | U-Net + cleanup | 0.6349 | 0.4801 | 8.19 |
| BRATS_088 | U-Net + SAM | 0.6940 | 0.6334 | 48.72 |
| BRATS_092 | FLAIR threshold | 0.2634 | 0.7178 | 411.27 |
| BRATS_092 | U-Net | 0.5100 | 0.3561 | 4.43 |
| BRATS_092 | U-Net + cleanup | 0.5076 | 0.3519 | 3.81 |
| BRATS_092 | U-Net + SAM | 0.5713 | 0.4272 | 7.54 |
| BRATS_111 | FLAIR threshold | 0.8038 | 0.7206 | 6.99 |
| BRATS_111 | U-Net | 0.9415 | 0.9109 | 2.32 |
| BRATS_111 | U-Net + cleanup | 0.9415 | 0.9106 | 2.30 |
| BRATS_111 | U-Net + SAM | 0.8775 | 0.9043 | 15.12 |
| BRATS_113 | FLAIR threshold | 0.8108 | 0.7532 | 16.74 |
| BRATS_113 | U-Net | 0.8851 | 0.8292 | 7.11 |
| BRATS_113 | U-Net + cleanup | 0.8851 | 0.8291 | 7.11 |
| BRATS_113 | U-Net + SAM | 0.8490 | 0.9481 | 45.60 |
| BRATS_120 | FLAIR threshold | 0.3102 | 0.6628 | 84.33 |
| BRATS_120 | U-Net | 0.6619 | 0.5486 | 3.52 |
| BRATS_120 | U-Net + cleanup | 0.6504 | 0.5333 | 3.44 |
| BRATS_120 | U-Net + SAM | 0.6682 | 0.5577 | 3.60 |
| BRATS_130 | FLAIR threshold | 0.1469 | 0.9700 | 630.71 |
| BRATS_130 | U-Net | 0.8813 | 0.8329 | 3.22 |
| BRATS_130 | U-Net + cleanup | 0.8819 | 0.8316 | 3.06 |
| BRATS_130 | U-Net + SAM | 0.8414 | 0.8970 | 13.20 |
| BRATS_133 | FLAIR threshold | 0.7018 | 0.6087 | 7.55 |
| BRATS_133 | U-Net | 0.8133 | 0.6905 | 0.46 |
| BRATS_133 | U-Net + cleanup | 0.8127 | 0.6896 | 0.45 |
| BRATS_133 | U-Net + SAM | 0.7237 | 0.5830 | 1.69 |
| BRATS_144 | FLAIR threshold | 0.6937 | 0.7719 | 23.26 |
| BRATS_144 | U-Net | 0.9087 | 0.8797 | 2.90 |
| BRATS_144 | U-Net + cleanup | 0.9087 | 0.8797 | 2.90 |
| BRATS_144 | U-Net + SAM | 0.8421 | 0.8331 | 7.46 |
| BRATS_156 | FLAIR threshold | 0.5978 | 0.8076 | 199.13 |
| BRATS_156 | U-Net | 0.7497 | 0.6492 | 18.41 |
| BRATS_156 | U-Net + cleanup | 0.7470 | 0.6438 | 17.79 |
| BRATS_156 | U-Net + SAM | 0.7692 | 0.8644 | 85.27 |
| BRATS_158 | FLAIR threshold | 0.2505 | 0.9100 | 263.69 |
| BRATS_158 | U-Net | 0.8974 | 0.8479 | 2.05 |
| BRATS_158 | U-Net + cleanup | 0.8979 | 0.8479 | 2.01 |
| BRATS_158 | U-Net + SAM | 0.8692 | 0.7861 | 1.11 |
| BRATS_161 | FLAIR threshold | 0.2921 | 0.8214 | 409.45 |
| BRATS_161 | U-Net | 0.6442 | 0.4927 | 3.99 |
| BRATS_161 | U-Net + cleanup | 0.6396 | 0.4875 | 3.97 |
| BRATS_161 | U-Net + SAM | 0.7135 | 0.6546 | 19.42 |
| BRATS_184 | FLAIR threshold | 0.1745 | 0.7787 | 210.44 |
| BRATS_184 | U-Net | 0.7029 | 0.6729 | 7.12 |
| BRATS_184 | U-Net + cleanup | 0.7045 | 0.6682 | 6.74 |
| BRATS_184 | U-Net + SAM | 0.6286 | 0.6259 | 10.76 |
| BRATS_188 | FLAIR threshold | 0.2334 | 0.7418 | 165.30 |
| BRATS_188 | U-Net | 0.6996 | 0.6698 | 8.78 |
| BRATS_188 | U-Net + cleanup | 0.6941 | 0.6586 | 8.56 |
| BRATS_188 | U-Net + SAM | 0.6297 | 0.6682 | 16.27 |
| BRATS_196 | FLAIR threshold | 0.7894 | 0.7249 | 18.67 |
| BRATS_196 | U-Net | 0.9392 | 0.9156 | 5.71 |
| BRATS_196 | U-Net + cleanup | 0.9396 | 0.9156 | 5.56 |
| BRATS_196 | U-Net + SAM | 0.8512 | 0.9325 | 43.23 |
| BRATS_197 | FLAIR threshold | 0.5999 | 0.5667 | 36.55 |
| BRATS_197 | U-Net | 0.6479 | 0.5415 | 14.71 |
| BRATS_197 | U-Net + cleanup | 0.6442 | 0.5349 | 14.23 |
| BRATS_197 | U-Net + SAM | 0.5913 | 0.5217 | 27.49 |
| BRATS_198 | FLAIR threshold | 0.6649 | 0.5181 | 7.31 |
| BRATS_198 | U-Net | 0.7949 | 0.6705 | 2.99 |
| BRATS_198 | U-Net + cleanup | 0.7942 | 0.6696 | 2.98 |
| BRATS_198 | U-Net + SAM | 0.9050 | 0.8851 | 12.85 |
| BRATS_203 | FLAIR threshold | 0.8088 | 0.7391 | 11.20 |
| BRATS_203 | U-Net | 0.8999 | 0.8840 | 10.20 |
| BRATS_203 | U-Net + cleanup | 0.9003 | 0.8836 | 10.02 |
| BRATS_203 | U-Net + SAM | 0.7847 | 0.9185 | 53.45 |
| BRATS_205 | FLAIR threshold | 0.6743 | 0.7361 | 63.86 |
| BRATS_205 | U-Net | 0.8273 | 0.7658 | 12.23 |
| BRATS_205 | U-Net + cleanup | 0.8290 | 0.7657 | 11.66 |
| BRATS_205 | U-Net + SAM | 0.8066 | 0.8849 | 44.17 |
| BRATS_208 | FLAIR threshold | 0.7192 | 0.7573 | 23.27 |
| BRATS_208 | U-Net | 0.8973 | 0.8408 | 2.21 |
| BRATS_208 | U-Net + cleanup | 0.8972 | 0.8403 | 2.19 |
| BRATS_208 | U-Net + SAM | 0.8406 | 0.9218 | 18.12 |
| BRATS_210 | FLAIR threshold | 0.6894 | 0.7585 | 42.24 |
| BRATS_210 | U-Net | 0.8561 | 0.8367 | 11.27 |
| BRATS_210 | U-Net + cleanup | 0.8560 | 0.8356 | 11.15 |
| BRATS_210 | U-Net + SAM | 0.7956 | 0.8912 | 33.36 |
| BRATS_237 | FLAIR threshold | 0.7985 | 0.6759 | 2.07 |
| BRATS_237 | U-Net | 0.9370 | 0.9183 | 5.12 |
| BRATS_237 | U-Net + cleanup | 0.9371 | 0.9175 | 5.00 |
| BRATS_237 | U-Net + SAM | 0.8973 | 0.9201 | 16.03 |
| BRATS_247 | FLAIR threshold | 0.7121 | 0.5718 | 2.53 |
| BRATS_247 | U-Net | 0.8241 | 0.7073 | 0.68 |
| BRATS_247 | U-Net + cleanup | 0.8232 | 0.7058 | 0.66 |
| BRATS_247 | U-Net + SAM | 0.7972 | 0.6840 | 2.38 |
| BRATS_271 | FLAIR threshold | 0.8185 | 0.7666 | 20.79 |
| BRATS_271 | U-Net | 0.8809 | 0.9191 | 32.69 |
| BRATS_271 | U-Net + cleanup | 0.8806 | 0.9161 | 32.07 |
| BRATS_271 | U-Net + SAM | 0.7492 | 0.9473 | 113.38 |
| BRATS_280 | FLAIR threshold | 0.8351 | 0.8029 | 23.83 |
| BRATS_280 | U-Net | 0.8697 | 0.8464 | 19.85 |
| BRATS_280 | U-Net + cleanup | 0.8698 | 0.8460 | 19.73 |
| BRATS_280 | U-Net + SAM | 0.8329 | 0.9488 | 65.47 |
| BRATS_286 | FLAIR threshold | 0.5453 | 0.8738 | 196.74 |
| BRATS_286 | U-Net | 0.8449 | 0.7732 | 8.41 |
| BRATS_286 | U-Net + cleanup | 0.8450 | 0.7731 | 8.39 |
| BRATS_286 | U-Net + SAM | 0.8872 | 0.8719 | 13.85 |
| BRATS_289 | FLAIR threshold | 0.4882 | 0.7762 | 116.14 |
| BRATS_289 | U-Net | 0.7538 | 0.7231 | 16.17 |
| BRATS_289 | U-Net + cleanup | 0.7556 | 0.7227 | 15.74 |
| BRATS_289 | U-Net + SAM | 0.7319 | 0.7990 | 31.81 |
| BRATS_291 | FLAIR threshold | 0.3222 | 0.8837 | 363.31 |
| BRATS_291 | U-Net | 0.5425 | 0.4797 | 29.13 |
| BRATS_291 | U-Net + cleanup | 0.5436 | 0.4787 | 28.48 |
| BRATS_291 | U-Net + SAM | 0.5107 | 0.5674 | 66.07 |
| BRATS_298 | FLAIR threshold | 0.7381 | 0.5964 | 2.03 |
| BRATS_298 | U-Net | 0.9014 | 0.9200 | 12.56 |
| BRATS_298 | U-Net + cleanup | 0.9014 | 0.9196 | 12.51 |
| BRATS_298 | U-Net + SAM | 0.8959 | 0.9554 | 18.37 |
| BRATS_301 | FLAIR threshold | 0.7102 | 0.7459 | 14.11 |
| BRATS_301 | U-Net | 0.8812 | 0.9279 | 7.08 |
| BRATS_301 | U-Net + cleanup | 0.8811 | 0.9268 | 7.04 |
| BRATS_301 | U-Net + SAM | 0.7711 | 0.9040 | 17.52 |
| BRATS_302 | FLAIR threshold | 0.1727 | 0.9876 | 316.13 |
| BRATS_302 | U-Net | 0.6667 | 0.7701 | 18.06 |
| BRATS_302 | U-Net + cleanup | 0.6733 | 0.7701 | 17.30 |
| BRATS_302 | U-Net + SAM | 0.6164 | 0.8052 | 27.01 |
| BRATS_320 | FLAIR threshold | 0.6038 | 0.4373 | 2.03 |
| BRATS_320 | U-Net | 0.9083 | 0.8893 | 12.44 |
| BRATS_320 | U-Net + cleanup | 0.9076 | 0.8879 | 12.42 |
| BRATS_320 | U-Net + SAM | 0.8687 | 0.9236 | 36.62 |
| BRATS_323 | FLAIR threshold | 0.7899 | 0.7361 | 7.96 |
| BRATS_323 | U-Net | 0.8891 | 0.9061 | 8.24 |
| BRATS_323 | U-Net + cleanup | 0.8887 | 0.9051 | 8.22 |
| BRATS_323 | U-Net + SAM | 0.7867 | 0.8875 | 23.00 |
| BRATS_327 | FLAIR threshold | 0.8553 | 0.7588 | 1.89 |
| BRATS_327 | U-Net | 0.9140 | 0.9405 | 14.43 |
| BRATS_327 | U-Net + cleanup | 0.9141 | 0.9394 | 14.23 |
| BRATS_327 | U-Net + SAM | 0.8777 | 0.9624 | 28.29 |
| BRATS_329 | FLAIR threshold | 0.6439 | 0.5667 | 15.26 |
| BRATS_329 | U-Net | 0.8243 | 0.8038 | 11.54 |
| BRATS_329 | U-Net + cleanup | 0.8263 | 0.8022 | 10.98 |
| BRATS_329 | U-Net + SAM | 0.7402 | 0.8302 | 32.55 |
| BRATS_330 | FLAIR threshold | 0.4508 | 0.8023 | 26.05 |
| BRATS_330 | U-Net | 0.8105 | 0.9275 | 5.36 |
| BRATS_330 | U-Net + cleanup | 0.8170 | 0.9268 | 5.07 |
| BRATS_330 | U-Net + SAM | 0.7653 | 0.8443 | 5.37 |
| BRATS_334 | FLAIR threshold | 0.8214 | 0.7136 | 4.10 |
| BRATS_334 | U-Net | 0.9178 | 0.9234 | 15.22 |
| BRATS_334 | U-Net + cleanup | 0.9175 | 0.9228 | 15.21 |
| BRATS_334 | U-Net + SAM | 0.8490 | 0.9543 | 50.36 |
| BRATS_345 | FLAIR threshold | 0.8538 | 0.7820 | 6.05 |
| BRATS_345 | U-Net | 0.8720 | 0.9534 | 28.37 |
| BRATS_345 | U-Net + cleanup | 0.8725 | 0.9530 | 28.16 |
| BRATS_345 | U-Net + SAM | 0.7854 | 0.9400 | 55.14 |
| BRATS_349 | FLAIR threshold | 0.8828 | 0.8846 | 14.14 |
| BRATS_349 | U-Net | 0.8899 | 0.9609 | 23.53 |
| BRATS_349 | U-Net + cleanup | 0.8900 | 0.9609 | 23.50 |
| BRATS_349 | U-Net + SAM | 0.8722 | 0.9686 | 29.89 |
| BRATS_362 | FLAIR threshold | 0.8281 | 0.7889 | 7.36 |
| BRATS_362 | U-Net | 0.8969 | 0.9135 | 7.80 |
| BRATS_362 | U-Net + cleanup | 0.8982 | 0.9131 | 7.58 |
| BRATS_362 | U-Net + SAM | 0.8928 | 0.8801 | 5.78 |
| BRATS_370 | FLAIR threshold | 0.7572 | 0.6780 | 4.76 |
| BRATS_370 | U-Net | 0.8755 | 0.8813 | 5.57 |
| BRATS_370 | U-Net + cleanup | 0.8755 | 0.8812 | 5.57 |
| BRATS_370 | U-Net + SAM | 0.8201 | 0.8849 | 11.53 |
| BRATS_377 | FLAIR threshold | 0.8560 | 0.7790 | 3.02 |
| BRATS_377 | U-Net | 0.8948 | 0.9580 | 13.49 |
| BRATS_377 | U-Net + cleanup | 0.8949 | 0.9578 | 13.47 |
| BRATS_377 | U-Net + SAM | 0.8441 | 0.9411 | 21.27 |
| BRATS_382 | FLAIR threshold | 0.3000 | 0.6942 | 89.94 |
| BRATS_382 | U-Net | 0.8255 | 0.7851 | 3.58 |
| BRATS_382 | U-Net + cleanup | 0.8292 | 0.7843 | 3.29 |
| BRATS_382 | U-Net + SAM | 0.7812 | 0.7798 | 6.64 |
| BRATS_386 | FLAIR threshold | 0.2057 | 0.8776 | 533.78 |
| BRATS_386 | U-Net | 0.6545 | 0.5189 | 5.35 |
| BRATS_386 | U-Net + cleanup | 0.6490 | 0.5105 | 5.03 |
| BRATS_386 | U-Net + SAM | 0.6433 | 0.5889 | 19.41 |
| BRATS_409 | FLAIR threshold | 0.8411 | 0.7276 | 0.41 |
| BRATS_409 | U-Net | 0.9338 | 0.9811 | 19.21 |
| BRATS_409 | U-Net + cleanup | 0.9335 | 0.9805 | 19.17 |
| BRATS_409 | U-Net + SAM | 0.8713 | 0.9631 | 39.54 |
| BRATS_413 | FLAIR threshold | 0.1149 | 0.9147 | 435.92 |
| BRATS_413 | U-Net | 0.5965 | 0.7379 | 22.90 |
| BRATS_413 | U-Net + cleanup | 0.6009 | 0.7372 | 22.29 |
| BRATS_413 | U-Net + SAM | 0.6422 | 0.8729 | 26.30 |
| BRATS_414 | FLAIR threshold | 0.2907 | 0.1701 | 0.02 |
| BRATS_414 | U-Net | 0.5618 | 0.3911 | 0.17 |
| BRATS_414 | U-Net + cleanup | 0.5592 | 0.3885 | 0.17 |
| BRATS_414 | U-Net + SAM | 0.5519 | 0.3820 | 0.36 |
| BRATS_435 | FLAIR threshold | 0.2848 | 0.9139 | 399.35 |
| BRATS_435 | U-Net | 0.8802 | 0.8259 | 4.49 |
| BRATS_435 | U-Net + cleanup | 0.8802 | 0.8239 | 4.28 |
| BRATS_435 | U-Net + SAM | 0.8794 | 0.8471 | 7.05 |
| BRATS_437 | FLAIR threshold | 0.7571 | 0.6237 | 3.12 |
| BRATS_437 | U-Net | 0.8828 | 0.8817 | 15.04 |
| BRATS_437 | U-Net + cleanup | 0.8825 | 0.8801 | 14.87 |
| BRATS_437 | U-Net + SAM | 0.7704 | 0.9224 | 61.32 |
| BRATS_447 | FLAIR threshold | 0.6037 | 0.4336 | 0.31 |
| BRATS_447 | U-Net | 0.8868 | 0.8047 | 1.09 |
| BRATS_447 | U-Net + cleanup | 0.8861 | 0.8036 | 1.09 |
| BRATS_447 | U-Net + SAM | 0.8798 | 0.8338 | 6.61 |
| BRATS_459 | FLAIR threshold | 0.0510 | 0.9829 | 473.67 |
| BRATS_459 | U-Net | 0.5534 | 0.8349 | 15.31 |
| BRATS_459 | U-Net + cleanup | 0.5588 | 0.8335 | 14.89 |
| BRATS_459 | U-Net + SAM | 0.4896 | 0.7520 | 17.10 |
| BRATS_466 | FLAIR threshold | 0.0484 | 0.9550 | 628.08 |
| BRATS_466 | U-Net | 0.6314 | 0.4909 | 1.07 |
| BRATS_466 | U-Net + cleanup | 0.6338 | 0.4909 | 0.98 |
| BRATS_466 | U-Net + SAM | 0.6954 | 0.5951 | 1.95 |
| BRATS_478 | FLAIR threshold | 0.5362 | 0.9055 | 113.76 |
| BRATS_478 | U-Net | 0.8387 | 0.8167 | 10.11 |
| BRATS_478 | U-Net + cleanup | 0.8416 | 0.8163 | 9.54 |
| BRATS_478 | U-Net + SAM | 0.7541 | 0.8471 | 30.89 |

## Representative failures

Largest paired SAM declines relative to the cleaned U-Net:

- `BRATS_073`: cleaned Dice 0.8451, SAM Dice 0.6992; SAM recall 0.8245; SAM FP 58.68 mL. Relative to cleanup, recall changed +0.0243 and false-positive volume changed +48.41 mL.
- `BRATS_044`: cleaned Dice 0.8454, SAM Dice 0.7109; SAM recall 0.7437; SAM FP 14.04 mL. Relative to cleanup, recall changed -0.1636 and false-positive volume changed +4.41 mL.
- `BRATS_271`: cleaned Dice 0.8806, SAM Dice 0.7492; SAM recall 0.9473; SAM FP 113.38 mL. Relative to cleanup, recall changed +0.0311 and false-positive volume changed +81.31 mL.

## Conclusion

On this fixed held-out split, frozen SAM reduced mean patient Dice relative to the U-Net with identical candidate cleanup by 0.0365. The result applies to this FLAIR-only pipeline and dataset split.

## Compute and limitations

The SAM benchmark used 8 validation slices; mean 1.831 s/slice, median 0.828 s/slice, maximum observed device allocation 3980247040 bytes. The first call took 8.581 s. A steady all-slice projection was 2.69 hours. The held-out run invoked SAM on 4112 of 11160 slices and spent 1.18 hours in SAM refinement; per-patient times are in `metrics/results.json`.
Only FLAIR is used. This is a 2D model evaluated on a fixed patient split of one public dataset; the original unlabelled MSD test set has no labels for this evaluation. Box prompts are generated from U-Net predictions, so missed tumours cannot be recovered when a slice has no U-Net candidate. SAM was trained on natural images and was used frozen. Validation choices are limited to the documented grids. These findings do not establish clinical performance or external generalization.

## Reproduction

Run the commands in `README.md` in order. `configs/selection.json` locks validation choices. The held-out command was `python -m brain_tumor.evaluate test --data ../brain-tumor-data/Task01_BrainTumour --export-dir artifacts/predictions`. Machine-readable aggregate and patient metrics are committed in `metrics/results.json`; individual NIfTI predictions remain outside Git under `artifacts/`.
