# Copyright (c) 2025 Haoyu Li
# Released under the MIT License.
# See LICENSE file in the project root for details.

#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Concurrency module for SpeQL.
=============

This module manages thread synchronization and background process handling.
"""

import sys
import threading
import time
from pathlib import Path
from typing import Optional, Union, Dict
from asyncio import Task

# -----------------------------------------------------------------------------
# Path Configuration
# -----------------------------------------------------------------------------

root_dir = str(Path(__file__).parent.parent)
sys.path.extend([
    root_dir,
    str(Path(root_dir) / "src"),
    str(Path(root_dir) / "util"),
])

# -----------------------------------------------------------------------------
# Global Variables
# -----------------------------------------------------------------------------

recent_tid: Dict[str, Optional[int]] = {
    "llm": None,
    "db": None,
}
running_sql: Dict[str, Optional[str]] = {
    "llm": None,
    "db": None,
}
running_inference: Optional[Task] = None
background_create: Optional[str] = None
background_create_tid: Optional[int] = None
priority: Dict[str, int] = {
    "llm": 0,
    "db": 0,
}

# Thread synchronization objects
tid_lock = threading.Lock()
background_create_event = threading.Event()
explain_cursor_lock = threading.Lock()
execute_cursor_lock = threading.Lock()
load_vector_db_lock = threading.Lock()

# -----------------------------------------------------------------------------
# Lock Management
# -----------------------------------------------------------------------------

def get_explain_cursor_lock() -> threading.Lock:
    """Returns the lock for explain cursor operations."""
    return explain_cursor_lock


def get_execute_cursor_lock() -> threading.Lock:
    """Returns the lock for execute cursor operations."""
    return execute_cursor_lock

def get_load_vector_db_lock() -> threading.Lock:
    """Returns the lock for load vector db operations."""
    return load_vector_db_lock

# -----------------------------------------------------------------------------
# Thread Management
# -----------------------------------------------------------------------------

def get_recent_tid(type: str) -> Optional[int]:
    """Returns the ID of the most recent thread."""
    return recent_tid[type]


def get_priority(type: str) -> int:
    """
    Gets the priority of the current thread if it's the most recent one.
    
    Returns:
        int: Current priority if thread is most recent, -1 otherwise
    """
    with tid_lock:
        return priority[type] if threading.get_ident() == get_recent_tid(type) else -1


def set_recent_tid(new_priority: int, new_running_sql: str | None, type: str) -> None:
    """
    Updates the most recent thread information.
    
    Args:
        new_priority: Priority level for the thread
        new_running_sql: SQL query being executed
        type: Type of the job
    """
    global recent_tid, priority, running_sql

    # Wait if same SQL is running and priority conditions aren't met
    while (new_running_sql == running_sql[type] and 
           not (new_priority > 0 and priority[type] == 0)):
        time.sleep(0.1)

    with tid_lock:
        recent_tid[type] = threading.get_ident()
        priority[type] = new_priority
        running_sql[type] = new_running_sql


def reset_recent_tid(type: str) -> None:
    """
    Destroy the existing thread and awake background thread.
    """
    global recent_tid, priority, running_sql

    with tid_lock:
        if recent_tid[type] == threading.get_ident():
            recent_tid[type] = get_background_tid()
            priority[type] = 0
            running_sql[type] = None
            if type == "db":
                set_background_create_event()

# -----------------------------------------------------------------------------
# Task Management
# -----------------------------------------------------------------------------

def set_running_inference(task: Task) -> None:
    """
    Updates the currently running task, cancelling existing ones if necessary.
    
    Args:
        task: New task to set as running
    """
    global running_inference

    with tid_lock:
        if threading.get_ident() != get_recent_tid("llm"):
            if not task.done():
                task.cancel()
        else:
            if running_inference is not None and not running_inference.done():
                running_inference.cancel()
            running_inference = task

# -----------------------------------------------------------------------------
# Background Process Management
# -----------------------------------------------------------------------------

def set_background_create(sql: str) -> None:
    """
    Register background thread to create table using idle resource.
    
    Args:
        sql: SQL query for background creation
    """
    global background_create

    with tid_lock:
        if threading.get_ident() == get_recent_tid("db"):
            background_create = sql


def get_background_create() -> Optional[str]:
    """Return the current background creation SQL."""
    return background_create


def set_background_create_event() -> None:
    """Wake up background thread to create table."""
    background_create_event.set()


def clear_background_create_event() -> None:
    """Clear the background creation event."""
    background_create_event.clear()


def wait_background_create_event() -> None:
    """Wait for the background creation event to be set."""
    background_create_event.wait()


def get_background_tid() -> Optional[int]:
    """Return the background thread ID."""
    return background_create_tid


def set_background_tid(new_background_create_tid: int) -> None:
    """
    Sets the background thread ID.
    
    Args:
        new_background_create_tid: New background thread ID to set
    """
    global background_create_tid
    background_create_tid = new_background_create_tid

# -----------------------------------------------------------------------------
# Middle Speculation Management
# -----------------------------------------------------------------------------

speculate_middle: Optional[Union[str, Task]] = None


async def get_speculate_middle() -> Optional[str]:
    """
    Retrieves the middle speculation result.
    
    Returns:
        Optional[str]: Speculation result or None if not available
    """
    global speculate_middle
    if speculate_middle is None:
        return None
    elif isinstance(speculate_middle, str):
        return speculate_middle
    else:
        try:
            return await speculate_middle
        except:
            return ""

def set_speculate_middle(task_or_string: Union[Task, str]) -> None:
    """
    Sets the middle speculation task or result.
    
    Args:
        task_or_string: Task or string to set as speculation
    """
    global speculate_middle
    speculate_middle = task_or_string
