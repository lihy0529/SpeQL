# Copyright (c) 2025 Haoyu Li
# Released under the MIT License.
# See LICENSE file in the project root for details.

#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Create Execute Module
====================

This module handles the execution of CREATE TABLE operations and manages
the associated metadata (query time, table size) collection and schema updates.

Key Features:
    - Execute CREATE TABLE statements
    - Collect query performance metrics
    - Update schema information
    - Track table size statistics
"""

import sys
import re
import json
from pathlib import Path
from typing import Optional, Dict, Any

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

from db_api import get_cursor
from log import log
from schema import get_schema


# -----------------------------------------------------------------------------
# Create Table Execute
# -----------------------------------------------------------------------------


async def execute(create_script: str, warm_up: bool = False) -> Optional[Dict[str, Any]]:
    """
    Executes a CREATE TABLE statement and collects associated metadata.

    This function performs the following operations:
    1. Executes the CREATE TABLE statement
    2. Extracts the table name from the statement
    3. Collects query execution time
    4. Records table size information
    5. Updates schema information

    Args:
        create_script (str): The CREATE TABLE SQL statement to execute

    Returns:
        dict: Metrics of the created table

    Example:
        >>> create_sql = 'CREATE TEMPORARY TABLE "example" AS SELECT * FROM table'
        >>> size = await execute(create_sql)
        >>> print(f"Created table size: {size}MB")
    """

    get_cursor()["execute"].execute(create_script)

    table_name = (
        re.search(r"CREATE TEMPORARY TABLE (\"\w+\")", create_script, re.IGNORECASE)
        .group(1)
        .lower()
        .replace('"', "")
    )

    get_cursor()["execute"].execute("""
select elapsed_time, execution_time, compile_time, planning_time from sys_query_history 
where query_id = pg_last_query_id()
""")
    
    result = get_cursor()["execute"].fetchone()
    metrics = {
        "elapsed_time": result[0] / 1000000,
        "execution_time": result[1] / 1000000,
        "compile_time": result[2] / 1000000,
        "planning_time": result[3] / 1000000,
    }

    get_cursor()["execute"].execute(
        f"""
SELECT "size" AS "size" FROM SVV_TABLE_INFO WHERE "table" = \'{table_name}\'
"""
    )
    try:
        size = get_cursor()["execute"].fetchone()[0]
    except Exception:
        # If we cannot get the size from an empty table
        size = 0
        
    metrics["create_size"] = size
    
    if warm_up:
        return metrics
    
    get_cursor()["execute"].execute(
        f"""
SELECT tablename, "column", "type" FROM pg_table_def WHERE tablename = \'{table_name}\'
"""
    )
    try:
        schema_diff = get_cursor()["execute"].fetchall()
    except Exception:
        # This should not happen
        raise Exception("Cannot get schema diff")

    get_schema()[schema_diff[0][0].upper()] = {}

    for row in schema_diff:
        get_schema()[schema_diff[0][0].upper()][row[1].upper()] = row[2]

    return metrics


# -----------------------------------------------------------------------------
# Drop Table Execute
# -----------------------------------------------------------------------------


def drop_warm_up(table_name: str) -> None:
    try:
        get_cursor()["execute"].execute(f"DROP TABLE IF EXISTS {table_name} CASCADE;")
    except Exception as e:
        log("error.txt", f"Cannot drop table {table_name}: {e}")
