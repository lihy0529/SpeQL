# Copyright (c) 2025 Haoyu Li
# Released under the MIT License.
# See LICENSE file in the project root for details.

#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Parameter configuration for SpeQL.
"""

import argparse
import sys
from pathlib import Path
from typing import Dict, Any, Optional

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
# Constants
# -----------------------------------------------------------------------------

INF = 1000000000

# -----------------------------------------------------------------------------
# Global Parameters
# -----------------------------------------------------------------------------

cert_path: Optional[str] = None
enable_param: Optional[Dict[str, bool]] = None
min_rule_length: Optional[int] = None
similarity_threshold: Optional[float] = None
dialect_param: Optional[Dict[str, str]] = None
vector_db_param: Optional[Dict[str, str]] = None
db_param: Optional[Dict[str, Any]] = None
llm_param: Optional[Dict[str, Any]] = None
plugin_param: Optional[Dict[str, Any]] = None
max_iteration: Optional[int] = None
test_param: Optional[Dict[str, bool]] = None

# -----------------------------------------------------------------------------
# Parameter Getters
# -----------------------------------------------------------------------------


def get_dialect_param() -> Dict[str, str]:
    """Returns dialect parameters."""
    return dialect_param


def get_min_rule_length() -> int:
    """Returns minimum rule length."""
    return min_rule_length


def get_similarity_threshold() -> float:
    """Returns similarity threshold."""
    return similarity_threshold


def get_vector_db_param() -> Dict[str, str]:
    """Returns vector database parameters."""
    return vector_db_param


def get_cert_path() -> str:
    """Returns certificate path."""
    return cert_path


def get_llm_param() -> Dict[str, Any]:
    """Returns LLM parameters."""
    return llm_param


def get_db_param() -> Dict[str, Any]:
    """Returns database parameters."""
    return db_param


def get_plugin_param() -> Dict[str, Any]:
    """Returns plugin parameters."""
    return plugin_param


def get_enable_param() -> Dict[str, bool]:
    """Returns enable flags."""
    return enable_param


def get_max_iteration() -> int:
    """Returns maximum retry count."""
    return max_iteration


def get_test_param() -> Dict[str, bool]:
    """Returns test parameters."""
    return test_param


def get_system_name() -> str:
    """Returns system name."""
    return "SpeQL"


# -----------------------------------------------------------------------------
# Argument Parser Configuration
# -----------------------------------------------------------------------------


def create_parser() -> argparse.ArgumentParser:
    """
    Creates and configures the argument parser.

    Returns:
        argparse.ArgumentParser: Configured argument parser
    """
    parser = argparse.ArgumentParser(
        description="Configuration parameters for the application"
    )

    # Basic parameters
    parser.add_argument("--min-rule-length", type=int, default=5)
    parser.add_argument("--similarity-threshold", type=float, default=0.6)
    parser.add_argument(
        "--cert-path",
        type=str,
        default=str(Path(__file__).parent.parent / "cert"),
    )
    parser.add_argument("--enable-background-thread", type=bool, default=True)
    parser.add_argument("--max-iteration", type=int, default=3)
    parser.add_argument("--enable-vector-db", type=bool, default=False)
    parser.add_argument("--enable-sample", type=bool, default=False)
    parser.add_argument("--enable-predict-inference", type=bool, default=True)
    parser.add_argument("--enable-aggressive-debug", type=bool, default=False)
    parser.add_argument("--enable-result-cache", type=bool, default=True)

    # Dialect parameters
    dialect_group = parser.add_argument_group("Dialect Parameters")
    dialect_group.add_argument("--dialect-input", type=str, default="tsql")
    dialect_group.add_argument("--dialect-endpoint", type=str, default="redshift")
    dialect_group.add_argument("--dialect-dataset", type=str, default="tsql")

    # Vector DB parameters
    vector_group = parser.add_argument_group("Vector Database Parameters")
    base_path = Path(__file__).parent.parent
    vector_group.add_argument(
        "--vector-db-database-path",
        type=str,
        default=str(base_path / "vector_db/vector_db.index"),
    )
    vector_group.add_argument(
        "--vector-db-dataset-path",
        type=str,
        default=str(base_path / "vector_db/dataset/"),
    )

    # Database parameters
    db_group = parser.add_argument_group("Database Parameters")
    
    # redshift
    db_group.add_argument(
        "--db-host",
        type=str,
        default="haoyu.8202XXXXXXXX.us-east-1.redshift-serverless.amazonaws.com",
    )
    db_group.add_argument("--db-port", type=int, default=5439)
    db_group.add_argument("--db-database", type=str, default="sample_data_dev")
    db_group.add_argument("--db-user", type=str, default="admin")
    db_group.add_argument("--db-timeout", type=int, default=30)
    db_group.add_argument("--db-search-path", type=str, default="ext_tpcds100")
    
    # # snowflake
    # db_group.add_argument(
    #     "--db-host",
    #     type=str,
    #     default="krncyeu-ts1XXX",
    # )
    # db_group.add_argument("--db-port", type=int, default=5439)
    # db_group.add_argument("--db-database", type=str, default="snowflake_sample_data")
    # db_group.add_argument("--db-user", type=str, default="HAOYU")
    # db_group.add_argument("--db-timeout", type=int, default=30)
    # db_group.add_argument("--db-search-path", type=str, default="tpcds_sf10tcl")

    # Plugin parameters
    plugin_group = parser.add_argument_group("Plugin Parameters")
    plugin_group.add_argument("--plugin-ip", type=str, default="0.0.0.0")
    plugin_group.add_argument("--plugin-port", type=int, default=5000)
    plugin_group.add_argument("--plugin-password", type=str, default="plugin_password")
    plugin_group.add_argument(
        "--cursor-identifier", type=str, default="/*CURSOR_IDENTIFIER*/"
    )
    plugin_group.add_argument("--plugin-query-cache-count", type=int, default=INF)
    plugin_group.add_argument("--plugin-preview", type=int, default=40)
    plugin_group.add_argument("--plugin-preview-char", type=int, default=4000)
    plugin_group.add_argument("--plugin-temporary-table-count", type=int, default=10)
    plugin_group.add_argument("--plugin-temporary-table-size", type=int, default=10000)
    plugin_group.add_argument("--plugin-debug-simple-message-count", type=int, default=3)
    plugin_group.add_argument(
        "--plugin-debug-simple-message-size", type=int, default=8192
    )
    # LLM parameters
    llm_group = parser.add_argument_group("LLM Parameters")
    llm_group.add_argument("--llm-accurate", type=str, default="gpt-4o-2024-08-06")
    llm_group.add_argument("--llm-fast", type=str, default="gpt-4o-mini")
    llm_group.add_argument("--llm-timeout", type=int, default=30)

    # Test parameters
    test_group = parser.add_argument_group("Test Parameters")
    test_group.add_argument("--test-output-optimize", type=bool, default=False)
    test_group.add_argument("--test-output-create", type=bool, default=False)
    test_group.add_argument("--test-output-cte", type=bool, default=False)
    test_group.add_argument("--test-output-main-query", type=bool, default=False)
    test_group.add_argument("--test-output-rewrite-cte", type=bool, default=False)
    test_group.add_argument(
        "--test-output-rewrite-main-query", type=bool, default=False
    )
    test_group.add_argument("--test-skip-create", type=bool, default=False)
    test_group.add_argument("--test-output-rule", type=bool, default=False)
    test_group.add_argument(
        "--test-output-useful-historical-sql", type=bool, default=False
    )
    test_group.add_argument("--test-output-useful-schema", type=bool, default=False)
    test_group.add_argument("--test-output-debug", type=bool, default=False)
    test_group.add_argument("--test-output-query", type=bool, default=False)
    test_group.add_argument("--test-warm-up", type=bool, default=False)
    return parser


# -----------------------------------------------------------------------------
# Parameter Setting
# -----------------------------------------------------------------------------


def set_param() -> None:
    """
    Sets global parameters based on command line arguments.
    """
    parser = create_parser()
    args = parser.parse_args()

    global cert_path, min_rule_length, similarity_threshold, dialect_param
    global vector_db_param, db_param, plugin_param, llm_param, max_iteration
    global enable_param, test_param

    cert_path = args.cert_path
    min_rule_length = args.min_rule_length
    similarity_threshold = args.similarity_threshold
    max_iteration = args.max_iteration

    enable_param = {
        "background_thread": args.enable_background_thread,
        "vector_db": args.enable_vector_db,
        "sample": args.enable_sample,
        "predict_inference": args.enable_predict_inference,
        "aggressive_debug": args.enable_aggressive_debug,
        "result_cache": args.enable_result_cache,
    }

    dialect_param = {
        "input": args.dialect_input,
        "endpoint": args.dialect_endpoint,
        "dataset": args.dialect_dataset,
    }

    vector_db_param = {
        "database_path": args.vector_db_database_path,
        "dataset_path": args.vector_db_dataset_path,
    }

    def read_secret(cert_path: str) -> str:
        """Reads secret from file."""
        with open(cert_path, "r") as f:
            return f.read().strip()

    db_param = {
        "host": args.db_host,
        "database": args.db_database,
        "port": args.db_port,
        "user": args.db_user,
        "timeout": args.db_timeout,
        "search_path": args.db_search_path,
        # redshift
        "password": read_secret(cert_path + "/redshift_db_password.secret"),
        # # snowflake
        # "password": read_secret(cert_path + "/snowflake_db_password.secret"),
    }

    plugin_param = {
        "ip_address": args.plugin_ip,
        "port": args.plugin_port,
        "plugin_password": args.plugin_password,
        "cursor_identifier": args.cursor_identifier,
        "query_cache_count": args.plugin_query_cache_count,
        "preview": args.plugin_preview,
        "preview_char": args.plugin_preview_char,
        "temporary_table_count": args.plugin_temporary_table_count,
        "temporary_table_size": args.plugin_temporary_table_size,
        "debug_simple_message_count": args.plugin_debug_simple_message_count,
        "debug_simple_message_size": args.plugin_debug_simple_message_size,
    }

    llm_param = {
        "accurate": args.llm_accurate,
        "fast": args.llm_fast,
        "api_key": read_secret(cert_path + "/openai_llm_key.secret"),
        "timeout": args.llm_timeout,
    }

    test_param = {
        "output_optimize": args.test_output_optimize,
        "output_create": args.test_output_create,
        "output_cte": args.test_output_cte,
        "output_main_query": args.test_output_main_query,
        "output_rewrite_cte": args.test_output_rewrite_cte,
        "output_rewrite_main_query": args.test_output_rewrite_main_query,
        "skip_create": args.test_skip_create,
        "output_rule": args.test_output_rule,
        "output_useful_historical_sql": args.test_output_useful_historical_sql,
        "output_useful_schema": args.test_output_useful_schema,
        "output_debug": args.test_output_debug,
        "output_query": args.test_output_query,
        "warm_up": args.test_warm_up,
    }


# Initialize parameters
set_param()
