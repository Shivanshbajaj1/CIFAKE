# Dataset run results

The supplied archive was extracted into `data/cifake/` with these balanced
class counts:

| Split | FAKE | REAL | Total |
|---|---:|---:|---:|
| Train | 50,000 | 50,000 | 100,000 |
| Test | 10,000 | 10,000 | 20,000 |

The CNN was trained for one full epoch as an end-to-end smoke run. Training
reserved 10,000 images from the training split for validation and used the
remaining 90,000 for fitting. Images are normalized to `[0, 1]` consistently
in training, evaluation, and app inference.

Held-out test results from `python evaluate.py`:

| Metric | Result |
|---|---:|
| Accuracy | 89.77% |
| Macro F1 | 89.77% |
| FAKE precision / recall | 91.79% / 87.35% |
| REAL precision / recall | 87.98% / 92.19% |

Confusion matrix (rows are actual labels, columns are predicted labels; class
order is FAKE, REAL):

```text
[[8735, 1265],
 [ 781, 9219]]
```

The saved `models/cifake_cnn.h5` is this one-epoch smoke-run checkpoint. The
normal training script defaults to 10 epochs with early stopping; set
`CIFAKE_EPOCHS=1` only to reproduce this quick run. More training may improve
or change these results.
