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
from concurrency import set_recent_tid, reset_recent_tid
from data_process import mask_sql_by_portion

async def test(test_data, config):

    test_data = mask_sql_by_portion(test_data, config)
    debug_result = await debug(test_data)
    print("\033[33m" + str(debug_result) + "\033[0m")


input = [
    {"query_number": 1, "mark": "a", "remove": "begin", "portion": 0.2},
    {"query_number": 1, "mark": "a", "remove": "end", "portion": 0.6},
    {"query_number": 1, "mark": "a", "remove": "random", "portion": 0.2},
]

if __name__ == "__main__":
    set_recent_tid(new_priority=1, new_running_sql="test", type="llm")

    for query in input:
        test_data = get_tpcds(query["query_number"], query["mark"])
        asyncio.run(
            test(test_data, {"remove": query["remove"], "portion": query["portion"]})
        )

    reset_recent_tid(type="llm")
