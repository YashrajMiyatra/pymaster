"""
LLM Client and tool call parser for PyMaster.
Supports local endpoints (Ollama, llama.cpp, LM Studio, vLLM) and direct HTTP streaming.
"""

import json
import re
from typing import List, Dict, Any, Generator, Optional
import httpx


class LLMResponse:
    """Encapsulates response text and any extracted tool invocations."""

    def __init__(self, content: str, tool_calls: Optional[List[Dict[str, Any]]] = None):
        self.content = content
        self.tool_calls = tool_calls or []

    def has_tool_calls(self) -> bool:
        return len(self.tool_calls) > 0


class LocalLLMClient:
    """Client for local OpenAI-compatible inference servers."""

    def __init__(
        self,
        base_url: str = "http://localhost:11434/v1",
        model: str = "qwen2.5-coder:1.5b",
        api_key: str = "local",
        timeout: float = 120.0,
    ):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.api_key = api_key
        self.timeout = timeout

    def check_health(self) -> bool:
        """Check if local endpoint is reachable."""
        try:
            with httpx.Client(timeout=3.0) as client:
                res = client.get(f"{self.base_url}/models")
                return res.status_code == 200
        except Exception:
            return False

    def list_local_models(self) -> List[str]:
        """Fetch list of loaded models from local server."""
        try:
            with httpx.Client(timeout=4.0) as client:
                res = client.get(f"{self.base_url}/models")
                if res.status_code == 200:
                    data = res.json()
                    return [m.get("id") for m in data.get("data", [])]
        except Exception:
            pass
        return []

    def stream_chat(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        temperature: float = 0.2,
    ) -> Generator[str, None, LLMResponse]:
        """Stream response tokens and yield chunks, then return the full LLMResponse."""
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }

        payload: Dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "stream": True,
        }

        if tools:
            payload["tools"] = tools
            payload["tool_choice"] = "auto"

        full_content = []
        raw_tool_calls = []

        try:
            with httpx.Client(timeout=self.timeout) as client:
                with client.stream(
                    "POST",
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json=payload,
                ) as response:
                    if response.status_code != 200:
                        err_text = response.read().decode("utf-8", errors="replace")
                        if response.status_code == 404 and "model" in err_text:
                            avail = self.list_local_models()
                            avail_str = ", ".join(f"'{m}'" for m in avail) if avail else "none"
                            raise RuntimeError(
                                f"Model '{self.model}' is not found in your local server.\n"
                                f"Available local models: [{avail_str}].\n"
                                f"Solution: Run with '--model {avail[0] if avail else 'your-model'}' or download via 'ollama pull {self.model}'"
                            )
                        raise RuntimeError(f"HTTP {response.status_code}: {err_text}")

                    for line in response.iter_lines():
                        if not line or not line.startswith("data: "):
                            continue
                        data_str = line[6:].strip()
                        if data_str == "[DONE]":
                            break

                        try:
                            chunk = json.loads(data_str)
                            choice = chunk.get("choices", [{}])[0]
                            delta = choice.get("delta", {})

                            # Capture content tokens
                            token = delta.get("content")
                            if token:
                                full_content.append(token)
                                yield token

                            # Capture function/tool call chunks
                            if "tool_calls" in delta:
                                for tc in delta["tool_calls"]:
                                    idx = tc.get("index", 0)
                                    while len(raw_tool_calls) <= idx:
                                        raw_tool_calls.append({"id": "", "function": {"name": "", "arguments": ""}})
                                    if "id" in tc and tc["id"]:
                                        raw_tool_calls[idx]["id"] = tc["id"]
                                    fn = tc.get("function", {})
                                    if "name" in fn and fn["name"]:
                                        raw_tool_calls[idx]["function"]["name"] += fn["name"]
                                    if "arguments" in fn and fn["arguments"]:
                                        raw_tool_calls[idx]["function"]["arguments"] += fn["arguments"]

                        except json.JSONDecodeError:
                            continue

        except httpx.ConnectError:
            err_msg = (
                f"\n[bold red]Connection Error:[/bold red] Could not connect to local LLM server at '{self.base_url}'.\n"
                f"Please ensure your local LLM engine (Ollama, llama-server, LM Studio) is running."
            )
            yield err_msg
            return LLMResponse(content=err_msg, tool_calls=[])

        total_text = "".join(full_content)
        parsed_tools = self._parse_tool_calls(raw_tool_calls, total_text)
        return LLMResponse(content=total_text, tool_calls=parsed_tools)

    def _parse_tool_calls(self, raw_calls: List[Dict[str, Any]], total_text: str) -> List[Dict[str, Any]]:
        """Parses tool calls from API tool_calls or extracts fallback JSON blocks from text."""
        parsed = []

        # 1. First check if native tool calls arrived
        for call in raw_calls:
            fn = call.get("function", {})
            name = fn.get("name")
            args_str = fn.get("arguments", "{}")
            if name:
                try:
                    args = json.loads(args_str) if args_str else {}
                except json.JSONDecodeError:
                    args = {"raw_arguments": args_str}
                parsed.append({"name": name, "arguments": args})

        if parsed:
            return parsed

        # 2. Fallback: Parse markdown JSON codeblocks like ```tool_call {"name": "...", "arguments": {...}} ```
        pattern = r"```(?:tool_call|json)?\s*(\{\s*\"tool\"|\{\s*\"name\".*?\})\s*```"
        matches = re.findall(pattern, total_text, re.DOTALL)
        for match in matches:
            try:
                data = json.loads(match)
                name = data.get("tool") or data.get("name")
                args = data.get("args") or data.get("arguments") or data.get("parameters") or {}
                if name:
                    parsed.append({"name": name, "arguments": args})
            except Exception:
                continue

        return parsed
