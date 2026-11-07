# -*- coding: utf-8 -*-
"""Typed extra-notes pages for Caching_Study_Notes.pdf."""


def typed_body(dag_b64):
    return _TYPED.replace("@@DAG@@", dag_b64)


_TYPED = u"""
<h1>Caching &#8212; extra notes</h1>
<div class="lead">Measured on this machine: Spark 4.3.0, Java 17, <code>local[12]</code>,
driver 6 GB, AQE off, <code>spark/4_caching.ipynb</code> replayed by
<code>scripts/caching_experiment.py</code>. Raw output in
<code>notes/caching_run/</code>.</div>

<div class="sec flow">
<h2>1 &#183; Before and after, in the SQL tab</h2>
<p>Same two <code>count()</code> actions on <code>df1</code> and <code>df2</code>. The only
difference between the runs is one call to <code>df_base.cache()</code>.</p>
<div class="fig"><img src="data:image/png;base64,@@DAG@@" style="width:68%;display:block;margin:0 auto"/></div>
<table>
<tr><th>Spark UI metric</th><th>no cache (query 1 / 2)</th><th>cached (query 4 / 5)</th></tr>
<tr><td><code>Scan parquet</code> &#8594; number of output rows</td><td>5,000</td>
    <td class="hl">0</td></tr>
<tr><td><code>Scan parquet</code> &#8594; number of files read</td><td>1</td>
    <td class="hl">0</td></tr>
<tr><td><code>Scan parquet</code> &#8594; size of files read</td><td>149.9 KiB</td>
    <td class="hl">0</td></tr>
<tr><td><code>Filter</code> &#8594; number of output rows</td><td>517</td><td>0</td></tr>
<tr><td><code>InMemoryTableScan</code> &#8594; number of output rows</td><td>&#8212;</td>
    <td class="hl">517</td></tr>
<tr><td>query duration</td><td>333 ms, 72 ms</td><td>48 ms, 38 ms</td></tr>
</table>
<p>The <code>Scan parquet</code> node is <b>still in the cached plan</b> &#8212; it is the
recipe hanging under <code>InMemoryRelation</code>. It reports zero because it was not
executed.</p>
<h3>Physical plan, side by side (trimmed)</h3>
<div class="cols">
<div><pre><span class="hl">no cache &#8212; the file is read again</span>
*(1) Project [... customer_group#8,
       test_column_1, birth_year#10]
+- *(1) Filter (city#6 = boston)
   +- *(1) ColumnarToRow
      +- FileScan parquet [...]
         PushedFilters: [EqualTo(city,boston)]</pre></div>
<div><pre><span class="hl">cached &#8212; the file is only the recipe</span>
*(1) Project [... customer_group#74,
       test_column_1, birth_year#328]
+- InMemoryTableScan [...]
   +- InMemoryRelation [...],
      StorageLevel(disk, memory,
                   deserialized, 1 replicas)
      +- *(1) Project [CASE WHEN ...]
         +- *(1) Filter (city#72 = boston)
            +- FileScan parquet [...]</pre></div>
</div>
<h3>And when the base is genuinely expensive</h3>
<p>The customers file is 150 KiB &#8212; too small to feel. Repeated on the 871 MB
<code>transactions.parquet</code>, grouped by <code>(cust_id, expense_type)</code>
(one real shuffle) and consumed twice:</p>
<table>
<tr><th></th><th>no cache</th><th>cached</th></tr>
<tr><td>fill the cache (first action)</td><td>&#8212;</td><td>1.70 s</td></tr>
<tr><td>two consumers of the base</td><td>3.19 s</td><td class="hl">0.51 s</td></tr>
<tr><td>total, this run</td><td>3.19 s</td><td>2.21 s</td></tr>
<tr><td>cost of each <i>further</i> reuse</td><td>~1.6 s</td><td class="hl">~0.25 s</td></tr>
</table>
<p>Cached base: 869,976 bytes across 32 partitions. The speed-up on the reuse is
<b>6.2&#215;</b>; the speed-up on the <i>whole job</i> is only 1.4&#215;, because the first
pass still has to happen. That gap is the whole economics of caching.</p>
<div class="one"><b>One-liner:</b> caching does not make the first pass faster. It makes
every pass after the first one nearly free.</div>
</div>

<div class="sec newpage">
<h2>2 &#183; <code>cache()</code> vs <code>persist()</code></h2>
<div class="rule">There is only one mechanism. <code>cache()</code> is
<code>persist()</code> with the default storage level.
<small>In the Spark source, <code>def cache() = persist()</code>. Nothing else differs:
same lazy marking, same <code>InMemoryRelation</code>, same block manager, same
<code>unpersist()</code>.</small></div>
<h3>Measured here</h3>
<pre>df.cache()                        -> Disk Memory Deserialized 1x Replicated
df.persist()                      -> Disk Memory Deserialized 1x Replicated
df.persist(MEMORY_AND_DISK_DESER) -> Disk Memory Deserialized 1x Replicated
df.persist(DISK_ONLY)             -> Disk Serialized 1x Replicated
cache() == persist() == persist(MEMORY_AND_DISK_DESER)?  True</pre>
<h3>The default is not the same for RDDs and DataFrames</h3>
<table>
<tr><th>API</th><th><code>cache()</code> / <code>persist()</code> default</th><th>why</th></tr>
<tr><td>RDD</td><td><code>MEMORY_ONLY</code></td><td>an RDD is opaque JVM objects; Spark
cannot compress what it cannot describe, and dropping a partition is cheap.</td></tr>
<tr><td>DataFrame / Dataset / SQL <code>CACHE TABLE</code></td>
<td><code>MEMORY_AND_DISK_DESER</code></td><td>Spark SQL knows the schema, so it stores a
compressed columnar block and can spill it to disk rather than throw away work the
optimizer already paid for.</td></tr>
</table>
<div class="warn"><b>Interview trap.</b> &#8220;What is the default storage level of
<code>cache()</code>?&#8221; is only answerable once you ask <i>on what</i>. Saying
<code>MEMORY_ONLY</code> for a DataFrame is the single most common wrong answer.</div>
<h3>So when do you use which</h3>
<table>
<tr><th>use</th><th>when</th></tr>
<tr><td><code>cache()</code></td><td>the default is fine &#8212; which is most of the time.
Shorter to read, and it is what the next person expects.</td></tr>
<tr><td><code>persist(level)</code></td><td>you have a reason to deviate: memory is tight
(<code>MEMORY_AND_DISK_SER</code>), the block must never be recomputed because it came from
a non-deterministic source (<code>DISK_ONLY</code>), or executors die often enough that
re-running the lineage hurts (<code>_2</code>).</td></tr>
</table>
<div class="say">&#8220;They are the same call &#8212; <code>cache()</code> is
<code>persist()</code> with no argument. I reach for <code>persist</code> only when I want
a non-default storage level: serialized when the cache is too big for memory, disk-only
when recomputing is expensive or non-deterministic, replicated when I am losing executors.
The one thing worth remembering is that the default differs by API: <code>MEMORY_ONLY</code>
for RDDs, <code>MEMORY_AND_DISK_DESER</code> for DataFrames.&#8221;</div>
<div class="one"><b>One-liner:</b> <code>cache()</code> is the convenience name;
<code>persist()</code> is the steering wheel.</div>
</div>

<div class="sec newpage">
<h2>3 &#183; The storage-level chart, row by row</h2>
<pre>Storage Level        Space used  CPU time  In memory  On-disk  Serialized
MEMORY_ONLY              High        Low       Y          N        N
MEMORY_ONLY_SER          Low         High      Y          N        Y
MEMORY_AND_DISK          High        Medium    Some       Some     Some
MEMORY_AND_DISK_SER      Low         High      Some       Some     Y
DISK_ONLY                Low         High      N          Y        Y</pre>
<p>Every cell in that table falls out of two facts:</p>
<ol>
<li><b>Serialized bytes are small and slow; deserialized JVM objects are big and fast.</b>
A JVM object carries a header, pointers and padding &#8212; typically 2&#8211;5&#215; the
size of the same data packed into a byte array. Serialized form has to be decoded on every
read, which is CPU.</li>
<li><b>Memory is fast but finite; disk is slow but kept.</b> A block that will not fit in
memory is either dropped (and recomputed later) or spilled.</li>
</ol>
<table>
<tr><th>row</th><th>why Space</th><th>why CPU</th><th>why the Y/N columns</th></tr>
<tr><td><code>MEMORY_ONLY</code></td><td><b>High</b> &#8212; JVM objects, no packing</td>
<td><b>Low</b> &#8212; nothing to decode, read straight out</td>
<td>memory Y / disk N / ser N. Blocks that don't fit are dropped and <i>recomputed on
demand</i> &#8212; no error, just a slow query later.</td></tr>
<tr><td><code>MEMORY_ONLY_SER</code></td><td><b>Low</b> &#8212; packed byte arrays</td>
<td><b>High</b> &#8212; deserialise on every single read</td>
<td>same memory-only eviction behaviour, just more of your data fits.</td></tr>
<tr><td><code>MEMORY_AND_DISK</code></td><td><b>High</b> &#8212; the in-memory part is
still deserialized objects</td><td><b>Medium</b> &#8212; RAM hits cost nothing, spilled
blocks cost a disk read <i>and</i> a deserialise</td><td>&#8220;Some&#8221; everywhere
because it is a mix: Spark keeps what fits in memory deserialized and writes the overflow
to disk serialized.</td></tr>
<tr><td><code>MEMORY_AND_DISK_SER</code></td><td><b>Low</b></td><td><b>High</b></td>
<td>same split, but compact, so far <i>fewer</i> blocks ever reach the disk. Usually the
best choice when a big cache does not fit.</td></tr>
<tr><td><code>DISK_ONLY</code></td><td><b>Low</b> &#8212; on disk, always serialized</td>
<td><b>High</b> &#8212; disk I/O plus deserialise, every read</td>
<td>memory N / disk Y / ser Y. Nothing can be evicted, so the block is guaranteed to be
there. Pay for that guarantee in latency.</td></tr>
</table>
<h3>The same thing, measured (customers.parquet, 5,000 rows)</h3>
<table>
<tr><th>level requested</th><th>in memory</th><th>on disk</th><th>how the UI labels it</th></tr>
<tr><td><code>MEMORY_AND_DISK_DESER</code> (<code>cache()</code>)</td><td>297,224 B</td>
<td>0</td><td>Disk Memory Deserialized 1x Replicated</td></tr>
<tr><td><code>MEMORY_ONLY</code></td><td>168,815 B</td><td>0</td>
<td>Memory <b>Serialized</b> 1x Replicated</td></tr>
<tr><td><code>MEMORY_ONLY_2</code></td><td>168,815 B</td><td>0</td>
<td>Memory Serialized <b>2x</b> Replicated</td></tr>
<tr><td><code>MEMORY_AND_DISK</code></td><td>168,815 B</td><td>0</td>
<td>Disk Memory Serialized 1x Replicated</td></tr>
<tr><td><code>DISK_ONLY</code></td><td>0</td><td>168,815 B</td>
<td>Disk Serialized 1x Replicated</td></tr>
<tr><td><code>DISK_ONLY_3</code></td><td>0</td><td>168,815 B</td>
<td>Disk Serialized <b>3x</b> Replicated</td></tr>
</table>
<p>Two things to read off that table. <b>297 KB vs 169 KB</b> is the deserialized/serialized
tax, exactly the &#8220;Space used High vs Low&#8221; column. And <code>MEMORY_AND_DISK</code>
shows <b>0 bytes on disk</b> &#8212; not a bug: memory was big enough, so nothing spilled.
Disk in the name is a fallback, not a destination.</p>
<div class="warn"><b>Two caveats on the chart.</b> (a) It is the <b>RDD</b> table. Spark SQL
always caches a compressed columnar block, so <code>MEMORY_ONLY</code> on a DataFrame still
reports &#8220;Serialized&#8221;; the only deserialized DataFrame level is
<code>MEMORY_AND_DISK_DESER</code>. (b) <code>_2</code> / <code>_3</code> replication did
nothing measurable above because <code>local[*]</code> has a single executor &#8212; you
only get real replicas on a real cluster.</div>
<div class="one"><b>One-liner:</b> start at <code>cache()</code>; move to
<code>MEMORY_AND_DISK_SER</code> when it does not fit; move to <code>DISK_ONLY</code> only
when recomputing is worse than reading from disk.</div>
</div>

<div class="sec newpage">
<h2>4 &#183; Lazy evaluation &#8212; why the base is built twice</h2>
<p>Transformations build a DAG and return immediately. Nothing runs until an action
(<code>show</code>, <code>count</code>, <code>collect</code>, <code>write</code>) asks for
rows. At that moment Spark walks the <b>whole</b> lineage from the source and executes it.</p>
<p>A DataFrame is a <i>recipe</i>, not a <i>result</i>. <code>df_base</code> is not
&#8220;a table of 517 Boston customers sitting somewhere&#8221;; it is the sentence
&#8220;read this parquet, keep city = boston, add customer_group&#8221;. Assigning it to a
variable and using it twice reuses the sentence, not the table &#8212; so the sentence is
executed twice.</p>
<pre>df_base = read &#8594; filter(city = boston) &#8594; CASE WHEN customer_group

df1 = df_base &#8594; test_column_1 &#8594; birth_year  &#8594; .show()   # replays all of df_base
df2 = df_base &#8594; test_column_2 &#8594; birth_month &#8594; .show()   # replays all of df_base again</pre>
<p><code>cache()</code> is how you turn the recipe into a result. After the first action the
<code>InMemoryRelation</code> holds real rows, and every DataFrame built on
<code>df_base</code> starts from those rows.</p>
<h3>The job that appears before you call any action</h3>
<p>From the video, and worth knowing: <code>spark.read.parquet(...)</code> shows up as a job
in the UI even though reading is not an action. That job is schema inference &#8212; Spark
opens the footer to learn the columns and types. Its <b>input size is 0</b>, which is how
you recognise it. (With a schema supplied by hand, or for a table in a metastore, it does
not appear at all.)</p>
<div class="one"><b>One-liner:</b> an action replays the entire lineage; a cache is the
only thing that shortens it.</div>
</div>

<div class="sec">
<h2>5 &#183; When <i>not</i> to cache, and what bites people</h2>
<table>
<tr><th>situation</th><th>what to do</th></tr>
<tr><td>The DataFrame is read once</td><td>Don't cache. You pay the write and the memory
for nothing.</td></tr>
<tr><td>The base is a plain scan with a pushed-down filter</td><td>Usually don't. Re-reading
columnar parquet with a pushed predicate can be cheaper than materialising a cache.</td></tr>
<tr><td>The base is wide and you only use three columns downstream</td><td>
<code>select()</code> first, <i>then</i> cache. Caching before projecting stores columns
nobody reads.</td></tr>
<tr><td>The expensive part is a shuffle you do once</td><td>Spark already keeps shuffle
files; a cache on top of a single shuffle often adds little.</td></tr>
<tr><td>The reuse spans several jobs or a loop (ML, iterative joins)</td><td>Cache &#8212;
this is the case the feature exists for.</td></tr>
</table>
<div class="warn"><b>Gotchas, in the order they catch people</b>
<ol>
<li><code>cache()</code> is lazy. <code>df.cache()</code> alone does nothing; the next
action fills it. <code>df.count()</code> is the usual way to force it.</li>
<li><code>show(5)</code> materialises only the partitions it touched, so the cache can be
<i>partially</i> filled and the Storage tab shows &#8220;50% cached&#8221;.</li>
<li><code>persist(other_level)</code> on an already-cached DataFrame is a <b>silent
no-op</b> &#8212; no error, no change. Call <code>unpersist()</code> first.</li>
<li>Caching a DataFrame does not cache the ones you built from it; each has its own
identity.</li>
<li><code>MEMORY_ONLY</code> blocks that do not fit are dropped silently and recomputed.
The symptom is a query that is mysteriously slow, not an error.</li>
<li>Cache competes with execution memory for the same unified pool. An over-eager cache
can push shuffles and joins into spilling.</li>
<li>Never cached forever: <code>unpersist()</code> once the reuse is over, especially in
notebooks and long-running apps.</li>
</ol></div>
<div class="one"><b>One-liner:</b> cache is a bet that recomputation costs more than memory
&#8212; check the bet in the Storage tab, not in your head.</div>
</div>

<div class="sec newpage">
<h2>6 &#183; Interview answers</h2>
<h3>&#8220;What does <code>cache()</code> do, and when would you use it?&#8221;</h3>
<div class="say">&#8220;Spark is lazy, so every action replays the whole lineage. If one
DataFrame feeds several downstream DataFrames, that lineage runs once per action.
<code>cache()</code> marks the DataFrame so that after the first action its rows are stored
in the block manager as an <code>InMemoryRelation</code>; everything downstream then reads
<code>InMemoryTableScan</code> instead of re-scanning the source. I use it when a
non-trivial intermediate &#8212; typically something that cost a shuffle &#8212; is read two
or more times.&#8221;</div>
<h3>&#8220;How do you <i>prove</i> the cache is working?&#8221;</h3>
<div class="say">&#8220;Three places. The physical plan gains an
<code>InMemoryTableScan</code> over an <code>InMemoryRelation</code>. In the SQL tab the
<code>Scan parquet</code> node drops to 0 rows and 0 bytes &#8212; it is still drawn, because
it is the recipe for rebuilding, but it is not executed. And the Storage tab shows the RDD,
its storage level, how many partitions are cached and the bytes in memory and on disk.&#8221;
</div>
<h3>&#8220;Difference between <code>cache</code> and <code>persist</code>?&#8221;</h3>
<div class="say">&#8220;None, except the argument. <code>cache()</code> calls
<code>persist()</code> with the default level, which is <code>MEMORY_ONLY</code> for RDDs and
<code>MEMORY_AND_DISK_DESER</code> for DataFrames. <code>persist</code> lets me pick:
serialized to fit more in memory at a CPU cost, disk-only when the block must never be
recomputed, <code>_2</code> for a replica when executor loss is a real risk.&#8221;</div>
<h3>&#8220;Your cached DataFrame does not fit in memory. What happens?&#8221;</h3>
<div class="say">&#8220;It depends on the level. With <code>MEMORY_ONLY</code> the blocks
that do not fit are simply not stored, and are recomputed from the lineage next time they are
needed &#8212; silently. With a <code>MEMORY_AND_DISK</code> level the overflow spills to the
executor's local disk instead. That is why <code>MEMORY_AND_DISK_SER</code> is the usual
answer for a cache that is too big: the compact form means less of it ever reaches disk.&#8221;
</div>
<h3>Quick-fire</h3>
<table>
<tr><th>question</th><th>answer</th></tr>
<tr><td>Is <code>cache()</code> an action?</td><td>No. It is lazy. The next action fills it.</td></tr>
<tr><td>Is <code>unpersist()</code> lazy?</td><td>No, it is eager &#8212; blocks go immediately.</td></tr>
<tr><td>Default level of <code>spark.sql("CACHE TABLE t")</code>?</td>
<td><code>MEMORY_AND_DISK_DESER</code>, and that statement is <b>eager</b> unless you write
<code>CACHE LAZY TABLE</code>.</td></tr>
<tr><td>Does caching survive a <code>spark.stop()</code>?</td><td>No. It lives in the
executors' memory and local disk for the life of the application.</td></tr>
<tr><td>Cache vs checkpoint?</td><td>Cache keeps the lineage (it can rebuild). Checkpoint
writes to reliable storage and <i>truncates</i> the lineage &#8212; use it to break very long
DAGs, not for speed.</td></tr>
<tr><td>Cache vs broadcast?</td><td>Cache reuses a DataFrame across actions. Broadcast ships
a small table to every executor for a join. Different problems.</td></tr>
</table>
<div class="one"><b>Study next in this repo:</b> <code>5_0_partitioning.ipynb</code>,
<code>6_0_bucketing.ipynb</code>, then <code>1_data_skew/</code> &#8212; caching interacts
with all three, because the thing worth caching is usually the output of a shuffle.</div>
</div>
"""


_LAND = u"""
<h1>Storage levels &#8212; the decision table</h1>
<div class="lead">One shared example throughout: a DataFrame whose cached form is
<b>10 GB deserialized / 3 GB serialized</b>, on a cluster with <b>6 GB</b> of storage memory
per executor.</div>
<table class="land">
<tr><th>Level</th><th>Rule of thumb</th><th>On the 10 GB / 6 GB example</th><th>What ends up where</th></tr>

<tr><td><code>MEMORY_ONLY</code><br/><span class="chip">RDD default</span></td>
<td>Fastest reads, biggest footprint. Only when the cache <b>comfortably</b> fits.</td>
<td>6 GB of blocks are kept, 4 GB are <b>dropped</b>. Those partitions are recomputed from
the lineage on every read &#8212; no warning, just a slow query.</td>
<td>%(svg_memonly)s</td></tr>

<tr><td><code>MEMORY_AND_DISK_DESER</code><br/><span class="chip">cache() on a DataFrame</span></td>
<td>The sane default. Fast where it fits, spilled where it doesn't, never recomputed.</td>
<td>6 GB stay in memory, 4 GB go to the executor's local disk. Nothing is lost.</td>
<td>%(svg_memdisk)s</td></tr>

<tr><td><code>MEMORY_AND_DISK_SER</code></td>
<td>The one to switch to when the cache is too big. Trades CPU for a far better hit rate.</td>
<td>The whole 3 GB serialized form fits in 6 GB &#8212; <b>zero</b> disk, and 3 GB of memory
left for execution. Every read pays a deserialise.</td>
<td>%(svg_ser)s</td></tr>

<tr><td><code>DISK_ONLY</code></td>
<td>When memory is needed for execution, or the source is non-deterministic / very expensive
to re-read.</td>
<td>3 GB on local disk, 6 GB of memory free for shuffles and joins. Slowest reads, but the
block is guaranteed present.</td>
<td>%(svg_disk)s</td></tr>

<tr><td><code>*_2</code> / <code>*_3</code></td>
<td>Resilience only. Doubles or triples the cost; buys you not re-running the lineage when an
executor dies.</td>
<td>20 GB instead of 10 GB for <code>MEMORY_ONLY_2</code>. Worth it only for long jobs on
spot / preemptible instances.</td>
<td>%(svg_rep)s</td></tr>
</table>
<p class="foot">&#128161; Order to try things in: <code>cache()</code> &#8594; check the
Storage tab &#8594; if it is not 100% cached, <code>MEMORY_AND_DISK_SER</code> &#8594; if
memory is still the bottleneck, <code>DISK_ONLY</code> or stop caching and let the optimizer
re-read parquet.</p>
"""

_LAND_SVG = {
    "svg_memonly": """<svg width="260" height="54" viewBox="0 0 260 54">
<rect x="2" y="8" width="130" height="24" fill="none" stroke="#1f4fb5" stroke-width="2"/>
<text class="skt" x="8" y="25">memory 6 GB</text>
<rect x="136" y="8" width="88" height="24" fill="none" stroke="#d62828" stroke-width="2"
 stroke-dasharray="5 3"/><text class="skt" x="142" y="25" fill="#d62828">4 GB lost</text>
<text class="skt" x="2" y="48" fill="#d62828">recomputed on every read</text></svg>""",
    "svg_memdisk": """<svg width="260" height="54" viewBox="0 0 260 54">
<rect x="2" y="8" width="130" height="24" fill="none" stroke="#1f4fb5" stroke-width="2"/>
<text class="skt" x="8" y="25">memory 6 GB</text>
<rect x="136" y="8" width="88" height="24" fill="none" stroke="#2a9d5c" stroke-width="2"/>
<text class="skt" x="142" y="25" fill="#2a9d5c">disk 4 GB</text>
<text class="skt" x="2" y="48" fill="#2a9d5c">nothing recomputed</text></svg>""",
    "svg_ser": """<svg width="260" height="54" viewBox="0 0 260 54">
<rect x="2" y="8" width="78" height="24" fill="none" stroke="#1f4fb5" stroke-width="2"/>
<text class="skt" x="8" y="25">cache 3 GB</text>
<rect x="84" y="8" width="78" height="24" fill="none" stroke="#2a9d5c" stroke-width="2"
 stroke-dasharray="4 3"/><text class="skt" x="90" y="25" fill="#2a9d5c">3 GB free</text>
<text class="skt" x="2" y="48">+ CPU on every read</text></svg>""",
    "svg_disk": """<svg width="260" height="54" viewBox="0 0 260 54">
<rect x="2" y="8" width="104" height="24" fill="none" stroke="#2a9d5c" stroke-width="2"
 stroke-dasharray="4 3"/><text class="skt" x="8" y="25" fill="#2a9d5c">memory free</text>
<rect x="110" y="8" width="88" height="24" fill="none" stroke="#1f4fb5" stroke-width="2"/>
<text class="skt" x="116" y="25">disk 3 GB</text>
<text class="skt" x="2" y="48" fill="#d62828">slowest reads, never evicted</text></svg>""",
    "svg_rep": """<svg width="260" height="54" viewBox="0 0 260 54">
<rect x="2" y="6" width="100" height="18" fill="none" stroke="#1f4fb5" stroke-width="2"/>
<text class="skt" x="8" y="20">exec A 10 GB</text>
<rect x="110" y="6" width="100" height="18" fill="none" stroke="#1f4fb5" stroke-width="2"/>
<text class="skt" x="116" y="20">exec B 10 GB</text>
<text class="skt" x="2" y="44" fill="#d62828">same data twice = survives one loss</text></svg>""",
}

LANDSCAPE_BODY = _LAND
for _k, _v in _LAND_SVG.items():
    LANDSCAPE_BODY = LANDSCAPE_BODY.replace("%(" + _k + ")s", _v)
