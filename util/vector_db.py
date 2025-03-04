# Copyright (c) 2025 Haoyu Li
# Released under the MIT License.
# See LICENSE file in the project root for details.

#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Vector Database Utility
"""

import sys
import os
import re
import faiss
import numpy as np
import sqlglot
from pathlib import Path
from typing import List, Dict, Optional, Any

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

from param import (
    get_vector_db_param,
    get_dialect_param,
    get_plugin_param,
    get_enable_param,
    get_test_param,
)
from llm_api import get_embedding
from log import append_test_info
from concurrency import get_load_vector_db_lock

# -----------------------------------------------------------------------------
# Global State
# -----------------------------------------------------------------------------

dataset: Optional[List[str]] = None
vector_database: Optional[Any] = None
useful_historical_sql_dict: Dict[str, str] = {}

# -----------------------------------------------------------------------------
# Dataset Management
# -----------------------------------------------------------------------------


def load_dataset() -> List[str]:
    """
    Loads and preprocesses SQL dataset from files.

    Returns:
        List[str]: Preprocessed SQL queries
    """
    dataset = []
    file_list_dir = get_vector_db_param()["dataset_path"]

    # Load SQL files
    sql_files = [f for f in os.listdir(file_list_dir) if f.endswith(".sql")]
    for file_name in sql_files:
        with open(file_list_dir + "/" + file_name, "r") as file:
            # Extract first SQL statement
            sql = file.read().split(";")[0]
            # Transpile to target dialect
            sql = sqlglot.transpile(
                sql,
                read=get_dialect_param()["dataset"],
                write=get_dialect_param()["endpoint"],
            )[0]
            dataset.append(sql)

    # Normalize SQL formatting
    dataset = [
        re.sub(
            r"(\'[^\']*\')|([^']+)",
            lambda m: (
                m.group(1)
                if m.group(1)
                else re.sub(
                    r"(<=|>=|!=|/\*|\*\/|<>|[=(),<>+\-*/])", r" \1 ", m.group(2)
                ).upper()
            ),
            sql,
        )
        for sql in dataset
    ]

    return dataset


# -----------------------------------------------------------------------------
# Vector Database Operations
# -----------------------------------------------------------------------------


def get_useful_historical_sql(sql: str) -> str:
    """
    Retrieves most similar historical SQL query.

    Args:
        sql: Input SQL query

    Returns:
        str: Most similar historical SQL query
    """
    global vector_database

    if not get_enable_param()["vector_db"]:
        return ""
    
    with get_load_vector_db_lock():
        if vector_database is None:
            load_vector_db()

    # Remove cursor identifier for comparison
    sql = sql.replace(get_plugin_param()["cursor_identifier"], "")

    # Return cached result if available
    if sql in useful_historical_sql_dict:
        return useful_historical_sql_dict[sql]

    # Find most similar query
    embedding = get_embedding(sql)
    embedding = np.array([embedding], dtype=np.float32)
    _, index = vector_database.search(embedding, 1)

    useful_historical_sql = dataset[index[0][0]]
    useful_historical_sql_dict[sql] = useful_historical_sql

    if get_test_param()["output_useful_historical_sql"]:
        append_test_info("useful_historical_sql", useful_historical_sql)

    return useful_historical_sql


def load_vector_db() -> None:
    """
    Loads or creates vector database for SQL similarity search.
    """
    global vector_database, dataset
    dataset = load_dataset()
    db_path = get_vector_db_param()["database_path"]

    if os.path.exists(db_path):
        vector_database = faiss.read_index(db_path)
    else:
        vector_database = _construct_vector_db(dataset)
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        faiss.write_index(vector_database, db_path)


def _construct_vector_db(history_list: List[str]) -> Any:
    """
    Constructs new vector database from SQL history.

    Args:
        history_list: List of historical SQL queries

    Returns:
        faiss.Index: Constructed vector database
    """
    embedding_list = np.array(
        [get_embedding(sql) for sql in history_list], dtype=np.float32
    )

    dimension = embedding_list.shape[1]
    index = faiss.IndexFlatL2(dimension)
    index.add(embedding_list)

    return index


def insert_into_vector_db(sql: str) -> None:
    """
    Inserts new SQL query into vector database.

    Args:
        sql: SQL query to insert
    """
    embedding = np.array([get_embedding(sql)], dtype=np.float32)
    vector_database.add(embedding)
    dataset.append(sql)
