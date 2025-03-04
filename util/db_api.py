# Copyright (c) 2025 Haoyu Li
# Released under the MIT License.
# See LICENSE file in the project root for details.

#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Database API Module
"""

import sys
import redshift_connector
import snowflake.connector
from pathlib import Path
from typing import Dict

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

from param import get_db_param, get_system_name, get_test_param, get_dialect_param, get_enable_param
from concurrency import get_execute_cursor_lock
from log import log

# -----------------------------------------------------------------------------
# Database Connection Management
# -----------------------------------------------------------------------------


def new_db_cursor(test: bool = False) -> redshift_connector.Cursor:
    """
    Creates a new database cursor with appropriate configuration. Parameters are
    retrieved from the `get_db_param()` function.
    
    Now supports Redshift and Snowflake.

    Args:
        test: Whether to connect to test schema

    Returns:
        redshift_connector.Cursor: Configured database cursor
        
    Raises:
        Exception: If the database is not supported
    """
    db_param = get_db_param()
    
    assert get_dialect_param()["endpoint"] in ["redshift", "snowflake"], "Unsupported database"

    # Establish connection
    if get_dialect_param()["endpoint"] == "redshift":
        connection = redshift_connector.connect(
            host=db_param["host"],
            database=db_param["database"],
            port=db_param["port"],
            user=db_param["user"],
            password=db_param["password"],
        )
        
    elif get_dialect_param()["endpoint"] == "snowflake":
        connection = snowflake.connector.connect(
            user=db_param["user"],
            password=db_param["password"],
            account=db_param["host"],
            database=db_param["database"],
            schema=db_param["search_path"],
        )

    connection.autocommit = True
    cursor = connection.cursor()

    # Set schema path
    if get_dialect_param()["endpoint"] == "redshift":
        schema_path = (
            f"{db_param['search_path']}_{get_system_name().lower()}_test"
            if test
            else db_param["search_path"]
        )
        print("schema_path", schema_path)
    
    
    elif get_dialect_param()["endpoint"] == "snowflake":
        schema_path = db_param["search_path"]
        
    if get_dialect_param()["endpoint"] == "redshift":
        cursor.execute(f"set search_path to {schema_path};")
        
    elif get_dialect_param()["endpoint"] == "snowflake":
        cursor.execute(f"use schema {schema_path};")

    # Set timeout
    if get_dialect_param()["endpoint"] == "redshift":
        cursor.execute(f"set statement_timeout to {db_param['timeout'] * 1000};")
        
    elif get_dialect_param()["endpoint"] == "snowflake":
        cursor.execute(f"alter session set statement_timeout_in_seconds = {db_param['timeout']};")
        
    if not get_enable_param()["result_cache"]:
        if get_dialect_param()["endpoint"] == "redshift":
            cursor.execute("SET enable_result_cache_for_session TO OFF;")
        
        elif get_dialect_param()["endpoint"] == "snowflake":
            cursor.execute("ALTER SESSION SET USE_CACHED_RESULT=FALSE;")
            
    return cursor


# -----------------------------------------------------------------------------
# Database Sampling for Testing
# -----------------------------------------------------------------------------


def sample_database() -> None:
    """
    Creates sample database schema for testing purposes.
    
    Now supports Redshift.
    
    Warning: This function is only for testing.

    Raises:
        AssertionError: If test parameters are not properly configured,
                        or the database is not supported
    """
    assert (
        get_test_param()["skip_create"] == True
    ), "SkipCreate should be True to sample database"
    assert get_dialect_param()["endpoint"] in [
        "redshift",
    ], "Only Redshift is supported"
    assert get_db_param()["search_path"] == "tpcds", "Only tpcds is supported"

    try:
        
        sample_cursor = new_db_cursor(test=True)
        sample_cursor.close()
        return
    except Exception:
        pass

    sample_cursor = new_db_cursor(test=False)
    test_search_path = f"{get_db_param()['search_path']}_{get_system_name().lower()}_test"

    sample_cursor.execute(f"CREATE SCHEMA IF NOT EXISTS {test_search_path};")

    try:
        sample_cursor.execute(
            "SELECT distinct tablename FROM pg_table_def "
            "WHERE schemaname NOT IN ('pg_catalog', 'information_schema')"
        )
        tables = sample_cursor.fetchall()

        for table in tables:
            try:
                sample_cursor.execute(
                    f"""
                CREATE TABLE {test_search_path}.{table[0]} AS
                SELECT * FROM {table[0]}
                WHERE FALSE;
                """
                )
                print(f"Created {test_search_path}.{table[0]}")
            except Exception as e:
                if "already exists" in str(e):
                    print(f"Already exists {test_search_path}.{table[0]}")
                else:
                    print(f"Error: {e}")

    except Exception as e:
        print(f"Error: {e}")
        sample_cursor.close()
        exit()


# -----------------------------------------------------------------------------
# Initialize Database Connections
# -----------------------------------------------------------------------------

# Sample database if in test mode
if get_test_param()["skip_create"]:
    try:
        with get_execute_cursor_lock():
            sample_database()
    except Exception as e:
        log("error.txt", f"{str(e)}")

# Initialize cursors
execute_cursor, explain_cursor = new_db_cursor(
    test=get_test_param()["skip_create"]
), new_db_cursor(test=get_test_param()["skip_create"])

# Get session ID
if get_dialect_param()["endpoint"] == "redshift":
    execute_cursor.execute("SELECT pg_backend_pid();")
    execute_session_id = execute_cursor.fetchone()[0]
elif get_dialect_param()["endpoint"] == "snowflake":
    execute_cursor.execute("SELECT CURRENT_SESSION();")
    execute_session_id = execute_cursor.fetchone()[0]

# -----------------------------------------------------------------------------
# Cursor Access Functions
# -----------------------------------------------------------------------------


def get_execute_session_id() -> int:
    """Returns the execution session ID."""
    return execute_session_id


def get_cursor() -> Dict[str, redshift_connector.Cursor]:
    """
    Returns dictionary containing database cursors.

    Returns:
        Dict with keys:
            - 'explain': Cursor for EXPLAIN queries
            - 'execute': Cursor for execution queries
    """
    return {
        "explain": explain_cursor,
        "execute": execute_cursor,
    }
