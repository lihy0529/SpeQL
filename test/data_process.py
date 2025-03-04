import sys, re, random
from pathlib import Path

root_dir = str(Path(__file__).parent.parent)
sys.path.extend(
    [
        root_dir,
        str(Path(root_dir) / "src"),
        str(Path(root_dir) / "util"),
    ]
)

from param import get_plugin_param

def mask_sql_by_portion(test_data, config):
    
    assert (
        config["portion"] >= 0 and config["portion"] <= 1
    ), "Portion should be between 0 and 1"
        
    test_data = re.split(r"(\s+|,)", test_data)
    length = len(test_data)
    
    if config["remove"] == "begin":
        test_data = test_data[int(config["portion"] * length) :]
        test_data = [get_plugin_param()["cursor_identifier"]] + test_data

    elif config["remove"] == "end":
        test_data = test_data[: int((1 - config["portion"]) * length)]
        test_data = test_data + [get_plugin_param()["cursor_identifier"]]

    elif config["remove"] == "random":
        cursor = random.randint(0, int((1 - config["portion"]) * length))
        test_data = (
            test_data[:cursor]
            + [get_plugin_param()["cursor_identifier"]]
            + test_data[cursor + int(config["portion"] * length) :]
        )

    else:
        raise ValueError(f"Invalid remove type: {config['remove']}")

    test_data = "".join(test_data)
    return test_data


def mask_sql_by_line(test_data, config):
    test_data = test_data.split("\n")
    length = len(test_data)

    if config["remove_line"] == -1:
        config["remove_line"] = length - 1
        
    assert (
        config["step"] > 0
    ), "Step should be greater than 0"
        
    assert (
        length > config["remove_line"]
    ), "RemoveLine should be greater than the number of lines in TestData"
        
    assert (
        config["remove_line"] >= config["step"]
    ), "RemoveLine should be greater than Step"

    if config["remove"] == "begin":
        prefix = []
        suffix = test_data[config["remove_line"] :]
        hidden = test_data[: config["remove_line"]]
    elif config["remove"] == "end":
        prefix = test_data[: len(test_data) - config["remove_line"]]
        suffix = []
        hidden = test_data[len(test_data) - config["remove_line"] :]
    elif config["remove"] == "random":
        cursor = random.randint(0, len(test_data) - config["remove_line"])
        prefix = test_data[:cursor]
        suffix = test_data[cursor + config["remove_line"] :]
        hidden = test_data[cursor : cursor + config["remove_line"]]
    else:
        raise ValueError(f"Invalid remove type: {config['remove']}")
    
    return {"prefix": prefix, "suffix": suffix, "hidden": hidden}