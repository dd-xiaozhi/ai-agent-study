import os
import sys
from typing import Annotated, Literal, TypedDict, Union

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, BaseMessage, AIMessage, ToolMessage
from langchain_core.tools import tool
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition

# 尝试加载环境变量
# 优先加载当前目录的 .env，如果没有，尝试加载 AutoGen 目录下的 .env (假设那里配置好了)
current_dir = os.path.dirname(os.path.abspath(__file__))
autogen_env = os.path.join(current_dir, "..", "AutoGen", ".env")

if os.path.exists("(.env"):
    load_dotenv()
elif os.path.exists(autogen_env):
    load_dotenv(autogen_env)
else:
    # 默认加载，可能在系统环境变量中
    load_dotenv()

# 配置模型
# 使用与 AutoGen 示例相同的 DeepSeek 或 OpenAI 配置
API_KEY = os.getenv("OPENAI_API_KEY")
BASE_URL = os.getenv("OPENAI_API_BASE_URL", "https://api.openai.com/v1")
MODEL_NAME = os.getenv("MODEL_NAME", "deepseek-ai/DeepSeek-V3.2") 

if not API_KEY:
    print("Warning: OPENAI_API_KEY not found in environment variables.")

# 定义工具
@tool
def get_weather(city: str):
    """查询指定城市的天气信息。"""
    print(f"\n[Tool] 查询天气: {city}")
    # 模拟数据
    if "北京" in city or "Beijing" in city:
        return "北京今天晴朗，气温 25°C，微风。"
    elif "上海" in city or "Shanghai" in city:
        return "上海今天多云，气温 22°C，有小雨。"
    elif "深圳" in city or "Shenzhen" in city:
        return "深圳今天炎热，气温 30°C。"
    else:
        return f"{city} 的天气未知，建议带伞。"

@tool
def search_web(query: str):
    """模拟网络搜索功能。"""
    print(f"\n[Tool] 搜索网络: {query}")
    return f"关于 '{query}' 的搜索结果：LangGraph 是一个用于构建有状态、多智能体应用的库，基于 LangChain 构建。"

tools = [get_weather, search_web]

# 定义状态
class AgentState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]

# 初始化模型
llm = ChatOpenAI(
    model=MODEL_NAME,
    openai_api_base=BASE_URL,
    openai_api_key=API_KEY,
    temperature=0,
    streaming=True
)

# 绑定工具
llm_with_tools = llm.bind_tools(tools)

# 定义节点函数
def agent_node(state: AgentState):
    """智能体节点：调用模型生成回复或工具调用"""
    messages = state["messages"]
    response = llm_with_tools.invoke(messages)
    return {"messages": [response]}

# 构建图
workflow = StateGraph(AgentState)

# 添加节点
workflow.add_node("agent", agent_node)
workflow.add_node("tools", ToolNode(tools))

# 添加边
workflow.add_edge(START, "agent")

# 条件边：如果模型决定调用工具，则通过 tools_condition 路由到 tools 节点
# 否则路由到 END
workflow.add_conditional_edges(
    "agent",
    tools_condition,
)

# 工具执行完后返回 agent 节点（ReAct 循环）
workflow.add_edge("tools", "agent")

# 编译图
app = workflow.compile()

def main():
    print("=" * 50)
    print("LangGraph Agent Demo (ReAct Pattern)")
    print("=" * 50)
    
    # 示例 1: 查询天气
    query1 = "北京的天气怎么样？"
    print(f"\nUser: {query1}")
    inputs = {"messages": [HumanMessage(content=query1)]}
    
    for event in app.stream(inputs, stream_mode="values"):
        message = event["messages"][-1]
        if isinstance(message, AIMessage) and message.content:
            print(f"Assistant: {message.content}")
    
    print("-" * 50)
    
    # 示例 2: 复杂查询（需要工具）
    query2 = "LangGraph 是什么？顺便帮我查一下上海的天气。"
    print(f"\nUser: {query2}")
    # 清空之前的状态（如果需要延续对话，可以保留 messages）
    inputs = {"messages": [HumanMessage(content=query2)]}
    
    # 使用 stream 获取逐步执行结果
    for chunk in app.stream(inputs, stream_mode="updates"):
        for node, values in chunk.items():
            print(f"--- Node: {node} ---")
            # print(values) # Debug info

    # 获取最终结果
    final_state = app.invoke(inputs)
    print(f"\nFinal Answer: {final_state['messages'][-1].content}")

if __name__ == "__main__":
    main()
