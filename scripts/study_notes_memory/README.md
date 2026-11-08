# Memory-management study-notes build

Regenerates `notes/Memory_Management_Study_Notes.pdf`.

There is no notebook for this chapter, so the source material is the
[Spark Memory Management](https://youtu.be/sXL1qgrPysg) video plus the two
boards that already live in this repo:

- `docs/images/memory_management.png` — the executor memory layout
- `docs/images/unified_memory.png`    — the four unified-memory cases

Both are used as the base image, with a handwritten (Caveat) layer positioned
on top in percent coordinates measured off the source pixels.

- `boards.py` — the annotated boards: absolute annotations, red rings, and the
  cropped unified-memory panels with their notes
- `hand.py`   — the handwritten pages that are not a board (five pools, the
  worked calculation, the container sketch)
- `typed.py`  — the typed extra-notes pages: exact formula, off-heap in depth,
  allocate/deallocate in code, how GC decides, GC in practice, symptom tables,
  interview answers

```
.venv/Scripts/python.exe -m pip install --target scripts/pylibs pypdf
.venv/Scripts/python.exe scripts/study_notes_memory/build.py
```

Prints the three parts with headless Chrome (page 1 and page 3 landscape) and
merges them with pypdf. 10 pages.
