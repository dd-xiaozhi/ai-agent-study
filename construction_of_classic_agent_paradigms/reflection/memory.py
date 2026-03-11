from typing import Dict, List, Any, Optional

class Memory:
    """
    短暂记忆模块，用于存储智能体行动与反思轨迹
    """
    def __init__(self):
        # 记忆列表
        self.records: List[Dict[str, Any]] = []

    def add_record(self, record_type: str, record_content: str) -> None:
        """
        添加记忆记录

        Args:
            record_type: 记忆类型 (`execution` | `reflection`)
            record_content: 记忆内容
        """
        record = { "type": record_type, "content": record_content }
        self.records.append(record)
        print(f"新增一条 {record_type} 记忆")

    def get_trajectory(self) -> str:
        """
        将所有的记忆记录拼接成一个字符串
        """
        trajectory_parts = []
        for record in self.records:
            if record['type'] == 'execution':
                trajectory_parts.append(f"--- 上一轮尝试 (代码) ---\n{record['content']}")
            elif record['type'] == 'reflection':
                trajectory_parts.append(f"--- 评审员反馈 ---\n{record['content']}")

        return "\n\n".join(trajectory_parts)

    def get_last_execution(self) -> Optional[str]:
        """
        获取最后一轮执行结果，如果不存在返回 None
        """
        # 反转列表遍历获取最后一个执行结果
        for record in reversed(self.records):
            if record['type'] == 'execution':
                return record['content']
        return None
