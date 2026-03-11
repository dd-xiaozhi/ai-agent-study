# -*- coding: utf-8 -*-
"""
三国狼人杀 - 基于AgentScope的中文版狼人杀游戏 (Refactored)
融合三国演义角色和传统狼人杀玩法
使用 SiliconFlow DeepSeek 模型
"""
import asyncio
import os
import random
from typing import List, Dict, Optional, Any, Literal
from collections import Counter
from pydantic import BaseModel, Field

import agentscope
from agentscope.agent import ReActAgent, AgentBase
from agentscope.model import OpenAIChatModel
from agentscope.pipeline import MsgHub, sequential_pipeline, fanout_pipeline
from agentscope.message import Msg
from agentscope.formatter import OpenAIChatFormatter

# ==========================================
# 1. 游戏角色定义 (from game_roles.py)
# ==========================================

class GameRoles:
    """游戏角色管理类"""
    
    ROLES = {
        "狼人": {
            "description": "狼人",
            "ability": "夜晚可以击杀一名玩家",
            "win_condition": "消灭所有好人或与好人数量相等",
            "team": "狼人阵营"
        },
        "预言家": {
            "description": "预言家",
            "ability": "每晚可以查验一名玩家的身份",
            "win_condition": "消灭所有狼人",
            "team": "好人阵营"
        },
        "女巫": {
            "description": "女巫",
            "ability": "拥有解药和毒药各一瓶，可以救人或杀人",
            "win_condition": "消灭所有狼人",
            "team": "好人阵营"
        },
        "猎人": {
            "description": "猎人",
            "ability": "被投票出局时可以开枪带走一名玩家",
            "win_condition": "消灭所有狼人",
            "team": "好人阵营"
        },
        "村民": {
            "description": "村民",
            "ability": "无特殊技能，依靠推理和投票",
            "win_condition": "消灭所有狼人",
            "team": "好人阵营"
        },
        "守护者": {
            "description": "守护者",
            "ability": "每晚可以守护一名玩家免受狼人攻击",
            "win_condition": "消灭所有狼人",
            "team": "好人阵营"
        }
    }
    
    CHARACTER_TRAITS = {
        "刘备": "仁德宽厚，善于团结众人，说话温和有礼",
        "关羽": "忠义刚烈，言辞直接，重情重义",
        "张飞": "性格豪爽，说话大声直接，容易冲动",
        "诸葛亮": "智慧超群，分析透彻，言辞谨慎",
        "赵云": "忠勇双全，话语简洁有力",
        "曹操": "雄才大略，善于权谋，话语犀利",
        "司马懿": "深谋远虑，城府极深，言辞含蓄",
        "周瑜": "才华横溢，略显傲气，分析精准",
        "孙权": "年轻有为，善于决断，话语果决"
    }
    
    @classmethod
    def get_role_desc(cls, role: str) -> str:
        """获取角色描述"""
        return cls.ROLES.get(role, {}).get("description", "未知角色")
    
    @classmethod
    def get_role_ability(cls, role: str) -> str:
        """获取角色技能"""
        return cls.ROLES.get(role, {}).get("ability", "无特殊技能")
    
    @classmethod
    def get_character_trait(cls, character: str) -> str:
        """获取角色性格特点"""
        return cls.CHARACTER_TRAITS.get(character, "性格温和，说话得体")
    
    @classmethod
    def is_werewolf(cls, role: str) -> bool:
        """判断是否为狼人"""
        return role == "狼人"
    
    @classmethod
    def is_villager_team(cls, role: str) -> bool:
        """判断是否为好人阵营"""
        return cls.ROLES.get(role, {}).get("team") == "好人阵营"
    
    @classmethod
    def get_standard_setup(cls, player_count: int) -> List[str]:
        """获取标准角色配置"""
        if player_count == 6:
            return ["狼人", "狼人", "预言家", "女巫", "村民", "村民"]
        elif player_count == 8:
            return ["狼人", "狼人", "狼人", "预言家", "女巫", "猎人", "村民", "村民"]
        elif player_count == 9:
            return ["狼人", "狼人", "狼人", "预言家", "女巫", "猎人", "守护者", "村民", "村民"]
        else:
            # 默认配置：约1/3狼人
            werewolf_count = max(1, player_count // 3)
            roles = ["狼人"] * werewolf_count
            
            # 添加神职
            remaining = player_count - werewolf_count
            if remaining >= 1:
                roles.append("预言家")
                remaining -= 1
            if remaining >= 1:
                roles.append("女巫")
                remaining -= 1
            if remaining >= 1:
                roles.append("猎人")
                remaining -= 1
            
            # 剩余为村民
            roles.extend(["村民"] * remaining)
            
            return roles

# ==========================================
# 2. 中文提示词 (from prompt_cn.py)
# ==========================================

class ChinesePrompts:
    """中文提示词管理类"""
    
    @staticmethod
    def get_role_prompt(role: str, character: str) -> str:
        """获取角色提示词"""
        base_prompt = f"""【系统指令】
你正在参与一个名为“三国狼人杀”的角色扮演游戏。
当前你的身份是：{character} ({role})。

【绝对禁令】
1. 禁止输出任何与游戏无关的内容（如代码、教程、翻译、项目介绍等）。
2. 禁止跳出角色设定。
3. 禁止输出 Markdown 代码块标记（如 ```json）。

【输出要求】
必须且仅能输出一个标准的 JSON 字符串，格式如下：
{{
    "reach_agreement": true/false,
    "confidence_level": 1-10的数字,
    "key_evidence": "以{character}的口吻描述你的观点"
}}

【示例】
正确输出：
{{
    "reach_agreement": false,
    "confidence_level": 8,
    "key_evidence": "吾观那厮贼眉鼠眼，定非善类！"
}}

错误输出：
```json
{{
    ...
}}
```

角色特点：
"""

        
        if role == "狼人":
            return base_prompt + f"""
- 你是狼人阵营，目标是消灭所有好人
- 夜晚可以与其他狼人协商击杀目标
- 白天要隐藏身份，误导好人
- 以{character}的性格说话和行动
"""
        elif role == "预言家":
            return base_prompt + f"""
- 你是好人阵营的预言家，目标是找出所有狼人
- 每晚可以查验一名玩家的真实身份
- 要合理公布查验结果，引导好人投票
- 以{character}的智慧和洞察力分析局势
"""
        elif role == "女巫":
            return base_prompt + f"""
- 你是好人阵营的女巫，拥有解药和毒药各一瓶
- 解药可以救活被狼人击杀的玩家
- 毒药可以毒杀一名玩家
- 要谨慎使用道具，在关键时刻发挥作用
"""
        elif role == "猎人":
            return base_prompt + f"""
- 你是好人阵营的猎人
- 被投票出局时可以开枪带走一名玩家
- 要在关键时刻使用技能，带走狼人
- 以{character}的勇猛和决断力行动
"""
        else:  # 村民
            return base_prompt + f"""
- 你是好人阵营的村民
- 没有特殊技能，只能通过推理和投票
- 要仔细观察，找出狼人的破绽
- 以{character}的性格参与讨论
"""

# ==========================================
# 3. 结构化输出模型 (from structured_output_cn.py)
# ==========================================

class DiscussionModelCN(BaseModel):
    """中文版讨论输出格式"""
    
    reach_agreement: bool = Field(
        description="是否已达成一致意见",
    )
    confidence_level: int = Field(
        description="对当前推理的信心程度(1-10)",
        ge=1, le=10
    )
    key_evidence: Optional[str] = Field(
        description="支持你观点的关键证据",
        default=None
    )


def get_vote_model_cn(agents: list[AgentBase]) -> type[BaseModel]:
    """获取中文版投票模型"""
    
    class VoteModelCN(BaseModel):
        """中文版投票输出格式"""
        
        vote: Literal[tuple(_.name for _ in agents)] = Field(
            description="你要投票淘汰的玩家姓名",
        )
        reason: str = Field(
            description="投票理由，简要说明为什么选择此人",
        )
        suspicion_level: int = Field(
            description="对被投票者的怀疑程度(1-10)",
            ge=1, le=10
        )
    
    return VoteModelCN


class WitchActionModelCN(BaseModel):
    """中文版女巫行动模型"""
    
    use_antidote: bool = Field(
        description="是否使用解药救人",
        default=False
    )
    use_poison: bool = Field(
        description="是否使用毒药杀人", 
        default=False
    )
    target_name: Optional[str] = Field(
        description="目标玩家姓名（救人或毒杀的对象）",
        default=None
    )
    action_reason: Optional[str] = Field(
        description="行动理由",
        default=None
    )


def get_seer_model_cn(agents: list[AgentBase]) -> type[BaseModel]:
    """获取中文版预言家模型"""
    
    class SeerModelCN(BaseModel):
        """中文版预言家查验格式"""
        
        target: Literal[tuple(_.name for _ in agents)] = Field(
            description="要查验的玩家姓名",
        )
        check_reason: str = Field(
            description="查验此人的原因",
        )
        priority_level: int = Field(
            description="查验优先级(1-10)",
            ge=1, le=10
        )
    
    return SeerModelCN


def get_hunter_model_cn(agents: list[AgentBase]) -> type[BaseModel]:
    """获取中文版猎人模型"""
    
    class HunterModelCN(BaseModel):
        """中文版猎人开枪格式"""
        
        shoot: bool = Field(
            description="是否使用开枪技能",
        )
        target: Optional[Literal[tuple(_.name for _ in agents)]] = Field(
            description="开枪目标玩家姓名",
            default=None
        )
        shoot_reason: Optional[str] = Field(
            description="开枪理由",
            default=None
        )
    
    return HunterModelCN


class WerewolfKillModelCN(BaseModel):
    """中文版狼人击杀模型"""
    
    target: str = Field(
        description="要击杀的玩家姓名",
    )
    kill_strategy: str = Field(
        description="击杀策略说明",
    )
    team_coordination: Optional[str] = Field(
        description="与狼队友的配合计划",
        default=None
    )


class GameAnalysisModelCN(BaseModel):
    """中文版游戏分析模型"""
    
    suspected_werewolves: List[str] = Field(
        description="怀疑的狼人名单",
        default_factory=list
    )
    trusted_players: List[str] = Field(
        description="信任的玩家名单", 
        default_factory=list
    )
    key_clues: List[str] = Field(
        description="关键线索列表",
        default_factory=list
    )
    next_strategy: str = Field(
        description="下一步策略",
    )

import json
import re

# ==========================================
# 4. 工具函数 (from utils_cn.py)
# ==========================================

def sanitize_msg(msg: Msg, agent_name: str) -> Msg:
    """清洗消息内容，去除幻觉和非法格式"""
    if not msg or not msg.content:
        print(f"WARNING: Empty msg from {agent_name}")
        msg.content = '{"reach_agreement": false, "confidence_level": 5, "key_evidence": "（沉思中...）"}'
        return msg

    content = str(msg.content)
    
    # 1. 检查非法关键词 (代码、链接等)
    blacklist = ["#include", "import ", "class ", "def ", "http", "github", "```java", "```python", "```c"]
    for word in blacklist:
        if word in content.lower():
            print(f"WARNING: Invalid keyword '{word}' found in {agent_name}'s msg: {content[:50]}...")
            msg.content = '{"reach_agreement": false, "confidence_level": 5, "key_evidence": "（我需要再思考一下...）"}'
            return msg

    # 2. 尝试提取 JSON
    # 移除 Markdown 代码块标记
    import re
    match = re.search(r"```json\s*(.*?)\s*```", content, re.DOTALL)
    if match:
        content = match.group(1)
    else:
        match = re.search(r"```\s*(.*?)\s*```", content, re.DOTALL)
        if match:
            content = match.group(1)
            
    msg.content = content.strip()
    return msg

def extract_json_from_text(text: str | list | Any) -> Dict[str, Any]:
    """从文本中提取JSON"""
    if isinstance(text, list):
        # 处理列表类型的content
        try:
            # 尝试提取其中的文本内容
            text_parts = []
            for item in text:
                if isinstance(item, str):
                    text_parts.append(item)
                elif isinstance(item, dict) and "text" in item:
                    text_parts.append(item["text"])
                else:
                    text_parts.append(str(item))
            text = "".join(text_parts)
        except Exception:
            text = str(text)
    elif not isinstance(text, str):
        text = str(text)

    try:
        # 尝试直接解析
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    
    # 尝试提取代码块
    match = re.search(r"```json\s*(.*?)\s*```", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass
            
    match = re.search(r"```\s*(.*?)\s*```", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass
            
    # 尝试提取 {}
    match = re.search(r"(\{.*\})", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass
            
    return {}


# 游戏常量
MAX_GAME_ROUND = 10
MAX_DISCUSSION_ROUND = 3
CHINESE_NAMES = [
    "刘备", "关羽", "张飞", "诸葛亮", "赵云",
    "曹操", "司马懿", "典韦", "许褚", "夏侯惇", 
    "孙权", "周瑜", "陆逊", "甘宁", "太史慈",
    "吕布", "貂蝉", "董卓", "袁绍", "袁术"
]


def get_chinese_name(character: str = None) -> str:
    """获取中文角色名"""
    if character and character in CHINESE_NAMES:
        return character
    return random.choice(CHINESE_NAMES)


def format_player_list(players: List[AgentBase], show_roles: bool = False) -> str:
    """格式化玩家列表为中文显示"""
    if not players:
        return "无玩家"
    
    if show_roles:
        return "、".join([f"{p.name}({getattr(p, 'role', '未知')})" for p in players])
    else:
        return "、".join([p.name for p in players])


def majority_vote_cn(votes: Dict[str, str]) -> tuple[str, int]:
    """中文版多数投票统计"""
    if not votes:
        return "无人", 0
    
    vote_counts = Counter(votes.values())
    most_voted = vote_counts.most_common(1)[0]
    
    return most_voted[0], most_voted[1]


def check_winning_cn(alive_players: List[AgentBase], roles: Dict[str, str]) -> Optional[str]:
    """检查中文版游戏胜利条件"""
    alive_roles = [roles.get(p.name, "村民") for p in alive_players]
    werewolf_count = alive_roles.count("狼人")
    villager_count = len(alive_roles) - werewolf_count
    
    if werewolf_count == 0:
        return "好人阵营胜利！所有狼人已被淘汰！"
    elif werewolf_count >= villager_count:
        return "狼人阵营胜利！狼人数量已达到或超过好人！"
    
    return None


def format_player_list_str(players: List[str]) -> str:
    """格式化玩家姓名列表"""
    if not players:
        return "无人"
    return "、".join(players)


class GameModerator(AgentBase):
    """中文版游戏主持人"""
    
    def __init__(self, notify_func=None) -> None:
        super().__init__()
        self.name = "游戏主持人"
        self.game_log: List[str] = []
        self.notify_func = notify_func
    
    async def announce(self, content: str) -> Msg:
        """发布游戏公告"""
        msg = Msg(
            name=self.name,
            content=f"📢 {content}",
            role="system"
        )
        self.game_log.append(content)
        # await self.print(msg) # Disable print to avoid double printing if notify handles it, or keep it.
        # Let's keep print for terminal usage, but maybe the server will capture stdout?
        # Better to keep print for now.
        print(f"\n[{self.name}] {content}")
        
        if self.notify_func:
            await self.notify_func(msg)
            
        return msg
    
    async def night_announcement(self, round_num: int) -> Msg:
        """夜晚阶段公告"""
        content = f"🌙 第{round_num}夜降临，天黑请闭眼..."
        return await self.announce(content)
    
    async def day_announcement(self, round_num: int) -> Msg:
        """白天阶段公告"""
        content = f"☀️ 第{round_num}天天亮了，请大家睁眼..."
        return await self.announce(content)
    
    async def death_announcement(self, dead_players: List[str]) -> Msg:
        """死亡公告"""
        if not dead_players:
            content = "昨夜平安无事，无人死亡。"
        else:
            content = f"昨夜，{format_player_list_str(dead_players)}不幸遇害。"
        return await self.announce(content)
    
    async def vote_result_announcement(self, voted_out: str, vote_count: int) -> Msg:
        """投票结果公告"""
        content = f"投票结果：{voted_out}以{vote_count}票被淘汰出局。"
        return await self.announce(content)
    
    async def game_over_announcement(self, winner: str) -> Msg:
        """游戏结束公告"""
        content = f"🎉 游戏结束！{winner}"
        return await self.announce(content)

# ==========================================
# 5. 游戏主逻辑 (from main_cn.py)
# ==========================================

class ThreeKingdomsWerewolfGame:
    """三国狼人杀游戏主类"""
    
    def __init__(self, notify_func=None):
        self.players: Dict[str, ReActAgent] = {}
        self.roles: Dict[str, str] = {}
        self.notify_func = notify_func
        self.moderator = GameModerator(notify_func=notify_func)
        self.alive_players: List[ReActAgent] = []
        self.werewolves: List[ReActAgent] = []
        self.villagers: List[ReActAgent] = []
        self.seer: List[ReActAgent] = []
        self.witch: List[ReActAgent] = []
        self.hunter: List[ReActAgent] = []
        
        # 女巫道具状态
        self.witch_has_antidote = True
        self.witch_has_poison = True
        
    async def create_player(self, role: str, character: str) -> ReActAgent:
        """创建具有三国背景的玩家"""
        name = get_chinese_name(character)
        self.roles[name] = role
        
        # 从环境变量获取 API Key 和 Base URL
        api_key = os.environ.get("OPENAI_API_KEY")
        base_url = os.environ.get("OPENAI_API_BASE_URL")
        # 用户指定的模型
        model_name = "deepseek-ai/DeepSeek-V3.2" 
        
        if not api_key:
            raise ValueError("Environment variable OPENAI_API_KEY is not set.")
        if not base_url:
            raise ValueError("Environment variable OPENAI_API_BASE_URL is not set.")

        agent = ReActAgent(
            name=name,
            sys_prompt=ChinesePrompts.get_role_prompt(role, character),
            model=OpenAIChatModel(
                model_name=model_name,
                api_key=api_key,
                client_args={
                    "base_url": base_url
                },
            ),
            formatter=OpenAIChatFormatter(),
        )
        
        # 角色身份确认
        await agent.observe(
            await self.moderator.announce(
                f"【{name}】你在这场三国狼人杀中扮演{GameRoles.get_role_desc(role)}，"
                f"你的角色是{character}。{GameRoles.get_role_ability(role)}"
            )
        )
        
        self.players[name] = agent
        return agent
    
    async def setup_game(self, player_count: int = 6):
        """设置游戏"""
        print("🎮 开始设置三国狼人杀游戏...")
        
        # 获取角色配置
        roles = GameRoles.get_standard_setup(player_count)
        characters = random.sample([
            "刘备", "关羽", "张飞", "诸葛亮", "赵云",
            "曹操", "司马懿", "周瑜", "孙权"
        ], player_count)
        
        # 创建玩家
        for i, (role, character) in enumerate(zip(roles, characters)):
            agent = await self.create_player(role, character)
            self.alive_players.append(agent)
            
            # 分配到对应阵营
            if role == "狼人":
                self.werewolves.append(agent)
            elif role == "预言家":
                self.seer.append(agent)
            elif role == "女巫":
                self.witch.append(agent)
            elif role == "猎人":
                self.hunter.append(agent)
            else:
                self.villagers.append(agent)
        
        # 游戏开始公告
        await self.moderator.announce(
            f"三国狼人杀游戏开始！参与者：{format_player_list(self.alive_players)}"
        )
        
        print(f"✅ 游戏设置完成，共{len(self.alive_players)}名玩家")
    
    async def werewolf_phase(self, round_num: int):
        """狼人阶段"""
        if self.notify_func:
            await self.notify_func({"type": "phase", "content": "狼人阶段", "task": "狼人请睁眼，选择今晚要击杀的目标"})
            
        if not self.werewolves:
            return None
            
        await self.moderator.announce(f"🐺 狼人请睁眼，选择今晚要击杀的目标...")
        
        # 狼人讨论
        async with MsgHub(
            self.werewolves,
            enable_auto_broadcast=False, # Disable auto broadcast to filter msgs
            announcement=await self.moderator.announce(
                f"狼人们，请讨论今晚的击杀目标。存活玩家：{format_player_list(self.alive_players)}"
            ),
        ) as werewolves_hub:
            # 讨论阶段
            for _ in range(MAX_DISCUSSION_ROUND):
                for wolf in self.werewolves:
                    # Debug: Check memory before generation
                    print(f"Checking memory for {wolf.name}")
                    if hasattr(wolf, 'memory') and wolf.memory:
                        # get_memory is async if using certain backends, but usually sync for InMemory.
                        # However, user report says it is a coroutine.
                        # Let's try to inspect if it is awaitable.
                        mems = wolf.memory.get_memory()
                        if asyncio.iscoroutine(mems):
                            mems = await mems
                        
                        if mems:
                            for m in mems:
                               if m.content is None or (isinstance(m.content, str) and ("```" in m.content or "http" in m.content or "github" in m.content.lower())):
                                   print(f"WARNING: Found invalid content msg in {wolf.name}'s memory: {m}")
                                   m.content = "" # HOTFIX: Clear invalid memory
                    
                    # 不使用 structured_model 以避免 API 兼容性问题
                    # Add hint prompt - MUST be a Msg object, not string!
                    hint_msg = Msg(name="System", content="请基于当前局势进行发言，必须返回JSON格式。", role="system")
                    msg = await wolf(hint_msg)
                    
                    # Sanitize
                    msg = sanitize_msg(msg, wolf.name)
                    
                    # Manual broadcast
                    werewolves_hub.broadcast(msg)

                    if self.notify_func and msg:
                        await self.notify_func(msg)
            
            # 投票击杀
            werewolves_hub.set_auto_broadcast(False)
            kill_votes = await fanout_pipeline(
                self.werewolves,
                msg=await self.moderator.announce("请选择击杀目标"),
                # structured_model=WerewolfKillModelCN, # Disable
                enable_gather=False,
            )
            
            # 广播投票消息
            if self.notify_func:
                for msg in kill_votes:
                    if msg:
                        await self.notify_func(msg)
            
            # 统计投票
            votes = {}
            for i, vote_msg in enumerate(kill_votes):
                # 手动解析 JSON
                if vote_msg and vote_msg.content:
                    data = extract_json_from_text(vote_msg.content)
                    votes[self.werewolves[i].name] = data.get("target")
                else:
                    # 如果返回无效,随机选择一个目标
                    print(f"⚠️ {self.werewolves[i].name} 的击杀投票无效,随机选择目标")
                    valid_targets = [p.name for p in self.alive_players if p.name not in [w.name for w in self.werewolves]]
                    votes[self.werewolves[i].name] = random.choice(valid_targets) if valid_targets else None
            
            killed_player, _ = majority_vote_cn(votes)
            return killed_player
    
    async def seer_phase(self):
        """预言家阶段"""
        if self.notify_func:
            await self.notify_func({"type": "phase", "content": "预言家阶段", "task": "预言家请睁眼，选择要查验的玩家"})
            
        if not self.seer:
            return
            
        seer_agent = self.seer[0]
        await self.moderator.announce("🔮 预言家请睁眼，选择要查验的玩家...")
        
        check_result = await seer_agent()
        if self.notify_func and check_result:
            await self.notify_func(check_result)

        # 检查返回结果是否有效
        if check_result and check_result.content:
            data = extract_json_from_text(check_result.content)
            target_name = data.get("target")
        else:
            data = {}
            target_name = None

        if not target_name:
            print(f"⚠️ 预言家未选择查验目标,跳过此阶段")
            return

        target_role = self.roles.get(target_name, "村民")
        
        # 告知预言家结果
        result_msg = f"查验结果：{target_name}是{'狼人' if target_role == '狼人' else '好人'}"
        await seer_agent.observe(await self.moderator.announce(result_msg))
    
    async def witch_phase(self, killed_player: str):
        """女巫阶段"""
        if self.notify_func:
            await self.notify_func({"type": "phase", "content": "女巫阶段", "task": "女巫请睁眼，决定是否使用药剂"})
            
        if not self.witch:
            return killed_player, None
            
        witch_agent = self.witch[0]
        await self.moderator.announce("🧙‍♀️ 女巫请睁眼...")
        
        # 告知女巫死亡信息
        death_info = f"今晚{killed_player}被狼人击杀" if killed_player else "今晚平安无事"
        await witch_agent.observe(await self.moderator.announce(death_info))
        
        # 女巫行动
        witch_action = await witch_agent()
        if self.notify_func and witch_action:
            await self.notify_func(witch_action)

        saved_player = None
        poisoned_player = None

        # 检查返回结果是否有效
        data = {}
        if witch_action and witch_action.content:
            data = extract_json_from_text(witch_action.content)
        
        if not data:
            print(f"⚠️ 女巫行动失败,视为不使用技能")
        else:
            if data.get("use_antidote") and self.witch_has_antidote:
                if killed_player:
                    saved_player = killed_player
                    self.witch_has_antidote = False
                    await witch_agent.observe(await self.moderator.announce(f"你使用解药救了{killed_player}"))

            if data.get("use_poison") and self.witch_has_poison:
                poisoned_player = data.get("target_name")
                if poisoned_player:
                    self.witch_has_poison = False
                    await witch_agent.observe(await self.moderator.announce(f"你使用毒药毒杀了{poisoned_player}"))
        
        # 确定最终死亡玩家
        final_killed = killed_player if not saved_player else None
        
        return final_killed, poisoned_player
    
    async def hunter_phase(self, shot_by_hunter: str):
        """猎人阶段"""
        if self.notify_func:
            await self.notify_func({"type": "phase", "content": "猎人阶段", "task": "猎人发动技能"})
            
        if not self.hunter:
            return None
            
        hunter_agent = self.hunter[0]
        if hunter_agent.name == shot_by_hunter:
            await self.moderator.announce("🏹 猎人发动技能，可以带走一名玩家...")
            
            hunter_action = await hunter_agent()
            if self.notify_func and hunter_action:
                await self.notify_func(hunter_action)

            # 检查返回结果是否有效
            data = {}
            if hunter_action and hunter_action.content:
                data = extract_json_from_text(hunter_action.content)

            if not data:
                print(f"⚠️ 猎人技能使用失败,视为放弃开枪")
                return None

            if data.get("shoot"):
                target = data.get("target")
                if target:
                    await self.moderator.announce(f"猎人{hunter_agent.name}开枪带走了{target}")
                    return target
                else:
                    print(f"⚠️ 猎人选择开枪但未指定目标,视为放弃")
                    return None
        
        return None
    
    def update_alive_players(self, dead_players: List[str]):
        """更新存活玩家列表"""
        for dead_name in dead_players:
            if dead_name:
                # 从存活列表移除
                self.alive_players = [p for p in self.alive_players if p.name != dead_name]
                # 从各阵营移除
                self.werewolves = [p for p in self.werewolves if p.name != dead_name]
                self.villagers = [p for p in self.villagers if p.name != dead_name]
                self.seer = [p for p in self.seer if p.name != dead_name]
                self.witch = [p for p in self.witch if p.name != dead_name]
                self.hunter = [p for p in self.hunter if p.name != dead_name]
    
    async def day_phase(self, round_num: int):
        """白天阶段"""
        if self.notify_func:
            await self.notify_func({"type": "phase", "content": f"第{round_num}天 白天", "task": "自由讨论与投票"})
            
        await self.moderator.day_announcement(round_num)
        
        # 讨论阶段
        async with MsgHub(
            self.alive_players,
            enable_auto_broadcast=False, # Disable auto broadcast to filter msgs
            announcement=await self.moderator.announce(
                f"现在开始自由讨论。存活玩家：{format_player_list(self.alive_players)}"
            ),
        ) as all_hub:
            # 每人发言一轮
            # await sequential_pipeline(self.alive_players)
            for player in self.alive_players:
                # Debug: Check memory before generation
                if hasattr(player, 'memory') and player.memory:
                     mems = player.memory.get_memory()
                     if asyncio.iscoroutine(mems):
                         mems = await mems
                     
                     if mems:
                         for m in mems:
                             if m.content is None or (isinstance(m.content, str) and ("```" in m.content or "http" in m.content or "github" in m.content.lower())):
                                 print(f"WARNING: Found invalid content msg in {player.name}'s memory: {m}")
                                 m.content = "" # HOTFIX: Clear invalid memory

                # Add hint prompt - MUST be a Msg object, not string!
                hint_msg = Msg(name="System", content="请基于当前局势进行发言，必须返回JSON格式。", role="system")
                msg = await player(hint_msg)
                
                # Sanitize
                msg = sanitize_msg(msg, player.name)
                
                # Manual broadcast
                all_hub.broadcast(msg)

                if self.notify_func and msg:
                    await self.notify_func(msg)
            
            # 投票阶段
            all_hub.set_auto_broadcast(False)
            vote_msgs = await fanout_pipeline(
                self.alive_players,
                await self.moderator.announce("请投票选择要淘汰的玩家"),
                # structured_model=get_vote_model_cn(self.alive_players), # Disable
                enable_gather=False,
            )
            
            # 广播投票消息
            if self.notify_func:
                for msg in vote_msgs:
                    if msg:
                        await self.notify_func(msg)
            
            # 统计投票
            votes = {}
            for i, vote_msg in enumerate(vote_msgs):
                # 手动解析 JSON
                if vote_msg and vote_msg.content:
                    data = extract_json_from_text(vote_msg.content)
                    votes[self.alive_players[i].name] = data.get("vote")
                else:
                    # 如果返回无效,默认弃票
                    print(f"⚠️ {self.alive_players[i].name} 的投票无效,视为弃票")
                    votes[self.alive_players[i].name] = None
            
            voted_out, vote_count = majority_vote_cn(votes)
            await self.moderator.vote_result_announcement(voted_out, vote_count)
            
            return voted_out
    
    async def run_game(self):
        """运行游戏主循环"""
        try:
            await self.setup_game()
            
            for round_num in range(1, MAX_GAME_ROUND + 1):
                print(f"\n🌙 === 第{round_num}轮游戏开始 ===")
                
                # 夜晚阶段
                await self.moderator.night_announcement(round_num)
                
                # 狼人击杀
                killed_player = await self.werewolf_phase(round_num)
                
                # 预言家查验
                await self.seer_phase()
                
                # 女巫行动
                final_killed, poisoned_player = await self.witch_phase(killed_player)
                
                # 更新死亡玩家
                night_deaths = [p for p in [final_killed, poisoned_player] if p]
                self.update_alive_players(night_deaths)
                
                # 死亡公告
                await self.moderator.death_announcement(night_deaths)
                
                # 检查胜利条件
                winner = check_winning_cn(self.alive_players, self.roles)
                if winner:
                    await self.moderator.game_over_announcement(winner)
                    return
                
                # 白天阶段
                voted_out = await self.day_phase(round_num)
                
                # 猎人技能
                hunter_shot = await self.hunter_phase(voted_out)
                
                # 更新死亡玩家
                day_deaths = [p for p in [voted_out, hunter_shot] if p]
                self.update_alive_players(day_deaths)
                
                # 检查胜利条件
                winner = check_winning_cn(self.alive_players, self.roles)
                if winner:
                    await self.moderator.game_over_announcement(winner)
                    return
                
                print(f"第{round_num}轮结束，存活玩家：{format_player_list(self.alive_players)}")
        
        except Exception as e:
            print(f"❌ 游戏运行出错：{e}")
            import traceback
            traceback.print_exc()


async def main():
    """主函数"""
    # 检查环境变量
    if "OPENAI_API_KEY" not in os.environ:
        print("❌ 请设置环境变量 OPENAI_API_KEY")
        return
    if "OPENAI_API_BASE_URL" not in os.environ:
        print("❌ 请设置环境变量 OPENAI_API_BASE_URL")
        return
    
    print("🎮 欢迎来到三国狼人杀（DeepSeek版）！")
    
    # 初始化 AgentScope
    agentscope.init()
    
    # 创建并运行游戏
    game = ThreeKingdomsWerewolfGame()
    await game.run_game()


if __name__ == "__main__":
    asyncio.run(main())
