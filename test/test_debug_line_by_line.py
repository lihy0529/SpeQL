import sys, asyncio, re, random
from pathlib import Path

root_dir = str(Path(__file__).parent.parent)
sys.path.extend(
    [
        root_dir,
        str(Path(root_dir) / "src"),
        str(Path(root_dir) / "util"),
    ]
)

from dataset import get_tpcds
from debug import debug
from param import get_plugin_param, get_test_param
from concurrency import set_recent_tid, reset_recent_tid, get_speculate_middle
from data_process import mask_sql_by_line
from math import ceil
from log import get_test_info, reset_test_info
from cost import increase_active_period, reset_active_period

test_param = get_test_param()
test_param["output_debug"] = True
test_param["search_path"] = "ext_tpcds100"


async def test(query):
    test_data = get_tpcds(query["query_number"], query["mark"])
    length = len(test_data.split("\n"))
    if query["step"] < 0:
        query["step"] = ceil(length * (-query["step"]))
        
    if query["remove_line"] >= length:
        query["remove_line"] = length - 1

    mask_sql = mask_sql_by_line(
        test_data,
        {
            "remove": query["remove"],
            "remove_line": query["remove_line"],
            "step": query["step"],
        },
    )
    prefix, suffix, hidden = mask_sql["prefix"], mask_sql["suffix"], mask_sql["hidden"]
    
    show_line = len(hidden) % query["step"]
    
    print(prefix)
    print(suffix)
    print(hidden)
    print(show_line)

    Record = []

    reset_active_period()
    while show_line <= len(hidden):
        test_data = (
            prefix
            + hidden[:show_line]
            + [get_plugin_param()["cursor_identifier"]]
            + suffix
        )
        test_data = "\n".join(test_data)
        reset_test_info()
        debug_result = await debug(test_data)
        if debug_result is None:
            increase_active_period()
        else:
            reset_active_period()
        from cost import get_max_retry
        print(get_max_retry())
        middle = await get_speculate_middle()
        debug_info = get_test_info("debug")
        print("\033[33m" + str(debug_result) + "\033[0m")
        show_line += query["step"]
        Record.append({"input": test_data, "debug": debug_result, "middle": middle, "debug_info": debug_info})

        if query["mark"] == "a":
            file_name = f"debug_line_by_line_tpcdsq{query['query_number']}_remove_{query['remove']}_remove_line_{query['remove_line']}_step_{query['step']}.json"
        else:
            assert query["mark"] == "b"
            file_name = (
                f"debug_line_by_line_tpcdsq{query['query_number']}_{query['mark']}_remove_{query['remove']}_remove_line_{query['remove_line']}_step_{query['step']}.json"
            )
        with open(str(Path(__file__).parent / "test_output" / file_name), "w") as f:
            import json

            json.dump(Record, f, indent=4)


input = [
    # # {"query_number": 16, "mark": "a", "remove": "end", "remove_line": -1, "step": -0.05},
    # {"query_number": 1, "mark": "a", "remove": "end", "remove_line": 20, "step": 1},
    # {"query_number": 2, "mark": "a", "remove": "end", "remove_line": 20, "step": 1},
    # {"query_number": 3, "mark": "a", "remove": "end", "remove_line": 20, "step": 1},
    # {"query_number": 4, "mark": "a", "remove": "end", "remove_line": 20, "step": 1},
    {"query_number": 5, "mark": "a", "remove": "end", "remove_line": 20, "step": 1},
    # {"query_number": 6, "mark": "a", "remove": "end", "remove_line": 20, "step": 1},
    # {"query_number": 7, "mark": "a", "remove": "end", "remove_line": 20, "step": 1},
    # {"query_number": 8, "mark": "a", "remove": "end", "remove_line": 20, "step": 1},
    # {"query_number": 9, "mark": "a", "remove": "end", "remove_line": 20, "step": 1},
    # {"query_number": 10, "mark": "a", "remove": "end", "remove_line": 20, "step": 1},
    # {"query_number": 11, "mark": "a", "remove": "end", "remove_line": 20, "step": 1},
    {"query_number": 12, "mark": "a", "remove": "end", "remove_line": 20, "step": 1},
    # {"query_number": 13, "mark": "a", "remove": "end", "remove_line": 20, "step": 1},
    # {"query_number": 14, "mark": "a", "remove": "end", "remove_line": 20, "step": 1},
    # {"query_number": 15, "mark": "a", "remove": "end", "remove_line": 20, "step": 1},
    # {"query_number": 16, "mark": "a", "remove": "end", "remove_line": 20, "step": 1},
    # {"query_number": 17, "mark": "a", "remove": "end", "remove_line": 20, "step": 1},
    # {"query_number": 18, "mark": "a", "remove": "end", "remove_line": 20, "step": 1},
    # {"query_number": 19, "mark": "a", "remove": "end", "remove_line": 20, "step": 1},
    # {"query_number": 20, "mark": "a", "remove": "end", "remove_line": 20, "step": 1},
    # {"query_number": 21, "mark": "a", "remove": "end", "remove_line": 20, "step": 1},
    # {"query_number": 22, "mark": "a", "remove": "end", "remove_line": 20, "step": 1},
    # {"query_number": 23, "mark": "a", "remove": "end", "remove_line": 20, "step": 1},
    # {"query_number": 24, "mark": "a", "remove": "end", "remove_line": 20, "step": 1},
    # {"query_number": 25, "mark": "a", "remove": "end", "remove_line": 20, "step": 1},
    # {"query_number": 26, "mark": "a", "remove": "end", "remove_line": 20, "step": 1},
    # {"query_number": 27, "mark": "a", "remove": "end", "remove_line": 20, "step": 1},
    # {"query_number": 28, "mark": "a", "remove": "end", "remove_line": 20, "step": 1},
    # {"query_number": 29, "mark": "a", "remove": "end", "remove_line": 20, "step": 1},
    # {"query_number": 30, "mark": "a", "remove": "end", "remove_line": 20, "step": 1},
    # {"query_number": 31, "mark": "a", "remove": "end", "remove_line": 20, "step": 1},
    # {"query_number": 32, "mark": "a", "remove": "end", "remove_line": 20, "step": 1},
    # {"query_number": 33, "mark": "a", "remove": "end", "remove_line": 20, "step": 1},
    # {"query_number": 34, "mark": "a", "remove": "end", "remove_line": 20, "step": 1},
    # {"query_number": 35, "mark": "a", "remove": "end", "remove_line": 20, "step": 1},
    # {"query_number": 36, "mark": "a", "remove": "end", "remove_line": 20, "step": 1},
    # {"query_number": 37, "mark": "a", "remove": "end", "remove_line": 20, "step": 1},
    # {"query_number": 38, "mark": "a", "remove": "end", "remove_line": 20, "step": 1},
    # {"query_number": 39, "mark": "a", "remove": "end", "remove_line": 20, "step": 1},
    # {"query_number": 40, "mark": "a", "remove": "end", "remove_line": 20, "step": 1},
    # {"query_number": 41, "mark": "a", "remove": "end", "remove_line": 20, "step": 1},
    # {"query_number": 42, "mark": "a", "remove": "end", "remove_line": 20, "step": 1},
    # {"query_number": 43, "mark": "a", "remove": "end", "remove_line": 20, "step": 1},
    # {"query_number": 44, "mark": "a", "remove": "end", "remove_line": 20, "step": 1},
    # {"query_number": 45, "mark": "a", "remove": "end", "remove_line": 20, "step": 1},
    # {"query_number": 46, "mark": "a", "remove": "end", "remove_line": 20, "step": 1},
    # {"query_number": 47, "mark": "a", "remove": "end", "remove_line": 20, "step": 1},
    # {"query_number": 48, "mark": "a", "remove": "end", "remove_line": 20, "step": 1},
    # {"query_number": 49, "mark": "a", "remove": "end", "remove_line": 20, "step": 1},
    # {"query_number": 50, "mark": "a", "remove": "end", "remove_line": 20, "step": 1},
    # {"query_number": 51, "mark": "a", "remove": "end", "remove_line": 20, "step": 1},
    # {"query_number": 52, "mark": "a", "remove": "end", "remove_line": 20, "step": 1},
    # {"query_number": 53, "mark": "a", "remove": "end", "remove_line": 20, "step": 1},
    # {"query_number": 54, "mark": "a", "remove": "end", "remove_line": 20, "step": 1},
    # {"query_number": 55, "mark": "a", "remove": "end", "remove_line": 20, "step": 1},
    # {"query_number": 56, "mark": "a", "remove": "end", "remove_line": 20, "step": 1},
    # {"query_number": 57, "mark": "a", "remove": "end", "remove_line": 20, "step": 1},
    # {"query_number": 58, "mark": "a", "remove": "end", "remove_line": 20, "step": 1},
    # {"query_number": 59, "mark": "a", "remove": "end", "remove_line": 20, "step": 1},
    # {"query_number": 60, "mark": "a", "remove": "end", "remove_line": 20, "step": 1},
    # {"query_number": 61, "mark": "a", "remove": "end", "remove_line": 20, "step": 1},
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
    # {"query_number": 75, "mark": "a", "remove": "end", "remove_line": 20, "step": 1},
    # {"query_number": 76, "mark": "a", "remove": "end", "remove_line": 20, "step": 1},
    # {"query_number": 77, "mark": "a", "remove": "end", "remove_line": 20, "step": 1},
    # {"query_number": 78, "mark": "a", "remove": "end", "remove_line": 20, "step": 1},
    # {"query_number": 79, "mark": "a", "remove": "end", "remove_line": 20, "step": 1},
    # {"query_number": 80, "mark": "a", "remove": "end", "remove_line": 20, "step": 1},
    # {"query_number": 81, "mark": "a", "remove": "end", "remove_line": 20, "step": 1},
    # {"query_number": 82, "mark": "a", "remove": "end", "remove_line": 20, "step": 1},
    # {"query_number": 83, "mark": "a", "remove": "end", "remove_line": 20, "step": 1},
    # {"query_number": 84, "mark": "a", "remove": "end", "remove_line": 20, "step": 1},
    # {"query_number": 85, "mark": "a", "remove": "end", "remove_line": 20, "step": 1},
    # {"query_number": 86, "mark": "a", "remove": "end", "remove_line": 20, "step": 1},
    # {"query_number": 87, "mark": "a", "remove": "end", "remove_line": 20, "step": 1},
    # {"query_number": 88, "mark": "a", "remove": "end", "remove_line": 20, "step": 1},
    # {"query_number": 89, "mark": "a", "remove": "end", "remove_line": 20, "step": 1},
    # {"query_number": 90, "mark": "a", "remove": "end", "remove_line": 20, "step": 1},
    # {"query_number": 91, "mark": "a", "remove": "end", "remove_line": 20, "step": 1},
    # {"query_number": 92, "mark": "a", "remove": "end", "remove_line": 20, "step": 1},
    # {"query_number": 93, "mark": "a", "remove": "end", "remove_line": 20, "step": 1},
    # {"query_number": 94, "mark": "a", "remove": "end", "remove_line": 20, "step": 1},
    # {"query_number": 95, "mark": "a", "remove": "end", "remove_line": 20, "step": 1},
    # {"query_number": 96, "mark": "a", "remove": "end", "remove_line": 20, "step": 1},
    # {"query_number": 97, "mark": "a", "remove": "end", "remove_line": 20, "step": 1},
    # {"query_number": 98, "mark": "a", "remove": "end", "remove_line": 20, "step": 1},
    # {"query_number": 99, "mark": "a", "remove": "end", "remove_line": 20, "step": 1},
    {"query_number": 14, "mark": "b", "remove": "end", "remove_line": 20, "step": 1},
    {"query_number": 23, "mark": "b", "remove": "end", "remove_line": 20, "step": 1},
    {"query_number": 24, "mark": "b", "remove": "end", "remove_line": 20, "step": 1},
    {"query_number": 39, "mark": "b", "remove": "end", "remove_line": 20, "step": 1},
]

if __name__ == "__main__":
    set_recent_tid(new_priority=1, new_running_sql="test", type="llm")

    for query in input:
        asyncio.run(test(query))

    reset_recent_tid(type="llm")
