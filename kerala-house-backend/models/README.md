# models/

Place your trained scikit-learn model file here:

    models/house_model.pkl

The file is excluded from Git via `.gitignore`.
Upload it manually or mount it via a Cloud Storage volume before deploying.

## Acceptable formats

| Format | How the predictor loads it |
|--------|---------------------------|
| Direct sklearn pipeline | `joblib.load()` → used as-is |
| Dict with `"model"` key | `joblib.load()["model"]` is extracted |

## Updating the model path

Set the `MODEL_PATH` environment variable to override the default path:

```
MODEL_PATH=models/my_custom_model.pkl
```
