# Copyright (c) 2025 Haoyu Li
# Released under the MIT License.
# See LICENSE file in the project root for details.

#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
LLM API module for SpeQL.
"""

import sys
import time
import json
import numpy as np
from pathlib import Path
from typing import List, Dict, Any, Union
from openai import OpenAI, APITimeoutError

# -----------------------------------------------------------------------------
# Path Configuration
# -----------------------------------------------------------------------------

root_dir = str(Path(__file__).parent.parent)
sys.path.extend(
    [
        root_dir,
        str(Path(root_dir) / "src"),
        str(Path(root_dir) / "util"),
    ]
)

# -----------------------------------------------------------------------------
# Local Imports
# -----------------------------------------------------------------------------

from param import get_llm_param, get_enable_param, get_test_param
from log import log, append_test_info

# -----------------------------------------------------------------------------
# OpenAI Client Configuration
# -----------------------------------------------------------------------------

openai_api = OpenAI(api_key=get_llm_param()["api_key"])

# -----------------------------------------------------------------------------
# LLM Interaction
# -----------------------------------------------------------------------------


async def get_llm_response(
    task: str, iterator: int, messages: List[Dict[str, str]], max_tokens: int = 8192
) -> str:
    """
    Gets response from LLM based on task type and iteration.

    Args:
        task: Type of task ('complex', 'middle', 'explain', 'simple')
        iterator: Current iteration number
        messages: List of conversation messages
        max_new_tokens: Maximum new tokens to generate

    Returns:
        str: LLM response content

    Raises:
        Should not raise any errors. If it does, it's a bug.
    """
    start_time = time.time()

    assert task in ["complex", "middle", "explain", "simple"], "Invalid task"

    try:
        if task == "complex" and get_enable_param()["predict_inference"]:
            model = (
                get_llm_param()["fast"] if iterator == 0 else get_llm_param()["accurate"]
            )
            response = openai_api.chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=max_tokens,
                prediction={"type": "content", "content": messages[-1]["content"]},
                timeout=get_llm_param()["timeout"],
            )

        elif task == "middle":
            assert iterator == 0, "Iterator should be 0 for Middle"
            response = openai_api.chat.completions.create(
                model=get_llm_param()["fast"],
                messages=messages,
                max_tokens=128,
                timeout=get_llm_param()["timeout"],
            )

        elif task in ["explain", "simple"]:
            model = (
                get_llm_param()["fast"] if iterator == 0 else get_llm_param()["accurate"]
            )
            response = openai_api.chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=max_tokens,
                timeout=get_llm_param()["timeout"],
            )

    except APITimeoutError:
        return "Inference timeout"

    except Exception as e:
        log("error.txt", f"{str(e)}")
        return "Error: LLM API error"

    end_time = time.time()

    output = response.choices[0].message.content
    prompt_tokens = response.usage.prompt_tokens
    completion_tokens = response.usage.completion_tokens

    record = {
        "task": task,
        "iterator": iterator,
        "time": end_time - start_time,
        "input_tokens": prompt_tokens,
        "output_tokens": completion_tokens,
        "output": output,
        "input": messages.copy(),
    }
    if get_test_param()["output_debug"]:
        append_test_info("debug", record)
    log("inference.txt", record, is_dict=True)

    return output


# -----------------------------------------------------------------------------
# Embedding Generation
# -----------------------------------------------------------------------------


def get_embedding(input_text: Union[str, List[str]]) -> np.ndarray:
    """
    Generates embeddings for input text using OpenAI's embedding model.

    Args:
        input_text: Text or list of texts to generate embeddings for

    Returns:
        np.ndarray: Numpy array containing the embedding vectors
    """
    return_val = (
        openai_api.embeddings.create(model="text-embedding-3-large", input=input_text)
        .data[0]
        .embedding
    )
    return np.array(return_val, dtype=np.float32)
