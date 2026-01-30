import ast

from LLMClient import LLMClient

PLANNER_PROMPT_TEMPLATE = """
    你是一个顶级的 AI 规划专家。你的任务是将用户提出的复杂问题分解成一个由多个简单步骤组成的行动计划。
    请确保计划中的每个步骤都是一个独立的、可执行的子任务，并且严格按照逻辑顺序排列。
    你的输出必须是一个Python列表，其中每个元素都是一个描述子任务的字符串。

    问题: {question}

    请严格按照以下格式输出你的计划,```python与```作为前后缀是必要的:
    ```python
    ["步骤1", "步骤2", "步骤3", ...]
    ```
    """

EXECUTOR_PROMPT_TEMPLATE = """
    你是一位顶级的AI执行专家。你的任务是严格按照给定的计划，一步一步解决问题。
    你将收到原始问题、完整计划、以及到目前为止已经完成的步骤和结果。
    请专注于解决“当前步骤”，并仅输出该步骤的最终答案，不要输出任何额外的解释和对话。记住只需要输出结果！！！
    
    # 原始问题
    {question}
    
    # 完整计划
    {plan}
    
    # 历史执行步骤和结果
    {history}
    
    # 当前步骤
    {current_step}
    
    请输出针对 “当前步骤” 的回答。
    """


class Planner:
    def __init__(self, llm_client: LLMClient):
        self.llmClient = llm_client

    def plan(self, question):
        """
        根据用户的问题生成执行计划
        :param question: 问题
        :return: 执行计划
        """
        prompt = PLANNER_PROMPT_TEMPLATE.format(question=question)

        messages = [{"role": "user", "content": prompt}]

        print("====================== LLM正在生成执行计划... ======================")

        response_txt = self.llmClient.generate(message=messages, stream=True) or ""
        print(f"✅ 计划已生成: \n{response_txt}")

        # 解析模型输出
        try:
            plan_str = response_txt.split("```python")[1].split("```")[0].strip()
            # 使用 ast.literal_eval 解析字符串为 Python List 对象
            plan_list = ast.literal_eval(plan_str)
            return plan_list if isinstance(plan_list, list) else []
        except Exception as e:
            print(f"❌ 解析计划时发生未知错误: {e}")
            return []


class Executor:

    def __init__(self, llm_client: LLMClient):
        self.llm_client = llm_client

    def execute(self, question: str, plan: list[str]) -> str:
        # 用于存储历史执行结果
        history = ""
        response_text = ""
        for i, step in enumerate(plan):
            print(f"------- 正在执行计划 {i} ------")

            prompt = EXECUTOR_PROMPT_TEMPLATE.format(
                question=question,
                plan=plan,
                history=history if history else "无",
                current_step=step
            )

            messages = [{"role": "user", "content": prompt}]

            response_text = self.llm_client.generate(message=messages, stream=True) or ""

            # 更新历史执行，为下一步做准备
            history += f"步骤 {i + 1}: {step}\n结果：{response_text}\n\n"

            print(f"步骤 {i + 1} [ {step} ]  已完成，结果：{response_text}\n")

        print("------- 计划执行完毕 --------\n")
        # 最后一步就是最终答案
        return response_text


class PlanAndSolveAgent:

    def __init__(self, llm_client: LLMClient):
        self.llm_client = llm_client
        self.planner = Planner(llm_client)
        self.executor = Executor(llm_client)

    def run(self, question: str):
        print(f'\n--------- 开始处理问题 --------- \n {question}')

        # 1.调用规划器生成执行计划
        ex_plan = self.planner.plan(question)

        if not ex_plan:
            print("❌ 无法生成执行计划，请检查问题或联系管理员")
            return

        # 2.调用执行器执行计划
        response_text = self.executor.execute(question, ex_plan)

        print(f"最终结果：\n{response_text}")


if __name__ == '__main__':
    llm_client = LLMClient(model="deepseek-chat")
    psa = PlanAndSolveAgent(llm_client)
    psa.run("爷爷的奶奶的奶奶的爸爸的姐姐的儿子是谁？")
