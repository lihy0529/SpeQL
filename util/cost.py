# Copyright (c) 2025 Haoyu Li
# Released under the MIT License.
# See LICENSE file in the project root for details.

#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Cost Module
=============

This module controls LLM inference frequency and retry count.
"""

import sys
from pathlib import Path
from Levenshtein import distance
from typing import Optional

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

from param import get_similarity_threshold, get_max_iteration

# -----------------------------------------------------------------------------
# Global Variables
# -----------------------------------------------------------------------------

active_period: int = 1
count_down: int = 0
max_retry: int = 0

# -----------------------------------------------------------------------------
# SQL Similarity Check
# -----------------------------------------------------------------------------


def check_new_sql(str1: Optional[str], str2: str) -> bool:
    """
    Checks if two SQL queries are significantly different based on Levenshtein distance.
    If the queries are significantly different, SpeQL clears the rule.

    Args:
        str1: First SQL query (can be None)
        str2: Second SQL query

    Returns:
        bool: True if queries are significantly different or str1 is None
    """
    if str1 is None:
        return True

    if max(len(str1), len(str2)) == 0:
        similarity = 1.0
    else:
        similarity = 1 - distance(str1, str2) / max(len(str1), len(str2))

    return similarity < get_similarity_threshold()


# -----------------------------------------------------------------------------
# Retry Management
# -----------------------------------------------------------------------------


def get_max_retry() -> int:
    """
    Returns the current maximum retry count. If SpeQL cannot easily fix the SQL,
    it will try to reduce the inference frequency because the SQL is in the early stage.
    We now use a naive method to control the inference frequency.

    Returns:
        int: Maximum number of retries allowed
    """
    return max_retry


def increase_active_period() -> None:
    global active_period
    active_period *= 2
    if active_period > 4:
        active_period = 4
    update_max_retry()


def reset_active_period() -> None:
    global active_period, count_down, max_retry
    active_period = 1
    count_down = 0
    max_retry = get_max_iteration()
    update_max_retry()


def update_max_retry() -> None:
    global count_down, max_retry

    if count_down > 0:
        max_retry = get_max_iteration()
        count_down -= 1
    else:
        max_retry = get_max_iteration()
        count_down = active_period
