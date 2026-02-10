from colorama import Fore
from camel.societies import RolePlaying
from camel.utils import print_text_animated
from camel.types import ModelType, TaskType

def main():
    # 1. 定义协作任务
    # Define the collaborative task
    task_prompt = """
创作一本关于"拖延症心理学"的短篇电子书，目标读者是对心理学感兴趣的普通大众。
要求：
1. 内容科学严谨，基于实证研究
2. 语言通俗易懂，避免过多专业术语
3. 包含实用的改善建议和案例分析
4. 字数控制在2000字以内
"""

    print(Fore.CYAN + f"Task Prompt:\n{task_prompt}\n")

    # 2. 定义角色
    # Define the roles involved in the task
    # 根据任务，设定"心理学家"（提供专业知识/指导）和"作家"（负责撰写）的角色
    user_role_name = "Psychologist" # User role: gives instructions and professional guidance
    assistant_role_name = "Writer"  # Assistant role: executes the writing task

    # 3. 初始化 RolePlaying
    # Initialize the RolePlaying session
    role_playing = RolePlaying(
        assistant_role_name=assistant_role_name,
        user_role_name=user_role_name,
        task_prompt=task_prompt,
        with_task_specify=True, # Allow task specification to refine the task
        task_specify_agent_kwargs=dict(model=ModelType.GPT_3_5_TURBO), # Use GPT-3.5 for task specification
    )

    # 4. 开始对话
    # Start the chat session
    # init_chat() generates the first message from the assistant to the user
    input_msg = role_playing.init_chat()
    
    # 5. 对话循环
    # Chat loop
    chat_turn_limit, n = 10, 0
    while n < chat_turn_limit:
        n += 1
        
        # Step the role playing session
        # input_msg is the message from the previous turn (or init)
        assistant_response, user_response = role_playing.step(input_msg)
        
        # Check for termination signals
        if assistant_response.terminated:
            print(Fore.GREEN + (f"{assistant_role_name} terminated. Reason: {assistant_response.info['termination_reasons']}"))
            break
        if user_response.terminated:
            print(Fore.GREEN + (f"{user_role_name} terminated. Reason: {user_response.info['termination_reasons']}"))
            break

        # Print the conversation
        print_text_animated(Fore.BLUE + f"AI User ({user_role_name}):\n{user_response.msg.content}\n")
        print_text_animated(Fore.GREEN + f"AI Assistant ({assistant_role_name}):\n{assistant_response.msg.content}\n")

        # Check if the task is done (basic check)
        if "CAMEL_TASK_DONE" in user_response.msg.content:
            break
            
        # Update input message for the next iteration (User's response becomes Assistant's input)
        input_msg = assistant_response.msg

if __name__ == "__main__":
    main()
