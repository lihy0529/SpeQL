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

from param import get_test_param, get_db_param
from concurrency import get_execute_cursor_lock
from log import reset_test_info

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

test_param["skip_create"] = False
db_param["search_path"] = "ext_tpcds10"
db_param["timeout"] = 1000

input = [
    {"query_number": 1, "mark": "a"},
    {"query_number": 2, "mark": "a"},
    {"query_number": 3, "mark": "a"},
    {"query_number": 4, "mark": "a"},
    {"query_number": 5, "mark": "a"},
    {"query_number": 6, "mark": "a"},
    {"query_number": 7, "mark": "a"},
    {"query_number": 8, "mark": "a"},
    {"query_number": 9, "mark": "a"},
    {"query_number": 10, "mark": "a"},
    {"query_number": 11, "mark": "a"},
    {"query_number": 12, "mark": "a"},
    {"query_number": 13, "mark": "a"},
    {"query_number": 14, "mark": "a"},
    {"query_number": 15, "mark": "a"},
    {"query_number": 16, "mark": "a"},
    {"query_number": 17, "mark": "a"},
    {"query_number": 18, "mark": "a"},
    {"query_number": 19, "mark": "a"},
    {"query_number": 20, "mark": "a"},
    {"query_number": 21, "mark": "a"},
    {"query_number": 22, "mark": "a"},
    {"query_number": 23, "mark": "a"},
    {"query_number": 24, "mark": "a"},
    {"query_number": 25, "mark": "a"},
    {"query_number": 26, "mark": "a"},
    {"query_number": 27, "mark": "a"},
    {"query_number": 28, "mark": "a"},
    {"query_number": 29, "mark": "a"},
    {"query_number": 30, "mark": "a"},
    {"query_number": 31, "mark": "a"},
    {"query_number": 32, "mark": "a"},
    {"query_number": 33, "mark": "a"},
    {"query_number": 34, "mark": "a"},
    {"query_number": 35, "mark": "a"},
    {"query_number": 36, "mark": "a"},
    {"query_number": 37, "mark": "a"},
    {"query_number": 38, "mark": "a"},
    {"query_number": 39, "mark": "a"},
    {"query_number": 40, "mark": "a"},
    {"query_number": 41, "mark": "a"},
    {"query_number": 42, "mark": "a"},
    {"query_number": 43, "mark": "a"},
    {"query_number": 44, "mark": "a"},
    {"query_number": 45, "mark": "a"},
    {"query_number": 46, "mark": "a"},
    {"query_number": 47, "mark": "a"},
    {"query_number": 48, "mark": "a"},
    {"query_number": 49, "mark": "a"},
    {"query_number": 50, "mark": "a"},
    {"query_number": 51, "mark": "a"},
    {"query_number": 52, "mark": "a"},
    {"query_number": 53, "mark": "a"},
    {"query_number": 54, "mark": "a"},
    {"query_number": 55, "mark": "a"},
    {"query_number": 56, "mark": "a"},
    {"query_number": 57, "mark": "a"},
    {"query_number": 58, "mark": "a"},
    {"query_number": 59, "mark": "a"},
    {"query_number": 60, "mark": "a"},
    {"query_number": 61, "mark": "a"},
    {"query_number": 62, "mark": "a"},
    {"query_number": 63, "mark": "a"},
    {"query_number": 64, "mark": "a"},
    {"query_number": 65, "mark": "a"},
    {"query_number": 66, "mark": "a"},
    {"query_number": 67, "mark": "a"},
    {"query_number": 68, "mark": "a"},
    {"query_number": 69, "mark": "a"},
    {"query_number": 70, "mark": "a"},
    {"query_number": 71, "mark": "a"},
    {"query_number": 72, "mark": "a"},
    {"query_number": 73, "mark": "a"},
    {"query_number": 74, "mark": "a"},
    {"query_number": 75, "mark": "a"},
    {"query_number": 76, "mark": "a"},
    {"query_number": 77, "mark": "a"},
    {"query_number": 78, "mark": "a"},
    {"query_number": 79, "mark": "a"},
    {"query_number": 80, "mark": "a"},
    {"query_number": 81, "mark": "a"},
    {"query_number": 82, "mark": "a"},
    {"query_number": 83, "mark": "a"},
    {"query_number": 84, "mark": "a"},
    {"query_number": 85, "mark": "a"},
    {"query_number": 86, "mark": "a"},
    {"query_number": 87, "mark": "a"},
    {"query_number": 88, "mark": "a"},
    {"query_number": 89, "mark": "a"},
    {"query_number": 90, "mark": "a"},
    {"query_number": 91, "mark": "a"},
    {"query_number": 92, "mark": "a"},
    {"query_number": 93, "mark": "a"},
    {"query_number": 94, "mark": "a"},
    {"query_number": 95, "mark": "a"},
    {"query_number": 96, "mark": "a"},
    {"query_number": 97, "mark": "a"},
    {"query_number": 98, "mark": "a"},
    {"query_number": 99, "mark": "a"},
    
    {"query_number": 14, "mark": "b"},
    {"query_number": 23, "mark": "b"},
    {"query_number": 24, "mark": "b"},
    {"query_number": 39, "mark": "b"},
]

# -------------------------------------------------------------------------------------------------

if test_param["skip_create"]:
    assert db_param["search_path"] == "tpcds", "Only tpcds is supported"


from concurrency import set_recent_tid, reset_recent_tid
from create_struct import temporary_table_pool
from log import get_test_info
from preview import preview
from dataset import get_tpcds
from parse import get_optimize


async def test(test_data):
    # test_data = get_optimize(test_data)
    import sqlglot
    print(sqlglot.parse_one(test_data).sql(pretty=True))
    preview_result = await preview(test_data)
    query_info = get_test_info("query")

    record = {
        "input": test_data,
        "query": query_info,
        "preview": preview_result,
    }
    if query["mark"] == "a":
        file_name = f"create_and_query_baseline_tpcdsq{query['query_number']}.json"
    else:
        assert query["mark"] == "b"
        file_name = f"create_and_query_baseline_tpcdsq{query['query_number']}_{query['mark']}.json"
    
    with open(str(Path(__file__).parent / "test_output" / file_name), "w") as f:
        json.dump(record, f, indent=4)

    return record


if __name__ == "__main__":

    set_recent_tid(new_priority=1, new_running_sql="test", type="db")
    import json

    for query in input:
        with get_execute_cursor_lock():
            temporary_table_pool.reset()
        reset_test_info()
        test_data = get_tpcds(query["query_number"], query["mark"])
        asyncio.run(test(test_data))
    
    reset_recent_tid(type="db")
