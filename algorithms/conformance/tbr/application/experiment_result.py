from dataclasses import dataclass


@dataclass
class ExperimentResult:
    network_statistics: dict
    processed_events: int
    average_requests_per_event: float
    average_fitness: float
    silent_transitions: int
    transitions: int
    places: int

    def __str__(self):
        return "\n".join((
            f"{'-+' * 15} Results {'+-' * 15}",
            str(self.network_statistics),
            f"Processed Events: {self.processed_events}",
            f"Average requests per event: {self.average_requests_per_event}",
            f"Average fitness: {self.average_fitness}",
            f"Silent Transitions: {self.silent_transitions}",
            f"Transitions: {self.transitions}",
            f"Places: {self.places}",
        ))
