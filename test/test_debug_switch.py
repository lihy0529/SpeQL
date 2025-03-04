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
from debug import get_last_runnable_sql, set_last_runnable_sql
from cost import check_new_sql
from concurrency import set_recent_tid, reset_recent_tid
from data_process import mask_sql_by_portion


async def test(test_data, config):

    test_data = mask_sql_by_portion(test_data, config)

    print(
        "\033[33m" + str(check_new_sql(get_last_runnable_sql(), test_data)) + "\033[0m"
    )
    set_last_runnable_sql(test_data)


input = [
    {"query_number": 1, "mark": "a", "remove": "begin", "portion": 0.5},
    {"query_number": 1, "mark": "a", "remove": "begin", "portion": 0.4},
    {"query_number": 1, "mark": "a", "remove": "begin", "portion": 0.3},
    {"query_number": 1, "mark": "a", "remove": "begin", "portion": 0.9},
]

if __name__ == "__main__":
    set_recent_tid(new_priority=1, new_running_sql="test", type="llm")

    for query in input:
        test_data = get_tpcds(query["query_number"], query["mark"])
        asyncio.run(
            test(test_data, {"remove": query["remove"], "portion": query["portion"]})
        )

    reset_recent_tid(type="llm")
