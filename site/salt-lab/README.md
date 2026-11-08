# Salt Lab

An interactive simulator for Spark data skew and the salting fix. Dial in a
skewed dataset, then watch the salt spread it across shuffle partitions.

**Live page:** https://me.zemingzhang.com/spark-salt-lab/

Companion to [`spark/1_data_skew/`](../../spark/1_data_skew/) — the notebooks
show the skew and the fix in Spark; this page lets you feel the shape of it.

## What it shows

- **Load per partition** — before and after salting, on a shared y-axis, so the
  collapse of the straggler is visible rather than re-scaled away.
- **Where the rows move** — a Sankey whose nodes are partitions and whose
  ribbons are rows travelling from their pre-salt partition to their post-salt
  one. Click a partition to isolate it, hover a ribbon to follow it.
- **How salting works** — a pan/zoom diagram of the salt → explode → join
  pipeline, with the notes beside it.

Everything is driven by five controls: dataset size (up to 5 billion rows),
distinct values, skew, partitions before and after salting, and the salt range.

## The hashing is real

Partitions are not approximated. The page implements Spark's own
`Murmur3_x86_32.hashUnsafeBytes` with seed 42, including Spark's non-standard
tail handling, and routes with `pmod(h, numPartitions)`. The implementation was
checked against `pyspark` 4.3 on 13 keys and matched all 13, so the partition
shown is the one Spark would pick.

Row counts are never materialised — every partition total is computed from the
key distribution — so 5 billion rows costs the same as a thousand.

## Where the pieces live

| path | what it is |
|---|---|
| `spark/1_data_skew/salting_simulator.html` | **the source.** Edited in the Claude artifact, committed here |
| `site/salt-lab/index.html` | generated page, wrapped in a real HTML document |
| `site/salt-lab/build.py` | regenerates `index.html`, and publishes it with `--push` |
| `site/salt-lab/.deploy/` | clone of `zemingzhang1/spark-salt-lab`, git-ignored |

`index.html` is generated — don't hand-edit it. The artifact source starts at
`<title>`, because the artifact platform supplies the doctype, charset, viewport
and a base reset at publish time. `build.py` adds those back, and pins the page
to dark, so it survives on a plain static host.

## Rebuilding and publishing

```
python site/salt-lab/build.py
```

```
python site/salt-lab/build.py --push
```

`--push` copies the generated page into `.deploy/` and pushes that clone to
`zemingzhang1/spark-salt-lab`, which is the repository GitHub Pages serves. It
never commits to this repository, it refuses to run if `.deploy/` points
anywhere other than the Pages repo, and it is a no-op when the page has not
changed. Pages takes a few minutes to rebuild afterwards.

Pushing needs the `zemingzhang1` account active in `gh` — that is held
per-shell, so run it from the PowerShell terminal where `gh auth status` lists
that account as active.

## Hosting

Static — no build step, no server. The custom domain `me.zemingzhang.com` is
configured on `zemingzhang1.github.io`; `spark-salt-lab` is a project page, so
it inherits the domain and is served from the `/spark-salt-lab/` path. React,
Plotly and the fonts load from public CDNs over HTTPS.
