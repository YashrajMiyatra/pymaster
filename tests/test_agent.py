"""
Test agent self-healing loop and mock tool execution.
"""

from typing import List, Dict, Any, Generator
import json
from pymaster.agent.core import PyMasterAgent
from pymaster.llm.client import LocalLLMClient, LLMResponse


class MockLLMClient(LocalLLMClient):
    """Simulates an LLM calling tools and self-healing a bug."""

    def __init__(self):
        super().__init__()
        self.step = 0

    def stream_chat(
        self,
        messages: List[Dict[str, Any]],
        tools: Any = None,
        temperature: float = 0.2,
    ) -> Generator[str, None, LLMResponse]:
        self.step += 1

        if self.step == 1:
            # Step 1: LLM decides to write a buggy file first
            yield "Let me write the calculator script."
            return LLMResponse(
                content="Writing calculator script...",
                tool_calls=[{
                    "name": "write_file",
                    "arguments": {
                        "path": "calc_test.py",
                        "content": "def calculate(a, b\n    return a + b\n",
                    },
                }],
            )
        elif self.step == 2:
            # Step 2: LLM checks syntax and finds the error
            yield "Let me check the syntax."
            return LLMResponse(
                content="Checking syntax...",
                tool_calls=[{
                    "name": "check_syntax",
                    "arguments": {"path": "calc_test.py"},
                }],
            )
        elif self.step == 3:
            # Step 3: LLM sees the syntax error and fixes it with edit_file!
            yield "Fixing the missing parenthesis in calc_test.py."
            return LLMResponse(
                content="Fixing syntax...",
                tool_calls=[{
                    "name": "edit_file",
                    "arguments": {
                        "path": "calc_test.py",
                        "target": "def calculate(a, b\n",
                        "replacement": "def calculate(a, b):\n",
                    },
                }],
            )
        elif self.step == 4:
            # Step 4: LLM verifies syntax again
            yield "Verifying fix."
            return LLMResponse(
                content="Verifying...",
                tool_calls=[{
                    "name": "check_syntax",
                    "arguments": {"path": "calc_test.py"},
                }],
            )
        else:
            # Step 5: Finalized!
            msg = "Calculator script written, syntax checked, and self-healed successfully!"
            yield msg
            return LLMResponse(content=msg, tool_calls=[])


def test_agent_self_healing_workflow():
    mock_llm = MockLLMClient()
    agent = PyMasterAgent(llm_client=mock_llm, max_turns=6)

    captured_tokens = []
    executed_tools = []

    final_resp = agent.run_turn(
        user_input="Build a calculate function",
        token_callback=lambda t: captured_tokens.append(t),
        tool_start_callback=lambda name, args: executed_tools.append(name),
    )

    # Verify tool execution order
    assert executed_tools == ["write_file", "check_syntax", "edit_file", "check_syntax"]
    assert "self-healed successfully" in final_resp

    # Clean up test artifact
    from pathlib import Path
    test_artifact = Path("calc_test.py")
    if test_artifact.exists():
        test_artifact.unlink()
