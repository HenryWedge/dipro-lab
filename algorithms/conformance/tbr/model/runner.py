from dpm_bench import ParticipantClient

from tokenbasedreplay.data.event import Event
from tokenbasedreplay.model.distributed.participant_interface import TBRParticipant, PlaceOperations
from tokenbasedreplay.model.distributed.place_resolver import PlaceResolver, PlaceResolverInterface
from tokenbasedreplay.model.distributed.participant_service import TokenReplayParticipant
from tokenbasedreplay.model.distributed.result import (
    ReplayLogResult,
    ReplayTraceResult,
)


def local_participants(participant_ids):
    return {
        participant_id: TokenReplayParticipant(participant_id)
        for participant_id in participant_ids
    }

class TBRTestRunner:

    def __init__(self, participant_ids, mode, local_services=None, participant_urls=None, timeout=10):
        endpoints = dict(local_services or {}) if mode == "local" else dict(participant_urls or {})
        self.local_services = endpoints if mode == "local" else None
        self.client = ParticipantClient(endpoints, TBRParticipant, mode=mode, timeout=timeout)
        self.place_client = ParticipantClient(endpoints, PlaceOperations, mode=mode, timeout=timeout)
        self.resolver_client = ParticipantClient(endpoints, PlaceResolverInterface, mode=mode, timeout=timeout)
        self.participant_ids = list(participant_ids)
        self.activity_owners = {}

    def install_model(self, model):
        self.activity_owners = dict(model.activity_owners)
        if "resolver" not in self.place_client.participant_ids:
            if self.local_services is None:
                raise ValueError("participant URLs must include 'resolver'")
            resolver = PlaceResolver(participant_client=self.place_client)
            self.local_services["resolver"] = resolver
            self.client.set_participants(self.local_services)
            self.place_client.set_participants(self.local_services)
            self.resolver_client.set_participants(self.local_services)
        if self.local_services is not None:
            for participant_id in self.participant_ids:
                self.local_services[participant_id].set_resolver_client(self.resolver_client)
        self.resolver_client.proxy("resolver").install_model(
            model.place_owners,
            model.final_marking,
        )
        for participant_id in self.participant_ids:
            self.client.proxy(participant_id).install_model(model.for_participant(participant_id))

    def replay_log(self, event_log, on_event=None):
        result = ReplayLogResult()
        for case_id, events in event_log.iter_traces():
            trace_result = ReplayTraceResult(case_id)

            for event_index, event in enumerate(events):
                participant_id = self.participant_id_for(event)
                if event.location != participant_id:
                    event = Event(event.case_id, event.activity, participant_id, event.time)
                response = self.client.proxy(participant_id).process_event(event, event_index)
                trace_result.add_event_result(response)
                if on_event is not None:
                    on_event(event, response)
            self.resolver_client.proxy("resolver").end_trace(case_id)
            result.add_trace_result(trace_result)

        result.participant_metrics = {
            participant_id: self.client.proxy(participant_id).get_token_metrics_for_case(case_id)
            for participant_id in self.participant_ids
        }

        return result

    def participant_id_for(self, event):
        owner = self.activity_owners.get(event.activity)
        if owner is not None:
            return owner
        if event.location in self.client.participant_ids:
            return event.location
        return None
