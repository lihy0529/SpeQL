import sys, asyncio, re
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
from param import get_plugin_param
from concurrency import set_recent_tid, reset_recent_tid
from format import prepare_sql, format, format_output
from preview import preview


async def test_format_output(test_data):
    prepare_sql_result = prepare_sql(test_data)

    rewrite = format(re.sub(r"/\*.*?\*/", "", format(prepare_sql_result["sql"]), re.DOTALL))
    preview_result = await preview(rewrite)
    assert preview_result is not None

    sql_to_preview = {
        prepare_sql_result["sql"]: {
            "modification": prepare_sql_result["sql"],
            "rewrite": rewrite,
            "preview": preview_result,
        }
    }
    return format_output(prepare_sql_result, sql_to_preview)


async def test(test_data):
    test_data = test_data + f"\n{get_plugin_param()['cursor_identifier']}"
    print("\033[33m---Test Format Output---\033[0m")

    print(await test_format_output(test_data))


input = [
    {"query_number": 1, "mark": "a"},
]

if __name__ == "__main__":
    set_recent_tid(new_priority=1, new_running_sql="test", type="llm")

    for query in input:
        test_data = get_tpcds(query["query_number"], query["mark"])
        asyncio.run(test(test_data))

    reset_recent_tid(type="llm")
