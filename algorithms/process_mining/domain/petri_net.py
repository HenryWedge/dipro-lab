class DiscoveredPetriNet:
    def __init__(self, algorithm, parameters, net, initial_marking,
                 final_marking, ):
        self.algorithm = algorithm
        self.parameters = parameters
        self.net = net
        self.initial_marking = initial_marking
        self.final_marking = final_marking

    def places_count(self):
        return len(self.net.places)

    def transitions_count(self):
        return len(self.net.transitions)

    def arcs_count(self):
        return len(self.net.arcs)

    def labeled_transitions_count(self):
        return len([t for t in self.net.transitions if t.label is not None])

    def silent_transitions_count(self):
        return len([t for t in self.net.transitions if t.label is None])
