# Copyright (c) 2025 Haoyu Li
# Released under the MIT License.
# See LICENSE file in the project root for details.

#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Debug Rule Module
===================

This module provides functionality for generating and managing replacement rules
for SQL query rewriting to reduce the LLM inference cost.
"""

import sys
import re
import difflib
from pathlib import Path
from typing import List, Dict

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

from param import get_min_rule_length, get_test_param
from log import append_test_info

# -----------------------------------------------------------------------------
# Global Variables
# -----------------------------------------------------------------------------

rule = []

# -----------------------------------------------------------------------------
# Rule Management
# -----------------------------------------------------------------------------


def get_rule() -> List[Dict[str, str]]:
    """
    Retrieves the current set of replacement rules.

    Returns:
        List[Dict[str, str]]: List of rules, each containing 'old' and 'new' patterns
    """
    global rule
    return rule


def set_rule(new_rule: List[Dict[str, str]]) -> None:
    """
    Updates the current set of replacement rules.

    Args:
        new_rule: List of replacement rules to set:
        [{
            "old": "pattern_to_replace",
            "new": "pattern_to_replace_with",
        }, ...]
    """
    global rule
    rule = new_rule
    if get_test_param()["output_rule"]:
        append_test_info("rule", rule)


# -----------------------------------------------------------------------------
# Pattern Validation
# -----------------------------------------------------------------------------


def validate_unique_occurrence(part: List[str], whole: List[str]) -> bool:
    """
    Checks if a pattern occurs exactly once in a given text. If so, we can
    safely replace the pattern. Otherwise the replacement will be ambiguous.

    Args:
        part: Pattern to search for
        whole: Text to search in

    Returns:
        bool: True if pattern occurs exactly once, False otherwise
    """
    if len(part) == 0:
        return False

    part, whole = "".join(part), "".join(whole)
    pattern = r"{}".format(re.escape(part))

    return len(re.findall(pattern, whole)) == 1


# -----------------------------------------------------------------------------
# Rule Generation
# -----------------------------------------------------------------------------


def get_replacement_rule(a: str, b: str) -> List[Dict[str, str]]:
    """
    Generates replacement rules by comparing two strings and finding unique patterns.

    The function uses sequence matching to identify differences between strings
    and generates rules for replacing patterns in string 'a' to transform it into 'b'.

    Args:
        a: Original string
        b: Target string

    Returns:
        List[Dict[str, str]]: List of replacement rules
    """
    local_rules = []
    string_b = b
    b = re.split(r"(\s+)", b)
    min_rule_length = get_min_rule_length()

    while True:
        mem_a = a
        a = re.split(r"(\s+)", a)
        sm = difflib.SequenceMatcher(None, a, b)
        opcodes = sm.get_opcodes()
        mem_right = 0
        local_rule = []

        for tag, i1, i2, j1, j2 in opcodes:
            if tag != "equal":
                left = i1
                right = i2

                if left < mem_right:
                    continue

                while True:
                    sub_a = a[left:right]
                    if (
                        validate_unique_occurrence(sub_a, a)
                        and right - left >= min_rule_length
                    ):
                        left_b = j1 - (i1 - left)
                        right_b = j2 + (right - i2)
                        left_b = max(0, left_b)
                        right_b = min(len(b), right_b)

                        if (
                            right != len(a)
                            and right_b != len(b)
                            and a[right] == b[right_b]
                        ):
                            right += 1
                            right_b += 1

                        mem_right = right
                        sub_a = "".join(a[left:right])
                        sub_b = "".join(b[left_b:right_b])

                        local_rule.append({"old": sub_a, "new": sub_b})
                        break

                    if left > mem_right:
                        left -= min(
                            left - mem_right, max(1, min_rule_length - (right - left))
                        )
                    elif right < len(a):
                        right += min(
                            len(a) - right, max(1, min_rule_length - (right - left))
                        )
                    else:
                        break

        local_rules += local_rule
        a = mem_a

        for rule in local_rule:
            a = a.replace(rule["old"], rule["new"])

        if a == string_b:
            break

    return local_rules
