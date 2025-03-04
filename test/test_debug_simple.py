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
from debug_simple import debug_simple
from concurrency import set_recent_tid, reset_recent_tid
from param import get_test_param
from log import get_test_info
from data_process import mask_sql_by_portion

test_param = get_test_param()
test_param["output_rule"] = True
test_param["output_useful_historical_sql"] = True
test_param["output_useful_schema"] = True


async def test(test_data, config):
    test_data = mask_sql_by_portion(test_data, config)
    print("Data: ", test_data)
    debug = await debug_simple(test_data)
    print(
        "\033[33m" + "Rule: " + (str(get_test_info("rule")[-1])
        if get_test_info("rule")
        else "Debug fail") + "\033[0m"
    )
    print(
        "\033[33m"
        + "UsefulHistoricalSQL: "
        + str(get_test_info("useful_historical_sql")[-1])
        + "\033[0m"
    )
    print(
        "\033[33m"
        + "UsefulSchema: "
        + str(get_test_info("useful_schema")[-1])
        + "\033[0m"
    )
    print("\033[33m" + str(debug) + "\033[0m")


input = [
    {"query_number": 1, "mark": "a", "remove": "begin", "portion": 0.1},
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
