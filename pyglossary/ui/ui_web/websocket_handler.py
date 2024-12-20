# Based on: https://github.com/Pithikos/python-websocket-server

# Copyright (c) 2024 Saeed Rasooli
# Copyright (c) 2024 https://github.com/glowinthedark (https://legbehindneck.com)
# Copyright (c) 2018 Johan Hanssen Seferidis

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

from __future__ import annotations

import errno
import json
import logging
import os
import posixpath
import struct
import threading
from base64 import b64encode
from hashlib import sha1
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler
from pathlib import Path
from typing import TYPE_CHECKING
from urllib.parse import unquote

from pyglossary.glossary_v2 import Glossary
from pyglossary.ui.ui_web.websocket_server import (
	CLOSE_STATUS_NORMAL,
	DEFAULT_CLOSE_REASON,
	FIN,
	MASKED,
	OPCODE,
	OPCODE_BINARY,
	OPCODE_CLOSE_CONN,
	OPCODE_CONTINUATION,
	OPCODE_PING,
	OPCODE_PONG,
	OPCODE_TEXT,
	PAYLOAD_LEN,
	PAYLOAD_LEN_EXT16,
	PAYLOAD_LEN_EXT64,
)

if TYPE_CHECKING:
	import socket as socketlib
	import socketserver
	from typing import Any


log = logging.getLogger("pyglossary.web.server")


class HTTPWebSocketHandler(SimpleHTTPRequestHandler):
	browse_roots = []

	@classmethod
	def add_browse_root(cls, path):
		"""Additional browse roots for css/js/etc resources."""
		cls.browse_roots.append(path)

	def __init__(
		self,
		socket: socketlib.socket,
		addr: tuple[str, int],  # (ip: str, port: int)
		server: socketserver.BaseServer,
		*args,
		**kwargs,
	):
		if hasattr(self, "_send_lock"):
			raise RuntimeError("_send_lock already exists")

		self._send_lock = threading.Lock()
		self.server = server

		webroot = str(Path(__file__).parent)
		self.browse_roots.append(webroot)

		super().__init__(
			socket,
			addr,
			server,
			*args,
			**kwargs,
			directory=webroot,
		)

	def translate_path(self, path):
		"""
		Overlay of https://github.com/python/cpython/blob/47c5a0f307cff3ed477528536e8de095c0752efa/Lib/http/server.py#L841
		patched to support multiple browse roots
		Translate a /-separated PATH to the local filename syntax.

		Components that mean special things to the local file system
		(e.g. drive or directory names) are ignored.  (XXX They should
		probably be diagnosed.)

		"""
		# abandon query parameters
		if self.command == "GET":
			path = path.split("?", 1)[0]
			path = path.split("#", 1)[0]
			# Handle explicit trailing slash when normalizing
			trailing_slash = path.rstrip().endswith("/")
			try:
				path = unquote(path, errors="surrogatepass")
			except UnicodeDecodeError:
				path = unquote(path)
			path = posixpath.normpath(path)
			# normpath already replaces // (or /// etc) with /
			pathParts = path.split("/")

			# Iterate through each browsing root to find a matching path
			for root in self.browse_roots:
				rootPath = os.path.join(root, *pathParts)

				# Normalize path and check if the file exists
				if os.path.exists(rootPath):
					if trailing_slash and os.path.isdir(rootPath):
						rootPath += "/"
					return rootPath

			# If no valid path found in any root, send 404
			self.send_error(HTTPStatus.NOT_FOUND, "Not found")
			return ""
		# fallback to super for other methods
		return super().translate_path(path)

	def do_GET(self):
		if self.path == "/config":
			self.send_config()
		else:
			super().do_GET()

	def send_config(self):
		self.send_response(HTTPStatus.OK)
		self.send_header("Content-Type", "application/json")
		self.end_headers()
		READ = 1  # 01
		WRITE = 2  # 10
		conversion_config = {
			name: {
				"desc": plug.description,
				"can": (READ * plug.canRead) | (WRITE * plug.canWrite),
				"ext": plug.ext,
			}
			for name, plug in Glossary.plugins.items()
		}
		self.wfile.write(json.dumps(conversion_config).encode())

	def do_POST(self):
		# custom ajax action for /convert POST
		if self.path == "/convert":
			self.handle_convert_job()
			return

		self.send_response(HTTPStatus.BAD_REQUEST)
		self.send_header("Content-Type", "application/json")
		self.end_headers()
		json.dump(
			{
				"value": f"{self.path}: POST unsupported",
			},
			self.wfile,
		)

	def setup(self):
		SimpleHTTPRequestHandler.setup(self)
		self.keep_alive = True
		self.handshake_done = False
		self.valid_client = False

	def handle(self):
		self.close_connection = True

		try:
			self.handle_one_request()
			while not self.close_connection:
				self.handle_one_request()
		except Exception as e:
			self.log_error(str(e))

	def handle_ws(self):
		while self.keep_alive:
			if not self.handshake_done:
				self.handshake()
			elif self.valid_client:
				self.read_next_message()

	def handle_convert_job(self):
		try:
			payload: dict[str, Any] = json.loads(
				self.rfile.read(int(self.headers.get("Content-Length", 0)))
			)
		except json.JSONDecodeError:
			self.json_decode_error()
			return
		except Exception as e:
			self.internal_exception(e)
			return

		log.debug(f"Handle convert request from {self.client_address[0]}")
		log.debug(f"POST PAYLOAD {payload}")

		try:
			self.server.ui_controller.start_convert_job(payload)
		except ValueError as e:
			self.validation_exception(e)
			return

		self.send_response(HTTPStatus.OK)
		self.send_header("Content-type", "text/html")
		self.end_headers()
		self.wfile.write(b"POST successful")

	def validation_exception(self, e: Exception) -> None:
		self.send_response(HTTPStatus.BAD_REQUEST)
		self.send_header("Content-type", "application/json")
		self.end_headers()
		json.dump({"error": str(e)}, self.wfile)

	def json_decode_error(self):
		self.send_response(HTTPStatus.BAD_REQUEST)
		self.send_header("Content-type", "application/json")
		self.end_headers()
		self.wfile.write(b"Invalid JSON data.")

	def internal_exception(self, e: Exception) -> None:
		log.error(e)
		self.send_response(HTTPStatus.INTERNAL_SERVER_ERROR)  # Internal Server Error
		self.send_header("Content-type", "text/html")
		self.end_headers()
		self.wfile.write(f"Error: {e!s}".encode())

	def _handle_one_request(self):
		self.raw_requestline = self.rfile.readline(65537)

		if len(self.raw_requestline) > 65536:
			self.requestline = ""
			self.request_version = ""
			self.command = ""
			self.send_error(HTTPStatus.REQUEST_URI_TOO_LONG)
			return
		if not self.raw_requestline:
			self.close_connection = True
			return
		if not self.parse_request():
			# An error code has been sent, just exit
			return
		if self.path.startswith("/ws") and self.headers.get("upgrade") == "websocket":
			self.handle_ws()
			return

		mname = "do_" + self.command
		if not hasattr(self, mname):
			self.send_error(
				HTTPStatus.NOT_IMPLEMENTED,
				f"Unsupported method ({self.command})",
			)
			return
		method = getattr(self, mname)
		method()
		self.wfile.flush()  # actually send the response if not already done.

	def handle_one_request(self):
		"""
		Handle a single HTTP/WS request.
		Override ootb method to delegate to WebSockets handler based
		on /ws path and presence of custom header: "upgrade: websocket".
		"""
		try:
			self._handle_one_request()
		except TimeoutError as e:
			# a read or a write timed out.  Discard this connection
			self.log_error("Request timed out: %r", e)
			self.close_connection = True

	def read_bytes(self, num):
		return self.rfile.read(num)

	def read_next_message(self):
		try:
			b1, b2 = self.read_bytes(2)
		except OSError as e:  # to be replaced with ConnectionResetError for py3
			if e.errno == errno.ECONNRESET:
				log.info("Client closed connection.")
				self.keep_alive = 0
				return
			b1, b2 = 0, 0
		except ValueError:
			b1, b2 = 0, 0

		opcode = b1 & OPCODE
		masked = b2 & MASKED
		payload_length = b2 & PAYLOAD_LEN

		if opcode == OPCODE_CLOSE_CONN:
			log.info("Client asked to close connection.")
			self.keep_alive = 0
			return
		if not masked:
			log.warning("Client must always be masked.")
			self.keep_alive = 0
			return
		if opcode == OPCODE_CONTINUATION:
			log.warning("Continuation frames are not supported.")
			return
		if opcode == OPCODE_BINARY:
			log.warning("Binary frames are not supported.")
			return
		if opcode == OPCODE_TEXT:
			opcode_handler = self.server.message_received_handler
		elif opcode == OPCODE_PING:
			opcode_handler = self.server.ping_received_handler
		elif opcode == OPCODE_PONG:
			opcode_handler = self.server.pong_received_handler
		else:
			log.warning(f"Unknown opcode {opcode:#x}.")
			self.keep_alive = 0
			return

		if payload_length == 126:
			payload_length = struct.unpack(">H", self.rfile.read(2))[0]
		elif payload_length == 127:
			payload_length = struct.unpack(">Q", self.rfile.read(8))[0]

		masks = self.read_bytes(4)
		message_bytes = bytearray()
		for message_byte in self.read_bytes(payload_length):
			message_byte ^= masks[len(message_bytes) % 4]  # noqa: PLW2901
			message_bytes.append(message_byte)
		opcode_handler(self, message_bytes.decode("utf8"))

	def send_message(self, message):
		self.send_text(message)

	def send_pong(self, message):
		self.send_text(message, OPCODE_PONG)

	def send_close(self, status=CLOSE_STATUS_NORMAL, reason=DEFAULT_CLOSE_REASON):
		"""
		Send CLOSE to client.

		Args:
			status: Status as defined in https://datatracker.ietf.org/doc/html/rfc6455#section-7.4.1
			reason: Text with reason of closing the connection

		"""
		if status < CLOSE_STATUS_NORMAL or status > 1015:
			raise Exception(f"CLOSE status must be between 1000 and 1015, got {status}")

		header = bytearray()
		payload = struct.pack("!H", status) + reason
		payload_length = len(payload)
		assert (
			payload_length <= 125
		), "We only support short closing reasons at the moment"

		# Send CLOSE with status & reason
		header.append(FIN | OPCODE_CLOSE_CONN)
		header.append(payload_length)
		with self._send_lock:
			try:
				self.request.send(header + payload)
			except Exception as e:
				self.log_error(f"ws: CLOSE not sent - client disconnected! {e!s}")

	def send_text(self, message, opcode=OPCODE_TEXT):
		"""
		Important: Fragmented(=continuation) messages are not supported since
		their usage cases are limited - when we don't know the payload length.
		"""
		# Validate message
		if isinstance(message, bytes):
			message = try_decode_UTF8(
				message
			)  # this is slower but ensures we have UTF-8
			if not message:
				log.warning("Can't send message, message is not valid UTF-8")
				return False
		elif not isinstance(message, str):
			log.warning(
				"Can't send message, message has to be a string or bytes. "
				f"Got {type(message)}"
			)
			return False

		header = bytearray()
		payload = encode_to_UTF8(message)
		payload_length = len(payload)

		# Normal payload
		if payload_length <= 125:
			header.append(FIN | opcode)
			header.append(payload_length)

		# Extended payload
		elif payload_length >= 126 and payload_length <= 65535:
			header.append(FIN | opcode)
			header.append(PAYLOAD_LEN_EXT16)
			header.extend(struct.pack(">H", payload_length))

		# Huge extended payload
		elif payload_length < 18446744073709551616:
			header.append(FIN | opcode)
			header.append(PAYLOAD_LEN_EXT64)
			header.extend(struct.pack(">Q", payload_length))

		else:
			raise Exception("Message is too big. Consider breaking it into chunks.")

		with self._send_lock:
			self.request.send(header + payload)  # type: ignore
			return None

	def handshake(self):
		try:
			key = self.headers.get("sec-websocket-key")
		except KeyError:
			log.warning("Client tried to connect but was missing a key")
			self.keep_alive = False
			return

		response = self.make_handshake_response(key)
		with self._send_lock:
			self.handshake_done = self.request.send(response.encode())
		self.valid_client = True
		self.server.new_client_handler(self)

	@classmethod
	def make_handshake_response(cls, key):
		return (
			"HTTP/1.1 101 Switching Protocols\r\n"
			"Upgrade: websocket\r\n"
			"Connection: Upgrade\r\n"
			f"Sec-WebSocket-Accept: {cls.calculate_response_key(key)}\r\n"
			"\r\n"
		)

	@classmethod
	def calculate_response_key(cls, key):
		seed = sha1(key.encode() + b"258EAFA5-E914-47DA-95CA-C5AB0DC85B11")
		response_key = b64encode(seed.digest()).strip()
		return response_key.decode("ASCII")

	def finish(self):
		self.server.client_left_handler(self)


def encode_to_UTF8(data: str) -> bytes:
	try:
		return data.encode("UTF-8")
	except UnicodeEncodeError as e:
		log.error(f"Could not encode data to UTF-8 -- {e}")
		return b""
	except Exception as e:
		raise e


def try_decode_UTF8(data: bytes) -> str | None:
	try:
		return data.decode("utf-8")
	except UnicodeDecodeError:
		return None
	except Exception as e:
		raise e
