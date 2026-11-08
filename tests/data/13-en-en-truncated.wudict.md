# Rich Sample
wudict: 1
from: en-US
to: en
author: Test Author
license: CC0-1.0
meta: custom meta value
x-custom-key: custom value

A **rich** synthetic sample for PyGlossary tests, with a [link](https://example.com).

## apple
## Apfel

An **apple** is a *fruit*.

## banana

A yellow fruit.
<!-- a comment -->

## cherry

A red fruit with a [link](https://example.com/cherry "Cherry page") and an image ![cherry](images/cherry.png "Cherry").

## date
## Dattel

A sweet fruit with `code` and <kbd>Ctrl</kbd>+<kbd>C</kbd>.

## bold name
## **bold** alias

A headword with markup.

## redirect
see: APPLE

## redirect-alias
see: Apfel

## redirect-missing
see: nowhere

## html-block

<div>
## swallowed
</div>

## lists

- one
- two
  - nested

1. first
2. second

## table

| left | center | right |
| :--- | :----: | ----: |
| a | b | c |
| 1 | 2 | 3 |

## code

```python
print("hello")
```

Text with a hard break  
and a soft
break.

## quote

> A quote
>
> with two paragraphs.

## details

<details>
<summary>More</summary>

Hidden **text**.

</details>

## media

![icon](images/icon.png)

<audio controls src="audio/sound.mp3"></audio>

<video src="video/clip.mp4"></video>

## empty-heading-group
## another-empty
Ã