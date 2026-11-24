from dataclasses import dataclass
from uuid import uuid4

from conformance.tbr.infrastructure.net_access import PetriNetAccess


@dataclass
class TransitionSpec:
    transition_id: str
    label: str | None
    is_silent: bool
    input_places: list[str]
    output_places: list[str]

@dataclass
class ParticipantTransitionSpec:
    transition_id: str
    is_silent: bool
    input_places: list[str]
    output_places: list[str]

@dataclass
class ParticipantTBRModel:
    transitions: list[ParticipantTransitionSpec]
    activity_transitions: dict[str, list[str]]
    silent_transition_ids: list[str]
    initial_marking: dict[str, int]

@dataclass
class SilentTransitionOption:
    handle: str
    input_places: list[str]

@dataclass
class IsMarkedResult:
    can_be_marked: bool
    pending_options: list[SilentTransitionOption]

@dataclass
class TBRModel:
    transitions: list[TransitionSpec]
    place_owners: dict[str, list[str]]
    activity_owners: dict[str, str]
    transition_owners: dict[str, str]
    initial_marking: dict[str, int]
    final_marking: dict[str, int]

    @classmethod
    def from_assignment(cls, discovered_model, participant_transitions, activity_owners, place_owners):
        access = PetriNetAccess(discovered_model)
        transitions = []
        transition_owners = {}
        transition_ids = {
            str(transition.name): str(uuid4())
            for transition in discovered_model.net.transitions
        }
        for participant_id, assigned_transitions in participant_transitions.items():
            for transition in assigned_transitions:
                transition_id = transition_ids[str(transition.name)]
                transition_owners[transition_id] = participant_id

        for transition in discovered_model.net.transitions:
            transition_id = transition_ids[str(transition.name)]
            transitions.append(
                TransitionSpec(
                    transition_id=transition_id,
                    label=transition.label,
                    is_silent=transition.label is None,
                    input_places=[str(place.name) for place in access.input_places(transition)],
                    output_places=[str(place.name) for place in access.output_places(transition)],
                )
            )

        return cls(
            transitions=transitions,
            place_owners={
                str(place.name): sorted(owner) if not isinstance(owner, str) else [owner]
                for place, owner in place_owners.items()
            },
            activity_owners=dict(activity_owners),
            transition_owners=transition_owners,
            initial_marking={
                str(place.name): amount
                for place, amount in discovered_model.initial_marking.items()
            },
            final_marking={
                str(place.name): amount
                for place, amount in discovered_model.final_marking.items()
            },
        )

    def for_participant(self, participant_id) -> ParticipantTBRModel:
        owned_places = {
            place_id: owners
            for place_id, owners in self.place_owners.items()
            if participant_id in owners
        }
        relevant_transitions = [
            transition
            for transition in self.transitions
            if self.transition_owners.get(transition.transition_id) == participant_id
            or set(transition.output_places) & set(owned_places)
        ]
        owned_transition_ids = {
            transition_id
            for transition_id, owner in self.transition_owners.items()
            if owner == participant_id
        }
        activity_transitions = {}
        for transition in relevant_transitions:
            if transition.transition_id in owned_transition_ids and transition.label is not None:
                activity_transitions.setdefault(transition.label, []).append(
                    transition.transition_id
                )

        return ParticipantTBRModel(
            transitions=[
                ParticipantTransitionSpec(
                    transition_id=transition.transition_id,
                    is_silent=transition.is_silent,
                    input_places=transition.input_places,
                    output_places=transition.output_places,
                )
                for transition in relevant_transitions
            ],
            activity_transitions=activity_transitions,
            silent_transition_ids=[
                transition.transition_id
                for transition in relevant_transitions
                if transition.transition_id in owned_transition_ids
                and transition.is_silent
            ],
            initial_marking={
                place_id: amount
                for place_id, amount in self.initial_marking.items()
                if place_id in owned_places and owned_places[place_id][0] == participant_id
            },
        )
