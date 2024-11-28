from __future__ import annotations

import base64
import logging
import re
from os.path import join

from pyglossary.text_utils import crc32hex

__all__ = ["extractInlineHtmlImages"]

log = logging.getLogger("pyglossary")

re_inline_image = re.compile('src="(data:image/[^<>"]*)"')


def extractInlineHtmlImages(
	defi: str,
	outDir: str,
	fnamePrefix: str = "",
) -> tuple[str, list[tuple[str, str]]]:
	imageDataDict: dict[str, bytes] = {}

	def subFunc(m: re.Match[str]) -> str:
		src = m.group(1)[len("data:image/") :]
		i = src.find(";")
		if i < 0:
			log.error(f"no semicolon, bad inline img src: {src[:60]}...")
			return ""
		imgFormat, src = src[:i], src[i + 1 :]
		if not src.startswith("base64,"):
			log.error(f"no 'base64,', bad inline img src: {src[:60]}...")
			return ""
		imgDataB64 = src[len("base64,") :]
		imgData = base64.b64decode(imgDataB64)
		imgFname = f"{fnamePrefix}{crc32hex(imgData)}.{imgFormat}"
		imageDataDict[imgFname] = imgData
		return f'src="./{imgFname}"'

	defi = re_inline_image.sub(subFunc, defi)

	images: list[tuple[str, str]] = []
	for imgFname, imgData in imageDataDict.items():
		imgPath = join(outDir, imgFname)
		with open(imgPath, mode="wb") as _file:
			_file.write(imgData)
		del imgData
		images.append((imgFname, imgPath))

	return defi, images
