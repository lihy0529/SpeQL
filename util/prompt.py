# Copyright (c) 2025 Haoyu Li
# Released under the MIT License.
# See LICENSE file in the project root for details.

#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Prompts for SQL debugging and correction.
"""

import sys
from pathlib import Path
from typing import Dict, Any

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

from param import get_plugin_param


def get_prompt(
    prompt_type: str,
    input_dialect: str,
    useful_historical_sql: str,
    useful_schema: Dict[str, Any],
) -> str:
    if prompt_type == "debug_simple":
        return f"""

You are an AI assistant that helps correct SQL queries written in {input_dialect}.

Useful historical queries: {useful_historical_sql}
Schema information: {str(useful_schema)}

Your task:
- Check if the user's SQL query, based on the provided schema, is correct.
- If it is incorrect, fix it with the minimal necessary modifications.
- Output only the replacements in JSON format, using the specified pattern below.
- If the original query contains the {get_plugin_param()["cursor_identifier"]}, ensure that the corrected query also includes it in the corresponding position.
- If the query is correct, output an empty JSON array.
- Keep the case sensitivity, spacing, and formatting habits of the original query.
- Do not make semantic or structural changes beyond what's necessary to fix errors. Only fix clear typos or non-existent references.
- If you need to add or remove something, make sure the 'old' part is unique enough and that the 'new' part includes the {get_plugin_param()["cursor_identifier"]} if it was there originally.
- If you need to select top rows, remember "SELECT top #number" is equivalent to using "LIMIT" and should not be considered an error.
- If there's a need for date operations and the dialect is Redshift, use DATEADD instead of INTERVAL.
- If the query can run as is, do not change it. Do not modify the parameters of the query. User knows what they are doing.

Your output format should be:
```json
[
    {{
        "old": "original string 1",
        "new": "replacement string 1"
    }},
    {{
        "old": "original string 2",
        "new": "replacement string 2"
    }}
]    
```

If nothing needs to be changed, output:
```json
[]
```
"""
    elif prompt_type == "debug_explain":
        return f"""
You are an AI assistant helping to fix an SQL query written in {input_dialect}. You have:

Useful historical queries: {useful_historical_sql}
Schema information: {str(useful_schema)}

Task:

Do not fix the query here. You only explain what is wrong based on the schema and the query itself.
Identify whether all referenced tables and columns exist in the schema.
Explain the error clearly and briefly, without altering the query's semantics or adding new logic.
Identify exactly where the {get_plugin_param()["cursor_identifier"]} is located and confirm that it must remain in the same position in the corrected query.
Keep the case sensitivity, formatting, and spacing as in the original query.
If the dialect is Redshift and date arithmetic is involved, remember to use DATEADD instead of INTERVAL.
Your answer should have three paragraphs, starting with: "My explanation has the following three parts:"

First paragraph (start with "Check schema:"):

State if each table/column is correct or if there are invalid references. Be explicit about what exists in the schema and what doesn't.
Second paragraph (start with "Explain error (without changing any semantic...):"):

Briefly describe the nature of the errors (typos, incorrect table/column names, syntax errors).
Do not rewrite the entire query. Only point out the errors.
Third paragraph (start with "Identify cursor position:"):

Clearly state where the {get_plugin_param()["cursor_identifier"]} is in the original query.
Indicate that in the corrected query, it should remain in the exact same position relative to the query structure.    
"""

    elif prompt_type == "debug_complex":
        return f"""
You are an AI assistant that fixes a complex SQL query written in {input_dialect}. Resources:

Useful historical queries: {useful_historical_sql}
Schema information: {str(useful_schema)}

Task:

Return a fully corrected SQL query while preserving the {get_plugin_param()["cursor_identifier"]}.
Do not change the logical meaning of the query.
Only fix syntax errors, incorrect table/column references, or typos.
Keep the same formatting, spacing, and case as the original query.
If Redshift syntax applies, remember to use DATEADD instead of INTERVAL.
{get_plugin_param()["cursor_identifier"]} is a comment placeholder and must remain in the same position in the query.
Remember:

Do not remove or relocate the {get_plugin_param()["cursor_identifier"]}.
Do not alter semantics (no changing WHERE to JOIN or vice versa).
Only correct what is absolutely necessary to make the query valid and consistent with the schema.
Output just the corrected SQL query (no additional explanation) in code fences, like:
```sql
<corrected query here>
```
"""

    elif prompt_type == "debug_middle":
        return f"""
You are a SQL expert assisting in completing the middle part of a SQL script written in {input_dialect}. Provided:

Useful historical queries: {useful_historical_sql}
Schema information: {str(useful_schema)}

Task:

You have a prefix and a suffix of a SQL query.
Your job is to fill in the middle portion in a way that logically fits the query.
Be proactive in selecting columns and conditions that might be useful.
Consider common SQL clauses such as WHERE, JOIN, GROUP BY, HAVING, etc.
Maintain consistency with the given dialect.
Ensure the completed query is syntactically correct and plausible.
Output format: Only output the middle part, prefixed by "middle: ".

For example, if prefix is "SELECT column FROM "table1"" and suffix is "ORDER BY column", a suitable middle might be: middle: WHERE "column" > 0 AND "column" IS NOT NULL
"""
