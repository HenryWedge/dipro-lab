from dataclasses import dataclass

from runtime.core import DistributedAlgorithm, operation

@dataclass(frozen=True)
class _ConsumePlan:
    place_id: str
    owner_id: str | None = None
    pending: tuple["_ConsumePlan", ...] = ()
    silent_handle: str | None = None


class PlaceResolverInterface(DistributedAlgorithm):
    @operation()
    def install_model(
        self,
        place_owners: dict[str, list[str]],
        final_marking: dict[str, int],
    ) -> None:
        pass

    @operation()
    def resolve_and_consume(self, case_id: str, place_id: str) -> None:
        pass

    @operation()
    def produce_token(self, case_id: str, place_id: str) -> None:
        pass

    @operation()
    def end_trace(self, case_id: str) -> None:
        pass


class PlaceResolveParticipant(PlaceResolverInterface):
    def __init__(self, participant_id="resolver", participant_client=None):
        self.participant_id = participant_id
        self.participant_client = participant_client
        self.network = None
        self.place_owners = {}
        self.final_marking = {}

    def set_network(self, network):
        self.network = network

    def install_model(self, place_owners, final_marking):
        self.place_owners = place_owners
        self.final_marking = final_marking


    def end_trace(self, case_id: str) -> None:
        for place_id, expected_tokens in self.final_marking.items():
            for _ in range(expected_tokens):
                self.resolve_and_consume(case_id, place_id)

    def resolve_and_consume(self, case_id: str, place_id: str):
        plan = self._can_be_marked(case_id, place_id, frozenset())
        if plan is None:
            owners = self.place_owners.get(place_id, [])
            if owners:
                self._call_owner(owners[0]).consume_place(case_id, place_id)
            return
        self._consume_plan(case_id, plan)

    def _can_be_marked(self, case_id, place_id, visited):
        if place_id in visited:
            return None
        visited = visited | {place_id}

        for owner_id in self.place_owners.get(place_id, []):
            result = self._call_owner(owner_id).is_place_marked(case_id, place_id)
            if result.can_be_marked:
                return _ConsumePlan(place_id, owner_id)
            for pending_option in result.pending_options:
                pending_plans = []
                for input_place in pending_option.input_places:
                    input_plan = self._can_be_marked(case_id, input_place, visited)
                    if input_plan is None:
                        break
                    pending_plans.append(input_plan)
                else:
                    return _ConsumePlan(
                        place_id,
                        owner_id=owner_id,
                        pending=tuple(pending_plans),
                        silent_handle=pending_option.handle,
                    )
        return None

    def _consume_plan(self, case_id, plan):
        if self._consume_if_marked(case_id, plan.place_id):
            return

        for pending_plan in plan.pending:
            self._consume_plan(case_id, pending_plan)
        if plan.silent_handle is not None:
            if self._consume_if_marked(case_id, plan.place_id):
                return
            self._call_owner(plan.owner_id).fire_silent_transition(
                case_id,
                plan.silent_handle,
            )
            if self._consume_if_marked(case_id, plan.place_id):
                return
        elif plan.owner_id is not None:
            self._call_owner(plan.owner_id).consume_place(case_id, plan.place_id)

    def _consume_if_marked(self, case_id, place_id):
        for owner_id in self.place_owners.get(place_id, []):
            owner = self._call_owner(owner_id)
            if owner.is_place_marked(case_id, place_id).can_be_marked:
                owner.consume_place(case_id, place_id)
                return True
        return False

    def _call_owner(self, owner_id):
        if self.participant_client is not None:
            return self.participant_client.proxy(owner_id)
        return self.network.call(owner_id)
