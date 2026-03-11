# AgentScope 三国狼人杀案例 (DeepSeek 重构版)

本目录包含 AgentScope 框架的实战案例，展示了如何使用 AgentScope 构建一个融合中国古典文化元素的多智能体在线游戏。
本项目已经过重构，将所有功能合并为单个文件，并适配 SiliconFlow (DeepSeek) 模型。

## 📁 文件说明

- `main.py` - 完整的游戏逻辑、角色定义、提示词和控制器（合并后的单文件）
- `README.md` - 本说明文档

## 🎮 案例特点

- **消息驱动架构**：展示 AgentScope 的核心消息传递机制
- **并发协作**：演示多智能体同时在线的实时交互
- **角色扮演**：每个智能体具备双重身份（游戏角色+三国人物）
- **结构化输出**：通过 Prompt Engineering 和手动解析实现稳定的 JSON 输出
- **单文件结构**：便于阅读和部署
- **DeepSeek 模型**：使用 DeepSeek-V3/V3.2 进行推理

## 🛠️ 环境准备

### 1. 安装依赖

```bash
pip install agentscope pydantic
```

### 2. 配置环境变量

需要设置 `OPENAI_API_KEY` 和 `OPENAI_API_BASE_URL`：

```bash
# Linux/Mac
export OPENAI_API_KEY="your-siliconflow-api-key"
export OPENAI_API_BASE_URL="https://api.siliconflow.cn/v1"

# Windows PowerShell
$env:OPENAI_API_KEY="your-siliconflow-api-key"
$env:OPENAI_API_BASE_URL="https://api.siliconflow.cn/v1"
```

### 3. 运行游戏

```bash
python main.py
```

## 🎭 游戏角色说明

### 游戏角色
- **狼人**：夜晚击杀好人，白天隐藏身份
- **预言家**：每晚查验一名玩家身份
- **女巫**：拥有解药和毒药各一瓶
- **猎人**：被投票出局时可开枪带走一名玩家
- **村民**：通过推理和投票找出狼人

### 三国人物
- **刘备**：仁德宽厚，善于团结众人
- **关羽**：忠义刚烈，言辞直接
- **张飞**：性格豪爽，容易冲动
- **诸葛亮**：智慧超群，分析透彻
- **曹操**：雄才大略，善于权谋
- **司马懿**：深谋远虑，城府极深
- **周瑜**、**孙权** 等

## 🎯 游戏流程

### 夜晚阶段
1. **狼人讨论**：狼人通过 MsgHub 协商击杀目标
2. **预言家查验**：预言家选择查验对象
3. **女巫行动**：女巫决定是否使用解药/毒药

### 白天阶段
1. **死亡公布**：公布夜晚死亡玩家
2. **自由讨论**：所有存活玩家参与讨论
3. **投票淘汰**：投票选择淘汰对象
4. **猎人技能**：被淘汰的猎人可开枪

## 🐛 常见问题

### Q: 游戏运行报错 `Value error, prefix is not allowed`?
A: 本项目已针对 SiliconFlow/DeepSeek 的 API 特性进行了适配，移除了原生 Structured Output 调用，改为手动解析 JSON，避免了此错误。如果遇到类似问题，请确保使用最新的 `main.py`。

### Q: 智能体输出格式错误？
A: 代码中内置了 `extract_json_from_text` 函数，能够从 Markdown 代码块或文本中提取 JSON，提高了鲁棒性。

---

*本案例展示了 AgentScope 框架在构建复杂多智能体应用方面的强大能力。*
