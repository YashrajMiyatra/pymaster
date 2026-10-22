"""
Base tool interface and registry for PyMaster.
"""

from typing import Callable, Any, Dict, List
import inspect
import json


class Tool:
    """Represents an executable tool callable by the autonomous agent."""

    def __init__(self, name: str, description: str, func: Callable, parameters: Dict[str, Any]):
        self.name = name
        self.description = description
        self.func = func
        self.parameters = parameters

    def execute(self, **kwargs) -> Any:
        try:
            return self.func(**kwargs)
        except Exception as e:
            return f"Error executing tool '{self.name}': {type(e).__name__}: {str(e)}"

    def to_schema(self) -> Dict[str, Any]:
        """Returns standard function calling schema."""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            },
        }


class ToolRegistry:
    """Registry holding all tools accessible to PyMaster."""

    def __init__(self):
        self._tools: Dict[str, Tool] = {}

    def register(self, name: str, description: str, parameters: Dict[str, Any]):
        def decorator(func: Callable):
            tool = Tool(name=name, description=description, func=func, parameters=parameters)
            self._tools[name] = tool
            return func
        return decorator

    def get(self, name: str) -> Tool | None:
        return self._tools.get(name)

    def list_tools(self) -> List[Tool]:
        return list(self._tools.values())

    def get_schemas(self) -> List[Dict[str, Any]]:
        return [tool.to_schema() for tool in self._tools.values()]

    def execute(self, name: str, **kwargs) -> Any:
        tool = self.get(name)
        if not tool:
            available = ", ".join(self._tools.keys())
            return (
                f"Error: Tool '{name}' does not exist! You can ONLY use one of: [{available}].\n"
                f"To implement features, create scripts, or organize folders, write the code into a file using 'write_file'."
            )
        return tool.execute(**kwargs)


# Global registry instance
registry = ToolRegistry()
