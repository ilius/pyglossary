import json
import logging
import webbrowser

from pyglossary.glossary_v2 import ConvertArgs, Glossary
from pyglossary.ui.base import UIBase
from pyglossary.ui.ui_web.server_ws_http import create_server

log = logging.getLogger("pyglossary")
HOST = "127.0.0.1"
PORT = 1984


class WebUI(UIBase):
	def __init__(self, progressbar: bool = True) -> None:
		UIBase.__init__(self)
		self._toPause = False
		self._resetLogFormatter = None
		self._progressbar = progressbar
		self.server = None

	def progressInit(self, title: str) -> None:
		self.server.send_message_to_all(
			json.dumps({"type": "progress", "text": title or "", "ratio": 0})
		)

	def progress(self, ratio: float, text=None) -> None:
		if not text:
			text = f"{int(ratio * 100)!s}%"

		self.server.send_message_to_all(
			json.dumps({"type": "progress", "text": text, "ratio": ratio})
		)

	def run(  # noqa: PLR0912, PLR0913
		self,
		inputFilename: str,  # noqa: ARG002
		outputFilename: str,  # noqa: ARG002
		inputFormat: str,  # noqa: ARG002
		outputFormat: str,  # noqa: ARG002
		reverse: bool = False,  # noqa: ARG002
		config: "dict | None" = None,
		readOptions: "dict | None" = None,
		writeOptions: "dict | None" = None,
		convertOptions: "dict | None" = None,
		glossarySetAttrs: "dict | None" = None,
	) -> bool:
		self.config = config or {}
		self.readOptions = readOptions or {}
		self.writeOptions = writeOptions or {}
		self.convertOptions = convertOptions or {}
		self.glossarySetAttrs = glossarySetAttrs or {}

		try:
			self.server = create_server(host=HOST, port=PORT, user_logger=log)
			self.server.ui_controller = self
			url = self.server.url
			log.info(url)
			webbrowser.open(url)
			self.server.run_forever()
		except OSError as e:
			if "Address already in use" in str(e):
				print(f"Server already running:\n{e!s}\n Use Menu -> Exit to stop")
				webbrowser.open(f"http://{HOST}:{PORT}/")
				return False
			raise e from None

		return True

	def start_convert_job(self, payload) -> bool:
		glos = Glossary(ui=self)

		self.inputFilename = payload.get("inputFilename")
		self.inputFormat = payload.get("inputFormat")
		self.outputFilename = payload.get("outputFilename")
		self.outputFormat = payload.get("outputFormat")
		self.readOptions = payload.get("readOptions") or self.readOptions
		self.writeOptions = payload.get("writeOptions") or self.writeOptions
		self.convertOptions = payload.get("convertOptions") or self.convertOptions

		log.debug(f"readOptions: {self.readOptions}")
		log.debug(f"writeOptions: {self.writeOptions}")
		log.debug(f"convertOptions: {self.convertOptions}")
		log.debug(f"config: {self.config}")

		glos.config = self.config

		for attr, value in self.glossarySetAttrs.items():
			setattr(glos, attr, value)

		try:
			finalOutputFile = glos.convert(
				ConvertArgs(
					inputFilename=self.inputFilename,
					inputFormat=self.inputFormat,
					outputFilename=self.outputFilename,
					outputFormat=self.outputFormat,
					readOptions=self.readOptions,
					writeOptions=self.writeOptions,
					**self.convertOptions,
				),
			)
		except Exception as e:
			log.critical(str(e))
			glos.cleanup()
			return False

		log.info("Convert finished")
		return bool(finalOutputFile)
