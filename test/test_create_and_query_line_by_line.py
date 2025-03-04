import sys, asyncio
from pathlib import Path

root_dir = str(Path(__file__).parent.parent)
sys.path.extend(
    [
        root_dir,
        str(Path(root_dir) / "src"),
        str(Path(root_dir) / "util"),
    ]
)

from param import get_test_param, get_plugin_param, INF, get_db_param
from concurrency import get_execute_cursor_lock

"""Warning
- Do not import db_api before 
"""
test_param = get_test_param()
db_param = get_db_param()

test_param["output_create"] = True
test_param["output_rewrite_cte"] = False
test_param["output_rewrite_main_query"] = True
test_param["output_optimize"] = True
test_param["output_main_query"] = False
test_param["output_cte"] = False
test_param["output_query"] = True
test_param["warm_up"] = True



confident = True

if not confident:
    test_param["skip_create"] = True
    db_param["search_path"] = "tpcds"

else:
    test_param["skip_create"] = False
    db_param["search_path"] = "ext_tpcds10"
    db_param["timeout"] = 15

"""
Warning:
    Do not import db_api before test_param["skip_create"] is set.
"""

"""
Error Summary:
- could not parse: This error is not a bug. SpeQLite falls back to original SQL.
- could not open relation with OID: This error does not always happen. https://community.holistics.io/t/redshift-only-fail-to-transform-data-error-could-not-open-relation-with-oid-xxx-error-during-import-transform-job/917
- limit clause should be empty in origin query: we haven't investigated this error, but it does not violate the ultimate result.
- invalid input syntax for type timestamp: "DAY": Probably an internal parser bug, but it does not violate the ultimate result.

"""
input = [
    # {"query_number": 1, "mark": "a", "remove": "end", "remove_line": 20, "step": 1},
    # {"query_number": 2, "mark": "a", "remove": "end", "remove_line": 20, "step": 1},
    # {"query_number": 3, "mark": "a", "remove": "end", "remove_line": 18, "step": 1},
    # {"query_number": 4, "mark": "a", "remove": "end", "remove_line": 20, "step": 1},
    # {"query_number": 5, "mark": "a", "remove": "end", "remove_line": 20, "step": 1},
    # {"query_number": 6, "mark": "a", "remove": "end", "remove_line": 20, "step": 1},
    # {"query_number": 7, "mark": "a", "remove": "end", "remove_line": 18, "step": 1},
    # {"query_number": 8, "mark": "a", "remove": "end", "remove_line": 20, "step": 1},
    # {"query_number": 9, "mark": "a", "remove": "end", "remove_line": 20, "step": 1},
    # {"query_number": 10, "mark": "a", "remove": "end", "remove_line": 20, "step": 1},
    # {"query_number": 11, "mark": "a", "remove": "end", "remove_line": 20, "step": 1},
    # {"query_number": 12, "mark": "a", "remove": "end", "remove_line": 20, "step": 1},
    # {"query_number": 13, "mark": "a", "remove": "end", "remove_line": 20, "step": 1},
    # {"query_number": 14, "mark": "a", "remove": "end", "remove_line": 20, "step": 1},
    # {"query_number": 15, "mark": "a", "remove": "end", "remove_line": 17, "step": 1},
    # {"query_number": 16, "mark": "a", "remove": "end", "remove_line": 20, "step": 1},
    # {"query_number": 17, "mark": "a", "remove": "end", "remove_line": 20, "step": 1},
    # {"query_number": 18, "mark": "a", "remove": "end", "remove_line": 20, "step": 1}, # could not parse. 
    # {"query_number": 19, "mark": "a", "remove": "end", "remove_line": 20, "step": 1},
    # {"query_number": 20, "mark": "a", "remove": "end", "remove_line": 20, "step": 1},
    # {"query_number": 21, "mark": "a", "remove": "end", "remove_line": 20, "step": 1},
    # {"query_number": 22, "mark": "a", "remove": "end", "remove_line": 20, "step": 1},
    # {"query_number": 23, "mark": "a", "remove": "end", "remove_line": 20, "step": 1},
    # {"query_number": 24, "mark": "a", "remove": "end", "remove_line": 20, "step": 1},
    # {"query_number": 25, "mark": "a", "remove": "end", "remove_line": 20, "step": 1},
    # {"query_number": 26, "mark": "a", "remove": "end", "remove_line": 18, "step": 1},
    # {"query_number": 27, "mark": "a", "remove": "end", "remove_line": 20, "step": 1},
    # {"query_number": 28, "mark": "a", "remove": "end", "remove_line": 20, "step": 1},
    # {"query_number": 29, "mark": "a", "remove": "end", "remove_line": 20, "step": 1},
    # {"query_number": 30, "mark": "a", "remove": "end", "remove_line": 20, "step": 1},
    # {"query_number": 31, "mark": "a", "remove": "end", "remove_line": 20, "step": 1},
    # {"query_number": 32, "mark": "a", "remove": "end", "remove_line": 20, "step": 1}, # invalid input syntax for type timestamp: "DAY"
    # {"query_number": 33, "mark": "a", "remove": "end", "remove_line": 20, "step": 1},
    # {"query_number": 34, "mark": "a", "remove": "end", "remove_line": 20, "step": 1},
    # {"query_number": 35, "mark": "a", "remove": "end", "remove_line": 20, "step": 1},
    # {"query_number": 36, "mark": "a", "remove": "end", "remove_line": 20, "step": 1},
    # {"query_number": 37, "mark": "a", "remove": "end", "remove_line": 14, "step": 1},
    # {"query_number": 38, "mark": "a", "remove": "end", "remove_line": 20, "step": 1},
    # {"query_number": 39, "mark": "a", "remove": "end", "remove_line": 20, "step": 1},
    # {"query_number": 40, "mark": "a", "remove": "end", "remove_line": 20, "step": 1},
    # {"query_number": 41, "mark": "a", "remove": "end", "remove_line": 20, "step": 1},
    # {"query_number": 42, "mark": "a", "remove": "end", "remove_line": 19, "step": 1},
    # {"query_number": 43, "mark": "a", "remove": "end", "remove_line": 16, "step": 1},
    # {"query_number": 44, "mark": "a", "remove": "end", "remove_line": 20, "step": 1},
    # {"query_number": 45, "mark": "a", "remove": "end", "remove_line": 17, "step": 1},
    # {"query_number": 46, "mark": "a", "remove": "end", "remove_line": 20, "step": 1},
    # {"query_number": 47, "mark": "a", "remove": "end", "remove_line": 20, "step": 1},
    # {"query_number": 48, "mark": "a", "remove": "end", "remove_line": 20, "step": 1},
    # {"query_number": 49, "mark": "a", "remove": "end", "remove_line": 20, "step": 1},
    # {"query_number": 50, "mark": "a", "remove": "end", "remove_line": 20, "step": 1},
    # {"query_number": 51, "mark": "a", "remove": "end", "remove_line": 20, "step": 1},
    # {"query_number": 52, "mark": "a", "remove": "end", "remove_line": 19, "step": 1},
    # {"query_number": 53, "mark": "a", "remove": "end", "remove_line": 20, "step": 1},
    # {"query_number": 54, "mark": "a", "remove": "end", "remove_line": 20, "step": 1},
    # {"query_number": 55, "mark": "a", "remove": "end", "remove_line": 11, "step": 1},
    # {"query_number": 56, "mark": "a", "remove": "end", "remove_line": 20, "step": 1},
    # {"query_number": 57, "mark": "a", "remove": "end", "remove_line": 20, "step": 1},
    # {"query_number": 58, "mark": "a", "remove": "end", "remove_line": 20, "step": 1}, # division by zero
    # {"query_number": 59, "mark": "a", "remove": "end", "remove_line": 20, "step": 1},
    # {"query_number": 60, "mark": "a", "remove": "end", "remove_line": 20, "step": 1},
    # {"query_number": 61, "mark": "a", "remove": "end", "remove_line": 20, "step": 1}, # column store_sales._col_0 does not exist; Numeric overflow. 
    # {"query_number": 62, "mark": "a", "remove": "end", "remove_line": 20, "step": 1},
    # {"query_number": 63, "mark": "a", "remove": "end", "remove_line": 20, "step": 1},
    # {"query_number": 64, "mark": "a", "remove": "end", "remove_line": 20, "step": 1},
    # {"query_number": 65, "mark": "a", "remove": "end", "remove_line": 20, "step": 1},
    # {"query_number": 66, "mark": "a", "remove": "end", "remove_line": 20, "step": 1},
    # {"query_number": 67, "mark": "a", "remove": "end", "remove_line": 20, "step": 1},
    # {"query_number": 68, "mark": "a", "remove": "end", "remove_line": 20, "step": 1},
    # {"query_number": 69, "mark": "a", "remove": "end", "remove_line": 20, "step": 1},
    # {"query_number": 70, "mark": "a", "remove": "end", "remove_line": 20, "step": 1},
    # {"query_number": 71, "mark": "a", "remove": "end", "remove_line": 20, "step": 1},
    # {"query_number": 72, "mark": "a", "remove": "end", "remove_line": 20, "step": 1},
    # {"query_number": 73, "mark": "a", "remove": "end", "remove_line": 20, "step": 1},
    # {"query_number": 74, "mark": "a", "remove": "end", "remove_line": 20, "step": 1},
    # {"query_number": 75, "mark": "a", "remove": "end", "remove_line": 20, "step": 1}, # Limit clause should be empty in origin query. 
    # {"query_number": 76, "mark": "a", "remove": "end", "remove_line": 20, "step": 1},
    # {"query_number": 77, "mark": "a", "remove": "end", "remove_line": 20, "step": 1},
    # {"query_number": 78, "mark": "a", "remove": "end", "remove_line": 20, "step": 1},
    # {"query_number": 79, "mark": "a", "remove": "end", "remove_line": 20, "step": 1},
    # {"query_number": 80, "mark": "a", "remove": "end", "remove_line": 20, "step": 1},
    # {"query_number": 81, "mark": "a", "remove": "end", "remove_line": 20, "step": 1},
    # {"query_number": 82, "mark": "a", "remove": "end", "remove_line": 14, "step": 1},
    # {"query_number": 83, "mark": "a", "remove": "end", "remove_line": 20, "step": 1},
    # {"query_number": 84, "mark": "a", "remove": "end", "remove_line": 18, "step": 1},
    # {"query_number": 85, "mark": "a", "remove": "end", "remove_line": 20, "step": 1},
    # {"query_number": 86, "mark": "a", "remove": "end", "remove_line": 20, "step": 1},
    # {"query_number": 87, "mark": "a", "remove": "end", "remove_line": 20, "step": 1},
    # {"query_number": 88, "mark": "a", "remove": "end", "remove_line": 20, "step": 1},
    # {"query_number": 89, "mark": "a", "remove": "end", "remove_line": 20, "step": 1},
    # {"query_number": 90, "mark": "a", "remove": "end", "remove_line": 19, "step": 1}, # AttributeError: 'NoneType' object has no attribute 'args'. 
    # {"query_number": 91, "mark": "a", "remove": "end", "remove_line": 20, "step": 1},
    # {"query_number": 92, "mark": "a", "remove": "end", "remove_line": 20, "step": 1}, # invalid input syntax for type timestamp: "DAY"
    # {"query_number": 93, "mark": "a", "remove": "end", "remove_line": 15, "step": 1},
    # {"query_number": 94, "mark": "a", "remove": "end", "remove_line": 20, "step": 1},
    # {"query_number": 95, "mark": "a", "remove": "end", "remove_line": 20, "step": 1},
    # {"query_number": 96, "mark": "a", "remove": "end", "remove_line": 13, "step": 1},
    # {"query_number": 97, "mark": "a", "remove": "end", "remove_line": 20, "step": 1},
    # {"query_number": 98, "mark": "a", "remove": "end", "remove_line": 20, "step": 1},
    # {"query_number": 99, "mark": "a", "remove": "end", "remove_line": 20, "step": 1},
    
    {"query_number": 14, "mark": "b", "remove": "end", "remove_line": 20, "step": 1},
    {"query_number": 23, "mark": "b", "remove": "end", "remove_line": 20, "step": 1},
    {"query_number": 24, "mark": "b", "remove": "end", "remove_line": 20, "step": 1},
    {"query_number": 39, "mark": "b", "remove": "end", "remove_line": 20, "step": 1},
]

# -------------------------------------------------------------------------------------------------

if test_param["skip_create"]:
    assert db_param["search_path"] == "tpcds", "Only tpcds is supported"

from concurrency import set_recent_tid, reset_recent_tid, set_speculate_middle
from create import create
from log import get_test_info, reset_test_info
from preview import preview
from dataset import get_debug_line_by_line
from create_struct import temporary_table_pool


async def test(query):
    test_data = get_debug_line_by_line(query)
    record = []
    assert (
        get_plugin_param()["query_cache_count"] == INF
        and get_plugin_param()["temporary_table_count"] == INF
        and get_plugin_param()["temporary_table_size"] == INF
    ), "QueryCache, TemporaryTable, and TemporaryTableSize should be +inf"
    for i, data in enumerate(test_data):

        set_speculate_middle(data["middle"])
        reset_test_info()

        if data["debug"] is not None:
            rewrite = await create(
                data["debug"] + get_plugin_param()["cursor_identifier"]
            )
            preview_result = await preview(rewrite)
        else:
            preview_result = None

        optimize_info = get_test_info("optimized_sql")
        rewrite_main_query_info = get_test_info("rewrite_main_query")
        rewrite_cte_info = get_test_info("rewrite_cte")
        create_info = get_test_info("create")
        cte_info = get_test_info("cte")
        main_query_info = get_test_info("main_query")
        query_info = get_test_info("query")

        record.append(
            {
                "input": data["debug"],
                "optimize": optimize_info,
                "create": create_info,
                "query": query_info,
                "rewrite_main_query": rewrite_main_query_info,
                # "rewrite_cte": rewrite_cte_info,
                # "cte": cte_info,
                # "main_query": main_query_info,
                "preview": preview_result,
            }
        )
        if query["mark"] == "a":
            file_name = f"create_and_query_line_by_line_tpcdsq{query['query_number']}_remove_{query['remove']}_remove_line_{query['remove_line']}_step_{query['step']}.json"

        else:
            assert query["mark"] == "b"
            file_name = f"create_and_query_line_by_line_tpcdsq{query['query_number']}_{query['mark']}_remove_{query['remove']}_remove_line_{query['remove_line']}_step_{query['step']}.json"

        with open(str(Path(__file__).parent / "test_output" / file_name), "w") as f:
            json.dump(record, f, indent=4)

    return record


if __name__ == "__main__":

    set_recent_tid(new_priority=1, new_running_sql="test", type="db")
    import json

    for query in input:
        print("\033[92m", query, "\033[0m")
        with get_execute_cursor_lock():
            temporary_table_pool.reset()

        asyncio.run(test(query))

    reset_recent_tid(type="db")
