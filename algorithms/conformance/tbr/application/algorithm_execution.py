from conformance.tbr.application.experiment_result import ExperimentResult
from distributed_event_factory.event_factory import EventFactory
from process_mining.adapters.pm4py.converter import Converter
from process_mining.datasource.distributed_event_factory_datasource import DistributedEventFactoryDataSource
from process_mining.datasource.xes_datasource import XesDataSource
from process_mining.domain.discovery import Discovery
from conformance.tbr.core.conformance_aggregation_participant import ConformanceAggregationParticipant
from conformance.tbr.assignment import ParticipantAssignment
from pm4py.visualization.petri_net import visualizer

from conformance.tbr.core.participant_service import TokenReplayParticipant
from conformance.tbr.core.place_resolver import PlaceResolveParticipant
from conformance.tbr.transport.wire import TBRModel
from runtime.local.local_network import LocalNetwork

class AlgorithmExecution:
    def run(self):
        #datasource = DistributedEventFactoryDataSource()
        datasource = XesDataSource()

        network = LocalNetwork()
        # network = HttpNetwork()

        # discovered_model = Discovery().discover_heuristics(Converter().from_event_log(event_log), dependency_threshold=0.0)
        discovered_model = Discovery().discover_inductive(Converter().from_datasource(datasource))
        datasource.reset()
        petri_net = visualizer.apply(
            discovered_model.net,
            discovered_model.initial_marking,
            discovered_model.final_marking
        )
        visualizer.view(petri_net)

        participant_transitions, activity_owners, place_owners = ParticipantAssignment(
            discovered_model,
            datasource
        ).build()
        datasource.reset()

        model = TBRModel.from_assignment(
            discovered_model,
            participant_transitions,
            activity_owners,
            place_owners,
        )

        for participant_id in participant_transitions:
            network.add_runtime(
                participant_id,
                TokenReplayParticipant(participant_id)
            )

        network.add_runtime("resolver", PlaceResolveParticipant())
        network.add_runtime("aggregator", ConformanceAggregationParticipant("aggregator"))
        network.call("resolver").install_model(model.place_owners, model.final_marking)

        for participant_id in participant_transitions:
            network.call(participant_id).install_model(model.for_participant(participant_id))

        fitness_scores = []
        current_case_id = None
        for event in datasource.next_event():
            if current_case_id is not None and event.case_id != current_case_id:
                network.call("resolver").end_trace(current_case_id)
                fitness_scores.append(
                    network.call("aggregator").calculate_fitness(current_case_id)
                )

            current_case_id = event.case_id
            if event.location not in network.get_participant_ids():
                print("Location ", event.location, " not supported")
            else:
                network.call(event.location).process_event(event)

        if current_case_id is not None:
            network.call("resolver").end_trace(current_case_id)
            fitness_scores.append(
                network.call("aggregator").calculate_fitness(current_case_id)
            )

        network_result = network.statistics.results()
        processed_events = network_result.get("process_event", 0)
        average_requests_per_event = (
            network_result.get("is_place_marked", 0) / processed_events
            if processed_events
            else 0.0
        )

        return ExperimentResult(
            network_statistics=network_result,
            processed_events=processed_events,
            average_requests_per_event=average_requests_per_event,
            average_fitness=(
                sum(score.fitness() for score in fitness_scores) / len(fitness_scores)
                if fitness_scores
                else 0.0
            ),
            silent_transitions=discovered_model.silent_transitions_count(),
            transitions=discovered_model.transitions_count(),
            places=discovered_model.places_count(),
        )

if __name__ == '__main__':
    print(AlgorithmExecution().run())
