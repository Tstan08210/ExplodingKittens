from card import *

class Player:
    def __init__(self, user_id, name):
        self.user_id = user_id
        self.name = name
        self.hand = []
        self.pending_turns = 0
        self.alive = True
    def add_card(self, card):
        self.hand.append(card)
    def remove_card(self, card):
        self.hand.remove(card)
    def has_card(self, card_type):
        for card in self.hand:
            if isinstance(card, card_type):
                return True
        return False
    def get_card(self, card_type):
        for card in self.hand:
            if isinstance(card, card_type):
                return card
        return None
    def get_card_by_name(self, name):
        normalized = name.strip().lower()
        for card in self.hand:
            if card.name.strip().lower() == normalized:
                return card
        return None
    @property
    def has_defuse(self):
        return self.has_card(DefuseCard)
    def use_defuse(self):
        card = self.get_card(DefuseCard)
        if card:
            self.remove_card(card)
            return card
        return None
    @property
    def count_nope(self):
        return sum(1 for card in self.hand if isinstance(card, NopeCard))
    def __str__(self):
        return self.name
    def __repr__(self):
        return self.name
    