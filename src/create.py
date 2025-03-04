# Copyright (c) 2025 Haoyu Li
# Released under the MIT License.
# See LICENSE file in the project root for details.

#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SQL Create Module
==================================

This module handles SQL query rewriting and execution

Key Features:
    - Query optimization and rewriting
    - Temporary table creation, caching, and eviction
    - Sample-based execution for large queries
"""

import sys
import threading
import redshift_connector
import re
import sqlglot
from pathlib import Path
from typing import Dict, Optional

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

from sqlglot.optimizer.scope import traverse_scope
from sqlglot.optimizer.scope import build_scope

from param import get_plugin_param, get_dialect_param, get_enable_param
from format import format
from concurrency import (
    get_recent_tid,
    set_background_create,
    get_execute_cursor_lock,
    get_priority,
)
from parse import get_parse, get_optimize
from sample import reset_sample
from create_rewrite import rewrite, get_powerset, resolve_alias_conflict
from param import get_max_iteration, get_test_param, get_db_param
from log import log, append_test_info
from sample import sample_script
from create_execute import execute, drop_warm_up
from extract import extract
from create_struct import temporary_table_pool
from dialect import support_rewrite
from create_concurrency import cancel_running_query
from create_rewrite import get_agg_func


# -----------------------------------------------------------------------------
# Rewrite and Execute
# -----------------------------------------------------------------------------


async def rewrite_and_execute_inner(
    create_script: str, query_script: str
) -> Dict[str, Optional[str]]:
    """
    Rewrites and executes a SQL query, specifically creating temporary tables.

    The function follows these steps:
    1. Rewrite both create and query scripts using existing temporary tables
    2. If needed, create a new temporary table (with retry logic for sampling)
    3. Return the rewritten query and/or temporary table reference

    Args:
        create_script: SQL script for creating temporary table
        query_script: SQL script to execute against the temporary table

    Returns:
        Dictionary containing:
            - 'name': Name of temporary table if query matches create script,
            None otherwise
            - 'script': Rewritten query script if different from create script,
            query script otherwise

    Example:
        >>> await rewrite_and_execute_inner(
            'SELECT "col1" FROM "table" WHERE "table"."col1" > 0',
            'SELECT "col1" FROM "table" WHERE "table"."col1" > 0 AND "table"."col2" > 0'
        )
        # CREATE TEMPORARY TABLE "tmp_tb" AS SELECT "table"."col1" FROM "table" WHERE "table"."col1" > 0
        {
            'name': "tmp_tb",
            'script': 'SELECT "tmp_tb"."col1" FROM "tmp_tb" WHERE "tmp_tb"."col2" > 0'
        }
    """
    check = temporary_table_pool.check(create_script, update_lru=True)
    create_script = rewrite(temporary_table_pool.get_query_cache_list(), create_script)
    query_script = rewrite(temporary_table_pool.get_query_cache_list(), query_script)

    if check["is_new"]:
        check = temporary_table_pool.check(create_script, update_lru=True)

    if not check["is_new"]:
        if create_script == query_script:

            try:
                get_parse(query_script).args.get("from").args.get("this")
                select_list = extract(query_script)["select"]
                select_list = [
                    f'{select_list[i]["alias"]} AS {select_list[i]["alias"]}'
                    for i in range(len(select_list))
                ]
                script = f"SELECT {', '.join(select_list)} FROM {check['name']} AS {check['name']}"

            except Exception:
                script = f"SELECT * FROM {check['name']} AS {check['name']}"
            return {
                "name": check["name"],
                "script": script,
            }

            

        else:
            return {
                "name": None,
                "script": query_script,
            }

    if support_rewrite(query_script):
        extract_query = extract(query_script)
        """
        Check if query has no joins, filters, grouping, or having clauses. If so,
        use the table name directly.
        """
        if all(
            not extract_query[clause] for clause in ["join", "where", "group", "having"]
        ):
            agg_func = get_agg_func(query_script)
            if agg_func is not None and all(
                agg_func[i] is not None for i in range(len(agg_func))
            ):
                return {
                    "name": extract_query["from"][0]["name"],
                    "script": query_script,
                }

    max_iteration = (
        get_max_iteration()
        if get_enable_param()["sample"] and support_rewrite(query_script)
        else 1
    )

    for retry_count in range(max_iteration):
        if get_recent_tid("db") != threading.get_ident():
            break
        try:
            sample_create_script = sample_script(create_script, retry_count)

            with get_execute_cursor_lock():
                if get_test_param()["warm_up"]:
                    # Warm up the query
                    create_metrics_warm_up = await execute(
                        f"CREATE TEMPORARY TABLE {check['name']} AS {sample_create_script}",
                        warm_up=True,
                    )

                    drop_warm_up(check["name"])
                create_metrics = await execute(
                    f"CREATE TEMPORARY TABLE {check['name']} AS {sample_create_script}",
                    warm_up=False,
                )

            if get_test_param()["output_create"]:
                if get_test_param()["warm_up"]:
                    append_test_info(
                        "create",
                        {
                            "create": f"CREATE TEMPORARY TABLE {check['name']} AS {create_script}",
                            "retry_time": retry_count,
                            "create_metrics": create_metrics,
                            "create_metrics_warm_up": create_metrics_warm_up,
                        },
                    )
                else:
                    append_test_info(
                        "create",
                        {
                            "create": f"CREATE TEMPORARY TABLE {check['name']} AS {create_script}",
                            "retry_time": retry_count,
                            "create_metrics": create_metrics,
                        },
                    )

            temporary_table_pool.update(
                create_script,
                is_sample=bool(retry_count),
                create_metrics=create_metrics,
            )

            return {
                "name": check["name"] if create_script == query_script else None,
                "script": rewrite(
                    temporary_table_pool.get_query_cache_list(), query_script
                ),
            }

        except redshift_connector.error.ProgrammingError as e:
            # Handle query cancellation (error code 57014)
            if isinstance(e.args[0], dict) and e.args[0].get("C") == "57014":
                create_metrics = {
                    "elapsed_time": get_db_param()["timeout"],
                    "execution_time": -1,
                    "compile_time": -1,
                    "planning_time": -1,
                    "create_size": 0,
                }
                if get_test_param()["warm_up"]:
                    append_test_info(
                        "create",
                        {
                            "create": f"CREATE TEMPORARY TABLE {check['name']} AS {create_script}",
                            "retry_time": retry_count,
                            "create_metrics": create_metrics,
                            "create_metrics_warm_up": create_metrics,
                        },
                    )

                else:
                    append_test_info(
                        "create",
                        {
                            "create": f"CREATE TEMPORARY TABLE {check['name']} AS {create_script}",
                            "retry_time": retry_count,
                            "create_metrics": create_metrics,
                        },
                    )

                continue

            query_script = None
            break

        except Exception as e:
            log("error.txt", f"{str(e)}. Create script: {create_script}")
            query_script = None
            break

    return {"name": None, "script": query_script}


async def rewrite_and_execute(script, metadata) -> Dict[str, Optional[str]]:
    """
    Rewrite and execute a query, handling both main and subqueries.
    """
    global temporary_table_pool
    script = resolve_alias_conflict(script)

    if metadata["is_main_query"]:
        if metadata["urgent"] or not support_rewrite(script):
            rewrite_script = rewrite(
                temporary_table_pool.get_query_cache_list(), script
            )
            return {"name": None, "script": rewrite_script}

        main_query_script = await get_powerset(script)
        return await rewrite_and_execute_inner(main_query_script, script)

    else:
        if metadata["urgent"]:
            rewrite_script = rewrite(
                temporary_table_pool.get_query_cache_list(), script
            )
            return {"name": None, "script": rewrite_script}
        return await rewrite_and_execute_inner(script, script)


# -----------------------------------------------------------------------------
# Create Inner
# -----------------------------------------------------------------------------


async def create_inner(sql: str) -> Optional[str]:
    """
    Process and rewrite SQL query with CTEs (Common Table Expressions).

    This function:
    1. Extracts CTEs in the query
    2. Creates temporary tables for CTEs where possible
    3. Rewrites the main query using temporary tables

    Args:
        sql: The SQL query to process

    Returns:
        Formatted and rewritten SQL query, or None if processing fails
    """
    global temporary_table_pool

    with get_execute_cursor_lock():
        temporary_table_pool.lru_evict()

    scope = build_scope(get_parse(sql))

    alias_to_name_list = []
    remaining_cte_list = []

    main_query_script = scope.expression.sql()
    urgent = True if get_priority("db") > 1 else False

    if urgent:
        cancel_running_query()

    for cte in scope.ctes:
        """
        Extract CTE script from CTE definition

        Example:
        >>> cte AS (SELECT * FROM "table")
        >>> cte_script = SELECT * FROM "table"
        """
        cte_script = re.search(
            r"^(\"\w+\")\s+AS\s*\((.*?)\)$", cte.sql(), re.IGNORECASE
        ).group(2)

        for alias_map in alias_to_name_list:
            cte_script = re.sub(
                rf"(?<!\.){re.escape(alias_map['alias'])}",
                f" {alias_map['name']}",
                cte_script,
            )

        cte_script = format(cte_script)

        rewrite = await rewrite_and_execute(
            cte_script,
            metadata={
                "is_main_query": False,
                "urgent": urgent,
            },
        )
        if get_test_param()["output_cte"]:
            append_test_info("cte", cte_script)

        if get_test_param()["output_rewrite_cte"]:
            append_test_info(
                "rewrite_cte", {"script": cte_script, "rewrite": rewrite["script"]}
            )

        if rewrite["name"] is not None:
            alias_to_name_list.append(
                {"alias": f'"{cte.alias_or_name}"', "name": rewrite["name"]}
            )

        else:
            if rewrite["script"] is not None:
                remaining_cte_list.append(
                    f"{cte.alias_or_name} AS ({rewrite['script']})"
                )

            else:
                return None

    for cte in scope.ctes:
        main_query_script = main_query_script.replace(cte.sql(), "")

    if main_query_script.lower().startswith("with"):
        main_query_script = main_query_script[len("with") :].strip()

    while main_query_script.startswith(","):
        main_query_script = main_query_script[1:].strip()


    for alias_map in alias_to_name_list:
        main_query_script = format(
            re.sub(
                rf"(?<!\.){re.escape(alias_map['alias'])}",
                f" {alias_map['name']}",
                main_query_script,
            )
        )

    if remaining_cte_list != []:
        main_query_script = format(
            f"WITH {', '.join(remaining_cte_list)} {main_query_script}"
        )

        if get_test_param()["output_main_query"]:
            append_test_info("main_query", main_query_script)

        if get_test_param()["output_rewrite_main_query"]:
            append_test_info(
                "rewrite_main_query",
                {"script": main_query_script, "rewrite": main_query_script},
            )

    elif main_query_script.lower().startswith("select"):
        if get_test_param()["output_main_query"]:
            append_test_info("main_query", main_query_script)

        try:
            get_parse(main_query_script).args.get("from").args.get("this")
            Pass = (
                extract(main_query_script)["join"] != []
                or extract(main_query_script)["where"] != []
                or extract(main_query_script)["group"] != []
            )

        except Exception:
            Pass = False

        if Pass:
            import time
            t = time.time()
            rewrite = await rewrite_and_execute(
                format(main_query_script),
                metadata={"is_main_query": True, "urgent": urgent},
            )
            print(f"rewrite_and_execute: {time.time() - t:.2f}")
            if get_test_param()["output_rewrite_main_query"]:
                append_test_info(
                    "rewrite_main_query",
                    {"script": main_query_script, "rewrite": rewrite["script"]},
                )

            main_query_script = (
                format(rewrite["script"]) if rewrite["script"] is not None else None
            )

        else:
            if get_test_param()["output_rewrite_main_query"]:
                append_test_info(
                    "rewrite_main_query",
                    {"script": main_query_script, "rewrite": main_query_script},
                )
    else:
        # Should not reach here
        log("error.txt", f"Should not reach here. Create script: {sql}")
        if get_test_param()["output_main_query"]:
            append_test_info("main_query", main_query_script)
        if get_test_param()["output_rewrite_main_query"]:
            append_test_info(
                "rewrite_main_query",
                {"script": main_query_script, "rewrite": main_query_script},
            )

    return main_query_script


async def create(sql: str) -> Optional[str]:
    """
    Process and rewrite SQL query.

    Args:
        sql: Input SQL query to process

    Returns:
        Formatted and rewritten SQL query, or original SQL if processing fails
    """
    if get_recent_tid("db") != threading.get_ident() or not sql:
        return None

    def remove_comment(sql_string: str) -> str:
        """
        Remove comments /*...*/ from the SQL query.

        Warning: This function is not perfect. It may not remove all comments when /* */ is nested.
        """
        return re.sub(r"/\*[^*]*\*+(?:[^/*][^*]*\*+)*/", "", sql_string, re.DOTALL)

    mem_sql = remove_comment(sql)
    mem_sql = format(remove_comment(format(mem_sql)))

    reset_sample()

    """
    Check if the query is a SELECT statement. If not, return None.
    """
    try:
        if (
            not isinstance(get_parse(mem_sql), sqlglot.exp.Select)
            and not isinstance(get_parse(mem_sql), sqlglot.exp.Union)
            and not isinstance(get_parse(mem_sql), sqlglot.exp.Intersect)
        ):
            return None
    except Exception:
        log("error.txt", f"Failed to parse query: {mem_sql}\nsql: {sql}")
        return None

    try:
        sql = sqlglot.transpile(
            sql,
            read=get_dialect_param()["input"],
            write=get_dialect_param()["endpoint"],
        )[0]
    except Exception:
        """
        Remove the cursor identifier from the query and try to transpile it again.
        If here is a comment between a keyword that has two or more words, sqlglot
        will not be able to parse the query. Possibly due to a bug in sqlglot.
        """
        try:
            sql = sqlglot.transpile(
                sql.replace(get_plugin_param()["cursor_identifier"], "")
                + " "
                + get_plugin_param()["cursor_identifier"],
                read=get_dialect_param()["input"],
                write=get_dialect_param()["endpoint"],
            )[0]
        except Exception:
            """
            If a query can be addressed by the DB endpoint but cannot be parsed by sqlglot,
            return the original query.
            """
            log("error.txt", f"Failed to transpile query, sql: {sql}")
            return mem_sql

    cursor_id = get_plugin_param()["cursor_identifier"][2:-2]

    if f"/* {cursor_id} */" not in sql:
        """
        If the CURSOR_IDENTIFIER was in the query but is eliminated by the transpile,
        add it back to the query. This is to conservably handle the possibility that
        the transpile function may not always preserve all the comments.
        """
        sql = sql + f" /* {cursor_id} */"

    scope_list = traverse_scope(get_parse(sql))
    scope_list = [
        scope for scope in scope_list if f"/* {cursor_id} */" in scope.expression.sql()
    ]

    if not scope_list:
        return mem_sql

    cte_list = []
    for cte in scope_list[-1].ctes:
        if f"/* {cursor_id} */" in cte.sql():
            break
        cte_list.append(cte)

    sql = remove_comment(sql)
    sql = format(remove_comment(format(sql)))
    set_background_create(sql)

    for i, scope in enumerate(scope_list):
        sql = scope.expression.sql()
        sql = remove_comment(sql)
        sql = format(remove_comment(format(sql)))

        if cte_list and i != len(scope_list) - 1:
            sql = format(f"with {', '.join([cte.sql() for cte in cte_list])}{sql}")

        try:
            optimize_sql = get_optimize(sql)
        except Exception:
            """
            If the (sub) query cannot be optimized, try another one until the last one.
            This is a normal SpeQL behavior.
            """
            if i == len(scope_list) - 1:
                return mem_sql
            continue

        try:
            sql = await create_inner(optimize_sql)
        except Exception as e:
            log("error.txt", f"Error: {e}")
            return mem_sql

        if get_test_param()["output_optimize"]:
            append_test_info("optimized_sql", optimize_sql)
        break

    return format(sql) if sql is not None else mem_sql
