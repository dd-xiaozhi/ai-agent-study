# AgentScope 三国狼人杀：零基础实战教程

欢迎来到 AgentScope 的世界！本教程将带你从零开始，看懂并运行一个基于 **AgentScope** 框架的“三国狼人杀”游戏。

我们将把你当成一位刚入职的“AI 导演”，教你如何用 AgentScope 组织一帮 AI 演员（Agent）来演一出好戏。

---

## 1. 什么是 AgentScope？

想象你要拍一部电影，你需要管理很多演员，还要规定谁在什么时候说话，谁能听到谁说话。

**AgentScope** 就是你的**剧组管理系统**。它帮你解决了以下问题：
*   **Agent (演员)**：帮你创建各种性格的 AI 角色。
*   **Message (台词)**：标准化演员说的话，让它们能互相听懂。
*   **Pipeline (调度)**：安排演员的出场顺序（是轮流说话，还是大家一起喊）。
*   **MsgHub (聊天室)**：管理谁能听到谁说话（比如狼人说悄悄话，村民听不见）。

---

## 2. 我们的“剧本”：三国狼人杀

在这个游戏中，我们将创建 6-9 个 AI 演员。他们既是**三国人物**（刘备、曹操等，决定性格），又是**狼人杀角色**（狼人、预言家等，决定功能）。

**文件结构：**
*   `refactored_game.py`: 我们的主程序，包含了所有的逻辑。

---

## 3. 核心概念与代码拆解

我们将通过代码片段，一一讲解 AgentScope 的核心原理。

### 3.1 Agent：创建你的 AI 演员

在 AgentScope 中，最基础的演员叫 `ReActAgent`（反应式智能体）。它不仅能说话，还能根据观察做出反应。

**代码位置**：`ThreeKingdomsWerewolfGame.create_player` 方法

```python
agent = ReActAgent(
    name="刘备",  # 演员的名字
    sys_prompt="你是刘备，扮演狼人...",  # 剧本：告诉他的人设和任务
    model=...,    # 大脑：使用哪个 LLM (如 DeepSeek)
)
```

**原理讲解：**
*   **sys_prompt (系统提示词)**：这是 Agent 的灵魂。我们在 `ChinesePrompts` 类里写好了，告诉 Agent：“你不仅要杀人，还要用刘备的语气说话，还要按 JSON 格式回复”。

### 3.2 Message：演员之间的“台词”

AgentScope 中的所有交流都通过 `Msg` 对象进行。

```python
msg = Msg(
    name="曹操",
    content="我看刘备鬼鬼祟祟的，像个狼人！",
    role="assistant"
)
```

**原理讲解：**
*   AgentScope 会自动把这些 `Msg` 存进 Agent 的**记忆**里。
*   当你调用 `agent()` 让它发言时，它会回顾之前的记忆（历史消息），然后决定下一句说什么。

### 3.3 MsgHub：神奇的“广播室”

这是 AgentScope 最强大的功能之一。在狼人杀里，我们需要区分“狼人频道”和“公开频道”。

**场景 1：狼人夜间悄悄话**

```python
# 创建一个狼人专属的聊天室
async with MsgHub(
    self.werewolves,  # 参与者：只有狼人
    enable_auto_broadcast=True  # 开启自动广播：一人说话，全员（狼）听见
) as werewolves_hub:
    
    # 在这个缩进块里的所有发言，只有狼人能听到！
    for wolf in self.werewolves:
        await wolf()  # 狼人发言
```

**原理讲解：**
*   `MsgHub` 就像一个临时的会议室。
*   `enter` (进入 with 块): 每个人带上耳机，进入加密频道。
*   `exit` (离开 with 块): 摘下耳机，回到公共频道。
*   **小白视角**：这解决了“怎么让狼人互相商量，却不让村民听见”这个大难题，而你只需要写一行 `with MsgHub...`。

### 3.4 Pipeline：导演的“调度令”

有了演员，怎么安排他们行动？AgentScope 提供了 `Pipeline`（流水线）。

**场景 2：白天轮流发言 (Sequential Pipeline)**

```python
from agentscope.pipeline import sequential_pipeline

# 让所有活着的玩家，按顺序每人说一句话
await sequential_pipeline(self.alive_players)
```

**场景 3：大家同时投票 (Fanout Pipeline)**

```python
from agentscope.pipeline import fanout_pipeline

# 就像大家同时举牌一样，并发执行
vote_msgs = await fanout_pipeline(
    self.alive_players,
    msg=..., # 主持人问：“请投票”
)
```

**原理讲解：**
*   `sequential_pipeline`: **串行**。A 说完 B 说，B 说完 C 说。适合讨论环节。
*   `fanout_pipeline`: **并发**。A, B, C 同时思考并给出结果。适合投票、闭眼杀人环节（为了效率）。

---

## 4. 游戏流程图解（Mermaid）

让我们看看这些组件是怎么串联起来的：

```mermaid
graph TD
    subgraph Init [剧组筹备]
        A[创建 Agent: 刘备/曹操...] --> B[分配身份: 狼人/预言家...]
    end

    subgraph Night [夜晚: MsgHub 的妙用]
        C[主持人宣布入夜] 
        --> D{是狼人吗?}
        D -- Yes --> E[进入狼人 MsgHub]
        E --> F[狼人A发言] --> G[狼人B发言] --> H[达成一致]
        H --> I[退出 MsgHub]
        D -- No --> J[村民闭眼 （跳过)]
    end

    subgraph Day [白天: Pipeline 的调度]
        K[主持人宣布天亮]
        --> L[进入全员 MsgHub]
        --> M[sequential_pipeline: 轮流发言]
        --> N[fanout_pipeline: 同时投票]
        --> O[退出 MsgHub]
    end

    B --> C
    I --> K
    J --> K
    O --> C
```

---

## 5. 关键代码实战分析

让我们深入到 `refactored_game.py` 的第 594 行 `werewolf_phase`（狼人阶段），看看它是如何运作的：

```python
async def werewolf_phase(self, round_num: int):
    # 1. 主持人宣布（这条消息所有人都收到了，但只有狼人会醒来）
    await self.moderator.announce(f"🐺 狼人请睁眼...")
    
    # 2. 开启狼人聊天室
    async with MsgHub(
        self.werewolves,  # 只传入狼人列表
        enable_auto_broadcast=True
    ) as werewolves_hub:
        
        # 3. 主持人在聊天室里发话（只有狼人听见）
        await self.moderator.announce("狼人们，请讨论击杀目标...")
        
        # 4. 狼人轮流发言讨论 (模拟多轮对话)
        for _ in range(MAX_DISCUSSION_ROUND):
            for wolf in self.werewolves:
                await wolf() # Agent 思考并生成回复
        
        # 5. 关闭自动广播，准备投票（避免投票结果互相干扰）
        werewolves_hub.set_auto_broadcast(False)
        
        # 6. 并发投票
        kill_votes = await fanout_pipeline(self.werewolves, ...)
```

**小白注意点：**
*   **结构化输出**：AI 说话很啰嗦，怎么知道它想杀谁？
    *   我们在 Prompt 里规定：“请返回 JSON 格式，包含 `target` 字段”。
    *   代码里用了 `extract_json_from_text` 工具函数，把 AI 的长篇大论变成程序能懂的 `{ "target": "张飞" }`。

---

## 6. 总结

通过这个项目，你学到了 AgentScope 的三大法宝：

1.  **Agent**: 你的智能演员，有设定、有模型。
2.  **MsgHub**: 控制谁能听到谁，实现“私聊”和“公聊”。
3.  **Pipeline**: 控制流程，是轮流来（讨论）还是大家一起来（投票）。

现在，你已经准备好运行这个游戏了！设置好你的 API Key，运行 `python refactored_game.py`，看着刘备和曹操互相飙戏吧！
