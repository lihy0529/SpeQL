import sys, asyncio
from pathlib import Path

root_dir = str(Path(__file__).parent.parent)
sys.path.extend([
    root_dir,
    str(Path(root_dir) / "src"),
    str(Path(root_dir) / "util"),
])

from dataset import get_tpcds
from debug import debug
from param import get_plugin_param
from concurrency import set_recent_tid, reset_recent_tid

async def test(test_data):
    test_data = test_data + f"\n{get_plugin_param()['cursor_identifier']}"
    debug_result = await debug(test_data)
    print("\033[33m" + debug_result + "\033[0m")

input = [
    {"query_number": 1, "mark": "a"},
    {"query_number": 2, "mark": "a"},
]

if __name__ == "__main__":
    set_recent_tid(new_priority=1, new_running_sql="test", type="llm")

    for query in input:
        test_data = get_tpcds(query["query_number"], query["mark"])
        asyncio.run(test(test_data))
    
    reset_recent_tid(type="llm")