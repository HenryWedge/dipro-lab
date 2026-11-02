from conformance.tbr.data.petrinet import DiscoveredPetriNet


class PetriNetAccess:
    def __init__(self, discovered_model: DiscoveredPetriNet):
        self.model = discovered_model
        self.net = discovered_model.net

    def places(self):
        return list(self.net.places)

    def transitions(self):
        return list(self.net.transitions)

    def input_places(self, transition):
        return [arc.source for arc in transition.in_arcs]

    def output_places(self, transition):
        return [arc.target for arc in transition.out_arcs]

    def is_silent(self, transition):
        return transition.label is None
