from dataclasses import dataclass

from conformance.tbr.infrastructure.net_access import PetriNetAccess


@dataclass
class TransitionSpec:
    transition_id: str
    label: str | None
    input_places: list[str]
    output_places: list[str]

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
    def from_assignment(cls, discovered_model, participants, activity_owners, place_owners):
        access = PetriNetAccess(discovered_model)
        transitions = []
        transition_owners = {}
        for participant_id, participant in participants.items():
            for transition in participant.transitions:
                transition_id = str(transition.name)
                transition_owners[transition_id] = participant_id

        for transition in discovered_model.net.transitions:
            transitions.append(
                TransitionSpec(
                    transition_id=str(transition.name),
                    label=transition.label,
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

    def for_participant(self, participant_id):
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
        return TBRModel(
            transitions=relevant_transitions,
            place_owners=owned_places,
            activity_owners=self.activity_owners,
            transition_owners=self.transition_owners,
            initial_marking={
                place_id: amount
                for place_id, amount in self.initial_marking.items()
                if place_id in owned_places and owned_places[place_id][0] == participant_id
            },
            final_marking=self.final_marking,
        )
