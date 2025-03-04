import sys, asyncio, json
from pathlib import Path

root_dir = str(Path(__file__).parent.parent)
sys.path.extend([
    root_dir,
    str(Path(root_dir) / "src"),
    str(Path(root_dir) / "util"),
])

from concurrency import set_recent_tid, reset_recent_tid
from debug_rule import get_replacement_rule

async def test(test_data):
    for data in test_data:
        if data["debug"]:
            print(get_replacement_rule(data["input"], data["debug"]))
    
input = [
    {"query_number": 3, "mark": "a"},
]

if __name__ == "__main__":
    set_recent_tid(new_priority=1, new_running_sql="test", type="llm")
    
    for query in input:
        file_name = f"debug_line_by_line_tpcdsq{query['query_number']}.json"
        file = str(Path(__file__).parent / "dataset" / "debug_line_by_line" / file_name)
        with open(file, "r") as f:
            test_data = json.load(f)
        asyncio.run(test(test_data))
    
    reset_recent_tid(type="llm")