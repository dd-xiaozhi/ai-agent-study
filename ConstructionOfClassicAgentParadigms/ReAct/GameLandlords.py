"""
斗地主小游戏，分别由不同的大模型扮演不懂的角色，直到牌局结束
"""

import random

from LLMClient import LLMClient

class Dealer:
    """
    发牌器
    """

    def __init__(self):
        self.suits = ['黑桃', '红桃', '方块', '梅花']
        self.ranks = [
            '3', '4', '5', '6', '7', '8', '9',
            '10', 'J', 'Q', 'K', 'A', '2'
        ]
        self.jokers = ['小王', '大王']
        self.deck = self._create_deck()

    def _create_deck(self):
        """生成一副完整的斗地主牌"""
        deck = [f"{suit} {rank}" for suit in self.suits for rank in self.ranks]
        deck.extend(self.jokers)
        return deck

    def shuffle(self):
        """洗牌"""
        random.shuffle(self.deck)

    def deal(self):
        """发牌：3人每人17张，剩余3张为底牌"""
        self.shuffle()
        players = {
            "A玩家": self.deck[0:17],
            "B玩家": self.deck[17:34],
            "C玩家": self.deck[34:51]
        }
        bottom_cards = self.deck[51:54]
        return players, bottom_cards


class Player:


    def __init__(self, llmClient: LLMClient) -> None:
        pass


if __name__ == "__main__":
    dealer = Dealer()
    players, bottom = dealer.deal()

    print("===== 斗地主发牌结果 =====")
    for player, cards in players.items():
        print(f"\n{player} ({len(cards)}张)：")
        print(sorted(cards))

    print("\n底牌 (3张)：")
    print(bottom)

    llm = LLMClient("deepseek-ai/DeepSeek-V3.2")
    llm.generate([{'role': 'user', 'content': '你是谁'}])