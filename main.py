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

from param import get_enable_param, get_plugin_param
from concurrency import set_recent_tid, reset_recent_tid, get_recent_tid

from cost import increase_active_period, reset_active_period
from create_concurrency import create_background
from create import create
from debug import debug
from debug_simple import get_initial_error_info
from preview import preview
from format import format_output, prepare_sql, format_modification
from log import log

# -----------------------------------------------------------------------------
# Global State
# -----------------------------------------------------------------------------

sql_to_preview: Dict[str, Dict[str, str]] = {
    get_plugin_param()["cursor_identifier"]: {
        "modification": "",
        "preview": "",
    }
}

# -----------------------------------------------------------------------------
# Query Processing
# -----------------------------------------------------------------------------

async def main_inner(self, prepare_result: Dict[str, Any]) -> None:
    """
    Process SQL query through debug, create, and preview pipelines.
    
    Args:
        prepare_result: Result of SQL query preparation
    """
    global sql_to_preview
    if prepare_result["sql"] in sql_to_preview:
        print("exist", sql_to_preview)
        self.send_json_response({"modification": format_modification(sql_to_preview[prepare_result["sql"]]["modification"])})
        return

    try:
        set_recent_tid(prepare_result["priority"], prepare_result["sql"], "llm")
        
        if prepare_result["sql"] in sql_to_preview:
            return
        
        modification = await debug(prepare_result["sql"])
        
        if get_recent_tid("llm") == threading.get_ident():
            if modification is not None:
                print("debug", modification)
                self.send_json_response({"modification": format_modification(modification)})
            else:
                self.send_json_response({"error_info": get_initial_error_info()})
    finally:
        reset_recent_tid("llm")
    try:
        set_recent_tid(prepare_result["priority"], modification, "db")
        
        if prepare_result["sql"] in sql_to_preview:
            return
        
        rewrite = await create(modification)
        preview_result = await preview(rewrite)
    finally:
        reset_recent_tid("db")
    if preview_result is not None:
        sql_to_preview[prepare_result["sql"]] = {
            "modification": modification,
            "preview": preview_result,
        }
        reset_active_period()
    else:
        increase_active_period()
# -----------------------------------------------------------------------------
# HTTP Request Handler
# -----------------------------------------------------------------------------

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
            .replace("\r\n", "\n")
        )
        
        prepare_result = prepare_sql(input_sql)
        print("prepare_result", prepare_result)
        if prepare_result is not None:
            log("input.txt", prepare_result, is_dict=True)
            start_time = time.time()
            asyncio.run(main_inner(self, prepare_result))
            result = format_output(prepare_result, sql_to_preview)
            latency = f"{time.time() - start_time:.2f}"
            log("record.txt", {"latency": latency, "input": input_sql, "output": result}, is_dict=True)
        else:
            result = format_output(prepare_result, sql_to_preview)
        self.send_json_response(result)
            
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
        (plugin_params["ip_address"], plugin_params["port"]), 
        Handler
    )
    
    print(
        f"Server running on http://{plugin_params['ip_address']}:"
        f"{plugin_params['port']}"
    )

    if get_enable_param()["background_thread"]:
        threading.Thread(
            target=lambda: asyncio.run(create_background()), 
            daemon=True
        ).start()

    server.serve_forever()
# -----------------------------------------------------------------------------
# Main Entry Point
# -----------------------------------------------------------------------------

if __name__ == "__main__":
    SpeQL()
