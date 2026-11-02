from conformance.tbr.core.token_metrics import TokenMetrics
from runtime.core import DistributedAlgorithm, Network


class ConformanceAggregationParticipant(DistributedAlgorithm):

    def __init__(self, participant_id):
        self.participant_id = participant_id

    def set_network(self, network: Network):
        self.network = network

    def calculate_fitness(self, case_id):
        return sum(
            [self.network.call(participant_id).get_token_metrics_for_case(case_id)
             for participant_id in self.network.get_participant_ids()
             if participant_id not in {self.participant_id, "resolver"}],
            start=TokenMetrics()
        )
