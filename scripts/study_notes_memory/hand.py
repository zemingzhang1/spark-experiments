# -*- coding: utf-8 -*-
"""Handwritten (Caveat) pages that are not an annotated board."""

FIVE_POOLS = """
<div class="hn def">
  <div class="hn-t">&#9997; Definition: the five pools inside one executor</div>
  <table class="ht wide">
    <tr><th>pool</th><th>what actually lives there</th><th>sized by</th></tr>
    <tr><td><b>Execution</b></td>
        <td>joins, shuffles, sorts, groupBy / aggregation buffers &mdash; the
            scratch space of a running task</td>
        <td><span class="cd">memory.fraction &times; (1 &minus; storageFraction)</span></td></tr>
    <tr><td><b>Storage</b></td>
        <td><span class="cd">cache()</span> / <span class="cd">persist()</span>
            blocks, broadcast variables</td>
        <td><span class="cd">memory.fraction &times; storageFraction</span></td></tr>
    <tr><td><b>User</b></td>
        <td>your own objects: lists, dicts, lookup maps, UDF closures,
            anything the JVM holds that is not a Spark buffer</td>
        <td>what is left: <span class="cd">(1 &minus; memory.fraction)</span> &minus; 300 MB</td></tr>
    <tr><td><b>Reserved</b></td>
        <td>Spark's own internal objects. Untouchable.</td>
        <td><span class="cd">300 MB</span>, hard-coded</td></tr>
    <tr><td><b>Overhead</b></td>
        <td>JVM metaspace + thread stacks, netty shuffle buffers,
            <b>PySpark worker processes</b></td>
        <td><span class="cd">max(384 MB, 0.10 &times; executor-memory)</span></td></tr>
  </table>
  <p class="tip">&#128161; Execution and Storage are the only two that can lend
     to each other. The other three are walls.</p>
</div>
"""

CALC = """
<div class="hn def">
  <div class="hn-t">&#9997; The whole calculation, once</div>
  <p>for <span class="cd">--executor-memory 10G</span>, defaults everywhere
     (take 1 GB = 1000 MB to keep the arithmetic readable):</p>
  <table class="ht wide calc">
    <tr><th>step</th><th>arithmetic</th><th>result</th></tr>
    <tr><td>on-heap total</td><td>what you typed</td><td><b>10 GB</b></td></tr>
    <tr><td>unified</td><td>0.6 &times; 10</td><td><b>6 GB</b></td></tr>
    <tr><td>&nbsp;&nbsp;&#8627; storage</td><td>0.5 &times; 6</td><td><b>3 GB</b></td></tr>
    <tr><td>&nbsp;&nbsp;&#8627; execution</td><td>6 &minus; 3</td><td><b>3 GB</b></td></tr>
    <tr><td>user + reserved</td><td>10 &minus; 6</td><td><b>4 GB</b></td></tr>
    <tr><td>&nbsp;&nbsp;&#8627; reserved</td><td>fixed constant</td><td><b>300 MB</b></td></tr>
    <tr><td>&nbsp;&nbsp;&#8627; user</td><td>4 GB &minus; 300 MB</td><td><b>3.7 GB</b></td></tr>
    <tr><td>overhead</td><td>max(384 MB, 10% of 10 GB)</td><td><b>1 GB</b></td></tr>
    <tr><td><b>container ask</b></td><td>10 + 1 + 0</td><td><b>11 GB</b></td></tr>
  </table>
  <p class="red">&#9888; The two people get wrong: 300 MB comes off the
     <u>user</u> slice, not the 6 GB; overhead is <u>added on top</u> of the
     10 GB. And Spark really subtracts the 300 MB <u>before</u> multiplying:
     0.6 &times; (10240 &minus; 300) = 5964 MB, not 6 GB &mdash; exact figures
     on the typed pages.</p>
</div>

<div class="hn def tight">
  <div class="hn-t">&#9997; Reading it backwards (the useful direction)</div>
  <ul>
    <li>node has <b>64 GB</b>, you want <b>4 executors</b> &rarr; 16 GB each
        <i>including</i> overhead</li>
    <li>overhead &asymp; 10% &rarr; solve
        <span class="cd">x + max(384, 0.1x) = 16</span> &rarr;
        <span class="cd">x &asymp; 14.5 GB</span>, so ask for
        <span class="cd">--executor-memory 14g</span></li>
    <li>that 14 GB buys you only <b>8.4 GB</b> of unified memory, and
        <b>4.2 GB</b> of execution space shared by every core on that executor</li>
    <li>5 cores per executor &rarr; roughly <b>840 MB</b> of execution memory per
        concurrent task. <span class="red">That</span> is the number that decides
        whether you spill.</li>
  </ul>
  <p class="tip">&#128161; Always divide execution memory by cores before
     claiming an executor is "big enough".</p>
</div>
"""

# A small sketch: what you type vs what the cluster manager hands out.
SKETCH = """
<div class="hn def tight wide1">
  <div class="hn-t">&#9997; What you type vs what you are charged for</div>
  <svg class="sk" width="100%" viewBox="0 0 900 112" preserveAspectRatio="xMinYMin meet">
    <text class="skt" x="2" y="22">you type</text>
    <rect x="2" y="30" width="196" height="26" fill="none" stroke="#1f4fb5" stroke-width="2"/>
    <text class="skt" x="12" y="48">--executor-memory 10G</text>
    <text class="skt" x="12" y="76">= the JVM heap,</text>
    <text class="skt" x="12" y="92">and nothing else</text>

    <path d="M206 42 C 228 42, 236 34, 246 30" fill="none" stroke="#d62828"
          stroke-width="2" stroke-linecap="round"/>
    <path d="M238 26 L249 29 L242 37" fill="none" stroke="#d62828"
          stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>

    <text class="skt" x="258" y="22" fill="#d62828">YARN / K8s actually reserves a 11 GB container</text>
    <rect x="258" y="28" width="470" height="78" fill="none" stroke="#d62828" stroke-width="2.4"/>

    <rect x="268" y="38" width="268" height="58" fill="none" stroke="#1f4fb5" stroke-width="2"/>
    <text class="skt" x="276" y="56">on-heap 10 GB</text>
    <text class="skt" x="276" y="73">5.8 unified &#183; 3.9 user</text>
    <text class="skt" x="276" y="89">&#183; 0.3 reserved</text>

    <rect x="548" y="38" width="170" height="58" fill="none" stroke="#2a9d5c" stroke-width="2"/>
    <text class="skt" x="556" y="56" fill="#2a9d5c">overhead 1 GB</text>
    <text class="skt" x="556" y="73" fill="#2a9d5c">off-heap would add</text>
    <text class="skt" x="556" y="89" fill="#2a9d5c">a third box here</text>

    <path d="M736 60 C 752 60, 758 54, 768 50" fill="none" stroke="#d62828"
          stroke-width="2" stroke-linecap="round"/>
    <path d="M760 46 L771 49 L764 57" fill="none" stroke="#d62828"
          stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
    <text class="skt" x="778" y="46" fill="#d62828">go past this line</text>
    <text class="skt" x="778" y="62" fill="#d62828">and the kernel kills</text>
    <text class="skt" x="778" y="78" fill="#d62828">the executor &#8212; you</text>
    <text class="skt" x="778" y="94" fill="#d62828">get no OOM trace</text>
  </svg>
</div>
"""


def page1_extra():
    """Goes under the annotated board on the landscape page."""
    return SKETCH


def page2():
    return FIVE_POOLS + CALC
