#!/usr/bin/env python3
"""
Reflection Agent 启动脚本
"""
import sys
import os

# 将包根目录添加到 Python 路径
project_root = os.path.dirname(os.path.abspath(__file__))
package_root = os.path.abspath(os.path.join(project_root, ".."))
sys.path.insert(0, package_root)

# 使用 importlib 动态导入
import importlib.util

# 导入 LLMClient
llm_module_path = os.path.join(package_root, "llm_client.py")
spec = importlib.util.spec_from_file_location("llm_client", llm_module_path)
llm_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(llm_module)
LLMClient = llm_module.LLMClient

# 导入 Memory
memory_module_path = os.path.join(project_root, "memory.py")
memory_spec = importlib.util.spec_from_file_location("memory", memory_module_path)
memory_module = importlib.util.module_from_spec(memory_spec)
sys.modules['memory'] = memory_module
memory_spec.loader.exec_module(memory_module)

# 设置 LLMClient 到 sys.modules
sys.modules['llm_client'] = llm_module

# 导入 ReflectionAgent
reflection_module_path = os.path.join(project_root, "reflection.py")
spec = importlib.util.spec_from_file_location("reflection", reflection_module_path)
reflection_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(reflection_module)
ReflectionAgent = reflection_module.ReflectionAgent

if __name__ == "__main__":
    llm_client = LLMClient(model="deepseek-chat")
    reflection_agent = ReflectionAgent(llm_client=llm_client)
    reflection_agent.run(task="编写一个函数，计算斐波那契数列的第 n 项")
