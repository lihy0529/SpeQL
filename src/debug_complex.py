# Copyright (c) 2025 Haoyu Li
# Released under the MIT License.
# See LICENSE file in the project root for details.

#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Debug Complex Module
======================

This module handles complex SQL debugging with LLM assistance. It tries at
most max_retry times to get a correct SQL query.
"""

import sys
import threading
import asyncio
from pathlib import Path

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
from llm_api import get_llm_response
from prompt import get_prompt
from debug_rule import get_replacement_rule
from schema import get_useful_schema
from vector_db import get_useful_historical_sql
from debug_simple import append_debug_simple_message, get_error_info
from debug_rule import set_rule, get_rule
from param import get_plugin_param, get_dialect_param
from concurrency import get_recent_tid, set_running_inference, get_explain_cursor_lock
from log import log
from cost import get_max_retry

# -----------------------------------------------------------------------------
# Debug Complex
# -----------------------------------------------------------------------------


async def debug_complex_inner(
    sql: str,
    error_info: str,
    explain_message: list,
    debug_message: list,
    complex_debug_iterator: int,
) -> str:
    """
    Inner function to handle complex SQL debugging with LLM assistance.

    Args:
        SQL: The SQL query to debug
        ErrorInfo: Error message from previous execution
        ExplainMessage: List of messages for explanation context
        DebugMessage: List of messages for debugging context
        ComplexDebugIterator: Current iteration count

    Returns:
        str: Rewritten SQL query or original SQL if max retries reached
    """
    explain_message.append({"role": "user", "content": f"{sql}\n{error_info}"})

    explain = await get_llm_response(
        "explain", complex_debug_iterator, explain_message, max_tokens=256
    )

    debug_message.append({"role": "user", "content": explain})
    message = debug_message.copy()

    for _ in range(get_max_retry()):
        rewrite = await get_llm_response("complex", complex_debug_iterator, message)

        if (
            "```sql" not in rewrite
            or "```" not in rewrite[rewrite.find("```sql") + len("```sql") :]
        ):
            message.append(
                {
                    "role": "user",
                    "content": """
Please output the correct SQL query starting with ```sql.
""",
                }
            )
            continue

        cursor_id = get_plugin_param()["cursor_identifier"]
        if rewrite.count(cursor_id) != 1:
            message.append(
                {
                    "role": "user",
                    "content": f"""
Please make sure the cursor identifier {cursor_id} is in the appropriate position!
""",
                }
            )
            continue

        rewrite = rewrite[rewrite.find("```sql") + len("```sql") :]
        rewrite = rewrite[: rewrite.find("```")].strip()
        debug_message.append({"role": "assistant", "content": f"```sql{rewrite}```"})
        return rewrite

    return f"```sql{sql}```"


async def debug_complex(sql: str) -> str | None:
    """
    Main complex debugging function that attempts to fix SQL queries using LLM.

    Args:
        SQL: The SQL query to debug

    Returns:
        str | None: Corrected SQL query or None if debugging fails/cancelled

    Raises:
        Exception: Happens when LLM response raises an error.
    """
    explain_message = [
        {
            "role": "system",
            "content": get_prompt(
                "debug_explain",
                get_dialect_param()["input"],
                get_useful_historical_sql(sql),
                get_useful_schema(sql),
            ),
        }
    ]

    debug_message = [
        {
            "role": "system",
            "content": get_prompt(
                "debug_complex",
                get_dialect_param()["input"],
                get_useful_historical_sql(sql),
                get_useful_schema(sql),
            ),
        },
        {"role": "user", "content": sql},
    ]

    rewrite = sql
    error_info = get_error_info()

    for complex_debug_iterator in range(get_max_retry()):
        if get_recent_tid("llm") != threading.get_ident():
            return None

        try:
            GetLLMResponse = asyncio.create_task(
                debug_complex_inner(
                    rewrite,
                    error_info,
                    explain_message,
                    debug_message,
                    complex_debug_iterator,
                )
            )
            set_running_inference(GetLLMResponse)
            rewrite = await GetLLMResponse

            try:
                with get_explain_cursor_lock():
                    get_cursor()["explain"].execute(f"EXPLAIN {rewrite}")

                    temp_rule = get_replacement_rule(sql, rewrite)
                    set_rule(
                        [
                            rule
                            for rule in temp_rule
                            if get_plugin_param()["cursor_identifier"]
                            not in rule["old"]
                        ]
                    )

                    append_debug_simple_message(
                        {
                            "role": "assistant",
                            "content": f"""
```json{str(get_rule())}```
""",
                        }
                    )

                    return rewrite

            except Exception as e:
                """
                Cannot explain the SQL query. Debug again until max_retry times.
                """
                error_info = str(e)

        except asyncio.CancelledError:
            return None

        except Exception as e:
            # This should not happen.
            log("error.txt", f"{str(e)}")
            raise e

    return None
