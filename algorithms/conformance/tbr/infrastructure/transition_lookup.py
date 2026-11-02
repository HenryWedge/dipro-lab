from pm4py.discovery import PetriNet

class TransitionLookup:
    def __init__(self, net: PetriNet):
        self.net = net
        self.transitions_by_label = self.index_labeled_transitions()

    def find_transition(self, activity):
        transitions = self.transitions_by_label.get(activity, [])
        if not transitions:
            return None
        return transitions[0]

    def find_transitions(self, activity):
        return list(self.transitions_by_label.get(activity, []))

    def ambiguous_labels(self):
        return {
            label: transitions
            for label, transitions in self.transitions_by_label.items()
            if len(transitions) > 1
        }

    def silent_transitions(self):
        return sorted(
            [transition for transition in self.net.transitions if transition.label is None],
            key=lambda transition: str(transition.name),
        )

    def index_labeled_transitions(self):
        transitions_by_label = {}
        for transition in self.net.transitions:
            if transition.label is None:
                continue
            transitions_by_label.setdefault(transition.label, []).append(transition)

        for transitions in transitions_by_label.values():
            transitions.sort(key=lambda transition: str(transition.name))
        return transitions_by_label
