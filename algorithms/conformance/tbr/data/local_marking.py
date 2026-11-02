class LocalMarking:
    def __init__(self):
        self.tokens = {}

    def get(self, place_id):
        return self.tokens.get(place_id, 0)

    def add(self, place_id, amount=1):
        self.tokens[place_id] = self.get(place_id) + amount

    def remove(self, place_id, amount=1):
        current_amount = self.get(place_id)
        if current_amount <= amount:
            self.tokens.pop(place_id, None)
            return
        self.tokens[place_id] = current_amount - amount

    def remaining_tokens(self):
        return sum(self.tokens.values())
