# -*- coding: utf-8 -*-
"""Annotated whiteboard pages for the Spark Memory Management study notes.

Both base images already live in the repo (they are the boards used in the
video); the handwritten layer is positioned on top of them in percent
coordinates measured off the source pixels.
"""


# ---------------------------------------------------------------- helpers --
def an(left, top, lines, width=None, red=False, size=None):
    """One absolutely-positioned handwritten annotation on a board."""
    sty = "left:%s%%;top:%s%%;" % (left, top)
    if width:
        sty += "width:%s%%;" % width
    if size:
        sty += "font-size:%spx;" % size
    cls = "an red" if red else "an"
    body = "<br>".join(lines) if isinstance(lines, (list, tuple)) else lines
    return '<div class="%s" style="%s">%s</div>' % (cls, sty, body)


def ring(left, top, w, h, rot=-2):
    """Red hand-drawn circle around something printed on the board."""
    return ('<div class="ring" style="left:%s%%;top:%s%%;width:%s%%;height:%s%%;'
            'transform:rotate(%sdeg)">&nbsp;</div>' % (left, top, w, h, rot))


C = lambda s: '<span class="circ">%s</span>' % s      # red circled token
K = lambda s: '<span class="cd">%s</span>' % s        # config / code chip


# ============================================================ BOARD 1 ======
# docs/images/memory_management.png  (2492 x 1358)
#   container  x 698-2184  y   50-1264      on-heap   x  764-1494  y  202-1204
#   execution  x 812-1452  y  326- 578      storage   x  812-1452  y  582- 832
#   user       x 812-1452  y  838-1056      reserved  x  812-1452  y 1062-1166
#   off-heap   x 1554-2120 y  342- 686      overhead  x 1554-2120 y  742- 986
def board1(img_b64):
    parts = [
        '<div class="board">',
        '<img src="data:image/png;base64,%s">' % img_b64,

        # ---- the whole calculation, written down the free left margin ----
        an(0.6, 0.5, [
            '<b>--executor-memory %s</b>' % C('10G'),
            'sizes the <u>on-heap</u> box only',
            '&times; 0.6 <i>memory.fraction</i> = <b>6 GB</b> unified',
            '&times; 0.5 <i>storageFraction</i> = <b>3 GB</b> storage',
            '&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;6 &minus; 3 = <b>3 GB</b> execution',
        ], width=27),

        an(0.6, 70.5, [
            '10 &minus; 6 = <b>4 GB</b> left over',
            '4 GB &minus; 300 MB = <b>3.7 GB</b> user memory',
            '<span class="red">300 MB reserved is a flat</span>',
            '<span class="red">constant &mdash; not a fraction</span>',
        ], width=27),

        # ---- numbers written inside each on-heap band ----
        an(33.4, 24.6, '<b>3 GB</b>', red=True),
        an(33.4, 45.2, '<b>3 GB</b>', red=True),
        an(33.4, 62.3, '<b>3.7 GB</b>', red=True),

        # ---- off-heap ----
        an(63.0, 25.8, [
            'managed by the <b>OS</b>, not the JVM',
            '&rarr; never scanned by GC',
        ], width=23, size=13.5),
        an(63.0, 41.0, [
            '<span class="red">off by default (size = 0)</span>',
            'own execution + storage split',
            'start at 10&ndash;20% of executor mem',
        ], width=24, size=13.5),

        # ---- overhead ----
        an(63.4, 67.6, '&rarr; <b>1 GB</b>, added on top of the 10 GB',
           red=True, width=24, size=13.5),

        # ---- what the cluster manager is actually asked for ----
        an(62.6, 74.5, [
            '<b>YARN / K8s container ask</b>',
            '= executor-memory + overhead',
            '&nbsp;&nbsp;(+ offHeap.size if enabled)',
            '= 10 + 1 = <b>11 GB</b>',
        ], width=25),

        # ---- red circles over text printed on the board ----
        ring(39.8, 18.7, 11.0, 3.4),      # spark.executor.memory
        ring(41.6, 81.0, 6.0, 3.8, 3),    # 300 MB
        ring(66.2, 36.4, 14.2, 3.6),      # spark.memory.offHeap.enabled
        ring(63.8, 64.7, 19.2, 3.3, 1),   # max(384 MB, 10% ...)
        '</div>',
        '<div class="foot">&#128161; <b>--executor-memory sizes the heap, not '
        'the container.</b> That gap &mdash; overhead, plus off-heap if you '
        'enabled it &mdash; is what gets an executor killed.</div>',
    ]
    return "\n".join(parts)


# ============================================================ BOARD 2 ======
# docs/images/unified_memory.png (1284 x 1594) cropped into five strips; each
# strip gets its handwritten note in the right-hand column.
CROPS = {                       # name: (left, upper, right, lower)
    "u0": (450,   36,  800,  315),
    "u1": (140,  338, 1075,  572),
    "u2": (140,  628, 1075,  862),
    "u3": (140,  975, 1075, 1152),
    "u4": (140, 1288, 1075, 1560),
}

ROWS = [
    ("u0", 32, [
        '<div class="hn-t2">&#9997; What "unified" means</div>',
        '<ul><li>execution + storage are <b>one pool</b> = '
        'memory.fraction &times; executor-memory</li>'
        '<li>storageFraction only says where the divider <i>starts</i>, '
        'not where it stays</li>'
        '<li>user memory and reserved sit <u>outside</u> it and never move</li></ul>',
    ]),
    ("u1", 100, [
        '<div class="hn-t2">1 &nbsp;&lt; Spark 1.6 &mdash; StaticMemoryManager</div>',
        '<ul><li>the divider is <span class="red"><b>FIXED</b></span></li>'
        '<li>execution could spill or OOM while storage sat half empty right '
        'next to it &mdash; pure waste</li>'
        '<li>you tuned the split by hand, per job</li></ul>',
    ]),
    ("u2", 100, [
        '<div class="hn-t2">2 &nbsp;&ge; Spark 1.6 &mdash; UnifiedMemoryManager</div>',
        '<ul><li>the divider is <span class="red"><b>MOVABLE</b></span></li>'
        '<li>storage is not using its half, so execution takes the '
        '<b>vacant</b> space</li>'
        '<li>nothing is evicted here &mdash; nobody was there</li></ul>',
    ]),
    ("u3", 100, [
        '<div class="hn-t2">3 &nbsp;Execution wants more, storage is full</div>',
        '<ul><li>storage <b>evicts its own</b> blocks, <span class="red">LRU'
        '</span> first, and hands the space over</li>'
        '<li>an evicted block is recomputed or read from disk later &mdash; you '
        'lose time, never correctness</li></ul>',
    ]),
    ("u4", 100, [
        '<div class="hn-t2">4 &nbsp;Storage wants more, execution is full</div>',
        '<ul><li>execution blocks are <span class="red"><b>never</b></span> '
        'evicted &mdash; a half-finished sort cannot be rebuilt from lineage</li>'
        '<li>storage evicts <b>its own</b> LRU blocks again, or the new block '
        'just does not get cached</li></ul>',
    ]),
]


def board2(crop_b64):
    rows = []
    for key, w, note in ROWS:
        rows.append(
            '<tr><td class="pic"><img src="data:image/png;base64,%s" '
            'style="width:%d%%"></td><td class="note">%s</td></tr>'
            % (crop_b64[key], w, "".join(note)))
    return (
        '<div class="b2head">&#9997; Unified memory &mdash; who gets to move '
        'the divider</div>'
        '<table class="b2">%s</table>' % "".join(rows)
        + '<div class="hn def tight">'
          '<div class="hn-t">The one rule</div>'
          '<p><b>Execution always wins.</b> Joins, shuffles, sorts and '
          'aggregations cannot be restarted halfway through from a lineage, so '
          'their memory is never taken away. Cached blocks can always be '
          'rebuilt, so they are the ones that go.</p>'
          '<p class="red">&#9888; Gotcha: a <span class="cd">.cache()</span> on a '
          'DataFrame that gets read once does not merely waste storage memory '
          '&mdash; it pushes execution into spilling, and then gets evicted '
          'anyway. Cache only what is read <u>twice or more</u>.</p>'
          '<p class="tip">&#128161; Storage borrows and gives it back; '
          'execution borrows and keeps it.</p></div>'
        + '<div class="hn def tight">'
          '<div class="hn-t">&#9997; Execution vs Storage, side by side</div>'
          '<table class="ht wide cmp">'
          '<tr><th>Execution (wins)</th><th>Storage (yields)</th></tr>'
          '<tr><td>joins, shuffles, sorts, groupBy buffers</td>'
          '<td>cache() / persist() blocks, broadcast variables</td></tr>'
          '<tr><td>lives for the length of one <b>task</b></td>'
          '<td>lives until evicted or unpersisted</td></tr>'
          '<tr><td>cannot be rebuilt mid-flight &rarr; <b>never evicted</b></td>'
          '<td>always rebuildable from lineage &rarr; <b>first to go</b></td></tr>'
          '<tr><td>when it runs out: <span class="red">spill to disk</span>, '
          'then OOM</td>'
          '<td>when it runs out: silently <span class="red">drops blocks</span> '
          '(Storage tab shows &lt;100% cached)</td></tr>'
          '<tr><td>knob: <span class="cd">memory.fraction</span>, and fewer '
          '<span class="cd">cores</span> per executor</td>'
          '<td>knob: <span class="cd">storageFraction</span>, or cache less / '
          'cache serialized</td></tr>'
          '</table></div>')
