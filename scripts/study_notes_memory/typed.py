# -*- coding: utf-8 -*-
"""Typed extra-notes pages for the Spark Memory Management study notes.

Sections 3-5 answer the questions asked after the video: what off-heap memory
really is, what "you have to allocate and deallocate it yourself" means in
code, and how garbage collection decides what to collect.
"""

BODY = r"""
<h1>Spark Memory Management &mdash; extra notes</h1>
<div class="lead">Typed follow-ups to the annotated boards: the exact formula the
board rounds off, off-heap memory in depth, what allocate/deallocate means in
real code, and how the JVM garbage collector actually decides what to free.</div>

<!-- ================================================================ 1 -->
<div class="sec">
<h2>1 &middot; The exact formula (the board rounds, on purpose)</h2>

<p>The video does <code>0.6 &times; 10 GB = 6 GB</code>. Spark does not. Reserved
memory comes off <b>first</b>, and only what is left gets multiplied:</p>

<pre>// UnifiedMemoryManager.getMaxMemory
usableMemory  = systemMemory - reservedMemory          // reservedMemory = 300 MB, hard-coded
maxMemory     = usableMemory * spark.memory.fraction   // the unified pool
onHeapStorage = maxMemory    * spark.memory.storageFraction</pre>

<table>
<tr><th>pool</th><th>board (teaching)</th><th>actual, for a 10 GiB heap</th></tr>
<tr><td>heap (<code>-Xmx</code>)</td><td>10 GB</td><td>10240 MB</td></tr>
<tr><td>reserved</td><td>300 MB</td><td>300 MB</td></tr>
<tr><td>usable</td><td>&mdash;</td><td>10240 &minus; 300 = <b>9940 MB</b></td></tr>
<tr><td>unified</td><td>0.6 &times; 10 = 6 GB</td><td>0.6 &times; 9940 = <b>5964 MB</b> (&asymp; 5.8 GiB)</td></tr>
<tr><td>&nbsp;&nbsp;storage (start)</td><td>3 GB</td><td>0.5 &times; 5964 = <b>2982 MB</b></td></tr>
<tr><td>&nbsp;&nbsp;execution (start)</td><td>3 GB</td><td><b>2982 MB</b></td></tr>
<tr><td>user</td><td>4 GB &minus; 300 MB = 3.7 GB</td><td>9940 &minus; 5964 = <b>3976 MB</b></td></tr>
</table>

<div class="warn"><b>Two things the simplified version hides.</b>
(a) Reserved is subtracted before the fraction, so you always get slightly
<i>less</i> unified memory than <code>0.6 &times; heap</code>.
(b) <code>Runtime.getRuntime.maxMemory</code> is itself a little below
<code>-Xmx</code> (one survivor space is never usable), so the real pool is
smaller again. Never size a job to the last hundred MB.</div>

<div class="one"><b>One-liner:</b> the board's arithmetic is right to within ~1%;
use it in an interview, but know that reserved comes off the top first.</div>
</div>

<!-- ================================================================ 2 -->
<div class="sec">
<h2>2 &middot; Every knob, with its default</h2>
<table>
<tr><th>property</th><th>default</th><th>what it controls</th></tr>
<tr><td><code>spark.executor.memory</code></td><td>1g</td>
    <td>the JVM heap (<code>-Xmx</code>) of each executor &mdash; and nothing
        outside it</td></tr>
<tr><td><code>spark.memory.fraction</code></td><td>0.6</td>
    <td>share of <i>(heap &minus; 300 MB)</i> given to the unified pool. Lower it
        only if your own objects (user memory) are being squeezed.</td></tr>
<tr><td><code>spark.memory.storageFraction</code></td><td>0.5</td>
    <td>where the execution/storage divider <b>starts</b>. It is also the
        floor: storage below this line cannot be evicted by execution.</td></tr>
<tr><td><i>reserved</i></td><td>300 MB</td>
    <td>hard-coded in <code>UnifiedMemoryManager</code>; no property exposes
        it</td></tr>
<tr><td><code>spark.executor.memoryOverhead</code></td>
    <td><code>max(384 MB, factor &times; executor.memory)</code></td>
    <td>everything in the process that is not the heap: metaspace, thread
        stacks, netty buffers, <b>Python workers</b>. Added on top of the
        heap when the container is requested.</td></tr>
<tr><td><code>spark.executor.memoryOverheadFactor</code></td><td>0.10</td>
    <td>the factor above (Spark 3.3+). Non-JVM applications on Kubernetes
        default to 0.40 instead, because PySpark lives here.</td></tr>
<tr><td><code>spark.memory.offHeap.enabled</code></td><td>false</td>
    <td>switch; on its own it does nothing</td></tr>
<tr><td><code>spark.memory.offHeap.size</code></td><td>0</td>
    <td>the actual pool. <b>0 means off even when enabled is true.</b></td></tr>
<tr><td><code>spark.executor.pyspark.memory</code></td><td>unset</td>
    <td>caps each Python worker. Unset means bounded only by the container
        &mdash; the usual cause of a killed PySpark executor.</td></tr>
<tr><td><code>spark.executor.cores</code></td><td>1 / all, by manager</td>
    <td>how many tasks share one executor's execution memory at once. This is
        the hidden divisor on every number above.</td></tr>
</table>
<div class="one"><b>One-liner:</b> only two of these are carved out of
<code>executor.memory</code> (<code>fraction</code> and
<code>storageFraction</code>); <code>memoryOverhead</code> and
<code>offHeap.size</code> are added on top of it.</div>
</div>

<!-- ================================================================ 3 -->
<div class="sec newpage">
<h2>3 &middot; Off-heap memory, properly</h2>

<h3>What "heap" even means</h3>
<p>The <b>heap</b> is the single block of memory the JVM reserves at startup
(<code>-Xmx</code>) and then hands out itself. Every <code>new</code> in Java
or Scala carves a piece out of it, every object carries a 12&ndash;16 byte
header so the JVM can find and describe it, and the <b>garbage collector owns
the whole region</b> &mdash; it walks it, frees it, and moves objects around
inside it.</p>

<p><b>Off-heap</b> memory is memory the JVM asks the operating system for
directly and then refuses to manage: a flat run of bytes at some address, with
no object headers, no type information, and no GC. All that lives on the heap
is a tiny handle &mdash; an 8-byte address and a length.</p>

<pre>on-heap  Row  ->  [hdr|ptr]-->[hdr|ptr]-->[hdr|"ACME"]      3 objects, ~90 bytes, GC walks all 3
off-heap Row  ->  0x7f3a1c00: 04 00 00 00 41 43 4D 45 ...    1 blob,  ~12 bytes, GC sees nothing</pre>

<h3>Turning it on</h3>
<pre>spark.memory.offHeap.enabled   true      # default false
spark.memory.offHeap.size      2g        # default 0  -- BOTH are required</pre>
<p>Setting only <code>enabled</code> gives you nothing: the size defaults to 0.
Once on, the same <code>UnifiedMemoryManager</code> runs a <b>second</b> pair of
pools &mdash; off-heap execution and off-heap storage &mdash; split by the same
<code>storageFraction</code>. Off-heap is not a different feature; it is a
second copy of the same picture, living outside the heap.</p>

<h3>What actually goes there</h3>
<table>
<tr><th>goes off-heap</th><th>does NOT go off-heap</th></tr>
<tr><td>Tungsten execution buffers: sort records, the aggregation hash map,
        shuffle write buffers (<code>UnsafeRow</code> pages)</td>
    <td>your Python / Scala objects, UDF closures, driver-side collections &mdash;
        those are user memory on the heap</td></tr>
<tr><td>blocks cached with <code>StorageLevel.OFF_HEAP</code></td>
    <td>JVM metaspace, thread stacks, netty network buffers &mdash; those come
        out of <code>memoryOverhead</code></td></tr>
</table>

<h3>Why you would want it</h3>
<ul>
<li><b>No GC pressure.</b> The collector never scans it, so a 20 GB off-heap
    cache costs zero pause time. This is the real reason.</li>
<li><b>Denser.</b> No object headers and no pointer chasing &mdash; a 10-character
    Java <code>String</code> is ~56 bytes on heap, ~14 bytes as a Tungsten
    binary field.</li>
<li><b>Predictable.</b> The footprint is exactly what you asked for; it does not
    balloon and then shrink after a collection.</li>
</ul>

<h3>What it costs</h3>
<ul>
<li><b>Slower per access.</b> Every read and write crosses a
    serialize/deserialize boundary instead of dereferencing a pointer.</li>
<li><b>Invisible.</b> A leak never shows up in a heap dump, and
    <code>jmap</code> will tell you the heap is fine while the container dies.</li>
<li><b>Still counted by the OS.</b> YARN and Kubernetes measure the whole
    process, not the heap.</li>
</ul>

<div class="warn"><b>Sizing trap.</b> Container = <code>executor.memory</code> +
<code>memoryOverhead</code> + <code>offHeap.size</code>. Spark 3.x adds
<code>offHeap.size</code> into the container request for you; on 2.x you had to
inflate <code>memoryOverhead</code> by hand. Either way, turning off-heap on
without giving the container more room just moves the OOM from the JVM to the
kernel.</div>

<div class="say">"I reach for off-heap when GC time on the Executors tab is
eating more than ~10% of task time and the live set is large &mdash; typically
a big cache or a wide aggregation. I start at 10&ndash;20% of executor memory,
and I raise the container ask by the same amount. If spilling, not GC, is the
problem, off-heap is the wrong lever; more execution memory is."</div>

<div class="one"><b>One-liner:</b> off-heap trades a little CPU per access for
no GC pauses at all &mdash; and it is slower than the heap but orders of
magnitude faster than spilling to disk, so it is the right choice when the
alternative is disk.</div>
</div>

<!-- ================================================================ 3 -->
<div class="sec newpage">
<h2>4 &middot; "You have to allocate and deallocate it yourself" &mdash; in code</h2>

<p>True of the <i>mechanism</i>, mostly false of <i>your job</i>. Three levels:</p>

<h3>Level 1 &mdash; on-heap: you allocate, the GC deallocates</h3>
<pre>byte[] buf = new byte[1024 * 1024];   // allocate: JVM carves 1 MB out of the heap
buf = null;                           // you only drop the reference...
                                      // ...the GC frees the bytes, whenever it feels like it</pre>
<p>There is no <code>free()</code> in Java. That is the whole point of a managed
heap &mdash; and the whole source of GC pauses.</p>

<h3>Level 2 &mdash; off-heap, the semi-manual way (DirectByteBuffer)</h3>
<pre>ByteBuffer buf = ByteBuffer.allocateDirect(1024 * 1024);  // OS memory, outside -Xmx
buf.putLong(0, 42L);
long v = buf.getLong(0);
// Still no free(): the native bytes go back only when the small on-heap
// DirectByteBuffer object becomes unreachable and its Cleaner runs. Keep that
// object in a cache or a static map and the OS memory is never returned.</pre>
<p>Capped by <code>-XX:MaxDirectMemorySize</code>; blowing that cap raises
<code>java.lang.OutOfMemoryError: Direct buffer memory</code>.</p>

<h3>Level 3 &mdash; off-heap, fully manual (what Spark itself does)</h3>
<pre>import org.apache.spark.unsafe.Platform;

long addr = Platform.allocateMemory(8L * 1024 * 1024);   // sun.misc.Unsafe.allocateMemory
try {
    Platform.putLong(null, addr, 42L);                   // write at a raw address
    long v = Platform.getLong(null, addr);
} finally {
    Platform.freeMemory(addr);   // &lt;-- YOU call this. The GC never will, and if you
}                                //     miss it the memory is gone until the JVM exits.</pre>

<h3>What Spark wraps around that, so you do not have to</h3>
<pre>// TaskMemoryManager.allocatePage(size, consumer)
//   off-heap -> MemoryAllocator.UNSAFE.allocate(size)   == Unsafe.allocateMemory
//   on-heap  -> MemoryAllocator.HEAP.allocate(size)     == new long[...]
//
// Every page belongs to a MemoryConsumer (sorter, aggregate map, shuffle writer)
// and is registered against the task; at task end cleanUpAllAllocatedMemory()
// -> freePage() -> Platform.freeMemory(addr) for every page the task took.</pre>

<h3>So what is actually <i>your</i> job?</h3>
<pre class="py"># 1. size it, and say so once
spark = (SparkSession.builder
         .config("spark.memory.offHeap.enabled", "true")
         .config("spark.memory.offHeap.size", "2g")
         .config("spark.executor.memoryOverhead", "1g")   # container must grow too
         .getOrCreate())
# 2. the only allocate/deallocate pair you write by hand:
from pyspark import StorageLevel
df.persist(StorageLevel.OFF_HEAP)   # allocate   -- blocks go to the off-heap store
df.unpersist()                      # deallocate -- or they sit there until the executor dies</pre>

<div class="warn"><b>&#10007; What the video implies:</b> "with off-heap, the
Spark developer has to allocate and deallocate memory."<br>
<b>&#10003; More precisely:</b> writing DataFrame or SQL code, you never call
<code>allocate</code> or <code>free</code> &mdash; <code>TaskMemoryManager</code>
does it and releases every page when the task finishes. What really lands on
you is: (a) <b>sizing</b> the pool and the container, (b) calling
<code>unpersist()</code> on <code>OFF_HEAP</code> blocks, and (c) the fact that
a leak here is <b>permanent and invisible</b>, because no GC is coming to clean
up after you. You only write real <code>allocate</code>/<code>free</code> pairs
if you implement your own <code>MemoryConsumer</code>, a custom data source, or
a JNI/native UDF.</div>

<div class="one"><b>One-liner:</b> on-heap, you forget and the GC forgives;
off-heap, you forget and the kernel kills you.</div>
</div>

<!-- ================================================================ 4 -->
<div class="sec newpage">
<h2>5 &middot; How the JVM knows an object is garbage &#9733;</h2>

<div class="rule">Reachability, not reference counts.
<small>An object is garbage when no chain of references from a <b>GC root</b>
reaches it &mdash; regardless of how many other objects point at it.</small></div>

<h3>Your hypothesis, graded</h3>
<p><i>"It goes through all the pointers you have in the program to see the
memory they point to. Any memory nothing points to, it deletes."</i></p>
<ul>
<li><b>&#10003; Right in spirit.</b> Java GC is a <b>tracing</b> collector: it
    follows pointers and keeps whatever it can reach. Nothing else survives.</li>
<li><b>&#10007; Correction 1 &mdash; direction.</b> It does not scan the heap
    looking for who points where. It starts from a small fixed set of
    <b>GC roots</b> and walks <i>outward</i>. Dead objects are never visited at
    all, which is why the cost of a collection is proportional to the
    <b>live</b> data, not to the garbage. Creating a million short-lived objects
    is nearly free; keeping a million alive is not.</li>
<li><b>&#10007; Correction 2 &mdash; "pointed to" is not the test.</b> Two dead
    objects pointing at each other are still garbage. "Reachable from a root" is
    the test, and that is exactly the case reference counting gets wrong.</li>
</ul>

<pre class="py"># island of isolation: both are "pointed to", both are still collected
a.next = b
b.prev = a
a = None
b = None        # no stack frame, no static field reaches them -> garbage</pre>

<div class="warn"><b>Worth knowing as a PySpark user:</b> the two halves of your
job use different schemes. <b>CPython</b> (the driver and the Python workers)
uses <b>reference counting</b> &mdash; an object dies the instant its count hits
zero &mdash; plus a cycle detector for exactly the island above. The <b>JVM</b>
(every executor) uses tracing only. So "it's freed when nothing points at it" is
the right mental model for your Python code and the wrong one for Spark's.</div>

<h3>What counts as a GC root</h3>
<ul>
<li>local variables and parameters in <b>every live stack frame</b> of
    <b>every thread</b></li>
<li><b>static fields</b> of every loaded class (and the classes / classloaders
    themselves)</li>
<li>JNI references held by native code</li>
<li>objects currently used as a <b>monitor</b> (something is synchronized on them)</li>
<li>a handful of JVM-internal references</li>
</ul>
<p>That last-but-one bullet is why a <code>static Map</code> cache is the classic
Java memory leak: a static field is a root, so everything it holds is live
forever, by definition.</p>

<h3>The actual algorithm: mark &rarr; sweep &rarr; compact</h3>
<table>
<tr><th>phase</th><th>what happens</th><th>cost driven by</th></tr>
<tr><td><b>Mark</b></td>
    <td>Starting at the roots, follow every reference transitively and set a
        "live" bit on each object reached.</td>
    <td>size of the <b>live set</b></td></tr>
<tr><td><b>Sweep</b></td>
    <td>Everything unmarked is, by definition, unreachable &mdash; no future
        line of code could name it. Its space is reclaimed.</td>
    <td>heap size</td></tr>
<tr><td><b>Compact</b></td>
    <td>Slide the survivors together so free space is one contiguous run and
        the next allocation is a pointer bump.</td>
    <td>bytes of live data moved</td></tr>
</table>

<div class="warn"><b>Stop-the-world.</b> Marking needs a reference graph that is
not changing underneath it, so application threads are halted at safepoints
while it runs (modern collectors do much of the marking concurrently, but never
all of it). <b>That pause is the whole reason off-heap memory exists.</b></div>

<div class="say">"Java GC is a tracing collector. It starts from GC roots &mdash;
thread stacks, statics, JNI handles &mdash; and marks everything transitively
reachable; whatever is left unmarked is freed. It is not reference counting, so
cyclic garbage is collected correctly, and the cost of a collection scales with
the live set rather than with the amount of garbage."</div>
</div>

<!-- ================================================================ 5 -->
<div class="sec newpage">
<h2>6 &middot; GC in practice: generations, G1, and why an executor stalls</h2>

<h3>The generational hypothesis</h3>
<p>Nearly all objects die young. So the heap is split, and the cheap collection
only looks at the part where that is true:</p>
<pre>|---------------- Young ----------------|------------- Old (Tenured) -------------|
|   Eden      | S0 | S1 |               |   long-lived: cached blocks, broadcast  |
|  new objs   | survivors |             |   maps, the SparkContext, your statics  |

Minor GC : Eden + one survivor only. Copies the few survivors out, wipes the rest.
           Milliseconds. Runs constantly.
Promotion: survive N minor GCs -> moved to Old.
Major/Full GC: touches Old. Has to mark the entire live set. Seconds, on a big heap.</pre>

<h3>Why this bites a Spark executor specifically</h3>
<ul>
<li>Shuffle and sort buffers are <b>short-lived and enormous</b> &rarr; they
    churn the young generation, which is fine.</li>
<li>Cached DataFrames are <b>long-lived and enormous</b> &rarr; they fill the old
    generation with millions of live objects. Every full GC must mark all of
    them, every time. A 30 GB heap holding a 25 GB live cache is a multi-second
    pause with every core idle.</li>
<li><b>Three ways out</b>, in the order to try them:
    <ol>
      <li>cache <b>serialized</b> (<code>MEMORY_AND_DISK_SER</code>) &mdash; one
          big <code>byte[]</code> instead of millions of objects, so the marker
          visits 1 object instead of 10<sup>7</sup>;</li>
      <li>move the cache <b>off-heap</b> &mdash; not scanned at all;</li>
      <li>run <b>more, smaller executors</b> instead of one giant one &mdash;
          pause time tracks heap size, and 4&times;16 GB pauses far less than
          1&times;64 GB.</li>
    </ol></li>
</ul>

<h3>Where to look</h3>
<p>Spark UI &rarr; <b>Executors</b> tab &rarr; <code>GC Time</code>, next to
<code>Task Time</code>. Rule of thumb: <b>GC Time above ~10% of Task Time means
GC is your bottleneck</b>, not your logic.</p>

<h3>Collectors worth knowing by name</h3>
<table>
<tr><th>collector</th><th>character</th><th>when</th></tr>
<tr><td><code>ParallelGC</code></td><td>multi-threaded, stop-the-world, best raw
    throughput, pauses grow with the heap</td><td>small heaps, batch jobs where
    a 2 s pause is irrelevant</td></tr>
<tr><td><code>G1GC</code></td><td>heap split into ~2000 regions, marks
    concurrently, collects the regions with most garbage first, aims at a
    <i>soft</i> pause target. <b>Default since Java 9.</b></td>
    <td>the sane default for executors above ~8 GB</td></tr>
<tr><td><code>ZGC</code> / <code>Shenandoah</code></td><td>nearly everything
    concurrent, sub-millisecond pauses, costs extra CPU and memory</td>
    <td>very large heaps where latency matters more than throughput</td></tr>
</table>

<pre>--conf spark.executor.extraJavaOptions="-XX:+UseG1GC \
  -XX:MaxGCPauseMillis=200 \
  -Xlog:gc*:file=/tmp/gc-%p.log:time,uptime:filecount=5,filesize=20M"</pre>

<div class="warn">Never set <code>-Xmx</code> in
<code>extraJavaOptions</code> &mdash; Spark sets it from
<code>spark.executor.memory</code> and the duplicate will either be ignored or
break the launch. And <code>System.gc()</code> is a request, not a command;
in a Spark job it is almost always the wrong fix.</div>

<div class="one"><b>One-liner:</b> GC cost is paid per <b>live</b> byte, so the
fix is never "collect more often" &mdash; it is "keep fewer live objects":
serialize the cache, move it off-heap, or shrink the executor.</div>
</div>

<!-- ================================================================ 6 -->
<div class="sec newpage">
<h2>7 &middot; Where does each thing live, and what breaks</h2>

<table>
<tr><th>region</th><th>holds</th><th>GC'd?</th><th>freed by</th><th>config</th></tr>
<tr><td>on-heap execution</td><td>shuffle / sort / agg buffers</td><td>yes</td>
    <td>task completion</td><td><code>memory.fraction</code></td></tr>
<tr><td>on-heap storage</td><td>cached blocks, broadcasts</td><td>yes</td>
    <td>LRU eviction, <code>unpersist()</code></td>
    <td><code>memory.storageFraction</code></td></tr>
<tr><td>user memory</td><td>your objects, UDF closures</td><td>yes</td>
    <td>GC, when unreachable</td><td>whatever is left over</td></tr>
<tr><td>reserved</td><td>Spark internals</td><td>yes</td><td>&mdash;</td>
    <td>300 MB, fixed</td></tr>
<tr><td>overhead</td><td>metaspace, thread stacks, netty buffers,
    <b>PySpark workers</b></td><td>no (not heap)</td><td>OS / process exit</td>
    <td><code>executor.memoryOverhead</code></td></tr>
<tr><td>off-heap</td><td>Tungsten pages, <code>OFF_HEAP</code> blocks</td>
    <td><b>no</b></td><td><code>TaskMemoryManager</code>, <code>unpersist()</code></td>
    <td><code>memory.offHeap.size</code></td></tr>
<tr><td>disk</td><td>spills, shuffle files, evicted blocks</td><td>n/a</td>
    <td>shuffle cleanup / app end</td><td><code>spark.local.dir</code></td></tr>
</table>

<h3>Symptom &rarr; which knob</h3>
<table>
<tr><th>what you see</th><th>what it means</th><th>what to change</th></tr>
<tr><td><code>Container killed by YARN for exceeding memory limits. 11.5 GB of
    11 GB physical memory used</code> &nbsp;/&nbsp; K8s exit code 137</td>
    <td>the <b>process</b> outgrew the container &mdash; almost always overhead,
        off-heap, or Python workers, not the heap</td>
    <td>raise <code>executor.memoryOverhead</code>; if PySpark-heavy, cap
        <code>spark.executor.pyspark.memory</code></td></tr>
<tr><td><code>java.lang.OutOfMemoryError: Java heap space</code></td>
    <td>the heap genuinely filled &mdash; too much cached, or too many
        concurrent tasks sharing one heap</td>
    <td>raise <code>executor.memory</code>, or lower
        <code>executor.cores</code>, or cache serialized</td></tr>
<tr><td><code>OutOfMemoryError: Direct buffer memory</code></td>
    <td>off-heap / direct buffers exceeded their cap</td>
    <td><code>memory.offHeap.size</code> or
        <code>-XX:MaxDirectMemorySize</code></td></tr>
<tr><td>Spill (memory) and Spill (disk) &gt; 0 on the Stages tab</td>
    <td>execution memory per task was too small for the partition</td>
    <td>more shuffle partitions, fewer cores per executor, or fix the skew
        &mdash; see the data-skew notes</td></tr>
<tr><td>GC Time &gt; 10% of Task Time</td><td>live set too large</td>
    <td><code>MEMORY_AND_DISK_SER</code>, off-heap, or smaller executors</td></tr>
<tr><td>Storage tab shows a cached DF at &lt;100%</td>
    <td>storage memory could not hold it; blocks are being evicted and
        recomputed</td>
    <td>serialize it, or stop caching it</td></tr>
</table>

<div class="one"><b>One-liner:</b> "killed" is a container problem, "OOM" is a
heap problem, "spill" is an execution-memory problem, and "GC" is a live-set
problem. They have four different fixes.</div>
</div>

<!-- ================================================================ 7 -->
<div class="sec newpage">
<h2>8 &middot; Interview answers</h2>

<h3>"Walk me through what <code>--executor-memory 10G</code> buys you."</h3>
<div class="say">"10 GB is the JVM heap, nothing else. Spark takes 300 MB off
the top as reserved, then <code>memory.fraction</code> 0.6 of the rest is the
unified pool &mdash; about 5.8 GiB &mdash; which <code>storageFraction</code> 0.5
splits into roughly 2.9 GiB of execution and 2.9 GiB of storage to start with.
The remaining ~3.9 GiB is user memory for my own objects. On top of the 10 GB,
not inside it, Spark asks the cluster manager for
<code>max(384 MB, 10%)</code> = 1 GB of overhead, so the container is 11 GB. If
I enabled off-heap, that is a third amount again."</div>

<h3>"What is unified memory, and what changed in 1.6?"</h3>
<div class="say">"Before 1.6, <code>StaticMemoryManager</code> fixed the line
between execution and storage, so a job could spill while half the storage pool
sat empty. Since 1.6, <code>UnifiedMemoryManager</code> makes that line movable:
either side can borrow the other's unused space. The asymmetry is that
execution can force storage to evict LRU blocks to get memory back, but storage
can never evict execution &mdash; a half-finished shuffle cannot be rebuilt from
lineage, a cached block always can."</div>

<h3>"When would you turn off-heap on, and what is the catch?"</h3>
<div class="say">"When GC time, not spilling, is the bottleneck &mdash; a big
cache or a wide aggregation on a large heap. It removes that memory from the
collector's reach entirely. The catches are that every access pays a
serialization cost, the container has to grow by the same amount or the kernel
kills the executor, and a leak there never shows up in a heap dump."</div>

<h3>"How does the JVM know an object can be collected?"</h3>
<div class="say">"Reachability from GC roots &mdash; thread stacks, static
fields, JNI handles, held monitors. The collector marks everything transitively
reachable from those and frees the rest. It is tracing, not reference counting,
so cycles of dead objects are collected correctly, and the cost scales with the
live set rather than the garbage."</div>

<h3>"A job keeps dying with 'Container killed by YARN'. Walk me through it."</h3>
<div class="say">"That message is about the OS process, not the heap, so raising
<code>executor.memory</code> usually makes it worse &mdash; it grows the
container. I look at overhead first: netty shuffle buffers and, for PySpark,
the Python worker processes all live there, and the 384 MB floor is far too
small for a Python job. I'd raise <code>memoryOverhead</code> to 10&ndash;20% of
executor memory, check whether off-heap is enabled and counted, and check
whether one skewed partition is making a single task huge."</div>
</div>

<!-- ================================================================ 8 -->
<div class="sec">
<h2>9 &middot; Cross-references and what is still open</h2>

<h3>Already covered in the other notes in this repo</h3>
<ul>
<li><b>Caching notes</b> &mdash; storage levels, <code>cache()</code> vs
    <code>persist()</code>, what eviction costs you, the Storage tab. The
    storage half of unified memory is explained there in detail; these notes do
    not repeat it.</li>
<li><b>Data-skew / salting / AQE notes</b> &mdash; spill is the symptom of
    execution memory running out on one fat partition; those notes have the
    measured runs.</li>
</ul>

<h3>Not covered yet</h3>
<ul>
<li><code>spark.executor.pyspark.memory</code> and how Python worker memory is
    accounted (it comes out of overhead, and is unbounded by default)</li>
<li>Dynamic allocation and how it interacts with cached blocks on an executor
    that is about to be removed</li>
<li>Tungsten internals: <code>UnsafeRow</code> layout, whole-stage codegen,
    and why they are what make off-heap worth having</li>
<li><code>spark.executor.cores</code> &times; execution memory &mdash; the real
    per-task budget, and how it drives
    <code>spark.sql.shuffle.partitions</code></li>
</ul>

<h3>Next, in order</h3>
<ol>
<li>Executor tuning (the next video in the playlist) &mdash; it is the direct
    sequel: how many cores and how much memory per executor, and why 5 cores is
    the usual answer.</li>
<li>Run one job twice, once with <code>MEMORY_AND_DISK</code> and once with
    <code>MEMORY_AND_DISK_SER</code>, and read GC Time off the Executors tab.
    That single measurement makes section 6 permanent.</li>
<li>Then shuffle partitions, which is where the per-task execution budget
    actually gets spent.</li>
</ol>
</div>
"""


def typed_body():
    return BODY
