# Rich Sample
wudict: 1
from: en
to: en
author: Test Author
license: CC0-1.0
meta: custom meta value
x-custom-key: custom value

<p>A <strong>rich</strong> synthetic sample for PyGlossary tests, with a <a href="https://example.com">link</a>.</p>

## apple
## Apfel
## redirect
## redirect-alias

<p>An <strong>apple</strong> is a <em>fruit</em>.</p>

## banana

<div>
<p>A yellow fruit.</p>
<!-- a comment -->
</div>

## cherry

<p>A red fruit with a <a href="https://example.com/cherry" title="Cherry page">link</a> and an image <img src="images/cherry.png" alt="cherry" title="Cherry" />.</p>

## date
## Dattel

<p>A sweet fruit with <code>code</code> and <kbd>Ctrl</kbd>+<kbd>C</kbd>.</p>

## bold name
## bold alias

<p>A headword with markup.</p>

## redirect-missing

<p><a href="entry://nowhere">nowhere</a></p>

## html-block

<div>
## swallowed
</div>

## lists

<div>
<ul>
<li>one</li>
<li>two
<ul>
<li>nested</li>
</ul>
</li>
</ul>
<ol>
<li>first</li>
<li>second</li>
</ol>
</div>

## table

<table>
<thead>
<tr>
<th style="text-align:left">left</th>
<th style="text-align:center">center</th>
<th style="text-align:right">right</th>
</tr>
</thead>
<tbody>
<tr>
<td style="text-align:left">a</td>
<td style="text-align:center">b</td>
<td style="text-align:right">c</td>
</tr>
<tr>
<td style="text-align:left">1</td>
<td style="text-align:center">2</td>
<td style="text-align:right">3</td>
</tr>
</tbody>
</table>

## code

<div>
<pre><code class="language-python">print(&quot;hello&quot;)
</code></pre>
<p>Text with a hard break<br />
and a soft
break.</p>
</div>

## quote

<blockquote>
<p>A quote</p>
<p>with two paragraphs.</p>
</blockquote>

## details

<details>
<summary>More</summary>
<p>Hidden <strong>text</strong>.</p>
</details>

## media

<div>
<p><img src="images/icon.png" alt="icon" /></p>
<p><audio controls src="audio/sound.mp3"></audio></p>
<p><video src="video/clip.mp4"></video></p>
</div>
