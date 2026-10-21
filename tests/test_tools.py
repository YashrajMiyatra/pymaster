"""
Unit tests for PyMaster tool suite.
"""

import os
from pathlib import Path
import pytest
from pymaster.tools.base import registry
from pymaster.tools.filesystem import read_file, write_file, edit_file, list_files
from pymaster.tools.ast_intel import check_syntax, inspect_symbols
from pymaster.tools.executor import run_inline_python, run_python_file


def test_tool_registry():
    schemas = registry.get_schemas()
    names = [s["function"]["name"] for s in schemas]
    assert "read_file" in names
    assert "write_file" in names
    assert "edit_file" in names
    assert "check_syntax" in names
    assert "inspect_symbols" in names
    assert "run_python_file" in names


def test_file_operations(tmp_path: Path):
    test_file = tmp_path / "sample.py"

    # Write file
    write_res = write_file(str(test_file), "def hello():\n    return 'world'\n")
    assert "Success" in write_res
    assert test_file.exists()

    # Read file
    read_res = read_file(str(test_file))
    assert "def hello()" in read_res

    # Edit file
    edit_res = edit_file(str(test_file), target="return 'world'", replacement="return 'universe'")
    assert "Success" in edit_res

    # Verify content
    read_res_updated = read_file(str(test_file))
    assert "return 'universe'" in read_res_updated


def test_ast_checker(tmp_path: Path):
    valid_file = tmp_path / "valid.py"
    write_file(str(valid_file), "def add(a: int, b: int) -> int:\n    return a + b\n")
    assert "Syntax OK" in check_syntax(str(valid_file))

    invalid_file = tmp_path / "broken.py"
    write_file(str(invalid_file), "def add(a, b\n    return a + b\n")
    assert "SYNTAX ERROR" in check_syntax(str(invalid_file))


def test_inspect_symbols(tmp_path: Path):
    sample_file = tmp_path / "module.py"
    content = '''
import math
from typing import List

class Calculator:
    """A sample calculator class."""
    def compute(self, x: int) -> int:
        """Compute square."""
        return x * x

def run_calc(nums: List[int]) -> int:
    """Sum calculations."""
    return sum(nums)
'''
    write_file(str(sample_file), content)
    intel = inspect_symbols(str(sample_file))
    assert "Calculator" in intel
    assert "run_calc" in intel
    assert "import math" in intel


def test_inline_execution():
    res = run_inline_python("print('PyMaster execution verified')")
    assert "PyMaster execution verified" in res
