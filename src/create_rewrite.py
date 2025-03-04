# Copyright (c) 2025 Haoyu Li
# Released under the MIT License.
# See LICENSE file in the project root for details.

#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Create Rewrite Module
=======================

This module provides functionality for rewriting and optimizing SQL queries.
It handles query analysis, aggregate function detection, and table/column matching.

Key Features:
    - SQL query rewriting
    - Get powerset of a main query
    - Resolve alias conflict of a main query
"""

import sys
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple

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

from format import format_clause, format
from sample import set_sample
from concurrency import get_speculate_middle
from schema import get_schema
from extract import extract
from dialect import support_rewrite
from create_struct import temporary_table_pool
from log import log

# -----------------------------------------------------------------------------
# Global Variables
# -----------------------------------------------------------------------------

agg_func_dict: Dict[str, List[Optional[str]]] = {}
rewrite_clause_dict: Dict[Tuple[str, str, str], list] = {}

# -----------------------------------------------------------------------------
# Get Aggregate Function
# -----------------------------------------------------------------------------


def get_agg_func(sql: str) -> Optional[List[Optional[str]]]:
    """
    Analyzes a SQL SELECT statement to identify aggregate functions (COUNT, MAX, MIN, SUM).

    Args:
        sql: The SQL SELECT statement to analyze

    Returns:
        List of aggregate function names (or None for non-aggregate columns)
        Returns None if invalid or non-parseable aggregate functions are found

    Example:
        # Parseable
        >>> get_agg_func("SELECT COUNT("t"."col"), "t"."name" FROM "table" t")
        ['count', None]

        # Unparseable
        >>> get_agg_func("SELECT COUNT(COUNT("t"."col")), "t"."name" FROM "table" t")
        None
    """
    global agg_func_dict

    if sql in agg_func_dict:
        return agg_func_dict[sql].copy()

    extract_sql = extract(sql)
    agg_func: List[Optional[str]] = []

    for item in [item["name"] for item in extract_sql["select"]]:
        """
        Match aggregate function pattern. The caller should ensure that the
        column should at least have a table reference.

        Example:
            >>> 'count("t"."col")' -> "count"
            >>> 'max("s"."t"."col")' -> "max"
            >>> 'max(count("t"."col"))' -> Cannot match
        """
        match_agg = re.match(
            r"^(count|max|min|sum)\s*\(\s*(\"[\w]+\"\.)?\"[\w]+\"\.\"[\w]+\"\s*\)$",
            item,
            re.IGNORECASE,
        )

        """
        Match column reference pattern. The caller should ensure that the
        column should at least have a table reference.
        
        Example:
            >>> "t"."col" -> "t"."col"
            >>> "s"."t"."col" -> "s"."t"."col"
        """
        match_column = re.match(
            r"^(\"[\w]+\"\.)?\"[\w]+\"\.\"[\w]+\"$", item, re.IGNORECASE
        )

        if match_agg:
            agg_func.append(match_agg.group(1).lower())
        elif match_column:
            agg_func.append(None)
        else:
            return None

    agg_func_dict[sql] = agg_func.copy()
    return agg_func_dict[sql]


# -----------------------------------------------------------------------------
# Match Table and Column
# -----------------------------------------------------------------------------


def match_table_and_column(cond: str, from_alias: str) -> Dict[str, List[str]]:
    """
    Extracts table and column references from a condition like "t1.col1 = t2.col2".

    Args:
        cond: Condition to analyze
        from_alias: Alias of the FROM clause table

    Returns:
        Dictionary containing:
            - 'Table': List of table references.
            - 'Column': List of column references whose table is in the FROM clause.

    Example:
        >>> match_table_and_column('"table1"."col1" = "schema2"."table2"."col2"', 'table1')
        {'Table': ['"table1"', '"schema2"."table2"'], 'Column': ['"col1"']}

        # Note: '"col2"' is not matched because it is not in the FROM clause.
    """
    pattern_schema_table_column = (
        r'(?P<schema>"\w+")\.(?P<table>"\w+")\.(?P<column>"\w+")'
    )
    pattern_table_column = r'(?P<table>"\w+")\.(?P<column>"\w+")'
    pattern_from_column = rf"{re.escape(from_alias)}\.(\"[\w]+\")"

    # Extract column references with given alias
    match_column_list = re.findall(pattern_from_column, cond)

    match_table_list = []
    # Extract fully qualified references (schema.table.column)
    matches = re.finditer(pattern_schema_table_column, cond)
    for match in matches:
        schema_table = f"{match.group('schema')}.{match.group('table')}"
        match_table_list.append(schema_table)
        # Remove matched portion from string to avoid double matching
        schema_table_column = f"{schema_table}.{match.group('column')}"
        cond = cond.replace(schema_table_column, "")

    # Extract table qualified references (table.column)
    matches = re.finditer(pattern_table_column, cond)
    for match in matches:
        match_table_list.append(match.group("table"))

    return {"table": match_table_list, "column": match_column_list}


# -----------------------------------------------------------------------------
# Rewrite Clause
# -----------------------------------------------------------------------------


def rewrite_clause_inner(origin: str, target: str, clause_type: str) -> dict:
    """
    Rewrites a specific clause of a SQL query based on origin and target queries.

    Args:
        origin: Original SQL query
        target: Target SQL query to rewrite
        clause_type: Type of clause to rewrite ('From', 'Select', 'Join', etc.)

    Returns:
        Dict containing:
            - 'Condition': Boolean indicating if rewrite is possible. If not, the condition is False and
            the 'Value' is an empty list. The caller should consider returning the target query.
            - 'Value': Rewritten clause value, which should be a list. However, the content in
            the list can be diverse according to the clause type. We explain the details event
            by event.
    """
    global rewrite_clause_dict

    if (origin, target, clause_type) in rewrite_clause_dict:
        return rewrite_clause_dict[(origin, target, clause_type)]

    extract_origin = extract(origin)
    extract_target = extract(target)
    if clause_type == "from":
        """
        Rewrite FROM clause. The caller uses it to match the target sql to an existing temporary
        table in result set cache.

        Return:
            {
                "condition": bool,
                "value": [
                    {
                        "name": str,
                        "alias": str
                    }
                ]
            }

        Example:
        # CREATE TEMPORARY TABLE "tmp_tb" AS ... FROM "table" as "tb";
        >>> origin = '... FROM "table" as "tb";'
        >>> target = '... FROM "table" as "tb";'
        >>> rewrite_clause_inner(origin, target, "from")
        {'condition': True, 'value': [{'name': '"tmp_tb"', 'alias': '"tmp_tb"'}]}

        Warning:
            The length of the 'value' field is always 1.
            Use return_value["value"][0]["name"] to get the name of the temporary table.
        """
        from_condition = extract_origin["from"][0] == extract_target["from"][0]

        if extract_origin["from"][0] is None:
            from_condition = False

        if from_condition:
            check = temporary_table_pool.check(origin, update_lru=False)
            from_value = [{"name": check["name"], "alias": check["name"]}]
        else:
            from_value = []

        return_value = {"condition": from_condition, "value": from_value}

    elif clause_type == "select":
        """
        Rewrite SELECT clause. The caller uses it to replace the table name in the SELECT clause of the target sql
        with the name of the temporary table. And it also handles the aggregate function and subset of columns.

        Return:
            {
                "condition": bool,
                "value": [
                    {
                        "name": str,
                        "alias": str
                    }
                ]
            }

        Example:
            # CREATE TEMPORARY TABLE "tmp_tb" AS SELECT "tb"."col1" AS "col1", "tb"."col2" AS "col2" ...
            >>> origin = 'SELECT "count("tb"."col1")" AS "col1", "tb"."col2" AS "col2" FROM ...'
            >>> target = 'SELECT "count("tb"."col1")" AS "col1" FROM ...'
            >>> rewrite_clause_inner(origin, target, "select")

            # If there is no Group By in rewritten target
            {'condition': True, 'value': [{'name': '"tmp_tb"."col1"', 'alias': 'col1'}]}

            # If there is a Group By in rewritten target
            {'condition': True, 'value': [{'name': '"count("tmp_tb"."col1")', 'alias': 'col1'}]}
        """
        select_condition = True

        for select_item in extract_target["select"]:
            if select_item not in extract_origin["select"]:
                select_condition = False
                break

        from_clause = rewrite_clause_inner(origin, target, "from")
        group_clause = rewrite_clause_inner(origin, target, "group")
        agg_func = get_agg_func(target)

        select = []
        if select_condition:
            for i in range(len(extract_target["select"])):
                if agg_func and agg_func[i] is not None and group_clause["value"]:
                    select.append(
                        {
                            "name": format(
                                agg_func[i]
                                + "("
                                + from_clause["value"][0]["alias"]
                                + "."
                                + extract_target["select"][i]["alias"]
                                + ")"
                            ),
                            "alias": extract_target["select"][i]["alias"],
                        }
                    )
                else:
                    select.append(
                        {
                            "name": format(
                                from_clause["value"][0]["alias"]
                                + "."
                                + extract_target["select"][i]["alias"]
                            ),
                            "alias": extract_target["select"][i]["alias"],
                        }
                    )

        return_value = {"condition": select_condition, "value": select}

    elif clause_type == "join":
        """
        Rewrite JOIN clause. Condition is True only if the target sql has a same of
        powerset of JOIN clauses in the origin sql. Powerset means that we can rewrite
        the JOIN clause with the name of the temporary table. This is one of the
        most tricky part of the rewrite.

        Return:
            {
                "condition": bool,
                "value": [
                    {
                        "table": {
                            "name": str,
                            "alias": str
                        },
                        "type": str,
                        "condition": [str]  # If the 'type' is not CROSS, the 'condition' is a
                                            # list of strings that are rewritten join conditions;
                                            # otherwise, it should be ['cross'] (use a string to
                                            # indicate the list is not empty)
                    }
                ]
            }

        Example:
            # Rewriteable
            >>> origin = "... INNER JOIN A INNER JOIN B"
            >>> target = "... INNER JOIN A INNER JOIN C INNER JOIN B"
            >>> rewrite_clause_inner(origin, target, "join")
            "... origin INNER JOIN C"

            # Not rewriteable
            >>> origin = "... INNER JOIN A INNER JOIN B LEFT JOIN D"
            >>> target = "... INNER JOIN A INNER JOIN C INNER JOIN B LEFT JOIN D"
            >>> rewrite_clause_inner(origin, target, "join")
            {'condition': False, 'value': []}
        """

        join_condition = True
        join = [
            {
                "table": {
                    "name": extract_target["join"][i]["table"]["name"],
                    "alias": extract_target["join"][i]["table"]["alias"],
                },
                "type": extract_target["join"][i]["type"],
                "condition": [],
            }
            for i in range(len(extract_target["join"]))
        ]

        outer_origin_ptr = 0
        mem_join_ptr = 0
        for outer_target_ptr in range(len(extract_target["join"])):

            if outer_origin_ptr == len(extract_origin["join"]):
                for inner_target_ptr in range(
                    len(extract_target["join"][outer_target_ptr]["condition"])
                ):
                    join[outer_target_ptr]["condition"].append(
                        extract_target["join"][outer_target_ptr]["condition"][
                            inner_target_ptr
                        ]
                    )

            elif (
                extract_target["join"][outer_target_ptr]["table"]
                != extract_origin["join"][outer_origin_ptr]["table"]
            ):
                for inner_target_ptr in range(
                    len(extract_target["join"][outer_target_ptr]["condition"])
                ):
                    join[outer_target_ptr]["condition"].append(
                        extract_target["join"][outer_target_ptr]["condition"][
                            inner_target_ptr
                        ]
                    )

            else:
                inner_origin_ptr = 0
                for inner_target_ptr in range(
                    len(extract_target["join"][outer_target_ptr]["condition"])
                ):
                    if inner_origin_ptr == len(
                        extract_origin["join"][outer_origin_ptr]["condition"]
                    ):
                        join[outer_target_ptr]["condition"].append(
                            extract_target["join"][outer_target_ptr]["condition"][
                                inner_target_ptr
                            ]
                        )

                    elif (
                        extract_target["join"][outer_target_ptr]["condition"][
                            inner_target_ptr
                        ]
                        != extract_origin["join"][outer_origin_ptr]["condition"][
                            inner_origin_ptr
                        ]
                    ):
                        join[outer_target_ptr]["condition"].append(
                            extract_target["join"][outer_target_ptr]["condition"][
                                inner_target_ptr
                            ]
                        )

                    else:
                        inner_origin_ptr += 1

                if inner_origin_ptr != len(
                    extract_origin["join"][outer_origin_ptr]["condition"]
                ):
                    join_condition = False

                outer_origin_ptr += 1
                if outer_origin_ptr == len(extract_origin["join"]):
                    mem_join_ptr = outer_target_ptr + 1

        """
        Original join condition is not included in the target sql.
        """
        if outer_origin_ptr != len(extract_origin["join"]):
            join_condition = False

        else:
            """
            Cannot rewrite the internal left/right/full/cross join condition.
            """
            for outer_join_ptr in range(mem_join_ptr):
                if join[outer_join_ptr]["condition"] != []:
                    for outer_join_ptr_2 in range(outer_join_ptr, mem_join_ptr):
                        if join[outer_join_ptr_2]["type"] != "INNER":
                            join_condition = False

            if join_condition:

                from_clause = rewrite_clause_inner(origin, target, "from")

                for outer_join_ptr in range(len(join)):
                    if join[outer_join_ptr]["type"] != "CROSS":
                        for inner_join_ptr in range(
                            len(join[outer_join_ptr]["condition"])
                        ):
                            match = match_table_and_column(
                                join[outer_join_ptr]["condition"][inner_join_ptr],
                                extract_origin["from"][0]["alias"],
                            )
                            """
                            Cannot refer to columns or tables that are not defined in the rewritten sql.
                            """
                            for table in match["table"]:
                                if (
                                    table != extract_origin["from"][0]["alias"]
                                    and table != join[outer_join_ptr]["table"]["alias"]
                                ):
                                    join_condition = False
                            for column in match["column"]:
                                if column not in [
                                    item["alias"] for item in extract_origin["select"]
                                ]:
                                    join_condition = False
                            """
                            Rewrite the join condition with the new table alias.
                            """
                            rewritten_condition = re.sub(
                                rf'(?<!\.){re.escape(extract_origin["from"][0]["alias"])}\.',
                                f"{from_clause['value'][0]['alias']}.",
                                join[outer_join_ptr]["condition"][inner_join_ptr],
                            )

                            join[outer_join_ptr]["condition"][
                                inner_join_ptr
                            ] = rewritten_condition

        if join_condition:
            join = [item for item in join if item["condition"]]
        else:
            join = []

        return_value = {"condition": join_condition, "value": join}

    elif clause_type in ["where", "having"]:
        """
        Rewrite WHERE or HAVING clause. Condition is True only if the target sql has a same of
        powerset of WHERE or HAVING clauses in the origin sql. Powerset means the target sql does
        not only have all the conditions in the origin sql, but also has more conditions.

        Return:
            {
                "condition": bool,
                "value": [str] # The rewritten where or having conditions
            }

        Example:
            >>> origin = "WHERE A"
            >>> target = "WHERE A AND B"
            # Rewrittion should be ... FROM origin WHERE B
        """
        origin_ptr = 0
        condition = True
        value = []
        from_clause = rewrite_clause_inner(origin, target, "from")

        for target_ptr in range(len(extract_target[clause_type])):
            need_processing = (
                origin_ptr == len(extract_origin[clause_type])
                or extract_target[clause_type][target_ptr]
                != extract_origin[clause_type][origin_ptr]
            )

            if need_processing:
                match = match_table_and_column(
                    extract_target[clause_type][target_ptr],
                    extract_origin["from"][0]["alias"],
                )

                for table in match["table"]:
                    if table != extract_origin["from"][0]["alias"]:
                        condition = False

                for column in match["column"]:
                    if column not in [
                        item["alias"] for item in extract_origin["select"]
                    ]:
                        condition = False

                if not condition:
                    break

                """
                Rewrite the condition with new table alias.

                Example:
                    # In temporary_table_pool.name_to_script: {'name': "tmp_tb", 'script': origin}
                    # In origin: '"table"."col1 = ..." -> '"tmp_tb"."col1 = ..."
                """

                rewritten_condition = extract_target[clause_type][target_ptr]

                for item in extract_origin["select"]:
                    """
                    Match aggregate function pattern.

                    Warning: This may not include all the aggregate functions. More testing is needed.
                    """
                    if (
                        re.match(
                            r"^(count|max|min|sum|avg)\s*\(\s*(\"[\w]+\"\.)?\"[\w]+\"\.\"[\w]+\"\s*\)$",
                            item["name"],
                            re.IGNORECASE,
                        )
                        and item["name"] in extract_target[clause_type][target_ptr]
                    ):
                        rewritten_condition = re.sub(
                            item["name"],
                            f"{extract_origin['from'][0]['alias']}.{item['alias']}",
                            rewritten_condition,
                        )

                """
                Check if the condition contains aggregate function.
                
                Warning: This may not include all the aggregate functions. More testing is needed.
                """
                if re.search(
                    r"(count|max|min|sum|avg)\s*\(.*\)",
                    rewritten_condition,
                    re.IGNORECASE,
                ):
                    condition = False
                    break

                rewritten_condition = re.sub(
                    rf'(?<!\.){re.escape(extract_origin["from"][0]["alias"])}\.',
                    f"{from_clause['value'][0]['alias']}.",
                    rewritten_condition,
                )
                value.append(rewritten_condition)

            else:
                origin_ptr = min(origin_ptr + 1, len(extract_origin[clause_type]))

        if origin_ptr != len(extract_origin[clause_type]):
            condition = False

        if condition:
            value = [item for item in value if item is not None]
        else:
            value = []

        return_value = {"condition": condition, "value": value}

    elif clause_type == "group":
        """
        Rewrite GROUP BY clause. This is the most tricky part of the rewrite. We guess there are still
        some bugs in the rewrite. More testing is needed.

        Return:
            {
                "condition": bool,
                "value": [str] # The rewritten group by columns
            }
        """
        from_clause = rewrite_clause_inner(origin, target, "from")
        where_clause = rewrite_clause_inner(origin, target, "where")
        join_clause = rewrite_clause_inner(origin, target, "join")

        has_no_filter = where_clause["value"] == [] and join_clause["value"] == []
        group_match = extract_target["group"] == extract_origin["group"]
        target_has_no_group = extract_target["group"] == []

        if (has_no_filter and group_match) or (
            target_has_no_group and (has_no_filter != group_match)
        ):
            group_condition, group = True, []
        elif not has_no_filter and not group_match and target_has_no_group:
            group_condition, group = False, []
        else:
            group_condition, group = True, extract_target["group"].copy()

            agg_func = get_agg_func(target)
            if not agg_func:
                group_condition = False

            select_string = ", ".join(
                [
                    f"{from_clause['value'][0]['alias']}.{extract_target['select'][i]['alias']} "
                    f"AS {extract_target['select'][i]['alias']}"
                    for i in range(len(extract_target["select"]))
                ]
            )
            where_string = " ".join(where_clause["value"])
            join_string = " ".join(
                [
                    " ".join(join_clause["value"][i]["condition"])
                    for i in range(len(join_clause["value"]))
                ]
            )
            combine_string = select_string + where_string + join_string

            for item in extract_target["group"]:
                if not re.search(r"\s+" + re.escape(item) + r"\s+", combine_string):
                    group_condition = False

                if item not in extract_origin["group"]:
                    group_condition = False

            where_and_join_conditions = where_clause["value"]
            for item in join_clause["value"]:
                if item["type"] != "CROSS":
                    where_and_join_conditions += item["condition"]

            for condition in where_and_join_conditions:
                is_valid = False
                for group_item in group:
                    """
                    Check if the column occurs exactly in some filter condition so that we can
                    reuse the aggregate function.

                    Warning: This is a dangerous part of the rewrite. Double check this part if
                    the query result mismatches.
                    """
                    if re.match(
                        rf"^{re.escape(group_item)}\s*=\s*(\"[\w]+\"\.)?(\"[\w]+\"\.)?\"[\w]+\"$",
                        condition,
                        re.IGNORECASE,
                    ):
                        is_valid = True
                    if re.match(
                        rf"^(\"[\w]+\"\.)?(\"[\w]+\"\.)?\"[\w]+\"\s*=\s*{re.escape(group_item)}$",
                        condition,
                        re.IGNORECASE,
                    ):
                        is_valid = True
                    if re.match(
                        rf"^{re.escape(group_item)}\s*IN\s*\((.*)\)$",
                        condition,
                        re.IGNORECASE,
                    ):
                        is_valid = True

                if not is_valid:
                    group_condition = False

            if not group_condition:
                group = []

        for i in range(len(group)):
            match = match_table_and_column(group[i], extract_origin["from"][0]["alias"])

            for table in match["table"]:
                if table != extract_origin["from"][0]["alias"]:
                    group_condition = False
                    break

                found_in_select = False
                for j in range(len(extract_origin["select"])):
                    if group[i] == extract_origin["select"][j]["name"]:
                        group[i] = (
                            f"{from_clause['value'][0]['alias']}."
                            f"{extract_origin['select'][j]['alias']}"
                        )
                        found_in_select = True
                        break

                if not found_in_select:
                    assert table == extract_origin["from"][0]["alias"]
                    group[i] = group[i].replace(
                        f"{table}.", f"{from_clause['value'][0]['alias']}."
                    )

        if not group_condition:
            group = []

        return_value = {"condition": group_condition, "value": group}

    elif clause_type == "order":
        """
        Rewrite ORDER BY clause. Handles column references in (schema.)?(table.)?column format.

        Return:
            {
                "condition": bool,
                "value": [str] # The rewritten order by expressions
            }

        Example:
            >>> target = "... ORDER BY table.col1 DESC"
            >>> rewrite_clause_inner(origin, target, "order")
            {'condition': True, 'value': ['tmp_tb.col1 DESC']}
        """
        order_condition = True
        order = []

        if extract_origin["order"]:
            return {"condition": False, "value": []}

        for item in extract_target["order"]:
            pattern_schema_table_column = (
                r'(?P<schema>"\w+")\.(?P<table>"\w+")\.(?P<column>"\w+")'
            )
            pattern_table_column = r'(?P<table>"\w+")\.(?P<column>"\w+")'
            pattern_column = r'(?P<column>"\w+")'

            full_column_list = []
            alias_column_list = []
            from_clause = rewrite_clause_inner(origin, target, "from")

            remaining = item
            matches_full = list(re.finditer(pattern_schema_table_column, item))
            if matches_full:
                for match in matches_full:
                    full_column = f"{match.group('schema')}.{match.group('table')}.{match.group('column')}"
                    remaining = remaining.replace(full_column, "")
                    full_column_list.append(full_column)

            matches_table = list(re.finditer(pattern_table_column, remaining))
            if matches_table:
                for match in matches_table:
                    full_column = f"{match.group('table')}.{match.group('column')}"
                    remaining = remaining.replace(full_column, "")
                    full_column_list.append(full_column)

            matches_column = list(re.finditer(pattern_column, remaining))
            if matches_column:
                for match in matches_column:
                    alias_column = match.group("column")
                    remaining = remaining.replace(alias_column, "")
                    alias_column_list.append(alias_column)

            if len(matches_full) + len(matches_table) + len(matches_column) > 1:
                order_condition = False

            for full_column in full_column_list:
                found = False
                for select_item in extract_origin["select"]:
                    if select_item["name"] == full_column:
                        prefix = (
                            f"{from_clause['value'][0]['alias']}.{select_item['alias']}"
                        )
                        suffix = item[item.find(full_column) + len(full_column) :]
                        order.append(f"{prefix}{suffix}")
                        found = True
                        break
                if not found:
                    order_condition = False

            for alias_column in alias_column_list:
                found = False
                for select_item in extract_origin["select"]:
                    if select_item["alias"] == alias_column:
                        prefix = select_item["alias"]
                        suffix = item[item.find(alias_column) + len(alias_column) :]
                        order.append(f"{prefix}{suffix}")
                        found = True
                        break

                if not found:
                    order_condition = False

        if not order_condition:
            order = []
        else:
            order = [item for item in order if item is not None]

        return_value = {"condition": order_condition, "value": order}

    elif clause_type == "limit":
        """
        Rewrite LIMIT clause. The origin query should not have a LIMIT clause,
        and the target LIMIT value must be a valid integer if it exists.

        Return:
            {
                "condition": bool,
                "value": [str] # The LIMIT value as a string
            }

        Example:
            >>> origin = "SELECT * FROM table"
            >>> target = "SELECT * FROM table LIMIT 10"
            >>> rewrite_clause_inner(origin, target, "limit")
            {'condition': True, 'value': ['10']}
        """
        if extract_origin["limit"]:
            extract_origin = extract(origin)
            raise AssertionError(
                f"LIMIT clause should be empty in origin query, origin: {origin}, extract_origin: {extract_origin}"
            )

        limit_condition = True
        if extract_target["limit"] and not re.match(
            r"^\d+$", extract_target["limit"][0]
        ):
            log("error.txt", f"Invalid LIMIT value in target query")
            return {"condition": False, "value": []}

        limit = extract_target["limit"].copy() if limit_condition else []
        return_value = {"condition": limit_condition, "value": limit}

    elif clause_type == "distinct":
        """
        Rewrite DISTINCT clause. The condition is True only if both queries
        have the same DISTINCT specification.

        Return:
            {
                "condition": bool,
                "value": [str] # The DISTINCT keyword if present
            }

        Example:
            >>> origin = "SELECT DISTINCT col FROM table"
            >>> target = "SELECT DISTINCT col FROM table"
            >>> rewrite_clause_inner(origin, target, "distinct")
            {'condition': True, 'value': ['DISTINCT']}
        """
        distinct_condition = extract_origin["distinct"] == extract_target["distinct"]
        distinct = extract_target["distinct"].copy() if distinct_condition else []
        return_value = {"condition": distinct_condition, "value": distinct}

    rewrite_clause_dict[(origin, target, clause_type)] = return_value.copy()
    return rewrite_clause_dict[(origin, target, clause_type)]


def rewrite_clause(origin: str, target: str) -> str:
    """
    Rewrites a target SQL query based on an origin query by comparing and rewriting each clause.

    Args:
        origin: Original SQL query to base the rewrite on
        target: Target SQL query to rewrite

    Returns:
        Rewritten SQL query if successful, otherwise returns original target query
    """

    clause_dict = {}
    for clause_type in [
        "distinct",
        "from",
        "join",
        "where",
        "group",
        "select",
        "having",
        "order",
        "limit",
    ]:
        clause = rewrite_clause_inner(origin, target, clause_type)
        if not clause["condition"]:
            return target
        clause_dict[clause_type] = clause["value"]
    result = format_clause(clause_dict)

    return result


def rewrite(original_script_list: List[str], target_script: str) -> str:
    """
    Attempts to rewrite a target SQL script based on a list of original scripts.

    Args:
        original_script_list: List of original SQL scripts to base the rewrite on
        target_script: Target SQL script to rewrite

    Returns:
        Rewritten SQL script if successful, otherwise returns target script
    """

    rewrite = target_script
    is_sample = False
    for item in original_script_list:
        if support_rewrite(item) and support_rewrite(target_script):
            target_script = format_clause(extract(target_script))
            rewrite = rewrite_clause(item, target_script)

        if rewrite != target_script:
            is_sample = temporary_table_pool.get_is_sample(item)
            if is_sample:
                set_sample()
            break
    return rewrite


# -----------------------------------------------------------------------------
# Get Powerset
# -----------------------------------------------------------------------------


async def get_powerset(script: str) -> str:
    """
    1. Generates a powerset of columns for a SQL query by adding additional columns
    that are not already present in the SELECT or GROUP BY clauses.
    2. Remove ORDER BY and LIMIT clauses.

    Args:
        script: The (MainQuery) SQL query

    Returns:
        Modified SQL query with additional columns added to SELECT and GROUP BY clauses
    """
    extract_script = extract(script)

    extract_script["order"] = []
    extract_script["limit"] = []

    middle = await get_speculate_middle()
    table_name = extract_script["from"][0]["name"][1:-1]
    alternative_columns = list(get_schema()[table_name].keys())

    columns_to_add = []
    agg_funcs = get_agg_func(script)

    if agg_funcs is not None and (
        agg_funcs == [None] * len(agg_funcs) or extract_script["group"]
    ):
        for col in alternative_columns:
            should_add = True

            # Skip if column already in SELECT
            for select_item in extract_script["select"]:
                if col in select_item["name"] or col in select_item["alias"]:
                    should_add = False
                    break

            # Skip if column already in GROUP BY
            for group_item in extract_script["group"]:
                if col in group_item:
                    should_add = False
                    break

            # Skip if column not in middle result
            if col not in middle:
                should_add = False

            if should_add:
                columns_to_add.append(col)

    extract_script["select"].extend(
        [
            {
                "name": f'{extract_script["from"][0]["alias"]}."{col}"',
                "alias": f'"{col}"',
            }
            for col in columns_to_add
        ]
    )

    if extract_script["group"]:
        extract_script["group"].extend(
            [f'{extract_script["from"][0]["alias"]}."{col}"' for col in columns_to_add]
        )

    return format_clause(extract_script)


# -----------------------------------------------------------------------------
# Resolve Alias Conflict
# -----------------------------------------------------------------------------


def resolve_alias_conflict(script: str) -> str:
    """
    Resolve any alias conflicts in the SELECT clause.

    Args:
        script: SQL query to format

    Returns:
        Formatted SQL query with resolved alias conflicts

    Example:
        >>> resolve_alias_conflict('SELECT col1 as c, col2 as c FROM t')
        'SELECT col1 as c, col2 as c_SpeQL_COL_1 FROM t'
    """
    if not support_rewrite(script):
        return format(script)

    select = extract(script)["select"]
    distinct = extract(script)["distinct"]
    alias_set = set()

    for i in range(len(select)):
        if select[i]["alias"] not in alias_set:
            alias_set.add(select[i]["alias"])
        else:
            select[i]["alias"] = f'"{select[i]["alias"][1:-1]}_COL_{i}"'
            alias_set.add(select[i]["alias"])

    format_select = ", ".join(
        f"{select[i]['name']} AS {select[i]['alias']}" for i in range(len(select))
    )

    from_clause_start = script.lower().find("from")
    formatted_script = f"SELECT {distinct[0] if distinct else ''} {format_select} {script[from_clause_start:]}"

    return format(formatted_script)
