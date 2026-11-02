class TokenMetrics:
    def __init__(
            self,
            produced=0,
            consumed=0,
            missing=0,
            remaining=0
    ):
        self.produced = produced
        self.consumed = consumed
        self.missing = missing
        self.remaining = remaining

    def fitness(self):
        if self.consumed == 0 or self.produced == 0:
            return 0.0
        return 0.5 * (1 - self.missing / self.consumed) + 0.5 * (1 - self.remaining / self.produced)

    def online_completeness(self):
        if self.consumed == 0 or self.produced == 0:
            return 0.0
        return (1 - (self.missing / self.consumed))

    def online_confindence(self):
        if self.consumed == 0 or self.produced == 0:
            return 0.0
        return (1 - (self.remaining / self.produced))

    def increment_produced(self, increment=1):
        self.produced = self.produced + increment

    def increment_consumed(self, increment=1):
        self.consumed = self.consumed + increment

    def increment_missing(self, increment=1):
        self.missing = self.missing + increment

    def increment_remaining(self, increment=1):
        self.remaining = self.remaining + increment

    def __str__(self) -> str:
        return f"produced: {self.produced}, consumed: {self.consumed}, missing: {self.missing}, remaining: {self.remaining}, conformance: {self.fitness()}, completeness:{self.online_completeness()}, confidence: {self.online_confindence()}"

    def __add__(self, other):
        return TokenMetrics(
            self.produced + other.produced,
            self.consumed + other.consumed,
            self.missing + other.missing,
            self.remaining + other.remaining
        )

    def to_wire(self):
        return {
            "produced": self.produced,
            "consumed": self.consumed,
            "missing": self.missing,
            "remaining": self.remaining,
        }

    @classmethod
    def from_wire(cls, value):
        return cls(
            produced=value.get("produced", 0),
            consumed=value.get("consumed", 0),
            missing=value.get("missing", 0),
            remaining=value.get("remaining", 0),
        )
