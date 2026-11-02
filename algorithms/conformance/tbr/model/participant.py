from dataclasses import dataclass

from conformance.tbr.data.local_marking import LocalMarking
from runtime.core import DistributedAlgorithm, operation


@dataclass
class WireMarking:
    tokens: dict[str, int]


class Participant(DistributedAlgorithm):
    def __init__(self, participant_id):
        self.participant_id = participant_id
        self.places = []
        self.transitions = []
        self.initial_marking = LocalMarking()
        self.case_markings = {}
        self.metrics = {}

    def set_initial_token(self, place_id, amount=1):
        self.initial_marking.add(place_id, amount)

    @operation()
    def init_case(self, case_id):
        marking = LocalMarking()
        for place_id, amount in self.initial_marking.tokens.items():
            marking.add(place_id, amount)
        self.case_markings[case_id] = marking

    @operation()
    def marking_for_case(self, case_id):
        if case_id not in self.case_markings:
            self.init_case(case_id)
        return self.case_markings[case_id]

    @operation()
    def mark_case(self, case_id: str) -> WireMarking:
        return WireMarking(dict(self.marking_for_case(case_id).tokens))

    @operation()
    def get_marking(self, case_id: str) -> WireMarking:
        return WireMarking(dict(self.marking_for_case(case_id).tokens))

    @operation()
    def has_token(self, place_id, case_id):
        return self.marking_for_case(case_id).get(place_id) > 0

    @operation()
    def consume_token_if_available(self, place_id, case_id):
        marking = self.marking_for_case(case_id)
        if not marking.get(place_id):
            return False
        marking.remove(place_id)
        return True

    @operation()
    def consume_token(self, place_id, case_id):
        self.marking_for_case(case_id).remove(place_id)

    @operation()
    def produce_token(self, place_id, case_id):
        self.marking_for_case(case_id).add(place_id)

    @operation()
    def get_metrics(self):
        return self.metrics

    @operation()
    def increment_metric(self, name, amount=1):
        self.metrics[name] = self.metrics.get(name, 0) + amount
        return self.metrics[name]
