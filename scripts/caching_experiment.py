"""
Caching experiment - evidence for spark/4_caching.ipynb.

Four parts:
  1. Faithful replay of the notebook (customers -> df_base -> df1 / df2) and a
     diff of the PHYSICAL PLAN with and without df_base.cache().
  2. A heavy, shuffle-bound base reused twice, so the saving shows up as
     wall-clock seconds and not just as a prettier plan.
  3. Every StorageLevel persisted in turn, with the bytes Spark actually puts
     in memory and on disk read back from the Spark UI REST API.
  4. cache() vs persist() - proof they are the same call.

Run:  .venv/Scripts/python.exe scripts/caching_experiment.py
Artefacts land in notes/caching_run/. The Spark UI is held open on
http://localhost:4040 for HOLD_SECONDS (default 900) so the DAGs can be
screenshotted.

Windows note: there is no winutils.exe / hadoop.dll on this machine, so Hadoop's
native directory listing (NativeIO$Windows.access0) blows up on a *directory*
path. Handing Spark the explicit list of part-files skips that code path - the
scan, the plans and the DAGs are identical.
"""
import glob
import json
import os
import sys
import time
import urllib.request

from pyspark.sql import SparkSession
from pyspark.storagelevel import StorageLevel
import pyspark.sql.functions as F

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = os.path.join(ROOT, "notes", "caching_run")
CUSTOMERS = os.path.join(ROOT, "data", "data_skew", "customers.parquet")
TRANSACTIONS = os.path.join(ROOT, "data", "data_skew", "transactions.parquet")
HOLD_SECONDS = int(os.environ.get("HOLD_SECONDS", "900"))

os.makedirs(OUT, exist_ok=True)
log_lines = []


def log(msg=""):
    print(msg, flush=True)
    log_lines.append(str(msg))


def flush_log():
    with open(os.path.join(OUT, "run_log.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(log_lines))


def parts(folder):
    """Explicit part-file list - see the Windows note in the docstring."""
    return sorted(glob.glob(os.path.join(folder, "*.parquet")))


def rest(path):
    url = "http://localhost:4040/api/v1" + path
    with urllib.request.urlopen(url, timeout=30) as r:
        return json.loads(r.read().decode("utf-8"))


spark = (
    SparkSession.builder
    .appName("caching_experiment")
    .config("spark.driver.memory", "6g")
    .config("spark.sql.files.maxPartitionBytes", "268435456")
    .config("spark.serializer", "org.apache.spark.serializer.KryoSerializer")
    .config("spark.sql.shuffle.partitions", "32")
    .config("spark.sql.adaptive.enabled", "false")   # keep the plans readable
    .config("spark.ui.enabled", "true")
    .master("local[*]")
    .getOrCreate()
)
sc = spark.sparkContext
sc.setLogLevel("ERROR")
app_id = sc.applicationId
log("Spark version : " + spark.version)
log("Spark UI      : http://localhost:4040")
log("Application   : " + app_id)
log("Cores         : " + str(sc.defaultParallelism))


def physical(df):
    return df._jdf.queryExecution().executedPlan().toString()


def timed(fn, label):
    t0 = time.time()
    out = fn()
    dt = time.time() - t0
    log("  %-34s %-12s wall=%7.2fs" % (label, out, dt))
    return dt


# =========================================================== PART 1 - PLANS ==
log("")
log("=" * 78)
log("PART 1 - THE NOTEBOOK, WITH AND WITHOUT cache()")
log("=" * 78)


def build_base():
    """Exactly df_base from the notebook: filter + CASE WHEN + select."""
    return (
        spark.read.parquet(*parts(CUSTOMERS))
        .filter(F.col("city") == "boston")
        .withColumn(
            "customer_group",
            F.when(F.col("age").between(20, 30), F.lit("young"))
             .when(F.col("age").between(31, 50), F.lit("mid"))
             .when(F.col("age") > 51, F.lit("old"))
             .otherwise(F.lit("kid")),
        )
        .select("cust_id", "name", "age", "gender", "birthday", "zip", "city",
                "customer_group")
    )


def children(base):
    df1 = (base
           .withColumn("test_column_1", F.lit("test_column_1"))
           .withColumn("birth_year", F.split("birthday", "/").getItem(2)))
    df2 = (base
           .withColumn("test_column_2", F.lit("test_column_2"))
           .withColumn("birth_month", F.split("birthday", "/").getItem(1)))
    return df1, df2


log("")
log("--- A: no cache ---")
base_a = build_base()
df1_a, df2_a = children(base_a)
base_a.show(5, False)
df1_a.count()
df2_a.count()
plan_a1, plan_a2 = physical(df1_a), physical(df2_a)
log(plan_a1)
log("")
log(plan_a2)

log("")
log("--- B: df_base.cache() ---")
base_b = build_base()
base_b.cache()
log("  storageLevel right after .cache(), before any action: %s"
    % base_b.storageLevel)
base_b.count()                      # the action that actually fills the cache
log("  storageLevel after the first action                 : %s"
    % base_b.storageLevel)
df1_b, df2_b = children(base_b)
df1_b.count()
df2_b.count()
plan_b1, plan_b2 = physical(df1_b), physical(df2_b)
log(plan_b1)
log("")
log(plan_b2)

log("")
log("--- plan diff, counted ---")
for tag, p1, p2 in [("NO CACHE", plan_a1, plan_a2), ("CACHED  ", plan_b1, plan_b2)]:
    log("  %s  Scan parquet       df1=%d df2=%d"
        % (tag, p1.count("Scan parquet"), p2.count("Scan parquet")))
    log("  %s  Filter (city)      df1=%d df2=%d"
        % (tag, p1.count("Filter "), p2.count("Filter ")))
    log("  %s  CASE WHEN rebuilt  df1=%d df2=%d"
        % (tag, p1.count("CASE WHEN"), p2.count("CASE WHEN")))
    log("  %s  InMemoryTableScan  df1=%d df2=%d"
        % (tag, p1.count("InMemoryTableScan"), p2.count("InMemoryTableScan")))
flush_log()

# ========================================================== PART 2 - TIMING ==
log("")
log("=" * 78)
log("PART 2 - A BASE EXPENSIVE ENOUGH TO FEEL (871 MB, one shuffle)")
log("=" * 78)

tx_paths = parts(TRANSACTIONS)
log("  transactions part-files: %d" % len(tx_paths))


def build_heavy():
    tx = spark.read.parquet(*tx_paths)
    cust = (spark.read.parquet(*parts(CUSTOMERS))
            .select("cust_id", F.col("city").alias("home_city")))
    return (
        tx
        .withColumn("amt", F.col("amt").cast("double"))
        .groupBy("cust_id", "expense_type")
        .agg(F.sum("amt").alias("total_amt"),
             F.count(F.lit(1)).alias("txn_count"))
        .join(F.broadcast(cust), "cust_id")
    )


def two_consumers(base):
    a = base.filter(F.col("expense_type") == "Groceries") \
            .agg(F.sum("total_amt")).collect()[0][0]
    b = base.groupBy("home_city").agg(F.sum("txn_count")).count()
    return round(a or 0, 2), b


log("")
log("--- A: no cache (the groupBy shuffle runs twice) ---")
heavy_a = build_heavy()
t_nocache = timed(lambda: two_consumers(heavy_a), "two consumers, no cache")

log("")
log("--- B: base.cache() (the groupBy shuffle runs once) ---")
heavy_b = build_heavy()
heavy_b.cache()
t_fill = timed(lambda: heavy_b.count(), "fill the cache (first action)")
t_cached = timed(lambda: two_consumers(heavy_b), "two consumers, cached")

try:
    rdds = rest("/applications/%s/storage/rdd" % app_id)
    cached_bytes = rdds[-1].get("memoryUsed", 0) if rdds else 0
    cached_parts = rdds[-1].get("numPartitions", 0) if rdds else 0
except Exception as e:                                       # noqa: BLE001
    cached_bytes, cached_parts = 0, 0
    log("  (REST read failed: %s)" % e)

log("")
log("--- verdict ---")
log("  no cache                        : %7.2fs" % t_nocache)
log("  cache fill + two consumers      : %7.2fs  (%.2f + %.2f)"
    % (t_fill + t_cached, t_fill, t_cached))
log("  second-and-later reads          : %7.2fs vs %7.2fs uncached"
    % (t_cached, t_nocache))
if t_cached > 0:
    log("  speed-up on the reuse           : %.1fx" % (t_nocache / t_cached))
log("  cached base in memory           : %s bytes across %s partitions"
    % ("{:,}".format(cached_bytes), cached_parts))
heavy_b.unpersist(blocking=True)
flush_log()

# =================================================== PART 3 - STORAGE LEVELS =
log("")
log("=" * 78)
log("PART 3 - WHAT EACH StorageLevel ACTUALLY COSTS")
log("=" * 78)
log("  (same DataFrame every time: the customers parquet, 5,000 rows)")
log("")

base_b.unpersist(blocking=True)
wide = spark.read.parquet(*parts(CUSTOMERS))

levels = [
    ("MEMORY_AND_DISK_DESER  <- .cache() default", StorageLevel.MEMORY_AND_DISK_DESER),
    ("MEMORY_ONLY", StorageLevel.MEMORY_ONLY),
    ("MEMORY_ONLY_2", StorageLevel.MEMORY_ONLY_2),
    ("MEMORY_AND_DISK", StorageLevel.MEMORY_AND_DISK),
    ("DISK_ONLY", StorageLevel.DISK_ONLY),
    ("DISK_ONLY_3", StorageLevel.DISK_ONLY_3),
]

storage_rows = []
log("  %-44s %12s %12s  %s" % ("level", "mem bytes", "disk bytes", "as the UI shows it"))
for name, level in levels:
    df = wide.select("*")          # fresh plan so Spark makes a fresh cache entry
    df.persist(level)
    df.count()
    time.sleep(1.5)
    row = {"level": name, "repr": str(level), "memory_bytes": 0,
           "disk_bytes": 0, "storageLevel": "", "partitions": 0}
    try:
        rdds = rest("/applications/%s/storage/rdd" % app_id)
        if rdds:
            r = rdds[-1]
            row["memory_bytes"] = r.get("memoryUsed", 0)
            row["disk_bytes"] = r.get("diskUsed", 0)
            row["storageLevel"] = r.get("storageLevel", "")
            row["partitions"] = r.get("numPartitions", 0)
    except Exception as e:                                   # noqa: BLE001
        log("  (REST storage read failed: %s)" % e)
    storage_rows.append(row)
    log("  %-44s %12s %12s  %s"
        % (name, "{:,}".format(row["memory_bytes"]),
           "{:,}".format(row["disk_bytes"]), row["storageLevel"]))
    df.unpersist(blocking=True)
    time.sleep(1.0)

with open(os.path.join(OUT, "storage_levels.json"), "w", encoding="utf-8") as f:
    json.dump(storage_rows, f, indent=2)
flush_log()

# ================================================ PART 4 - cache vs persist ==
log("")
log("=" * 78)
log("PART 4 - cache() vs persist()")
log("=" * 78)

d1 = wide.select("*")
d1.cache()
d1.count()
lvl_cache = str(d1.storageLevel)
d1.unpersist(blocking=True)

d2 = wide.select("*")
d2.persist()                        # persist() with no argument
d2.count()
lvl_persist_default = str(d2.storageLevel)
d2.unpersist(blocking=True)

d3 = wide.select("*")
d3.persist(StorageLevel.MEMORY_AND_DISK_DESER)
d3.count()
lvl_persist_explicit = str(d3.storageLevel)
d3.unpersist(blocking=True)

d4 = wide.select("*")
d4.persist(StorageLevel.DISK_ONLY)
d4.count()
lvl_persist_disk = str(d4.storageLevel)
log("  df.cache()                            -> " + lvl_cache)
log("  df.persist()                          -> " + lvl_persist_default)
log("  df.persist(MEMORY_AND_DISK_DESER)     -> " + lvl_persist_explicit)
log("  df.persist(DISK_ONLY)                 -> " + lvl_persist_disk)
log("  cache() == persist() == persist(MEMORY_AND_DISK_DESER)? %s"
    % (lvl_cache == lvl_persist_default == lvl_persist_explicit))
log("")
log("  re-persisting without unpersist first:")
try:
    d4.persist(StorageLevel.MEMORY_ONLY)
    log("    no error - level is now %s" % d4.storageLevel)
except Exception as e:                                       # noqa: BLE001
    log("    %s: %s" % (type(e).__name__, str(e).splitlines()[0]))
d4.unpersist(blocking=True)
log("  after unpersist()                     -> " + str(d4.storageLevel))

# ------------------------------------------------------------------ DUMPS ---
for fn, txt in [("plan_nocache_df1.txt", plan_a1), ("plan_nocache_df2.txt", plan_a2),
                ("plan_cached_df1.txt", plan_b1), ("plan_cached_df2.txt", plan_b2)]:
    with open(os.path.join(OUT, fn), "w", encoding="utf-8") as f:
        f.write(txt)

try:
    sql_nodes = rest("/applications/%s/sql?details=true&length=300" % app_id)
    with open(os.path.join(OUT, "sql_queries.json"), "w", encoding="utf-8") as f:
        json.dump(sql_nodes, f, indent=2)
    log("")
    log("--- SQL tab, for the screenshots ---")
    for q in sql_nodes:
        log("  id=%-4s %-46s %sms"
            % (q.get("id"), str(q.get("description"))[:44], q.get("duration", 0)))
except Exception as e:                                       # noqa: BLE001
    log("SQL REST read failed: %s" % e)

log("")
log("Artefacts written to " + OUT)
log("Spark UI held open on http://localhost:4040 for %ds" % HOLD_SECONDS)
flush_log()

sys.stdout.flush()
time.sleep(HOLD_SECONDS)
spark.stop()
