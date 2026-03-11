import os
from typing import Dict, List
from openai import OpenAI


class LLMClient:
    """
    LLM客户端, 基于 OpenAI API 封装
    """
    def __init__(self, model: str, apiKey: str = None, baseUrl: str = None, timeout: int = None):
        if not model:
            raise ValueError("model is required")
        self.model = model
        self.apiKey = apiKey or os.getenv("OPENAI_API_KEY")
        self.baseUrl = baseUrl or os.getenv("OPENAI_API_BASE_URL")
        self.timeout = timeout or 30

        if not all([self.model, self.apiKey, self.baseUrl]):
            raise ValueError("模型、API密钥和服务地址必须被提供或在环境变量中定义。")

        self.client = OpenAI(
            api_key=self.apiKey,
            base_url=self.baseUrl,
            timeout=self.timeout
        )

    def generate(self,
                 message: List[Dict[str, str]],
                 temperature: float = 0,
                 stream: bool = True
                 ) -> str:
        """
        调用大模型，生成回答
        """
        print(f"================ 🧠 正在调用 {self.model} 模型 ================")
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=message,
                temperature=temperature,
                stream=stream
            )

            print("✅ 大语言模型响应成功:")
            collected_content = []
            for chunk in response:
                content = chunk.choices[0].delta.content or ""
                print(content, end="", flush=True)
                collected_content.append(content)
            # 输出结束后换行
            print()
            return "".join(collected_content)
        except Exception as e:
            print(f"❌ 调用大模型失败: {e}")
            return None


if __name__ == "__main__":
    try:
        llmClient = LLMClient(model="deepseek-chat")

        exampleMessages = [
            {"role": "system", "content": "你是一个 python 代码生成助手，请根据用户的需求生成 python 代码。"},
            {"role": "user", "content": "写一个快速排序算法"}
        ]

        print("--- 调用LLM ---")
        responseText = llmClient.generate(exampleMessages, stream=True)
        if responseText:
            print("\n\n--- 完整模型响应 ---")
            print(responseText)

    except ValueError as e:
        print(e)
