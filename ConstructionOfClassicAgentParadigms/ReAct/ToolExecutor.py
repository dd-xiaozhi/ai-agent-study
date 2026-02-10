from typing import Any, Dict
from SearchTool import search


class ToolExecutor:
    """
    工具执行器, 用于执行工具函数
    """
    def __init__(self):
        self.tools: Dict[str, Dict[str, Any]] = {}

    def register_tool(self, tool_name: str, tool_desc: str, tool_func: callable) -> None:
        """
        向工具箱中注册一个新工具。
        """
        if tool_name in self.tools:
            print(f"⚠️ 工具 {tool_name} 已存在，直接替换。")
        self.tools[tool_name] = {
            "desc": tool_desc,
            "func": tool_func
        }
        print(f"工具 '{tool_name}' 已注册。")
    

        """
        获取工具列表
        """
        return list(self.tools.keys())
    
    def getTool(self, tool_name: str) -> callable:
        """
        获取工具
        """
        return self.tools.get(tool_name, {}).get("func", None)
    
    def getAvailableTools(self) -> str:
        """
        获取所有可用工具的格式化描述字符串。
        """
        return "\n".join([
            f"- {name}: {info['desc']}" 
            for name, info in self.tools.items()
        ])


if __name__ == "__main__":
    tool_executor = ToolExecutor()
    tool_executor.register_tool("search", "搜索工具", search)
    search_tool = tool_executor.getTool("search")
    print(search_tool("今天广州的天气怎么样"))
    print(tool_executor.getAvailableTools())