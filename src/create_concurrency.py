# Copyright (c) 2025 Haoyu Li
# Released under the MIT License.
# See LICENSE file in the project root for details.

#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Create Concurrency Module
========================

This module handles concurrent user input operations and query scheduling in the database system.
It provides mechanisms for background task processing and query cancellation.

Key Features:
    - Background creation after SpeQL returns the immediate preview to user
    - Query cancellation when user input is changed
"""

import sys
import threading
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

from db_api import get_cursor, get_execute_session_id
from parse import get_optimize
from log import log
from concurrency import (
    get_recent_tid,
    get_background_create,
    wait_background_create_event,
    clear_background_create_event,
    get_background_tid,
    set_background_tid,
    get_explain_cursor_lock,
)


# -----------------------------------------------------------------------------
# Query Cancellation
# -----------------------------------------------------------------------------


def cancel_running_query() -> None:
    """
    Cancels any running queries associated with the current session.

    This function acquires a lock to safely access the explain cursor,
    identifies running queries for the current session, and attempts to
    cancel them.

    Returns:
        None

    Raises:
        Exception: This should not happen. If it happens, it means a bug in the
        query cancellation logic.

    Example:
        >>> cancel_running_query()
        # Cancels any running queries for current session
    """
    get_explain_cursor_lock().acquire()
    try:
        get_cursor()["explain"].execute(
            """
SELECT session_id, query_text FROM sys_query_history WHERE status='running';
"""
        )
        running_query_list = get_cursor()["explain"].fetchall()

        for item in running_query_list:
            if item[0] == get_execute_session_id():
                try:
                    get_cursor()["explain"].execute(f"CANCEL {get_execute_session_id()};")
                except Exception as e:
                    # Query may have completed between listing and cancellation attempt
                    log("error.txt", f"Failed to cancel query: {e}")
                    pass
    except Exception as e:
        # This should not happen.
        log("error.txt", f"Failed to cancel query: {e}")
        raise e
    finally:
        get_explain_cursor_lock().release()


# -----------------------------------------------------------------------------
# Background Processing
# -----------------------------------------------------------------------------


async def create_background() -> None:
    """
    Asynchronous background processor for create operations.

    This function runs in a continuous loop, waiting for create events
    that SpeQL returns after user input. This function uses idle
    resources to create temporary tables. When new user input is received,
    this function should be cancelled and wait for the next create event.

    Steps:
        1. Register background thread identification
        2. Wait for create events
        3. Process and execute the creation operation
        4. Go back to step 2

    Returns:
        None

    Note:
        This function is designed to use idle resources and should be
        started as a background task.

    Example:
        >>> threading.Thread(
                target=lambda: asyncio.run(create_background()),
                daemon=True
            ).start()
        # Wait for create events and create temporary tables
    """
    set_background_tid(threading.get_ident())

    while True:
        wait_background_create_event()
        clear_background_create_event()

        if get_recent_tid("db") != get_background_tid():
            continue

        sql = get_background_create()

        if sql is not None:
            try:
                # Check if the SQL is valid, and transform it to a formatted SQL
                sql = get_optimize(sql)
            except Exception as e:
                # This happens when the SQL is invalid. It probably means the
                # sqlglot optimizer cannot optimize the SQL. Possibly a bug.
                log("error.txt", f"{str(e)}")
                continue

            from create import create_inner

            await create_inner(sql)
