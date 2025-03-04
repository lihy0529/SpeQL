import sys
from pathlib import Path

root_dir = str(Path(__file__).parent.parent)

sys.path.extend([
    root_dir,
    str(Path(root_dir) / "src"),
    str(Path(root_dir) / "util"),
])

from schema import get_schema
from concurrency import set_recent_tid, reset_recent_tid

if __name__ == "__main__":
    set_recent_tid(new_priority = 1, new_running_sql = "test", type="llm")
    print(get_schema())
    reset_recent_tid(type="llm")



