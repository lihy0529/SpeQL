# Copyright (c) 2025 Haoyu Li
# Released under the MIT License.
# See LICENSE file in the project root for details.

#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Extract module for SpeQL.
"""

import sys
import re
from pathlib import Path
from typing import Dict

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
# Local Imports
# -----------------------------------------------------------------------------

from parse import get_parse, parse_table, parse_condition
from log import log

# -----------------------------------------------------------------------------
# SQL Clause Extraction
# -----------------------------------------------------------------------------

def extract_inner(sql: str, clause_type: str) -> list:
    """
    Extracts and parses specific clauses from SQL query.
    
    Args:
        sql: SQL query to parse
        clause_type: Type of clause to extract ('Select', 'From', etc.)
        
    Returns:
        list: Parsed clause components. The return type differs according to the clause_type
        
    Raises:
        AssertionError: If clause_type is not supported
    """
    parsed = get_parse(sql)
    
    if clause_type == "select":
        """
        Extract the select clause.
        
        Returns:
            [
                {
                    "alias": "alias_name",
                    "table": "table_name",
                }
            ]
        """
        select = parsed.args.get("expressions", [])
        select = [parse_table(expr) for expr in select]
        return [item for item in select if item is not None]

    elif clause_type == "from":
        """
        Extract the from clause.
        
        Returns:
            [
                {
                    "alias": "alias_name",
                    "table": "table_name",
                }
            ]
        
        Warning:
            The return type is a list of dictionaries. Though the length is 1.
            In other words, callers should use extract_inner(sql, "from")[0]['name']
            to get the table name.
        """
        try:
            from_clause = parsed.args.get("from").args.get("this")
        except Exception as e:
            raise e

        assert from_clause is not None
        
        from_table = parse_table(from_clause)
        assert from_table is not None
        
        return [from_table]

    elif clause_type == "join":
        """
        Extract the join clause.
        
        Returns:
            [
                {
                    "table": {
                        "alias": "alias_name",
                        "table": "table_name",
                    },
                    "type": "join_type", # INNER, LEFT, RIGHT, FULL, CROSS
                    "condition": [
                        "condition_1",
                        "condition_2",
                        ...
                    ]
                }
            ]
        """
        join_expressions = parsed.args.get("joins", [])
        joins = []
        
        for join_expr in join_expressions:
            join_item = {
                "table": parse_table(join_expr.args.get("this"))
            }

            if join_expr.args.get("on") is None:
                join_item["type"] = "CROSS"
                join_item["condition"] = []
            
            else:
                join_item["type"] = (join_expr.args.get("side") 
                                   if join_expr.args.get("side") 
                                   else "INNER")
                
                assert join_item["type"] in ["INNER", "LEFT", "RIGHT", "FULL", "CROSS"]
                
                join_condition = join_expr.args.get("on")
                assert join_condition is not None
                
                if "and" in join_condition.sql().lower():
                    join_item["condition"] = [
                        cond.sql() for cond in join_condition.flatten()
                    ]
                    for i, cond in enumerate(join_item["condition"]):
                        if " OR " in cond.upper():
                            join_item["condition"][i] = f"( {cond} )"
                
                else:
                    conditions = [cond.sql() for cond in join_condition.flatten()]
                    join_item["condition"] = [" = ".join(conditions)]
                    
            joins.append(join_item)
        
        return joins

    elif clause_type in ["where", "having"]:
        """
        Extract the where or having clause.
        
        Returns:
            [
                "condition_1",
                "condition_2",
                ...
            ]
        """
        extract_clause = parsed.args.get(clause_type)
        if extract_clause:
            extract_clause = extract_clause.this
            return parse_condition(extract_clause)
        return []

    elif clause_type == "group":
        """
        Extract the group clause.
        
        Returns:
            [
                "column_1",
                "column_2",
                ...
            ]
        """
        from_clause = extract_inner(sql, "from")
        group = parsed.args.get("group")
        
        if not group:
            return []
            
        group_items = [expr.sql() for expr in group.flatten()]
        
        """
        Replace numeric references with actual column references.
        """
        for i, item in enumerate(group_items):
            if re.match(r"^\d+$", item):
                group_items[i] = (f"{from_clause[0]['alias']}."
                                f"{select[int(item)]['alias']}")
        return group_items
    
    elif clause_type == "order":
        """
        Extract the order clause.
        
        Returns:
            [
                "column_1",
                "column_2",
                ...
            ]
            
        Warning:
            The order clause may contain ASC/DESC/NULLS FIRST/NULLS LAST.
            We haven't encountered any issues yet, but using flatten() 
            is a simple implementation. It may have potential issues.
        """
        order = parsed.args.get("order")
        return [expr.sql() for expr in order.flatten()] if order else []

    elif clause_type == "limit":
        """
        Extract the limit clause.
        
        Returns:
            [
                "limit_value", # str(int)
            ]
            
        Warning:
            It will raise an AttributeError if we use the following code:
                limit = parsed.args.get("limit")
                return [limit.sql()[len("limit "):]] if limit else []
            We haven't investigated the reason yet, but we suspect it's 
            related to the way the parser handles the limit clause.
        """
        
        limit = parsed.args.get("limit")
        return [limit.sql()[len("limit "):]] if limit else []

    elif clause_type == "distinct":
        """
        Extract the distinct clause.
        
        Returns:
            ["distinct"] OR []
        """
        distinct = parsed.args.get("distinct")
        return [distinct.sql()] if distinct else []

    else:
        # This should never happen.
        assert False, f"Unsupported clause type: {clause_type}"

extract_dict = {}

def extract(sql: str) -> Dict[str, list]:
    """
    Extracts all supported clauses from a SQL query.
    
    Args:
        sql: SQL query to parse
        
    Returns:
        Dict[str, list]: Dictionary containing parsed components of each 
        clause. Return type differs according to the clause_type. See 
        extract_inner() for details.
    """
    if sql not in extract_dict:
        extract_dict[sql] = {
            "select": extract_inner(sql, "select"),
            "from": extract_inner(sql, "from"),
            "join": extract_inner(sql, "join"),
            "where": extract_inner(sql, "where"),
            "group": extract_inner(sql, "group"),
            "order": extract_inner(sql, "order"),
            "having": extract_inner(sql, "having"),
            "limit": extract_inner(sql, "limit"),
            "distinct": extract_inner(sql, "distinct"),
        }.copy()
    return extract_dict[sql].copy()
