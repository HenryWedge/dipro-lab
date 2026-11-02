from datetime import datetime, timedelta

from process_mining.adapters.pm4py.converter import Converter
from process_mining.domain.discovery import Discovery
from process_mining.domain.event import Event
from process_mining.domain.event_log import EventLog
from conformance.tbr.infrastructure.splitter import EventLogSplitter
from conformance.tbr.core.conformance_aggregation_participant import ConformanceAggregationParticipant
from conformance.tbr.assignment import ParticipantAssignment
from pm4py.visualization.petri_net import visualizer

from conformance.tbr.core.participant_service import TokenReplayParticipant
from conformance.tbr.core.place_resolver import PlaceResolveParticipant
from conformance.tbr.transport.wire import TBRModel
from runtime.local.local_network import LocalNetwork


def t(m):
    return datetime(2026,1,1) + timedelta(minutes=m)

training_log_silent_transition = EventLog({"c1":[
    Event("c1", "Start", "node-1", t(0)),
    Event("c1", "Review", "node-2", t(1)),
    Event("c1", "Approve", "node-1", t(2)),
    Event("c1", "Finish", "node-2", t(3))], "c2": [
    Event("c2", "Start", "node-1", t(4)),
    Event("c2", "Approve", "node-1", t(5)),
    Event("c2", "Finish", "node-2", t(6))
]})

test_log_silent_transition = EventLog({ "c3": [
    Event("c3", "Start", "node-1", t(7)),
    Event("c2", "Approve", "node-1", t(7.5)),
    Event("c3", "Finish", "node-2", t(8))]
})

training_log_place_with_two_owners = [
    ("c1", "Start", "node-1"),
    ("c1", "A", "node-2"),
    ("c1", "End", "node-4"),
    ("c2", "Start", "node-1"),
    ("c2", "B", "node-3"),
    ("c2", "End", "node-4"),
]

training_log_place_with_loop = [
    ("c1", "Start", "node-1"),
    ("c1", "A", "node-2"),
    ("c1", "A", "node-2"),
    ("c1", "A", "node-2"),
    ("c1", "B", "node-3"),
    ("c1", "End", "node-4"),
]

REPLAY_TRACE = (
    ("c3", "Start", "node-1"),
    ("c3", "B", "node-2"),
    ("c3", "End", "node-4"),
)

REPLAY_TRACE_with_loop = [
    ("c2", "Start", "node-1"),
    ("c2", "A", "node-2"),
    ("c2", "A", "node-2"),
    ("c2", "B", "node-3"),
    ("c2", "A", "node-2"),
    ("c2", "B", "node-3"),
    ("c2", "End", "node-4"),
]


class AlgorithmExecution:
    def run(self):
        base_splitter = EventLogSplitter(
            file_path=str("/home/here/UNI/Repo/bachelorarbeit/data/Sepsis.xes"),
            training_split=1.0,
            location_key="org:group",
            random_seed="abc",
        )
        case_ids = base_splitter.log.case_ids()
        training = base_splitter.log.filter_case_ids(case_ids[:100])
        #training = training_log_silent_transition
        test = base_splitter.log.filter_case_ids(case_ids[:100])
        #test = training
        #test = test_log_silent_transition

        event_log = training
        #discovered_model = Discovery().discover_heuristics(Converter().from_event_log(event_log), dependency_threshold=0.0)
        discovered_model = Discovery().discover_inductive(Converter().from_event_log(event_log))

        petri_net = visualizer.apply(
            discovered_model.net,
            discovered_model.initial_marking,
            discovered_model.final_marking
        )
        visualizer.view(petri_net)

        participant_transitions, activity_owners, place_owners = ParticipantAssignment(
            discovered_model,
            event_log,
        ).build()

        model = TBRModel.from_assignment(
            discovered_model,
            participant_transitions,
            activity_owners,
            place_owners,
        )

        network = LocalNetwork()
        #network = HttpNetwork()
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
        conformance_log = test
        i = 0
        for case_id, events in conformance_log.iter_traces():
            for event in events:
                i = i + 1
                if event.location not in network.get_participant_ids():
                    print("Location ", event.location, " not supported")
                else:
                    network.call(event.location).process_event(event)
                if i % 1 == 0:
                    fitness = network.call("aggregator").calculate_fitness(event.case_id)
                #print(fitness)
                #print(event)
                #print(network.statistics.results())
                #print(network.tracer.results(),"\n")
                #network.tracer.reset()
            network.call("resolver").end_trace(case_id)
            fitness_scores.append(network.call("aggregator").calculate_fitness(case_id))

        print("-+"*15, "Results", "+-"*15)
        network_result = network.statistics.results()
        print(network_result)
        processed_events = network_result.get('process_event')
        print("Processed Events: ", processed_events)
        print("Average requests per event: ", network_result.get('is_place_marked') / processed_events)
        print("Average fitness: ", sum([score.fitness() for score in fitness_scores]) / len(fitness_scores))
        print("Silent Transitions: ", discovered_model.silent_transitions_count())
        print("Transitions: ",discovered_model.transitions_count())
        print("Places: ",discovered_model.places_count())

if __name__ == '__main__':
    AlgorithmExecution().run()
