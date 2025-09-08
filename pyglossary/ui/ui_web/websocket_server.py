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

import json
import sys
import threading
from http.server import HTTPServer
from socketserver import ThreadingMixIn
from typing import TYPE_CHECKING, Any, Protocol

__all__ = [
	"CLOSE_STATUS_NORMAL",
	"DEFAULT_CLOSE_REASON",
	"FIN",
	"MASKED",
	"OPCODE",
	"OPCODE_BINARY",
	"OPCODE_CLOSE_CONN",
	"OPCODE_CONTINUATION",
	"OPCODE_PING",
	"OPCODE_PONG",
	"OPCODE_TEXT",
	"PAYLOAD_LEN",
	"PAYLOAD_LEN_EXT16",
	"PAYLOAD_LEN_EXT64",
	"HttpWebsocketServer",
]

if TYPE_CHECKING:
	import logging
	from collections.abc import Callable

	class ServerType(Protocol):
		def send_message_to_all(self, msg: str | dict) -> None: ...
		def shutdown(self) -> None: ...

	class HandlerType(Protocol):
		def send_pong(self, message: str | bytes) -> None: ...

		def send_close(
			self,
			status: int,
			reason: bytes,
		) -> None: ...

		def set_keep_alive(self, keep_alive: bool) -> None: ...

		def finish(self) -> None: ...


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
DEFAULT_CLOSE_REASON = b""


class API:
	def run_forever(self, threaded: bool = False) -> None:
		raise NotImplementedError

	def new_client(self, client: dict[str, Any], server: ServerType) -> None:
		pass

	def client_left(self, client: dict[str, Any], server: ServerType) -> None:
		pass

	def message_received(
		self,
		client: dict[str, Any],
		server: ServerType,
		message: str,
	) -> None:
		pass

	def set_fn_new_client(
		self,
		fn: Callable[[dict[str, Any], ServerType], None],
	) -> None:
		self.new_client = fn

	def set_fn_client_left(
		self,
		fn: Callable[[dict[str, Any], ServerType], None],
	) -> None:
		self.client_left = fn

	def set_fn_message_received(self, fn) -> None:  # noqa: ANN001
		self.message_received = fn

	def send_message(self, client: dict[str, Any], msg: str | bytes) -> None:
		self._unicast(client, msg)

	def send_message_to_all(self, msg: str | dict) -> None:
		if isinstance(msg, str):
			self._multicast(msg)
		else:
			self._multicast(json.dumps(msg))

	def deny_new_connections(
		self,
		status: int = CLOSE_STATUS_NORMAL,
		reason: int = DEFAULT_CLOSE_REASON,
	) -> None:
		self._deny_new_connections(status, reason)

	def allow_new_connections(self) -> None:
		self._allow_new_connections()

	def shutdown_gracefully(
		self,
		status: int = CLOSE_STATUS_NORMAL,
		reason: int = DEFAULT_CLOSE_REASON,
	) -> None:
		self._shutdown_gracefully(status, reason)

	def shutdown_abruptly(self) -> None:
		self._shutdown_abruptly()

	def disconnect_clients_gracefully(
		self,
		status: int = CLOSE_STATUS_NORMAL,
		reason: int = DEFAULT_CLOSE_REASON,
	) -> None:
		self._disconnect_clients_gracefully(status, reason)

	def disconnect_clients_abruptly(self) -> None:
		self._disconnect_clients_abruptly()


class HttpWebsocketServer(ThreadingMixIn, HTTPServer, API):
	"""
	A websocket server waiting for clients to connect.

	Args:
		port(int): Port to bind to
		host(str): Hostname or IP to listen for connections. By default 127.0.0.1
			is being used. To accept connections from any client, you should use
			0.0.0.0.
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
		handlerClass: type,
		logger: logging.Logger,
		host: str = "127.0.0.1",
		port: int = 0,
	) -> None:
		# server's own logger
		HTTPServer.__init__(self, (host, port), handlerClass)
		self.host = host
		self.port = self.socket.getsockname()[1]

		self.clients = []
		self.id_counter = 0
		self.thread = None
		self.headers = None
		self.ui_controller = None
		self.logger = logger
		self._deny_clients = False

	@property
	def url(self) -> str:
		return f"http://{self.host}:{self.port}/"

	def info(self, *args, **kwargs) -> None:  # noqa: ANN002
		self.logger.info(*args, **kwargs)

	def error(self, *args, **kwargs) -> None:  # noqa: ANN002
		self.logger.error(*args, **kwargs)

	def exception(self, *args, **kwargs) -> None:  # noqa: ANN002
		self.logger.error(*args, **kwargs)

	def run_forever(self, threaded: bool = False) -> None:
		cls_name = self.__class__.__name__
		try:
			self.info(f"Listening on http://{self.host}:{self.port}/")
			if threaded:
				self.daemon = True
				self.thread = threading.Thread(
					target=super().serve_forever,
					daemon=True,
				)
				self.info(f"Starting {cls_name} on thread {self.thread.getName()}.")
				self.thread.start()
			else:
				self.thread = threading.current_thread()
				self.info(f"Starting {cls_name} on main thread.")
				super().serve_forever()
		except KeyboardInterrupt:
			self.server_close()
			self.info("Server terminated.")
		except Exception as e:
			self.exception(str(e), exc_info=True)
			sys.exit(1)

	def message_received_handler(self, handler: HandlerType, msg: str) -> None:
		self.message_received(self.handler_to_client(handler), self, msg)

	def ping_received_handler(self, handler: HandlerType, msg: str) -> None:
		handler.send_pong(msg)

	def pong_received_handler(self, handler: HandlerType, msg: str) -> None:
		pass

	def new_client_handler(self, handler: HandlerType) -> None:
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

	def client_left_handler(self, handler: HandlerType) -> None:
		client = self.handler_to_client(handler)
		if not client:
			self.logger.warning("client handler was not found")
			return
		self.client_left(client, self)
		if client in self.clients:
			self.clients.remove(client)

	def _unicast(self, receiver_client: dict[str, Any], msg: str | bytes) -> None:
		receiver_client["handler"].send_message(msg)

	def _multicast(self, msg: str | bytes) -> None:
		for client in self.clients:
			try:
				self._unicast(client, msg)
			except Exception as e:
				print(str(e))

	def handler_to_client(self, handler: HandlerType) -> dict[str, Any] | None:
		for client in self.clients:
			if client["handler"] == handler:
				return client
		return None

	def _terminate_client_handler(self, handler: HandlerType) -> None:
		handler.set_keep_alive(False)
		handler.finish()

	def _terminate_client_handlers(self) -> None:
		"""Ensures request handler for each client is terminated correctly."""
		for client in self.clients:
			self._terminate_client_handler(client["handler"])

	def _shutdown_gracefully(
		self,
		status: int = CLOSE_STATUS_NORMAL,
		reason: bytes = DEFAULT_CLOSE_REASON,
	) -> None:
		"""Send a CLOSE handshake to all connected clients before terminating server."""
		self.keep_alive = False
		self._disconnect_clients_gracefully(status, reason)
		self.server_close()
		self.shutdown()

	def _shutdown_abruptly(self) -> None:
		"""Terminate server without sending a CLOSE handshake."""
		self.keep_alive = False
		self._disconnect_clients_abruptly()
		self.server_close()
		self.shutdown()

	def _disconnect_clients_gracefully(
		self,
		status: int = CLOSE_STATUS_NORMAL,
		reason: bytes = DEFAULT_CLOSE_REASON,
	) -> None:
		"""Terminate clients gracefully without shutting down the server."""
		for client in self.clients:
			client["handler"].send_close(status, reason)
		self._terminate_client_handlers()

	def _disconnect_clients_abruptly(self) -> None:
		"""
		Terminate clients abruptly
		(no CLOSE handshake) without shutting down the server.
		"""
		self._terminate_client_handlers()

	def _deny_new_connections(
		self,
		status: int,
		reason: bytes,
	) -> None:
		self._deny_clients = {
			"status": status,
			"reason": reason,
		}

	def _allow_new_connections(self) -> None:
		self._deny_clients = False
