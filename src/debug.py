# Copyright (c) 2025 Haoyu Li
# Released under the MIT License.
# See LICENSE file in the project root for details.

#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Debug Module
=============

This module provides a main debugging pipeline for SQL queries. It attempts to
auto complete and fix SQL queries through multiple approaches. If it succeeds,
SpeQL will send the correct SQL query to the create module. Otherwise, SpeQL
will not preview immediate results to the user.
"""

import sys
import asyncio
from pathlib import Path
from typing import Optional

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
# Local Imports
# -----------------------------------------------------------------------------

from debug_simple import debug_simple, clear_debug_simple_message
from debug_complex import debug_complex
from debug_middle import speculate_middle
from debug_rule import set_rule
from cost import check_new_sql
from concurrency import set_speculate_middle
from param import get_enable_param

# -----------------------------------------------------------------------------
# Global Variables
# -----------------------------------------------------------------------------

last_runnable_sql = None

# -----------------------------------------------------------------------------
# SQL State Management
# -----------------------------------------------------------------------------

def get_last_runnable_sql() -> Optional[str]:
    """
    Retrieves the last successfully executed SQL query. This function is used to
    check if the new SQL query is significantly different from the last runnable
    SQL query, possibly due to the user switches between files. If it is, SpeQL
    will clear the rule and start from scratch.
    
    Returns:
        Optional[str]: Last runnable SQL query or None if not set
    """
    global last_runnable_sql
    return last_runnable_sql


def set_last_runnable_sql(sql: str) -> None:
    """
    Updates the last successfully executed SQL query.
    
    Args:
        sql: SQL query to store
    """
    global last_runnable_sql
    last_runnable_sql = sql

# -----------------------------------------------------------------------------
# Main Debug Function
# -----------------------------------------------------------------------------

async def debug(sql: str) -> Optional[str]:
    """
    Main debugging pipeline that attempts to fix SQL queries through multiple approaches.
    
    The function follows this process:
    1. Attempts simple debugging first
    2. Falls back to complex debugging if simple debugging fails
    3. Updates middle speculation and last runnable SQL if successful
    
    Args:
        sql: SQL query to debug
        
    Returns:
        Optional[str]: Debugged SQL query if successful, None otherwise
    """
    
    
    
    if check_new_sql(get_last_runnable_sql(), sql):
        set_rule([])
        clear_debug_simple_message()
    
    if not get_enable_param()["aggressive_debug"]:
        set_rule([])
    return_value = await debug_simple(sql)

    if return_value is None:
        return_value = await debug_complex(sql)

    if return_value is not None:
        set_speculate_middle(asyncio.create_task(speculate_middle(return_value)))
        set_last_runnable_sql(return_value)
        
    return return_value
