import sys
import os

# 添加父目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from llm_client import LLMClient
from memory import Memory

INITIAL_PROMPT_TEMPLATE = """
    你是一位资深的 Python 专家。请根据以下要求，编写一个 Python 函数。
    你的代码必须要包含完整的函数名、文档字符串、并遵循 PEP 8 规范。

    要求：{task}

    请直接输出代码，不要包含任何额外的解释
    """

REFLECTION_PROMPT_TEMPLATE = """
    你是一位极其严格的代码评审专家和资深算法工程师，对代码的性能有极致的要求。
    你的任务是审查以下 Python 代码，并专注于找出其在 <strong>算法效率</strong> 上的主要瓶颈。

    # 原始任务：
    {task}

    # 代审查的代码：
    ```python
    {code}
    ```

    请分析该代码的时间复杂度，并思考是否存在一种<strong>算法上更优</strong>的解决方案来显著提升性能。
    如果存在，请清洗地指出当前算法的不足，并提出具体的、可行的改进算法建议（列入，使用筛法替代试除法）。
    如果代码在算法层面已经达最优，才能回答"无需改进"。

    请直接输出你的反馈，不要包含任何额外的解释。
    """

REFINE_PROMPT_TEMPLATE = """
    你是一位资深的 Python 专家。你正在根据一位代码审查专家的反馈来优化你的代码。

    # 原始任务：
    {task}

    # 你上一轮尝试的代码：
    ```python
    {last_code_attempt}
    ```
    评审员的反馈：
    {reviewer_feedback}

    请根据评审员的反馈，生成一个优化后的新版本代码。
    你的代码必须要包含完整的函数名、文档字符串、并遵循 PEP 8 规范。
    请直接输出优化后的代码，不需要包含任何额外的解释。
    """


class ReflectionAgent:

    def __init__(self, llm_client: LLMClient, max_iterations: int = 3):
        self.llm_client = llm_client
        self.max_iterations = max_iterations
        self.memory = Memory()

    def run(self, task: str):
        print(f"🔍 开始执行任务: {task}")

        # -------------------- 初始执行 --------------------
        print("\n--- 正在进行初始尝试 ---")
        initial_prompt = INITIAL_PROMPT_TEMPLATE.format(task=task)
        initial_code = self._get_llm_response(initial_prompt)
        self.memory.add_record(record_type="execution", record_content=initial_code)

        # -------------------- 迭代执行：反思优化 --------------------
        for i in range(self.max_iterations):
            print(f"\n--- 正在进行第 {i + 1}/{self.max_iterations} 轮反思优化 ---")

            # a.反思
            print("\n-> 正在进行反思...")
            last_code_attempt = self.memory.get_last_execution()
            reflection_prompt = REFLECTION_PROMPT_TEMPLATE.format(
                task=task, code=initial_code
            )
            reflection_feedback = self._get_llm_response(reflection_prompt)
            self.memory.add_record(
                record_type="reflection", record_content=reflection_feedback
            )

            # b.检查是否需要停止
            if "无需改进" in reflection_feedback:
                print("✅ 代码在算法层面已经达最优，无需继续优化，任务完成。")
                break

            # c.优化
            print("\n-> 正在进行优化...")
            refine_prompt = REFINE_PROMPT_TEMPLATE.format(
                task=task,
                last_code_attempt=last_code_attempt,
                reviewer_feedback=reflection_feedback,
            )
            refined_code = self._get_llm_response(refine_prompt)
            self.memory.add_record(record_type="execution", record_content=refined_code)

        final_code = self.memory.get_last_execution()
        print(f"\n🎉 最终执行结果: {final_code}")

    def _get_llm_response(self, prompt: str) -> str:
        """
        调用大模型，生成回答
        """
        messages = [{"role": "user", "content": prompt}]

        return self.llm_client.generate(messages, stream=True) or ""


if __name__ == "__main__":
    llm_client = LLMClient(model="deepseek-chat")
    reflection_agent = ReflectionAgent(llm_client=llm_client)
    reflection_agent.run(task="编写一个排序算法")
