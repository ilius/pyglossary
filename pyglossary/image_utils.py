import re
import base64
import logging
from os.path import join

from pyglossary.text_utils import crc32hex

log = logging.getLogger("pyglossary")

re_inline_image = re.compile('src="(data:image/[^<>"]*)"')


def extractInlineHtmlImages(
	defi: str,
	outDir: str,
	fnamePrefix: str = "",
) -> "Tuple[str, List[Tuple[str, str]]]":
	images = []  # type: List[Tuple[str, str]]

	def subFunc(m: "Match"):
		nonlocal images
		src = m.group(1)[len("data:image/"):]
		i = src.find(";")
		if i < 0:
			log.error(f"no semicolon, bad inline img src: {src[:60]}...")
			return
		imgFormat, src = src[:i], src[i + 1:]
		if not src.startswith("base64,"):
			log.error(f"no 'base64,', bad inline img src: {src[:60]}...")
			return
		imgDataB64 = src[len("base64,"):]
		imgData = base64.b64decode(imgDataB64)
		imgFname = f"{fnamePrefix}{crc32hex(imgData)}.{imgFormat}"
		imgPath = join(outDir, imgFname)
		with open(imgPath, 'wb') as _file:
			_file.write(imgData)
		images.append((imgFname, imgPath))
		return f'src="./{imgFname}"'

	defi = re_inline_image.sub(subFunc, defi)

	return defi, images
