# Copyright (c) 2025 Haoyu Li
# Released under the MIT License.
# See LICENSE file in the project root for details.

#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Formatting module for SpeQL.

This module provides functions to format SQL queries and handle cursor positioning.
It also includes functions to format query results and modifications.
"""

import sys
import re
import pandas as pd
from pathlib import Path
from typing import Dict, List, Optional, Any, Union

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

from parse import parse_preview
from param import get_plugin_param
from dialect import patch
from db_api import get_cursor
from sample import get_sample
from concurrency import get_recent_tid, get_background_tid

# -----------------------------------------------------------------------------
# Global State
# -----------------------------------------------------------------------------

format_dict: Dict[str, str] = {}

# -----------------------------------------------------------------------------
# SQL Formatting Functions
# -----------------------------------------------------------------------------


def format(sql_string: str) -> str:
    """
    Formats SQL string with consistent styling.

    Args:
        sql_string: Raw SQL string

    Returns:
        str: Formatted SQL string
    """
    if sql_string in format_dict:
        return format_dict[sql_string]

    mem_string = sql_string
    sql_string = patch(sql_string)

    """
    Convert comments
        >>> "-- This is a comment" -> "/* This is a comment */"
    """
    sql_string = re.sub(r"--(.*?)(\n|$)", r"/*\1 */\2", sql_string)

    """
    Remove semicolons
        >>> "SELECT * FROM table;" -> "SELECT * FROM table"
    """
    sql_string = sql_string.replace(";", "")

    """
    Convert keywords to uppercase; Add spaces around operators
        >>> "sum(a + b)*c" -> "SUM ( A + B ) * C"
    """
    sql_string = re.sub(
        r"(\'[^\']*\')|([^']+)",
        lambda m: (
            m.group(1)
            if m.group(1)
            else re.sub(
                r"(<=|>=|!=|/\*|\*\/|<>|->|[=(),<>+\*/])", r" \1 ", m.group(2)
            ).upper()
        ),
        sql_string,
    )

    sql_string = re.sub(r"\s+", " ", sql_string)

    """
    Recover cursor identifier
        >>> "/* SELECT * FROM table */" -> "/* SELECT * FROM table */"
    """
    sql_string = sql_string.replace(
        f"/* {get_plugin_param()['cursor_identifier'][2:-2]} */",
        get_plugin_param()["cursor_identifier"],
    )

    format_dict[mem_string] = sql_string.strip()
    return format_dict[mem_string]


def format_clause(clause_dict: Dict[str, Any]) -> str:
    """
    Formats SQL clauses into a complete query.

    Args:
        clause_dict: Dictionary containing SQL clause components

    Returns:
        str: Formatted SQL query

    Raises:
        Exception: If formatting fails
    """
    sql_parts = ["SELECT"]

    if clause_dict["distinct"]:
        sql_parts.append("DISTINCT")

    try:
        select_items = [
            f"{item['name']} AS {item['alias']}" for item in clause_dict["select"]
        ]
        sql_parts.append(", ".join(select_items))
    except Exception as e:
        raise e

    sql_parts.append("FROM")
    sql_parts.append(
        f"{clause_dict['from'][0]['name']} AS {clause_dict['from'][0]['alias']}"
    )

    for join in clause_dict["join"]:
        if join["type"] != "CROSS":
            join_type = join["type"] if join["type"] != "INNER" else ""
            join_parts = [
                f"{join_type} JOIN",
                f"{join['table']['name']} AS {join['table']['alias']}",
                "ON",
                " AND ".join(join["condition"]),
            ]
            sql_parts.append(" ".join(join_parts))
        else:
            sql_parts.append(
                f"CROSS JOIN {join['table']['name']} " f"AS {join['table']['alias']}"
            )

    if clause_dict["where"]:
        sql_parts.extend(["WHERE", " AND ".join(clause_dict["where"])])

    if clause_dict["group"]:
        sql_parts.extend(["GROUP BY", ", ".join(clause_dict["group"])])

    if clause_dict["having"]:
        sql_parts.extend(["HAVING", " AND ".join(clause_dict["having"])])

    if clause_dict["order"]:
        sql_parts.extend(["ORDER BY", ", ".join(clause_dict["order"])])

    if clause_dict["limit"]:
        sql_parts.extend(["LIMIT", clause_dict["limit"][0]])

    return format(" ".join(sql_parts))


def prepare_sql(sql: str) -> Optional[Dict[str, Union[str, int]]]:
    """
    Prepares SQL query for processing by handling cursor position and spacing.
    The prefix and suffix are used to handle the scenario when the user is
    editing the first CTE.
    """
    cursor_id = get_plugin_param()["cursor_identifier"]
    cursor_position = sql.find(cursor_id)

    """
    Calculate cursor priority based on newlines
    - Inline SQL has priority 0
    - SQL with newlines has priority 1
    - SQL with multiple newlines has priority > 1
    """

    priority = (lambda m: m.group().count("\n") if m else 0)(
        re.search(r"\n\s*$", sql[:cursor_position])
    ) + (lambda m: m.group().count("\n") if m else 0)(
        re.search(r"^\n\s*", sql[cursor_position + len(cursor_id) :])
    )
    
    if priority < 3:
        priority = 1
    space_before = sql[len(sql[:cursor_position].rstrip()) : cursor_position]
    if len(space_before) >= 1:
        space_before = space_before[1:]

    space_after = sql[cursor_position + len(cursor_id) :]
    space_after = space_after[: len(space_after) - len(space_after.lstrip())]
    if len(space_after) >= 1:
        space_after = space_after[:-1]

    sql = (
        sql[: cursor_position - len(space_before)]
        + cursor_id
        + sql[cursor_position + len(cursor_id) + len(space_after) :]
    )

    if sql.strip() == cursor_id.strip() or priority == 0:
        return None

    """
    Handle CTE pattern
    
    Example:
        >>> -- This is a comment \
        >>> with cte as ( \
        >>>     select * from table \
        >>> )
        
        >>> prefix: -- This is a comment \
        >>>         with cte as (
        
        >>> raw_sql: select * from table 
        
        >>> suffix: )
    """
    cte_pattern = (
        r"^\s*"
        r"((--.*(?:\n|$))|(/\*.*?\*/\s*))*"  # Comments before WITH
        r"with\s+"
        r"((--.*(?:\n|$))|(/\*.*?\*/\s*))*"  # Comments after WITH
        r'"?[\w]+"?\s+as\s*\(\s*'
        r"(select.*?\))"  # Main query
        r"\s*$"
    )

    match_cte = re.match(
        cte_pattern,
        sql.lower(),
        re.IGNORECASE | re.DOTALL,
    )

    if match_cte:
        prefix = sql[: match_cte.start(7)]
        raw_sql = sql[match_cte.start(7) : match_cte.end(7)]
        suffix = sql[match_cte.end(7) :]
    else:
        prefix, raw_sql, suffix = "", sql, ""

    return {
        "sql": raw_sql,
        "prefix": prefix,
        "suffix": suffix,
        "priority": priority,
        "space_before": space_before,
        "space_after": space_after,
    }


def format_output(
    prepare_result: Optional[Dict[str, Any]], sql_to_preview: Dict[str, Dict[str, str]]
) -> Dict[str, str]:
    """
    Formats SQL output with preview and modifications.

    Args:
        prepare_result: Dictionary containing SQL parts and formatting info
        sql_to_preview: Dictionary mapping SQL to preview and modification info

    Returns:
        Dict[str, str]: Dictionary containing:
            - Preview: Query result preview
            - Modification: Modified SQL query
    """

    if prepare_result is None:
        preview, modification, show = "", "", False
    else:
        if (
            prepare_result["priority"] == 0
            or prepare_result["sql"] not in sql_to_preview
        ):
            (
                preview,
                modification,
                show,
            ) = (
                "",
                "",
                False,
            )
        else:
            preview = sql_to_preview[prepare_result["sql"]]["preview"]
            show = True
            cursor_id = get_plugin_param()["cursor_identifier"]

            # modification = (
            #     prepare_result["prefix"]
            #     + (
            #         sql_to_preview[prepare_result["sql"]]["modification"]
            #         if prepare_result["priority"] > 1
            #         else prepare_result["sql"]
            #     )
            #     + prepare_result["suffix"]
            # )

            
            # cursor_position = modification.find(cursor_id)

            # modification = (
            #     modification[:cursor_position]
            #     + prepare_result["space_before"]
            #     + cursor_id
            #     + prepare_result["space_after"]
            #     + modification[cursor_position + len(cursor_id) :]
            # )

            # modification = modification.replace(cursor_id, "")

            # with open("preview.sql", "w") as f:
            #     f.write(
            #         sql_to_preview[prepare_result["sql"]]["modification"].replace(
            #             cursor_id, ""
            #         )
            #     )
            # with open("preview.txt", "w") as f:
            #     f.write(sql_to_preview[prepare_result["sql"]]["preview"])
            
            modification = sql_to_preview[prepare_result["sql"]][
                "modification"
            ].replace(cursor_id, "")
            modification = modification.rstrip()
            if modification.endswith(";"):
                modification = modification[:-1].rstrip()
            

    complete = True if get_recent_tid("llm") == get_background_tid() else False

    return {
        "preview": preview,
        "modification": modification,
        "complete": complete,
        "show": show,
    }
    
def format_modification(modification: Optional[str]) -> Optional[str]:
    if modification is None:
        return None
    cursor_id = get_plugin_param()["cursor_identifier"]
    modification = modification.replace(cursor_id, "").rstrip()
    if modification.endswith(";"):
        modification = modification[:-1].rstrip()
    return modification


def format_preview(result: List[Any]) -> str:
    """
    Formats query result preview with truncation.

    Args:
        result: Query result rows

    Returns:
        str: Formatted preview string with comments
    """
    preview_lines = (
        pd.DataFrame(
            [parse_preview(str(row)) for row in result],
            columns=[desc[0] for desc in get_cursor()["execute"].description],
        )
        .to_string()
        .split("\n")
    )

    truncated_preview = []
    char_count = 0
    plugin_params = get_plugin_param()

    for i, line in enumerate(preview_lines):
        if (
            i == plugin_params["preview"]
            or char_count + len(line) > plugin_params["preview_char"]
        ):
            truncated_preview.append("...")
            break

        truncated_preview.append(line)
        char_count += len(line)

    if get_sample():
        truncated_preview.append("SpeQL may make mistakes. Check important info.")

    return "\n".join(truncated_preview)
