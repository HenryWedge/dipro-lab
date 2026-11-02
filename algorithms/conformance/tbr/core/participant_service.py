from uuid import uuid4

from conformance.tbr.core.participant_interface import TBRParticipant
from conformance.tbr.core.token_metrics import TokenMetrics
from conformance.tbr.transport.wire import IsMarkedResult, SilentTransitionOption, TBRModel
from runtime.core import Network


class TokenReplayParticipant(TBRParticipant):
    def __init__(self, participant_id):
        self.participant_id = participant_id
        self.model = None
        self.transitions = {}
        self.transitions_by_activity = {}
        self.silent_transition_handles = {}
        self.case_markings = {}
        self.metrics = dict()

    def set_network(self, network: Network):
        self.network = network

    def case_metrics(self, case_id):
        if not case_id in self.metrics:
            self.metrics[case_id] = TokenMetrics()
        return self.metrics[case_id]

    def install_model(self, model: TBRModel):
        self.model = model
        self.transitions = {item.transition_id: item for item in model.transitions}
        self.silent_transition_handles = {
            str(uuid4()): transition
            for transition in model.transitions
            if transition.label is None
            and model.transition_owners.get(transition.transition_id) == self.participant_id
        }
        self.transitions_by_activity = {}
        for transition in model.transitions:
            if transition.label is not None:
                self.transitions_by_activity.setdefault(transition.label, []).append(transition)

    # TODO here. Consider all candidates
    def process_event(self, event):
        case_id = event.case_id
        if case_id not in self.case_markings:
            self._init_case(case_id)

        candidates = self.transitions_by_activity.get(event.activity, [])
        if not candidates:
            print("activity ", event.activity, " not supported at this node")
            return
        else:
            transition = candidates[0]

        for place_id in transition.input_places:
            self.network.call("resolver").resolve_and_consume(case_id, place_id)

        for place_id in transition.output_places:
            self.mark_place(case_id, place_id)

    def _init_case(self, case_id: str):
        self.case_markings[case_id] = dict(self.model.initial_marking)

    def mark_place(self, case_id: str, place_id: str) -> None:
        if not case_id in self.case_markings:
            self._init_case(case_id)
        marking = self.case_markings[case_id]
        marking[place_id] = marking.get(place_id, 0) + 1
        self.case_metrics(case_id).increment_produced()

    def _get_remaining_tokens(self, case_id):
        if not case_id in self.case_markings:
            return 0
        case_marking = self.case_markings[case_id]
        return sum([case_marking[marking] for marking in case_marking])

    def consume_place(self, case_id, place_id) -> None:
        if case_id not in self.case_markings:
            self._init_case(case_id)
        self.case_metrics(case_id).increment_consumed()
        if self.case_markings[case_id].get(place_id, 0) > 0:
            self.case_markings[case_id][place_id] -= 1
        else:
            self.case_metrics(case_id).increment_missing()

    def fire_silent_transition(self, case_id: str, handle: str) -> None:
        transition = self.silent_transition_handles[handle]
        for place_id in transition.output_places:
            self.mark_place(case_id, place_id)

    def _get_silent_transitions_to_place(self, place_id: str):
        return [
            transition
            for transition in self.transitions.values()
            if transition.label is None and place_id in transition.output_places
        ]

    def is_place_marked(self, case_id: str, place_id: str) -> IsMarkedResult:
        if case_id not in self.case_markings:
            self._init_case(case_id)
        marking = self.case_markings.get(case_id, {})
        if marking.get(place_id, 0) >= 1:
            return IsMarkedResult(True, [])
        handles_by_transition = {
            transition.transition_id: handle
            for handle, transition in self.silent_transition_handles.items()
        }
        pending_options = [
            SilentTransitionOption(
                handles_by_transition[transition.transition_id],
                transition.input_places,
            )
            for transition in self._get_silent_transitions_to_place(place_id)
            if transition.transition_id in handles_by_transition
        ]
        return IsMarkedResult(False, pending_options)

    def get_token_metrics_for_case(self, case_id):
        return TokenMetrics(
            produced=self.case_metrics(case_id).produced,
            consumed=self.case_metrics(case_id).consumed,
            missing=self.case_metrics(case_id).missing,
            remaining=self._get_remaining_tokens(case_id),
        )
