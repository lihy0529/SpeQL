from pathlib import Path
import sys, json

root_dir = str(Path(__file__).parent.parent)
sys.path.extend(
    [
        root_dir,
        str(Path(root_dir) / "src"),
        str(Path(root_dir) / "util"),
    ]
)

ReadList = []


def get_tpcds(Number, Mark="a"):
    with open(
        str(Path(__file__).parent.resolve())
        + "/dataset/tpcds/"
        + "tpcdsq"
        + str(Number)
        + ".sql",
        "r",
    ) as File:
        SQL = File.read().split(";")
        if Mark == "a":
            return SQL[0]
        else:
            assert Mark == "b", "Mark should be a or b"
            assert len(SQL) == 3, "SQL should have 2 parts, though the last one is empty"
            return SQL[1]


def get_debug_line_by_line(query):
    if query["mark"] == "a":
        FileName = f"debug_line_by_line_tpcdsq{query['query_number']}_remove_{query['remove']}_remove_line_{query['remove_line']}_step_{query['step']}.json"

    else:
        assert query["mark"] == "b", "Mark should be a or b"
        FileName = f"debug_line_by_line_tpcdsq{query['query_number']}_{query['mark']}_remove_{query['remove']}_remove_line_{query['remove_line']}_step_{query['step']}.json"

    with open(
        str(Path(__file__).parent.resolve())
        + "/dataset/debug_line_by_line/"
        + FileName,
        "r",
    ) as File:
        return json.load(File)