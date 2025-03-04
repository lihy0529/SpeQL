# Copyright (c) 2025 Haoyu Li
# Released under the MIT License.
# See LICENSE file in the project root for details.

#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Log message and error information.
"""

import os
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional
from datetime import datetime
import json

# -----------------------------------------------------------------------------
# Path Configuration
# -----------------------------------------------------------------------------

root_dir = str(Path(__file__).parent.parent)
sys.path.extend([
    root_dir,
    str(Path(root_dir) / "src"),
    str(Path(root_dir) / "util"),
])

# -----------------------------------------------------------------------------
# Log Directory Configuration
# -----------------------------------------------------------------------------

date = datetime.now().strftime("%Y-%m-%d %H:%M:%S").replace(" ", "_").replace(":", "-")
log_path = str(Path(__file__).parent.resolve() / ".." / "log" / date)

# -----------------------------------------------------------------------------
# Global Variables
# -----------------------------------------------------------------------------

test_info: Dict[str, List[Any]] = {}

# -----------------------------------------------------------------------------
# Logging Functions
# -----------------------------------------------------------------------------

def log(file: str, message: str | Dict[str, Any] = "", split: str = "\n", is_dict: bool = False, with_indent: bool = False) -> None:
    """
    Logs a message to a specified file in the log directory.
    """
    if not os.path.exists(log_path):
        os.makedirs(log_path)

    with open(log_path + "/" + file, "a") as f:
        if is_dict:
            message = {'date_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | message
            if with_indent:
                f.write(f"{json.dumps(message, indent=4)}{split}")
            else:
                f.write(f"{json.dumps(message)}{split}")
        else:
            f.write(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} {message}{split}")
    
    if file == "error.txt":
        print(message)
        import traceback
        traceback.print_exc()

# -----------------------------------------------------------------------------
# Test Information Management
# -----------------------------------------------------------------------------

def append_test_info(key: str, value: Any) -> None:
    """
    Appends a value to the test information dictionary under specified key.
    """
    global test_info
    if key not in test_info:
        test_info[key] = []
    test_info[key].append(value)


def get_test_info(key: str) -> Optional[List[Any]]:
    """
    Retrieves test information for a specified key.
    """
    global test_info
    return test_info.get(key)


def reset_test_info() -> None:
    """
    Resets the test information dictionary to empty.
    """
    global test_info
    test_info = {}
