# -*- coding: utf-8 -*-
"""Content for Caching_Study_Notes.pdf - handwritten notes, circles, typed pages."""

BADGES = "①②③④⑤⑥⑦⑧⑨⑩"


def badge(i):
    return '<span class="bdg">%s</span>' % BADGES[i - 1]


UP_SVG = ('<svg width="70" height="34" viewBox="0 0 70 34">'
          '<path d="M8 30 C 18 24, 26 10, 40 6" fill="none" stroke="#d62828" '
          'stroke-width="2.2" stroke-linecap="round"/>'
          '<path d="M31 3 L41 5.5 L34 13" fill="none" stroke="#d62828" '
          'stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/></svg>')


def note(title, items=(), tip=None, extra="", up=False, cls="hn"):
    h = ['<div class="%s">' % cls, '<div class="hn-t">%s</div>' % title]
    if up:
        h.append('<div class="arwrow">%s<span class="arwlab">'
                 'match the circles in the output above</span></div>' % UP_SVG)
    if items:
        h.append("<ul>")
        for n, (code, text) in enumerate(items, 1):
            lead = badge(n) + " " if code is not None else ""
            cd = '<span class="cd">%s</span> <span class="to">&#10230;</span> ' % code if code else ""
            h.append("<li>%s%s%s</li>" % (lead, cd, text))
        h.append("</ul>")
    if extra:
        h.append(extra)
    if tip:
        h.append('<p class="tip">&#128161; %s</p>' % tip)
    h.append("</div>")
    return "\n".join(h)


def gotcha(text):
    return '<p style="color:#d62828"><b>&#9888; Gotcha:</b> %s</p>' % text


# --------------------------------------------------------------- sketches ---
LINEAGE_SKETCH = '''
<svg class="sk" width="660" height="196" viewBox="0 0 660 196">
  <text class="skt" x="4" y="16" style="font-size:17px">Lazy evaluation: what .show() really triggers</text>
  <!-- df1 row -->
  <text class="skt" x="6" y="60">df1</text>
  <rect x="44" y="40" width="92" height="28" rx="5" fill="none" stroke="#1f4fb5" stroke-width="2"/>
  <text class="skt" x="52" y="59">df_base</text>
  <path d="M138 54 L196 54" stroke="#1f4fb5" stroke-width="1.8" marker-end="url(#ar)"/>
  <rect x="198" y="40" width="118" height="28" rx="5" fill="none" stroke="#1f4fb5" stroke-width="2"/>
  <text class="skt" x="206" y="59">test_column_1</text>
  <path d="M318 54 L372 54" stroke="#1f4fb5" stroke-width="1.8" marker-end="url(#ar)"/>
  <rect x="374" y="40" width="100" height="28" rx="5" fill="none" stroke="#1f4fb5" stroke-width="2"/>
  <text class="skt" x="382" y="59">birth_year</text>
  <path d="M476 54 L524 54" stroke="#1f4fb5" stroke-width="1.8" marker-end="url(#ar)"/>
  <text class="skt" x="528" y="59" fill="#d62828">.show()</text>
  <!-- df2 row -->
  <text class="skt" x="6" y="124">df2</text>
  <rect x="44" y="104" width="92" height="28" rx="5" fill="none" stroke="#1f4fb5" stroke-width="2"/>
  <text class="skt" x="52" y="123">df_base</text>
  <path d="M138 118 L196 118" stroke="#1f4fb5" stroke-width="1.8" marker-end="url(#ar)"/>
  <rect x="198" y="104" width="118" height="28" rx="5" fill="none" stroke="#1f4fb5" stroke-width="2"/>
  <text class="skt" x="206" y="123">test_column_2</text>
  <path d="M318 118 L372 118" stroke="#1f4fb5" stroke-width="1.8" marker-end="url(#ar)"/>
  <rect x="374" y="104" width="108" height="28" rx="5" fill="none" stroke="#1f4fb5" stroke-width="2"/>
  <text class="skt" x="382" y="123">birth_month</text>
  <path d="M484 118 L524 118" stroke="#1f4fb5" stroke-width="1.8" marker-end="url(#ar)"/>
  <text class="skt" x="528" y="123" fill="#d62828">.show()</text>
  <!-- the shared box -->
  <rect x="36" y="30" width="108" height="112" rx="10" fill="none" stroke="#2a9d5c" stroke-width="2.4"/>
  <text class="skt" x="36" y="164" fill="#2a9d5c">built TWICE without cache &#8594; cache it once</text>
  <defs><marker id="ar" markerWidth="8" markerHeight="8" refX="7" refY="3" orient="auto">
    <path d="M0,0 L7,3 L0,6 z" fill="#1f4fb5"/></marker></defs>
</svg>'''

LEVEL_AXES_SKETCH = '''
<svg class="sk" width="620" height="150" viewBox="0 0 620 150">
  <text class="skt" x="4" y="16" style="font-size:17px">Two independent dials</text>
  <text class="skt" x="10" y="48">SER &#8212;&#8212;&#8212;&#8212;&#8212;&#8212;&#8594; DESER</text>
  <text class="skt" x="250" y="48" fill="#2a9d5c">small + slow</text>
  <text class="skt" x="250" y="68" fill="#d62828">big + fast</text>
  <line x1="12" y1="56" x2="236" y2="56" stroke="#1f4fb5" stroke-width="1.6"/>
  <text class="skt" x="10" y="106">MEMORY &#8212;&#8212;&#8594; DISK</text>
  <text class="skt" x="250" y="106" fill="#2a9d5c">fast, can be evicted</text>
  <text class="skt" x="250" y="126" fill="#d62828">slow, survives</text>
  <line x1="12" y1="114" x2="236" y2="114" stroke="#1f4fb5" stroke-width="1.6"/>
  <text class="skt" x="430" y="48">&#215; replication (1x / 2x / 3x)</text>
  <text class="skt" x="430" y="68" fill="#d62828">= same cost, N times</text>
</svg>'''


# ------------------------------------------------------- handwritten notes --
HAND = {}

HAND["whatcache"] = note(
    "&#9997; Definition: what <span class='cd'>.cache()</span> does",
    items=[
        (None, "Marks this DataFrame: <b>\"the next time anyone needs you, "
               "don't rebuild &#8212; read the stored copy\"</b>."),
        (None, "It is <b>lazy</b>. The call above only wraps the plan in an "
               "<span class='cd'>InMemoryRelation</span> node and returns the "
               "same DataFrame &#8212; that is the "
               "<span class='cd'>DataFrame[cust_id: string, ...]</span> line printed above."),
        (None, "The <span class='cd'>.show(5)</span> under it is the <b>action</b> "
               "that actually fills the cache."),
        (None, "What gets stored is <b>df_base after the filter and the CASE WHEN</b> "
               "&#8212; 517 Boston rows, not the 5,000 in the file."),
    ],
    extra=gotcha("<span class='cd'>.show(5)</span> only materialises the partitions it "
                 "had to touch. Use <span class='cd'>df.count()</span> when you want the "
                 "whole thing in the cache before the real work starts.") + LINEAGE_SKETCH,
    tip="Cache what you read <b>twice or more</b>. Caching a DataFrame used once "
        "is pure cost.",
    cls="hn def",
)

HAND["plan1"] = note(
    "&#9997; Reading the physical plan after <span class='cd'>cache()</span>",
    items=[
        ("InMemoryTableScan", "df1 reads the <b>cached block</b>, not the parquet file."),
        ("InMemoryRelation", "the cached block itself. Everything indented under it is "
                             "the <b>recipe</b>, kept so Spark can rebuild a block that "
                             "gets evicted or lost."),
        ("StorageLevel(disk, memory, deserialized, 1 replicas)",
         "the default that <span class='cd'>.cache()</span> picks = "
         "<span class='cd'>MEMORY_AND_DISK_DESER</span>."),
        ("split(birthday#47, /, -1)[2] AS birth_year#317",
         "the only <b>new</b> work df1 does on top of the cache."),
    ],
    up=True,
    extra=gotcha("<span class='cd'>FileScan parquet</span> is still printed, under "
                 "<span class='cd'>InMemoryRelation</span>. That is the recipe, not a "
                 "re-read. In the Spark UI the same node reports "
                 "<b>0 rows, 0 ms, 0 bytes</b>."),
    tip="Plan text &#8800; work done. The row counts in the SQL tab are the truth.",
)

HAND["plan2"] = note(
    "&#9997; Why df2 is now almost free",
    items=[
        ("InMemoryTableScan", "the <b>same</b> cached block df1 used. One copy, two readers."),
        ("CASE WHEN ... AS customer_group#57",
         "sits <b>inside</b> the InMemoryRelation &#8212; so it was computed once, when "
         "the cache was filled, not again for df2."),
        ("split(birthday#47, /, -1)[1] AS birth_month#659",
         "df2's only new column."),
    ],
    up=True,
    extra="<p><b>Without the cache</b> this plan reads the parquet, re-runs "
          "<span class='cd'>Filter (city = boston)</span> and rebuilds "
          "<span class='cd'>customer_group</span> a <b>second</b> time &#8212; the whole "
          "lineage, from scratch.</p>"
          "<table class='ht'><tr><th>measured here</th><th>no cache</th>"
          "<th>cached</th></tr>"
          "<tr><td>Scan parquet &#8594; rows</td><td>5,000</td><td>0</td></tr>"
          "<tr><td>size of files read</td><td>149.9 KiB</td><td>0</td></tr>"
          "<tr><td>Filter &#8594; rows</td><td>517</td><td>0</td></tr>"
          "<tr><td>InMemoryTableScan &#8594; rows</td><td>&#8212;</td><td>517</td></tr>"
          "<tr><td>query duration</td><td>333 / 72 ms</td><td>48 / 38 ms</td></tr></table>",
    tip="Spark 4.3.0, local[12], customers.parquet, the two <span class='cd'>count()</span> "
        "queries of each run.",
)

HAND["levels"] = note(
    "&#9997; Why each row of that chart looks like that",
    extra="<table class='ht wide'>"
          "<tr><th>level</th><th>the one sentence</th><th>pay with</th></tr>"
          "<tr><td>MEMORY_ONLY</td><td>JVM objects, straight in RAM &#8212; nothing to "
          "decode on the way out</td><td>RAM. Blocks that don't fit are "
          "<b>silently dropped</b> and recomputed</td></tr>"
          "<tr><td>MEMORY_ONLY_SER</td><td>same place, packed into byte arrays &#8212; "
          "about 2&#8211;5&#215; smaller</td><td>CPU: every read has to deserialise</td></tr>"
          "<tr><td>MEMORY_AND_DISK</td><td>RAM first, overflow spills to local disk "
          "instead of being thrown away</td><td>medium: RAM hits are fast, spilled "
          "blocks cost a disk read</td></tr>"
          "<tr><td>MEMORY_AND_DISK_SER</td><td>the compact version of the same deal &#8212; "
          "more fits in RAM, so fewer spills</td><td>CPU on every read</td></tr>"
          "<tr><td>DISK_ONLY</td><td>never in RAM; always serialised bytes on local disk</td>"
          "<td>CPU + disk I/O on every read &#8212; but it never evicts</td></tr>"
          "</table>"
          "<p><b>Read the chart as two dials, not five choices:</b></p>" + LEVEL_AXES_SKETCH
          + gotcha("For <b>DataFrames</b> the chart is the RDD-era one. Spark SQL always "
                   "stores a compressed columnar form, so "
                   "<span class='cd'>MEMORY_ONLY</span> on a DataFrame still shows up as "
                   "<i>Memory Serialized</i> in the UI. Measured on the same 5,000 rows: "
                   "<b>DESER 297,224 B</b> vs <b>SER 168,815 B</b>."),
    tip="Space and CPU trade against each other; memory and disk trade speed against "
        "survival. Replication (_2, _3) multiplies <i>both</i> costs and buys only "
        "resilience.",
    cls="hn def",
)

HAND["unpersist"] = note(
    "&#9997; Changing the storage level",
    items=[
        (None, "<span class='cd'>unpersist()</span> <b>then</b> "
               "<span class='cd'>persist(level)</span> &#8212; that order is required."),
        (None, "<span class='cd'>unpersist()</span> is <b>eager</b>: it drops the blocks "
               "right away. Everything downstream goes back to recomputing."),
        (None, "After it, <span class='cd'>df.storageLevel</span> is "
               "<span class='cd'>StorageLevel.NONE</span>."),
    ],
    extra=gotcha("Calling <span class='cd'>persist(ANOTHER_LEVEL)</span> on a DataFrame "
                 "that is already cached <b>does not raise and does not change anything</b>. "
                 "Tested here: a DISK_ONLY DataFrame asked for MEMORY_ONLY stayed "
                 "<i>Disk Serialized 1x Replicated</i>. Silent no-op &#8212; the reason the "
                 "cell above unpersists first.")
          + '<p style="color:#d62828"><b>&#9888; In this cell:</b> it rebuilds '
            '<span class="cd">df2</span> with df1\'s columns and then shows '
            '<span class="cd">df1</span>. The new df2 is never used &#8212; harmless in the '
            'video, but don\'t copy the pattern.</p>',
    tip="Long notebook / long job? <span class='cd'>unpersist()</span> as soon as the "
        "reuse is over, so the block manager can give the memory back.",
    cls="hn def",
)

HAND["close"] = note(
    "&#9997; The whole chapter in five lines",
    items=[
        (None, "Spark is lazy: an action replays the <b>entire</b> lineage, every time."),
        (None, "Two actions on one base = that base built twice."),
        (None, "<span class='cd'>cache()</span> cuts the lineage: the base becomes an "
               "<span class='cd'>InMemoryRelation</span> and everything downstream reads it."),
        (None, "<span class='cd'>cache()</span> <b>is</b> "
               "<span class='cd'>persist()</span>; persist is the one that takes an argument."),
        (None, "Measured on a real 871 MB shuffle here: 3.19 s &#8594; 0.51 s on the reuse, "
               "<b>6.2&#215; faster</b>."),
    ],
    tip="Interview line: <i>\"cache is a bet that recomputation costs more than memory. "
        "If the DataFrame is read once, you lose the bet.\"</i>",
    cls="hn def",
)

AFTER = {7: "whatcache", 8: "plan1", 9: "plan2", 10: "levels", 11: "unpersist",
         12: "close"}

CIRCLES = {
    "plan1": [
        ("InMemoryTableScan", 1),
        ("InMemoryRelation", 2),
        ("StorageLevel(disk, memory, deserialized, 1 replicas)", 3),
        ("split(birthday#47, /, -1)[2] AS birth_year#317", 4),
    ],
    "plan2": [
        ("InMemoryTableScan", 1),
        ("CASE WHEN", 2),
        ("split(birthday#47, /, -1)[1] AS birth_month#659", 3),
    ],
}
