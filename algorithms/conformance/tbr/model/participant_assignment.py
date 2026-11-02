from conformance.tbr.data.event_log import EventLog
from conformance.tbr.data.net_access import PetriNetAccess
from conformance.tbr.data.petrinet import DiscoveredPetriNet
from conformance.tbr.model.participant import Participant
from conformance.tbr.model.participant_service import TokenReplayParticipant
from conformance.tbr.model.transition_lookup import TransitionLookup


class ParticipantAssignment:
    def __init__(self, discovered_model: DiscoveredPetriNet, training_log: EventLog):
        self.discovered_model = discovered_model
        self.training_log = training_log
        self.participant_mapping = {}
        self.activity_to_participant = {}
        self.place_to_participant = {}

    def build(self):
        net_access = PetriNetAccess(self.discovered_model)
        transition_lookup = TransitionLookup(self.discovered_model.net)
        transition_to_participants = {}
        initial_place_to_participants = {}

        for _, events in self.training_log.iter_traces():
            for event in events:
                if event.location is None:
                    raise ValueError(f"Event {event} hat keine Participant-Location.")

                transition = transition_lookup.find_transition(event.activity)
                if transition is None:
                    continue

                participant = self.participant_for(event.location)
                self.add_unique(participant.transitions, transition)
                transition_to_participants.setdefault(transition, set()).add(event.location)
                self.activity_to_participant[event.activity] = event.location

        initial_places = list(self.discovered_model.initial_marking)

        # The first visible event in each trace identifies the participant
        # responsible for the initial places of that trace.
        for _, events in self.training_log.iter_traces():
            first_visible_participant = next(
                (
                    event.location
                    for event in events
                    if transition_lookup.find_transition(event.activity) is not None
                ),
                None,
            )
            if first_visible_participant is None:
                continue
            for place in initial_places:
                initial_place_to_participants.setdefault(place, set()).add(
                    first_visible_participant
                )

        for place, participant_ids in initial_place_to_participants.items():
            for participant_id in participant_ids:
                self.assign_place(self.participant_for(participant_id), place)

        for transition, participant_ids in transition_to_participants.items():
            for place in net_access.output_places(transition):
                for participant_id in participant_ids:
                    self.assign_place(self.participant_for(participant_id), place)

        # Propagate each place's owners through silent transitions until no new
        # place ownership can be discovered. Start silent transitions use the
        # initially marked places as their effective inputs as well.
        silent_transitions = transition_lookup.silent_transitions()
        changed = True
        while changed:
            changed = False
            for transition in silent_transitions:
                input_places = net_access.input_places(transition) or initial_places
                participant_ids = set()
                for place in input_places:
                    participant_ids.update(self.place_to_participant.get(place, set()))

                for participant_id in participant_ids:
                    participant = self.participant_for(participant_id)
                    self.add_unique(participant.transitions, transition)
                    for place in net_access.output_places(transition):
                        if participant_id not in self.place_to_participant.get(place, set()):
                            self.assign_place(participant, place)
                            changed = True

        self.assign_initial_marking()
        return self.participant_mapping, self.activity_to_participant, self.place_to_participant

    def participant_for(self, participant_id):
        if participant_id not in self.participant_mapping:
            #TODO hrei: Refactor
            self.participant_mapping[participant_id] = Participant(participant_id)
        return self.participant_mapping[participant_id]

    def assign_place(self, participant, place):
        self.add_unique(participant.places, place)
        self.place_to_participant.setdefault(place, set()).add(participant.participant_id)

    def assign_initial_marking(self):
        for place, amount in self.discovered_model.initial_marking.items():
            participant_ids = self.place_to_participant.get(place, set())
            if participant_ids:
                participant_id = sorted(participant_ids, key=str)[0]
                self.participant_mapping[participant_id].set_initial_token(place, amount)

    @staticmethod
    def add_unique(values, value):
        if value not in values:
            values.append(value)
