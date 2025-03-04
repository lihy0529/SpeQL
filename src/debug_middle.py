# Copyright (c) 2025 Haoyu Li
# Released under the MIT License.
# See LICENSE file in the project root for details.

#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Debug Middle Module
====================

This module provides functionality for debugging the middle part of an SQL query.
It uses the LLM to speculate and complete the middle part of the query. It will
be used when getting powerset of a main query.
"""

import sys
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

from llm_api import get_llm_response
from prompt import get_prompt
from schema import get_useful_schema
from vector_db import get_useful_historical_sql
from param import get_plugin_param, get_dialect_param


# -----------------------------------------------------------------------------
# Speculate Middle
# -----------------------------------------------------------------------------


async def speculate_middle(sql: str) -> str:
    """
    Speculates and completes the middle part of an SQL query where the cursor is positioned.
    
    Args:
        sql: Input SQL query containing a cursor identifier
        
    Returns:
        str: The speculated middle part of the SQL query
    """
    cursor_id = get_plugin_param()["cursor_identifier"]
    cursor_pos = sql.find(cursor_id)
    
    Input = {
        "prefix": sql[:cursor_pos],
        "suffix": sql[cursor_pos + len(cursor_id):]
    }

    message = [
        {
            "role": "system",
            "content": get_prompt(
                "debug_middle",
                get_dialect_param()["input"],
                get_useful_schema(sql),
                get_useful_historical_sql(sql),
            ),
        },
        {
            "role": "user",
            "content": f"""
prefix: {Input['prefix']}
suffix: {Input['suffix']}
""",
        },
    ]


    return_value = await get_llm_response("middle", 0, message)
    return_value = return_value[return_value.find("middle: ") + len("middle: "):]

    return return_value
