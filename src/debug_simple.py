# Copyright (c) 2025 Haoyu Li
# Released under the MIT License.
# See LICENSE file in the project root for details.

#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Debug Simple Module
===================

This module provides functionality for debugging SQL queries.
It uses the LLM to generate debug rules and apply them to the SQL query.
If it passes, SpeQL will not send it to debug_complex.
"""

import sys
import re
import json
import threading
import asyncio
from pathlib import Path

# -----------------------------------------------------------------------------
# Path Configuration
# -----------------------------------------------------------------------------

root_dir = str(Path(__file__).parent.parent)
sys.path.extend(
    [
        root_dir,
        str(Path(root_dir) / "src"),
        str(Path(root_dir) / "util"),
    ]
)

# -----------------------------------------------------------------------------
# Local Imports
# -----------------------------------------------------------------------------

from prompt import get_prompt
from schema import get_useful_schema
from debug_rule import set_rule, get_rule
from param import get_dialect_param, get_plugin_param, get_enable_param
from llm_api import get_llm_response
from concurrency import get_recent_tid, set_running_inference, get_explain_cursor_lock
from db_api import get_cursor
from vector_db import get_useful_historical_sql
from log import log
from cost import get_max_retry

# -----------------------------------------------------------------------------
# Global Variables
# -----------------------------------------------------------------------------

debug_simple_message = [{}]
error_info = None

# -----------------------------------------------------------------------------
# Error Info Passing
# -----------------------------------------------------------------------------


def set_error_info(new_error_info: str) -> None:
    """
    Sets the global error information.

    Args:
        new_error_info: New error message to store
    """
    global error_info
    error_info = new_error_info


def get_error_info() -> str:
    """
    Retrieves the current error information.

    Returns:
        str: Current error message
    """
    global error_info
    return error_info

def set_initial_error_info(new_initial_error_info: str) -> None:
    """
    Sets the initial error information.

    Args:
        new_initial_error_info: New initial error message to store
    """
    global initial_error_info
    initial_error_info = new_initial_error_info

def get_initial_error_info() -> str:
    """
    Retrieves the current initial error information.

    Returns:
        str: Current initial error message
    """
    global initial_error_info
    return initial_error_info


# -----------------------------------------------------------------------------
# Debug Message Management
# -----------------------------------------------------------------------------


def append_debug_simple_message(message: dict) -> None:
    """
    Appends a new message to the debug message history.

    Args:
        message: Message dictionary with 'role' and 'content' keys
    """
    global debug_simple_message
    debug_simple_message.append(message)
    
def clear_debug_simple_message() -> None:
    """
    Clears the debug message history.
    """
    global debug_simple_message
    debug_simple_message = [{}]


def get_debug_simple_message(sql: str) -> list:
    """
    Prepares and returns the debug message context for a given SQL query.

    Args:
        sql: The SQL query to debug

    Returns:
        list: List of message dictionaries forming the debug context
    """
    global debug_simple_message

    debug_simple_message[0] = {
        "role": "system",
        "content": get_prompt(
            "debug_simple",
            get_dialect_param()["input"],
            get_useful_historical_sql(sql),
            get_useful_schema(sql),
        ),
    }

    if debug_simple_message[-1]["role"] == "user":
        debug_simple_message.pop()

    while (
        len(str(debug_simple_message)) > get_plugin_param()["debug_simple_message_size"]
        and len(debug_simple_message) >= 3
    ):
        debug_simple_message.pop(1)
        debug_simple_message.pop(1)

    if len(debug_simple_message) > get_plugin_param()["debug_simple_message_count"] * 2 + 1:
        # Every debug simple iteration has 2 messages: 1 user and 1 assistant
        # The first message is system
        debug_simple_message.pop(1)
        debug_simple_message.pop(1)

    assert (
        len(debug_simple_message) <= get_plugin_param()["debug_simple_message_count"] * 2 + 1
    )

    debug_simple_message.append({"role": "user", "content": sql})

    return debug_simple_message


# -----------------------------------------------------------------------------
# Debug Simple
# -----------------------------------------------------------------------------


async def debug_simple_inner(
    sql: str, temp_debug_simple_message: list, debug_simple_iterator: int
) -> list:
    """
    Inner function to handle the debug message processing and rule generation.

    Args:
        sql: SQL query to debug
        temp_debug_simple_message: Temporary debug message context
        debug_simple_iterator: Current iteration count

    Returns:
        list: Generated debug rules
    """
    for _ in range(get_max_retry()):
        valid = True
        return_val = await get_llm_response(
            "simple", debug_simple_iterator, temp_debug_simple_message, 256
        )

        if "```json" not in return_val:
            temp_debug_simple_message.append(
                {
                    "role": "user",
                    "content": """
Please output the correct JSON format starting with ```json.
""",
                }
            )
            valid = False
            continue

        try:
            return_val = return_val[
                return_val.find("```json") + len("```json") : return_val.rfind("```")
            ]
            return_val = json.loads(return_val)

        except Exception as e:
            """
            JSON format error
            """
            temp_debug_simple_message.append(
                {
                    "role": "user",
                    "content": """
Please output the correct JSON format starting with ```json
and ending with ```.
""",
                }
            )
            valid = False
            continue

        for rule in return_val:
            if rule["old"] not in sql:
                rule_old = re.sub(r"\s+", r"\\s+", re.escape(rule["old"]))
                match = re.search(rule_old, sql)
                rule["old"] = match.group(0) if match is not None else rule["old"]

            cursor_id = get_plugin_param()["cursor_identifier"]
            if (cursor_id in rule["old"]) and (cursor_id not in rule["new"]):
                temp_debug_simple_message.append(
                    {
                        "role": "user",
                        "content": f"""
Error: {cursor_id} is in rule old: "{rule['old']}"
it should also be in rule new: "{rule['new']}",
please fix it.
""",
                    }
                )
                valid = False
                break

            if (cursor_id not in rule["old"]) and (cursor_id in rule["new"]):
                rule["new"] = rule["new"].replace(cursor_id, "")

            if sql.find(rule["old"]) != sql.rfind(rule["old"]):
                temp_debug_simple_message.append(
                    {
                        "role": "user",
                        "content": f"""
Error: rule old: "{rule['old']}" should be unique,
your output appears more than once, please fix it.
""",
                    }
                )
                valid = False
                break

        if valid:
            return [item for item in return_val if item["old"] != item["new"]]

    return []


async def debug_simple(sql: str) -> str | None:
    """
    Main debugging function that processes SQL queries and applies debug rules.

    Args:
        sql: SQL query to debug

    Returns:
        str | None: Debugged SQL query or None if debugging fails/cancelled
    """
    debug_simple_message = get_debug_simple_message(sql)
    
    temp_rule, temp_debug_simple_message = (
        get_rule().copy(),
        debug_simple_message.copy(),
    )
    for debug_simple_iterator in range(get_max_retry() if get_enable_param()["aggressive_debug"] else get_max_retry() + 1):
        if get_recent_tid("llm") != threading.get_ident():
            return None
        
        if get_enable_param()["aggressive_debug"] or debug_simple_iterator > 0:
            try:
                get_llm_response_task = asyncio.create_task(
                    debug_simple_inner(
                        sql, temp_debug_simple_message, debug_simple_iterator if get_enable_param()["aggressive_debug"] else debug_simple_iterator - 1
                    )
                )
                
                set_running_inference(get_llm_response_task)
                temp_rule += await get_llm_response_task

            except asyncio.CancelledError:
                continue

            except Exception as e:
                # Should not reach here
                log("error.txt", f"{str(e)}")
                raise e

        temp_sql = sql
        for rule in temp_rule:
            temp_sql = temp_sql.replace(rule["old"], rule["new"])

        try:
            with get_explain_cursor_lock():
                find_semicolon = temp_sql.find(";")
                
                if find_semicolon != -1 and temp_sql[find_semicolon:].strip() != "":
                    raise Exception("Only one SQL statement is supported")
                
                get_cursor()["explain"].execute(f"EXPLAIN {temp_sql}")
                set_rule([rule for rule in temp_rule if rule["old"] in temp_sql])

                if get_rule() != []:
                    debug_simple_message.append(
                        {"role": "assistant", "content": f"```json{str(get_rule())}```"}
                    )
                return temp_sql

        except Exception as e:
            """
            Cannot explain the SQL query. Debug again until max_retry times.
            """
            error_info = str(e)
            if debug_simple_iterator == 0:
                set_initial_error_info(error_info)

        temp_debug_simple_message.append(
            {"role": "assistant", "content": f"```json\n{str(temp_rule)}\n```"}
        )
        temp_debug_simple_message.append(
            {"role": "user", "content": f"{temp_sql}\n{error_info}"}
        )

    set_error_info(error_info)
    return None
