# Copyright (c) 2025 Haoyu Li
# Released under the MIT License.
# See LICENSE file in the project root for details.

#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Class: Temporary Table Pool
=============================

This module provides functionality for managing temporary tables in the SpeQL system.
It implements an LRU (Least Recently Used) eviction strategy to prevent memory overflow.

Key Components:
    - TemporaryTablePool: Core class managing temporary table creation and eviction
    - LRU based table management
    - Query result caching
    - Metadata tracking
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

from param import get_plugin_param, get_system_name
from db_api import get_cursor
from log import log

# -----------------------------------------------------------------------------
# Temporary Table Pool
# -----------------------------------------------------------------------------


class TemporaryTablePool:
    """
    Manages a pool of temporary tables with LRU eviction strategy.

    This pool maintains the mapping from the script to the table name, the LRU
    list, and metadata (size, sample status).
    """

    def __init__(self) -> None:
        """Initialize an empty table pool with tracking structures."""
        # Maps scripts to table name
        self.script_to_name = {}
        # Counter for unique table names, is incremented when creating a new table
        self.index = 0
        # Tracks table access order. The item in lru is the same as the key in script_to_name
        self.lru = []

    def lru_evict(self) -> None:
        """
        Evict least recently used tables when size/count limits are exceeded.

        Implements a size-aware LRU eviction policy that considers both the
        number of tables and their total size in MB.

        Returns:
            None

        Example:
            >>> TemporaryTablePool.lru_evict()
            # Evicts least recently used tables if size/count limits are exceeded
        """
        iterator = -1
        size = sum(
            [self.script_to_name[script]["size"] for script in self.script_to_name]
        )

        while (
            len(self.lru) > get_plugin_param()["temporary_table_count"]
            or size > get_plugin_param()["temporary_table_size"]
        ):
            if iterator == -len(self.lru) - 1:
                log(
                    "error.txt",
                    f"Error: Cannot drop any temporary table",
                )
                break

            try:
                # Attempt to drop the least recently used table
                table_name = self.script_to_name[self.lru[iterator]]["name"]
                get_cursor()["execute"].execute(f"DROP TABLE IF EXISTS {table_name}")

                log(
                    "mem_mgmt.txt",
                    {"type": "drop", "name": table_name, "size": self.script_to_name[self.lru[iterator]]['size']},
                    is_dict=True,
                )

                # Update tracking structures
                size -= self.script_to_name[self.lru[iterator]]["size"]
                del self.script_to_name[self.lru[iterator]]
                self.lru.pop(iterator)

                iterator = -1

            except Exception as e:
                # If other temporary tables depend on this table, it will not be dropped
                iterator -= 1

    def check(self, script, update_lru=True) -> dict:
        """
        Check if a script has an associated temporary table and optionally update its LRU status.

        This method looks up whether a given SQL script already has a temporary table created for it.
        If found, it can optionally move that table to the front of the LRU (least recently used) list
        to mark it as recently accessed.

        Args:
            script (str): The SQL script to check for an existing temporary table
            update_lru (bool): If True, moves an existing table to front of LRU list.
                             If False, just checks existence without updating access order.

        Returns:
            dict: Information about the temporary table:
                {
                    'name': str,     # Name of existing or to-be-created table
                    'is_new': bool    # True if table needs to be created, False if exists
                }

        Example:
            >>> # CREATE TEMPORARY TABLE SpeQL_temp_table_1 AS SELECT * FROM table1;

            >>> # Table was created before
            >>> TemporaryTablePool.check("SELECT * FROM table1;")
            {'name': '"SpeQL_temp_table_1"', 'is_new': False}

            >>> # Table was not created before
            >>> TemporaryTablePool.check("SELECT * FROM table2;")
            {'name': '"SpeQL_temp_table_2"', 'is_new': True}

        """
        if script in self.script_to_name:
            if update_lru:
                # Move accessed table to front of LRU list
                for i in range(len(self.lru)):
                    if self.lru[i] == script:
                        self.lru = [self.lru[i]] + self.lru[:i] + self.lru[i + 1 :]
                        break
            return {"name": self.script_to_name[script]["name"], "is_new": False}
        else:
            return {
                "name": f'"{get_system_name().upper()}_TEMP_TABLE_{self.index + 1}"',
                "is_new": True,
            }

    def update(self, script, is_sample, create_metrics) -> None:
        """
        Register a new temporary table in the pool. The caller must ensure that
        the script has not been registered in the pool.

        Args:
            script (str): Script identifier
            is_sample (bool): Whether table contains sampled data. This may happen
            when the table is created from a sampled table due to timeout.
            create_metrics (dict): Metrics of the create operation

        Returns:
            None

        """
        self.index += 1
        assert script not in self.script_to_name, "Script already registered"

        name = f'"{get_system_name().upper()}_TEMP_TABLE_{self.index}"'

        # Register new table
        self.script_to_name[script] = {
            "name": name,
            "is_sample": is_sample,
            "size": create_metrics["create_size"],
        }

        log(
            "mem_mgmt.txt",
            {"type": "create", "name": name, "script": script, "is_sample": is_sample, "create_metrics": create_metrics},
            is_dict=True,
        )

        # Update tracking lists
        self.lru = [script] + self.lru

    def reset(self) -> None:
        """
        Reset the temporary table pool. For testing use when you want to run multiple queries
        without restarting the system.

        Warning: You still need to run clear_debug_simple_message() to clear the debug message
        if you are using LLM debugging module.
        """
        for script in self.lru:
            try:

                get_cursor()["execute"].execute(
                    f"DROP TABLE IF EXISTS {self.script_to_name[script]['name']} CASCADE;"
                )
            except Exception as e:
                log(
                    "error.txt",
                    f"Error: Cannot drop table {script}: {e}",
                )

        self.script_to_name = {}
        self.index = 0
        self.lru = []

    def get_is_sample(self, script) -> bool:
        """
        Return whether a table contains sampled data. The caller must ensure that
        the script has been registered in the pool.

        Args:
            script (str): Script identifier

        Returns:
            bool: Whether the table contains sampled data
        """
        assert script in self.script_to_name, "Script not registered"
        return self.script_to_name[script]["is_sample"]

    def get_query_cache_list(self) -> list:
        """
        Return the current query cache list. At most get_plugin_param()["query_cache_count"] items.
        SpeQL will use the query cache to rewrite the query.
        """
        return self.lru[: get_plugin_param()["query_cache_count"]]


# -----------------------------------------------------------------------------
# Global Instance
# -----------------------------------------------------------------------------

temporary_table_pool = TemporaryTablePool()
