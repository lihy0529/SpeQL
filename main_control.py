# Copyright (c) 2025 Haoyu Li
# Released under the MIT License.
# See LICENSE file in the project root for details.

#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Main module for SpeQL.

This module provides the main entry point for the SpeQL server.
It handles HTTP requests, processes SQL queries, and manages concurrency.
"""

import sys
import json
import asyncio
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Dict, Any
from pathlib import Path
import time

# -----------------------------------------------------------------------------
# Path Configuration
# -----------------------------------------------------------------------------

sys.path.extend([
    str(Path("src")),
    str(Path("util"))
])

# -----------------------------------------------------------------------------
# Local Imports
# -----------------------------------------------------------------------------

from db_api import get_cursor
from param import get_plugin_param
from concurrency import get_explain_cursor_lock
from preview import preview
from create_concurrency import cancel_running_query
from concurrency import set_recent_tid, reset_recent_tid
from log import log

class Handler(BaseHTTPRequestHandler):
    """Handles HTTP POST requests for SQL processing."""
    
    def do_POST(self) -> None:
        """Process POST request containing SQL query."""
        
        content_length = int(self.headers["Content-Length"])
        raw_data = self.rfile.read(content_length).decode("utf-8")
        assert get_plugin_param()["cursor_identifier"] in raw_data, "Attack detected"
        input_sql = (
            json.loads(raw_data)
            .get("content", "")
            .replace("\r\n", "\n").replace(get_plugin_param()["cursor_identifier"], "")
        )
        start_time = time.time()
        try:
            log("input.txt", {"input": input_sql}, is_dict=True)
            
            set_recent_tid(new_priority=2, new_running_sql=input_sql, type="db")
            cancel_running_query()
            with get_explain_cursor_lock():
                result = get_cursor()["explain"].execute(f"EXPLAIN {input_sql}")
            result = asyncio.run(preview(input_sql))
            self.send_json_response({"preview": result, "modification": input_sql, "complete": True, "show": True})
        
        except Exception as e:
            result = str(e)
            self.send_json_response({"preview": result, "modification": input_sql, "complete": True, "show": True})
        finally:
            reset_recent_tid("db")
        latency = f"{time.time() - start_time:.2f}"
        log("record.txt", {"latency": latency, "input": input_sql, "output": result}, is_dict=True)
            
    def send_json_response(self, data: Dict[str, Any]) -> None:
        """Send JSON response to client."""
        if not hasattr(self, 'headers_sent'):
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.send_header("Cache-Control", "no-cache")
            self.end_headers()
            self.headers_sent = True
        message = f"data: {json.dumps(data)}\n\n"
        self.wfile.write(message.encode("utf-8"))
        self.wfile.flush()

# -----------------------------------------------------------------------------
# Server Setup
# -----------------------------------------------------------------------------

def SpeQL() -> None:
    """Initialize and run the SpeQL server."""
    plugin_params = get_plugin_param()
    server = ThreadingHTTPServer(
        (plugin_params["ip_address"], plugin_params["port"] + 1), 
        Handler
    )
    
    print(
        f"Control group server running on http://{plugin_params['ip_address']}:"
        f"{plugin_params['port'] + 1}"
    )

    server.serve_forever()
# -----------------------------------------------------------------------------
# Main Entry Point
# -----------------------------------------------------------------------------

if __name__ == "__main__":
    SpeQL()
