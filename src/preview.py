# Copyright (c) 2025 Haoyu Li
# Released under the MIT License.
# See LICENSE file in the project root for details.

#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Preview module for SpeQL.

This module provides functionality to generate a preview of SQL query results.
Sample the query if the query takes too long.
"""

import sys
import re
import threading
import redshift_connector
from pathlib import Path
from typing import Optional, Any, Dict
import sqlglot

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

from format import format_preview, format
from sqlglot import exp
from concurrency import get_recent_tid, get_execute_cursor_lock
from param import (
    get_plugin_param,
    get_enable_param,
    get_test_param,
    get_db_param,
    get_dialect_param,
    get_max_iteration,
)
from db_api import get_cursor
from log import log, append_test_info
from sample import sample_script
from parse import get_parse

# -----------------------------------------------------------------------------
# SQL Processing
# -----------------------------------------------------------------------------


def reset_limit(sql: Optional[str]) -> Optional[str]:
    """
    Resets or adds a LIMIT clause to the SQL query based on preview settings.

    Args:
        sql: SQL query to process

    Returns:
        str: SQL query with updated LIMIT clause
    """
    
    if sql is None:
        return sql
    
    parsed = get_parse(sql)

    if (
        not isinstance(parsed, sqlglot.exp.Select)
        and not isinstance(parsed, sqlglot.exp.Union)
        and not isinstance(parsed, sqlglot.exp.Intersect)
    ):
        return None

    limit_clause = parsed.find(exp.Limit)

    if not limit_clause:
        parsed.set("limit", exp.Limit())
        limit = str(get_plugin_param()["preview"] + 1)
        parsed.set("limit", exp.Limit(expression=exp.Literal.number(limit)))
    else:
        limit = limit_clause.expression.sql()
        if not re.match(r"\d+", limit) or int(limit) > get_plugin_param()["preview"]:
            limit = str(get_plugin_param()["preview"] + 1)
        limit_clause.set("expression", exp.Literal.number(limit))

    sql = sqlglot.transpile(
        parsed.sql(),
        read=get_dialect_param()["input"],
        write=get_dialect_param()["endpoint"],
    )[0]

    return format(sql)


# -----------------------------------------------------------------------------
# Query Execution
# -----------------------------------------------------------------------------


async def query(sql: str) -> Optional[Any]:

    get_cursor()["execute"].execute(sql)

    preview_result = format_preview(get_cursor()["execute"].fetchall())

    try:
        get_cursor()["execute"].execute(
            """
select elapsed_time, execution_time, compile_time, planning_time from sys_query_history 
where query_id = pg_last_query_id()
"""
        )
        metrics = get_cursor()["execute"].fetchone()
        metrics = {
            "elapsed_time": metrics[0] / 1000000,
            "execution_time": metrics[1] / 1000000,
            "compile_time": metrics[2] / 1000000,
            "planning_time": metrics[3] / 1000000,
        }

    except Exception as e:
        metrics = {
            "elapsed_time": -1,
            "execution_time": -1,
            "compile_time": -1,
            "planning_time": -1,
        }
        
    log("preview.txt", {"preview": preview_result, "script": sql, "metrics": metrics}, is_dict=True)

    return {"preview": preview_result, "metrics": metrics}


# -----------------------------------------------------------------------------
# Preview Generation
# -----------------------------------------------------------------------------


async def preview(sql: str) -> Optional[Any]:
    """
    Generates a preview of SQL query results.

    Args:
        sql: SQL query to preview

    Returns:
        Optional[Any]: Formatted preview results or None if preview fails
    """

    sql = reset_limit(sql)
    
    if sql is None or get_recent_tid("db") != threading.get_ident():
        return None

    max_attempts = get_max_iteration() if get_enable_param()["sample"] else 1
    for retry_time in range(max_attempts):
        if get_recent_tid("db") != threading.get_ident():
            break
        try:
            with get_execute_cursor_lock():
                sample_sql = sample_script(sql, retry_time)
                if get_test_param()["warm_up"]:
                    result_warm_up = await query(sample_sql)
                result = await query(sample_sql)
                if get_test_param()["output_query"]:
                    if get_test_param()["warm_up"]:
                        append_test_info(
                            "query",
                            {
                                "query": sql,
                                "preview": result["preview"],
                                "retry_time": retry_time,
                                "query_metrics": result["metrics"],
                                "query_metrics_warm_up": result_warm_up["metrics"],
                            },
                        )
                    else:
                        append_test_info(
                            "query",
                            {
                                "query": sql,
                                "preview": result["preview"],
                                "retry_time": retry_time,
                                "query_metrics": result["metrics"],
                            },
                        )

                return result["preview"]

        except redshift_connector.error.ProgrammingError as e:
            if isinstance(e.args[0], dict) and e.args[0].get("C") == "57014":
                metrics = {
                    "elapsed_time": get_db_param()["timeout"],
                    "execution_time": -1,
                    "compile_time": -1,
                    "planning_time": -1,
                }
                if get_test_param()["output_query"]:
                    if get_test_param()["warm_up"]:
                        append_test_info(
                            "query",
                            {
                                "query": sql,
                                "retry_time": retry_time,
                                "query_metrics": metrics,
                                "query_metrics_warm_up": metrics,
                            },
                        )
                    else:
                        append_test_info(
                            "query",
                            {
                                "query": sql,
                                "retry_time": retry_time,
                                "query_metrics": metrics,
                            },
                        )
                continue

            log("error.txt", f"{str(e)}")
            break

        except Exception as e:
            log("error.txt", f"{str(e)}")
            break

    return None
