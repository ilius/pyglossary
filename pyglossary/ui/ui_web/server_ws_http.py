"""
Hybrid server implementing HTTP and WebSocket on the same port.
Based on HTTPServer, SimpleHTTPRequestHandler.

Customized version of `python-websocket-server`:
- Original repository: https://github.com/Pithikos/python-websocket-server
- Author: Johan Hanssen Seferidis
- License: MIT
The MIT License (MIT)

Copyright (c) 2018 Johan Hanssen Seferidis

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

---

MODIFICATIONS
=============

Add custom endpoints:
- ws://localhost:1984/ws : 2-way client-server communication
- GET /config            : Returns plugins metadata as JSON
- POST /convert          : Starts a conversion job; takes JSON with paths + formats

Web root:
- `pyglossary/ui/ui_web`

Entry point:
- `pyglossary/ui/ui_web/index.html`

Author of this customized version:
- GitHub: @glowinthedark
- Website: https://legbehindneck.com
"""

import errno
import json
import logging
import struct
import sys
import threading
import traceback
from base64 import b64encode
from hashlib import sha1
from http import HTTPStatus
from http.server import HTTPServer, SimpleHTTPRequestHandler
from socketserver import ThreadingMixIn

from pyglossary.glossary_v2 import Glossary

serverlog = logging.getLogger(__name__)
logging.basicConfig()

"""
+-+-+-+-+-------+-+-------------+-------------------------------+
 0				   1				   2				   3
 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
+-+-+-+-+-------+-+-------------+-------------------------------+
|F|R|R|R| opcode|M| Payload len |	Extended payload length	|
|I|S|S|S|  (4)  |A|	 (7)	 |			 (16/64)		   |
|N|V|V|V|	   |S|			 |   (if payload len==126/127)   |
| |1|2|3|	   |K|			 |							   |
+-+-+-+-+-------+-+-------------+ - - - - - - - - - - - - - - - +
|	 Extended payload length continued, if payload len == 127  |
+ - - - - - - - - - - - - - - - +-------------------------------+
|					 Payload Data continued ...				|
+---------------------------------------------------------------+
"""

FIN = 0x80
OPCODE = 0x0F
MASKED = 0x80
PAYLOAD_LEN = 0x7F
PAYLOAD_LEN_EXT16 = 0x7E
PAYLOAD_LEN_EXT64 = 0x7F

OPCODE_CONTINUATION = 0x0
OPCODE_TEXT = 0x1
OPCODE_BINARY = 0x2
OPCODE_CLOSE_CONN = 0x8
OPCODE_PING = 0x9
OPCODE_PONG = 0xA

CLOSE_STATUS_NORMAL = 1000
DEFAULT_CLOSE_REASON = bytes("", encoding="utf-8")


class WebLogHandler(logging.Handler):
	def __init__(self, server) -> None:
		logging.Handler.__init__(self)
		self.srv = server

	def emit(self, record: logging.LogRecord):
		msg = ""
		if record.getMessage():
			msg = self.format(record)
		msg = msg.replace("\x00", "")

		if record.exc_info:
			_type, value, tback = record.exc_info
			tback_text = "".join(
				traceback.format_exception(_type, value, tback),
			)
			if msg:
				msg += "\n"
			msg += tback_text

		self.srv.send_message_to_all({"type": "info", "text": msg})


class API:
	def run_forever(self, threaded=False):
		return self._run_forever(threaded)

	def new_client(self, client, server):
		pass

	def client_left(self, client, server):
		pass

	def message_received(self, client, server, message):
		pass

	def set_fn_new_client(self, fn):
		self.new_client = fn

	def set_fn_client_left(self, fn):
		self.client_left = fn

	def set_fn_message_received(self, fn):
		self.message_received = fn

	def send_message(self, client, msg):
		self._unicast(client, msg)

	def send_message_to_all(self, msg):
		if isinstance(msg, str):
			self._multicast(msg)
		else:
			self._multicast(json.dumps(msg))

	def deny_new_connections(
		self, status=CLOSE_STATUS_NORMAL, reason=DEFAULT_CLOSE_REASON
	):
		self._deny_new_connections(status, reason)

	def allow_new_connections(self):
		self._allow_new_connections()

	def shutdown_gracefully(
		self, status=CLOSE_STATUS_NORMAL, reason=DEFAULT_CLOSE_REASON
	):
		self._shutdown_gracefully(status, reason)

	def shutdown_abruptly(self):
		self._shutdown_abruptly()

	def disconnect_clients_gracefully(
		self, status=CLOSE_STATUS_NORMAL, reason=DEFAULT_CLOSE_REASON
	):
		self._disconnect_clients_gracefully(status, reason)

	def disconnect_clients_abruptly(self):
		self._disconnect_clients_abruptly()


class HttpWebsocketServer(ThreadingMixIn, HTTPServer, API, logging.Handler):

	"""
		A websocket server waiting for clients to connect.

	Args:
		port(int): Port to bind to
		host(str): Hostname or IP to listen for connections. By default 127.0.0.1
			is being used. To accept connections from any client, you should use
			0.0.0.0.
		user_logger: custom logger used a callback for web client messages
		loglevel: Logging level from logging module to use for logging. By default
			warnings and errors are being logged.

	Properties:
		clients(list): A list of connected clients. A client is a dictionary
			like below.
				{
				'id'	  : id,
				'handler' : handler,
				'address' : (addr, port)
				}

	"""

	allow_reuse_address = True
	daemon_threads = True  # comment to keep threads alive until finished

	def __init__(
		self,
		host="127.0.0.1",
		port=0,
		user_logger=None,
		loglevel=logging.DEBUG,
	):
		# server's own logger
		HTTPServer.__init__(self, (host, port), HTTPWebSocketHandler)
		self.host = host
		self.port = self.socket.getsockname()[1]

		self.clients = []
		self.id_counter = 0
		self.thread = None
		self.headers = None
		self.ui_controller = None

		self._deny_clients = False
		# the logger that is echoed to the web client
		self.user_logger = user_logger
		self.user_logger.addHandler(WebLogHandler(self))
		self.level = loglevel
		serverlog.setLevel(loglevel)
		self.user_logger.setLevel(loglevel)

	@property
	def url(self) -> str:
		return f"http://{self.host}:{self.port}/"

	def _run_forever(self, threaded):
		cls_name = self.__class__.__name__
		try:
			serverlog.info(f"Listening on http://{self.host}/{self.port}/")
			if threaded:
				self.daemon = True
				self.thread = threading.Thread(
					target=super().serve_forever, daemon=True, logger=serverlog
				)
				serverlog.info(
					f"Starting {cls_name} on thread {self.thread.getName()}."
				)
				self.thread.start()
			else:
				self.thread = threading.current_thread()
				serverlog.info(f"Starting {cls_name} on main thread.")
				super().serve_forever()
		except KeyboardInterrupt:
			self.server_close()
			serverlog.info("Server terminated.")
		except Exception as e:
			serverlog.error(str(e), exc_info=True)
			sys.exit(1)

	def _message_received_(self, handler, msg):
		self.message_received(self.handler_to_client(handler), self, msg)

	def _ping_received_(self, handler, msg):
		handler.send_pong(msg)

	def _pong_received_(self, handler, msg):
		pass

	def _new_client_(self, handler):
		if self._deny_clients:
			status = self._deny_clients["status"]
			reason = self._deny_clients["reason"]
			handler.send_close(status, reason)
			self._terminate_client_handler(handler)
			return

		self.id_counter += 1
		client = {
			"id": self.id_counter,
			"handler": handler,
			"address": handler.client_address,
		}
		self.clients.append(client)
		self.new_client(client, self)

	def _client_left_(self, handler):
		client = self.handler_to_client(handler)
		self.client_left(client, self)
		if client in self.clients:
			self.clients.remove(client)

	def _unicast(self, receiver_client, msg):
		receiver_client["handler"].send_message(msg)

	def _multicast(self, msg):
		for client in self.clients:
			try:
				self._unicast(client, msg)
			except Exception as e:
				print(str(e))

	def handler_to_client(self, handler):
		for client in self.clients:
			if client["handler"] == handler:
				return client
		return None

	def _terminate_client_handler(self, handler):
		handler.keep_alive = False
		handler.finish()
		handler.connection.close()

	def _terminate_client_handlers(self):
		"""Ensures request handler for each client is terminated correctly."""
		for client in self.clients:
			self._terminate_client_handler(client["handler"])

	def _shutdown_gracefully(
		self, status=CLOSE_STATUS_NORMAL, reason=DEFAULT_CLOSE_REASON
	):
		"""Send a CLOSE handshake to all connected clients before terminating server."""
		self.keep_alive = False
		self._disconnect_clients_gracefully(status, reason)
		self.server_close()
		self.shutdown()

	def _shutdown_abruptly(self):
		"""Terminate server without sending a CLOSE handshake."""
		self.keep_alive = False
		self._disconnect_clients_abruptly()
		self.server_close()
		self.shutdown()

	def _disconnect_clients_gracefully(
		self, status=CLOSE_STATUS_NORMAL, reason=DEFAULT_CLOSE_REASON
	):
		"""Terminate clients gracefully without shutting down the server."""
		for client in self.clients:
			client["handler"].send_close(status, reason)
		self._terminate_client_handlers()

	def _disconnect_clients_abruptly(self):
		"""
		Terminate clients abruptly
		(no CLOSE handshake) without shutting down the server.
		"""
		self._terminate_client_handlers()

	def _deny_new_connections(self, status, reason):
		self._deny_clients = {
			"status": status,
			"reason": reason,
		}

	def _allow_new_connections(self):
		self._deny_clients = False


class HTTPWebSocketHandler(SimpleHTTPRequestHandler):
	def __init__(self, socket, addr, server: HttpWebsocketServer, *args, **kwargs):
		self.server: HttpWebsocketServer = server
		assert not hasattr(self, "_send_lock"), "_send_lock already exists"
		self._send_lock = threading.Lock()

		super().__init__(
			socket, addr, server, *args, **kwargs, directory="pyglossary/ui/ui_web"
		)

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
		else:
			self.send_response(HTTPStatus.BAD_REQUEST)
			self.send_header("Content-Type", "application/json")
			self.end_headers()
			self.wfile.write(
				json.dumps({"value": f"{self.path}: POST unsupported"}).encode()
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
			content_length = int(self.headers.get("Content-Length", 0))

			post_data = self.rfile.read(content_length)

			try:
				payload = json.loads(post_data)
				serverlog.debug(f"Handle convert request from {self.client_address[0]}")
				serverlog.debug(f"POST PAYLOAD {payload}")
			except json.JSONDecodeError:
				self.send_response(HTTPStatus.BAD_REQUEST)
				self.send_header("Content-type", "application/json")
				self.end_headers()
				self.wfile.write(b"Invalid JSON data.")
				return

			required_fields = [
				"inputFilename",
				"inputFormat",
				"outputFilename",
				"outputFormat",
			]
			missing_fields = [
				field for field in required_fields if not payload.get(field)
			]

			if missing_fields:
				self.send_response(HTTPStatus.BAD_REQUEST)
				self.send_header("Content-type", "application/json")
				self.end_headers()
				error_message = {
					"error": "Missing or empty fields",
					"missing_fields": missing_fields,
				}
				self.wfile.write(json.dumps(error_message).encode())
				return

			self.server.ui_controller.start_convert_job(payload)

			self.send_response(HTTPStatus.OK)
			self.send_header("Content-type", "text/html")
			self.end_headers()
			self.wfile.write(b"POST request received and JSON data stored.")

		except Exception as e:
			# Step 8: Handle any unexpected errors
			serverlog.error(e)
			self.send_response(
				HTTPStatus.INTERNAL_SERVER_ERROR
			)  # Internal Server Error
			self.send_header("Content-type", "text/html")
			self.end_headers()
			self.wfile.write(f"Error: {e!s}".encode())

	def handle_one_request(self):
		"""
		Handle a single HTTP request.

		You normally don't need to override this method; see the class
		__doc__ string for information on how to handle specific HTTP
		commands such as GET and POST.

		"""
		try:
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
			if (
				self.path.startswith("/ws")
				and self.headers.get("upgrade") == "websocket"
			):
				self.handle_ws()
			else:
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
		except TimeoutError as e:
			# a read or a write timed out.  Discard this connection
			self.log_error("Request timed out: %r", e)
			self.close_connection = True
			return

	def read_bytes(self, num):
		return self.rfile.read(num)

	def read_next_message(self):
		try:
			b1, b2 = self.read_bytes(2)
		except OSError as e:  # to be replaced with ConnectionResetError for py3
			if e.errno == errno.ECONNRESET:
				serverlog.info("Client closed connection.")
				self.keep_alive = 0
				return
			b1, b2 = 0, 0
		except ValueError:
			b1, b2 = 0, 0

		opcode = b1 & OPCODE
		masked = b2 & MASKED
		payload_length = b2 & PAYLOAD_LEN

		if opcode == OPCODE_CLOSE_CONN:
			serverlog.info("Client asked to close connection.")
			self.keep_alive = 0
			return
		if not masked:
			serverlog.warning("Client must always be masked.")
			self.keep_alive = 0
			return
		if opcode == OPCODE_CONTINUATION:
			serverlog.warning("Continuation frames are not supported.")
			return
		if opcode == OPCODE_BINARY:
			serverlog.warning("Binary frames are not supported.")
			return
		if opcode == OPCODE_TEXT:
			opcode_handler = self.server._message_received_
		elif opcode == OPCODE_PING:
			opcode_handler = self.server._ping_received_
		elif opcode == OPCODE_PONG:
			opcode_handler = self.server._pong_received_
		else:
			serverlog.warning(f"Unknown opcode {opcode:#x}.")
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
				serverlog.warning("Can't send message, message is not valid UTF-8")
				return False
		elif not isinstance(message, str):
			serverlog.warning(
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
			serverlog.warning("Client tried to connect but was missing a key")
			self.keep_alive = False
			return

		response = self.make_handshake_response(key)
		with self._send_lock:
			self.handshake_done = self.request.send(response.encode())
		self.valid_client = True
		self.server._new_client_(self)

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
		self.server._client_left_(self)


def encode_to_UTF8(data):
	try:
		return data.encode("UTF-8")
	except UnicodeEncodeError as e:
		serverlog.error(f"Could not encode data to UTF-8 -- {e}")
		return False
	except Exception as e:
		raise (e)
		return False


def try_decode_UTF8(data):
	try:
		return data.decode("utf-8")
	except UnicodeDecodeError:
		return False
	except Exception as e:
		raise (e)


#  ======================= IMPLEMENTATION SECTION =========================


def new_client(client, server):
	client_id = client.get("id", "n/a")
	print(f"New client connected and was given id {client_id}")
	server.send_message_to_all(
		{"type": "info", "text": f"ws: client id 🔗: {client_id}"}
	)


# Called on client disconnecting
def client_left(client, server):
	serverlog.info(
		f'{server}: Client({(client and client.get("id")) or -1}) disconnected'
	)


# Callback invoked when client sends a message
def message_received(client, server, message):
	if message == "ping":
		print(f"Client({client.get('id')}) said: {message}")
		server.send_message_to_all({"type": "info", "text": "ws: pong ✔️"})
	elif message == "exit":
		try:
			server.send_message_to_all(
				{"type": "info", "text": "\n\nws: shutdown request received ✔️"}
			)
			server.shutdown()
		except Exception as e:
			serverlog.warning(str(e))


def create_server(host="127.0.0.1", port=9001, user_logger=None):
	server = HttpWebsocketServer(
		host=host, port=port, user_logger=user_logger, loglevel=logging.DEBUG
	)
	server.set_fn_new_client(new_client)
	server.set_fn_client_left(client_left)
	server.set_fn_message_received(message_received)
	return server
