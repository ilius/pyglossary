from __future__ import annotations

import json
import logging
import webbrowser
from pathlib import Path
from typing import Any

from pyglossary.glossary_v2 import ConvertArgs, Glossary
from pyglossary.ui.base import UIBase
from pyglossary.ui.ui_web.websocket_main import create_server

log = logging.getLogger("pyglossary.web")

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
		inputFilename: str,
		outputFilename: str,
		inputFormat: str,
		outputFormat: str,
		reverse: bool = False,
		config: dict[str, Any] | None = None,
		readOptions: dict[str, Any] | None = None,
		writeOptions: dict[str, Any] | None = None,
		convertOptions: dict[str, Any] | None = None,
		glossarySetAttrs: dict[str, Any] | None = None,
	) -> bool:
		if reverse:
			raise ValueError("reverse is not supported")
		self.inputFilename = inputFilename
		self.outputFilename = outputFilename
		self.inputFormat = inputFormat
		self.outputFormat = outputFormat
		self.config = config or {}
		self.readOptions = readOptions or {}
		self.writeOptions = writeOptions or {}
		self.convertOptions = convertOptions or {}
		self.glossarySetAttrs = glossarySetAttrs or {}

		try:
			self.server = create_server(host=HOST, port=PORT)
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

	def getPayloadStr(self, payload: dict[str, Any], name: str) -> str:
		value = payload.get(name)
		if value is None:
			return ""
		if not isinstance(value, str):
			raise ValueError(f"{name} must be string")
		return value

	def getPayloadDict(self, payload: dict[str, Any], name: str) -> dict:
		value = payload.get(name)
		if value is None:
			return {}
		if not isinstance(value, dict):
			raise ValueError(f"{name} must be a dict")
		return {}

	def start_convert_job(self, payload: dict[str, Any]) -> bool:
		glos = Glossary(ui=self)

		inputFilename = (
			self.getPayloadStr(payload, "inputFilename") or self.inputFilename
		)
		if not inputFilename:
			raise ValueError("inputFilename is missing")
		inputFormat = self.getPayloadStr(payload, "inputFormat") or self.inputFormat
		if not inputFormat:
			raise ValueError("inputFormat is missing")
		outputFilename = (
			self.getPayloadStr(payload, "outputFilename") or self.outputFilename
		)
		if not outputFilename:
			raise ValueError("outputFilename is missing")
		outputFormat = self.getPayloadStr(payload, "outputFormat") or self.outputFormat
		if not outputFormat:
			raise ValueError("outputFormat is missing")
		readOptions = self.getPayloadDict(payload, "readOptions") or self.readOptions
		writeOptions = self.getPayloadDict(payload, "writeOptions") or self.writeOptions
		convertOptions = (
			self.getPayloadDict(payload, "convertOptions") or self.convertOptions
		)

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
					# allow ~ in paths
					inputFilename=str(Path(inputFilename).expanduser().resolve()),
					inputFormat=inputFormat,
					outputFilename=str(Path(outputFilename).expanduser().resolve()),
					outputFormat=outputFormat,
					readOptions=readOptions,
					writeOptions=writeOptions,
					**convertOptions,
				),
			)
		except Exception as e:
			log.critical(str(e))
			glos.cleanup()
			return False

		log.info("Convert finished")
		return bool(finalOutputFile)
