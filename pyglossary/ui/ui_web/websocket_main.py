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

import base64
import json
import logging
import os.path
from pathlib import Path

from pyglossary.glossary_types import EntryType
from pyglossary.glossary_v2 import Glossary
from pyglossary.ui.ui_web.weblog import WebLogHandler
from pyglossary.ui.ui_web.websocket_handler import HTTPWebSocketHandler
from pyglossary.ui.ui_web.websocket_server import HttpWebsocketServer

MAX_IMAGE_SIZE = 512000
DEFAULT_MAX_BROWSE_ENTRIES = 42


log = logging.getLogger("pyglossary.web.server")
log.setLevel(logging.DEBUG)

"""
Custom endpoints:
- ws://localhost:1984/ws : 2-way client-server communication
- GET /config            : Returns plugins metadata as JSON
- POST /convert          : Starts a conversion job; takes JSON with paths + formats
"""

#  ======================= IMPLEMENTATION SECTION =========================


def new_client(client, server):
	client_id = client.get("id", "n/a")
	print(f"New client connected and was given id {client_id}")
	server.send_message_to_all(
		{"type": "info", "text": f"ws: client id 🔗: {client_id}"}
	)


# Called on client disconnecting
def client_left(client, server):
	log.info(f'{server}: Client({(client and client.get("id")) or -1}) disconnected')


# Callback invoked when client sends a message
def message_received(client, server, message):
	if message == "ping":
		print(f"Client({client.get('id')}) said: {message}")
		server.send_message_to_all({"type": "info", "text": "ws: pong ✔️"})

	elif "browse" in message:
		try:
			handle_browse_request(client, server, message)
		except Exception as e:
			log.error(f"{e!s} handling client message {client}")

	elif message == "exit":
		try:
			server.send_message_to_all(
				{"type": "info", "text": "\n\nws: shutdown request received ✔️"}
			)
			server.shutdown()
		except Exception as e:
			log.warning(str(e))


def browse_check_entry(entry: EntryType, wordQuery: str) -> str | None:
	# get first max entries if no word or filter until max results
	if wordQuery and not entry.s_word.lower().startswith(wordQuery.lower()):
		return None
	html_entry = None
	if entry.defiFormat in {"h", "m", "x"}:
		return f"""<dt>{entry.s_word}</dt><dd>{entry.defi}</dd>"""

	html_entry = f"&#128206;<pre>{entry.s_word} ({entry.size()})</pre>"
	if (
		entry.isData()
		and entry.size() < MAX_IMAGE_SIZE
		and entry.s_word.lower().endswith((".jpg", "jpeg", ".png"))
	):
		extension = Path(entry.s_word).suffix[1:]
		html_entry += f"""
		<img class="data"
		src="data:image/{extension};base64,{base64.b64encode(entry.data).decode('utf-8')}"
		alt="{entry.s_word}"/>
		"""
	return html_entry


def handle_browse_request(client, server, message):
	log.debug(f"processing client #{client} message")
	params = json.loads(message)
	wordQuery = params.get("word")
	glossary_path = params.get("path")
	glossary_format = params.get("format")
	max_results = int(params.get("max", DEFAULT_MAX_BROWSE_ENTRIES))

	if not glossary_path or not os.path.exists(glossary_path):
		log.error(f"invalid PATH: '{glossary_path}'")
		server.send_message_to_all(
			{"type": "browse", "error": f"invalid path: '{glossary_path}'"}
		)
		return

	glos_path = Path(glossary_path).expanduser().resolve()

	# add parent folder as a browse root to allow resolution of
	# .css/.js/.jpg resources for .mdx files
	HTTPWebSocketHandler.add_browse_root(str(glos_path.parent))

	glos = Glossary(ui=None)

	if not glos.directRead(glossary_path, formatName=glossary_format):
		server.send_message_to_all(
			{
				"type": "browse",
				"error": f"Error reading {glossary_path} with format {glossary_format}",
			}
		)

	num_results = 0
	for entry in glos:
		html_entry = browse_check_entry(entry, wordQuery)
		if not html_entry:
			continue
		num_results += 1
		try:
			server.send_message_to_all(
				{
					"type": "browse",
					"data": html_entry,
					"num": num_results,
					"max": max_results,
				}
			)
		except Exception as e:
			server.send_message_to_all(
				{"type": "browse", "error": f"exception: '{e!s}'"}
			)
		finally:
			server.send_message_to_all(
				{
					"type": "browse",
					"data": f"<hr>Total: {num_results}",
					"num": num_results,
					"max": max_results,
				}
			)
		if num_results >= max_results:
			break


def create_server(host: str, port: int):
	server = HttpWebsocketServer(
		HTTPWebSocketHandler,
		log,
		host=host,
		port=port,
	)
	log.addHandler(WebLogHandler(server))
	server.set_fn_new_client(new_client)
	server.set_fn_client_left(client_left)
	server.set_fn_message_received(message_received)
	return server
