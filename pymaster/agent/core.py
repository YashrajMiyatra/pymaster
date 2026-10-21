"""
Autonomous Agent execution engine for PyMaster.
Executes the Plan -> Tool -> Observe -> Self-Heal loop.
"""

from typing import List, Dict, Any, Callable, Optional
import json
from pymaster.agent.prompts import SYSTEM_PROMPT
from pymaster.llm.client import LocalLLMClient, LLMResponse
from pymaster.tools.base import registry


class PyMasterAgent:
    """The central autonomous Python coding agent."""

    def __init__(
        self,
        llm_client: LocalLLMClient,
        max_turns: int = 15,
        system_prompt: str = SYSTEM_PROMPT,
        workspace_dir: str = ".",
    ):
        self.llm = llm_client
        self.max_turns = max_turns
        self.workspace_dir = workspace_dir
        self.messages: List[Dict[str, Any]] = [
            {"role": "system", "content": system_prompt}
        ]

    def reset_conversation(self):
        """Clears memory back to base system prompt."""
        self.messages = [self.messages[0]]

    def run_turn(
        self,
        user_input: str,
        token_callback: Optional[Callable[[str], None]] = None,
        tool_start_callback: Optional[Callable[[str, Dict[str, Any]], None]] = None,
        tool_result_callback: Optional[Callable[[str, Any], None]] = None,
    ) -> str:
        """
        Executes one full user interaction, which may trigger multiple autonomous tool iterations.
        """
        self.messages.append({"role": "user", "content": user_input})
        turns = 0
        final_answer = ""

        while turns < self.max_turns:
            turns += 1

            # 1. Fetch available tools from the registry
            tools_schema = registry.get_schemas()

            # 2. Stream generation from local LLM
            stream_gen = self.llm.stream_chat(
                messages=self.messages,
                tools=tools_schema if tools_schema else None,
            )

            # Consume the generator, firing token callbacks for UI streaming and capturing the generator return value
            response_tokens = []
            llm_response = None
            while True:
                try:
                    token = next(stream_gen)
                    response_tokens.append(token)
                    if token_callback:
                        token_callback(token)
                except StopIteration as e:
                    if isinstance(e.value, LLMResponse):
                        llm_response = e.value
                    break

            if llm_response is None:
                total_text = "".join(response_tokens)
                parsed_tools = self.llm._parse_tool_calls([], total_text)
                llm_response = LLMResponse(content=total_text, tool_calls=parsed_tools)

            final_answer = llm_response.content

            # 3. If no tool calls were requested, we are done!
            if not llm_response.has_tool_calls():
                self.messages.append({"role": "assistant", "content": llm_response.content})
                break

            # 4. Otherwise, execute each requested tool call
            self.messages.append({
                "role": "assistant",
                "content": llm_response.content,
                "tool_calls": [
                    {
                        "id": f"call_{i}",
                        "type": "function",
                        "function": {
                            "name": tc["name"],
                            "arguments": json.dumps(tc["arguments"]),
                        },
                    }
                    for i, tc in enumerate(llm_response.tool_calls)
                ],
            })

            for i, tc in enumerate(llm_response.tool_calls):
                name = tc["name"]
                args = tc["arguments"]

                if tool_start_callback:
                    tool_start_callback(name, args)

                # Execute tool
                tool_output = registry.execute(name, **args)

                if tool_result_callback:
                    tool_result_callback(name, tool_output)

                # Append tool observation back into conversation
                self.messages.append({
                    "role": "tool",
                    "tool_call_id": f"call_{i}",
                    "name": name,
                    "content": str(tool_output),
                })

        return final_answer
