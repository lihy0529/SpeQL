# Copyright (c) 2025 Haoyu Li
# Released under the MIT License.
# See LICENSE file in the project root for details.

#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Dialect module for SpeQL.
"""

import re
import sys
from pathlib import Path
from typing import List

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
# Local Import
# -----------------------------------------------------------------------------

from log import log
from extract import extract

# -----------------------------------------------------------------------------
# SQL Possible Keywords and Dialects
# -----------------------------------------------------------------------------

def get_keyword_list() -> List[str]:
    """
    Returns a list of SQL keywords used for syntax validation.
    
    Returns:
        List[str]: Common SQL keywords in lowercase
    """
    return [
        "add", "all", "alter", "and", "any", "as", "between", "by",
        "cascade", "case", "cast", "coalesce", "column", "constraint",
        "create", "current_date", "current_time", "current_timestamp",
        "date", "delete", "distinct", "drop", "else", "end", "except",
        "exists", "false", "foreign", "from", "full", "group", "having",
        "ifnull", "ilike", "in", "index", "inner", "insert", "intersect",
        "interval", "into", "is", "join", "key", "left", "like", "limit",
        "materialized", "not", "now", "null", "offset", "on", "or",
        "order", "outer", "primary", "references", "right", "select",
        "sequence", "set", "some", "table", "temporary", "then", "time",
        "timestamp", "top", "true", "union", "unique", "update", "values",
        "view", "when", "where", "substring", "with",
    ]


def get_dialect_list() -> List[str]:
    """
    Returns a list of supported SQL dialects.
    
    Returns:
        List[str]: Supported SQL dialect names
    """
    return [
        "atheta", "bigquery", "clickhouse", "databricks", "doris",
        "drill", "duckdb", "hive", "materialize", "mysql", "oracle",
        "postgres", "presto", "prql", "redshift", "risingwave",
        "snowflake", "spark", "spark2", "sqlite", "starrocks",
        "tableau", "teradata", "trino", "tsql",
    ]

# -----------------------------------------------------------------------------
# Check if the SQL script supports rewriting
# -----------------------------------------------------------------------------

def support_rewrite(script: str) -> bool:
    """
    Checks if a SQL script supports rewriting by validating against unsupported keywords.
    
    Args:
        script: SQL script to validate
        
    Returns:
        bool: True if script supports rewriting, False otherwise
    """
    unsupport_keyword_list = [
        "select", "offset", "union", "intersect",
    ]

    pattern = r"\b(.*?)\b(" + "|".join(unsupport_keyword_list) + r")\b(.*?)\b"
    select_pos = script.lower().find("select") + len("select ")
    check_unsupport_keyword = re.search(
        pattern,
        script[select_pos:],
        re.IGNORECASE,
    )
    if check_unsupport_keyword is not None:
        return False
    try:
        extract(script)
        return True
    except Exception as e:
        return False

# -----------------------------------------------------------------------------
# SQL Patching
# -----------------------------------------------------------------------------

def patch(sql: str) -> str:
    """
    Applies various patches to SQL script for compatibility.
    
    Patches include:
    - Converting DOUBLE to DOUBLE PRECISION
    - Fixing date format padding
    - Fixing FROM clause formatting
    
    Args:
        sql: SQL script to patch
        
    Returns:
        str: Patched SQL script
    """
    
    sql = re.sub(r"\bAS DOUBLE\b", "AS DOUBLE PRECISION", sql)
    sql = re.sub(r"\bPRECISION PRECISION\b", "PRECISION", sql)
    
    sql = re.sub(
        r"'(\d{4})-(\d{1})-(\d{1,2})'",
        lambda m: f"'{m.group(1)}-{int(m.group(2)):02d}-{int(m.group(3)):02d}'",
        sql,
    )
    sql = re.sub(
        r"'(\d{4})-(\d{2})-(\d{1})'",
        lambda m: f"'{m.group(1)}-{m.group(2)}-{int(m.group(3)):02d}'",
        sql,
    )
    
    sql = re.sub(
        r"FROM\s+\(\s*\"(\w+)\"\s+AS\s+\"(\w+)\"\)", 
        r'FROM "\1" AS "\2"', 
        sql
    )
    
    return sql
