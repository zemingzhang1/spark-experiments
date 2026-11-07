# Caching study-notes build

Regenerates `notes/Caching_Study_Notes.pdf` from `spark/4_caching.ipynb`.

- `content.py` — handwritten (Caveat) margin notes, the red-circle token map, SVG sketches
- `typed.py`  — the typed extra-notes pages and the landscape decision table
- `build.py`  — patches the notebook with placeholders, runs nbconvert, injects the notes,
  prints each part with headless Chrome and merges them with pypdf

```
.venv/Scripts/python.exe -m pip install --target scripts/pylibs pypdf   # only extra dep
.venv/Scripts/python.exe scripts/study_notes_caching/build.py
```

`build.py` expects `notes/caching_run/dag_before_after.png`, produced by
`scripts/caching_experiment.py` plus two Spark UI screenshots (SQL queries 1 and 4).
