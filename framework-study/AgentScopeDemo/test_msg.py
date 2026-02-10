from agentscope.message import Msg
from agentscope.formatter import OpenAIChatFormatter
import asyncio

async def test():
    msg = Msg(name="Test", content=None, role="user")
    print(f"Msg: {msg}")
    print(f"Content: {msg.content}")
    
    if hasattr(msg, 'get_content_blocks'):
        blocks = msg.get_content_blocks()
        print(f"Blocks: {blocks}")
    else:
        print("No get_content_blocks method")

    formatter = OpenAIChatFormatter()
    try:
        formatted = await formatter.format([msg])
        print(f"Formatted: {formatted}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test())
