# Copyright (c) 2025 Haoyu Li
# Released under the MIT License.
# See LICENSE file in the project root for details.

#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Query Sampling Module
"""

import sys
import re
import traceback
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

from extract import extract
from param import get_dialect_param

# -----------------------------------------------------------------------------
# Global State
# -----------------------------------------------------------------------------

is_sample: bool = False

# -----------------------------------------------------------------------------
# Sample State Management
# -----------------------------------------------------------------------------


def set_sample() -> None:
    """Set sampling flag to True."""
    global is_sample
    is_sample = True


def reset_sample() -> None:
    """Clear sampling flag."""
    global is_sample
    is_sample = False


def get_sample() -> bool:
    """Return the sampling flag. If True, SpeQL will alert the user."""
    return is_sample


# -----------------------------------------------------------------------------
# Query Sampling
# -----------------------------------------------------------------------------


def sample_script(sql: str, retry_time: int) -> str:
    """
    Modifies SQL query to sample data based on retry count.
    Now supports Redshift and Snowflake.

    Args:
        sql: Original SQL query
        retry_time: Number of retry attempts

    Returns:
        str: Modified SQL query with sampling if applicable,
             original query otherwise
    
    Raises:
        Exception: If the database is not supported

    Note:
        Sampling reduces data by factor of 2^retry_time
    """
    if retry_time == 0:
        return sql

    try:
        from_clause = extract(sql)["from"]
    except Exception:
        traceback.print_exc()
        return sql

    # Verify single table reference pattern exists
    table_pattern = (
        f"FROM {re.escape(from_clause[0]['name'])} "
        f"AS {re.escape(from_clause[0]['alias'])}"
    )

    if sql.lower().count(table_pattern.lower()) != 1:
        return sql

    # Apply sampling transformation
    sampling_ratio = 1 / (2**retry_time)
    
    if get_dialect_param()["endpoint"] == "redshift":
        sampled_query = re.sub(
            table_pattern,
            f"FROM (SELECT * FROM {from_clause[0]['name']} "
            f"WHERE RANDOM() < {sampling_ratio}) "
            f"AS {from_clause[0]['alias']}",
            sql,
            flags=re.IGNORECASE,
        )
        
    elif get_dialect_param()["endpoint"] == "snowflake":
        sampled_query = re.sub(
            table_pattern,
            f"FROM (SELECT * FROM {from_clause[0]['name']} "
            f"TABLESAMPLE ({int(sampling_ratio * 100)} PERCENT) "
            f"AS {from_clause[0]['alias']}",
            sql,
            flags=re.IGNORECASE,
        )
    
    else:
        raise Exception("Unsupported database")

    from format import format
    return format(sampled_query)
