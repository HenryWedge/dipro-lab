from typing import Iterator

from distributed_event_factory.event_factory import EventFactory
from distributed_event_factory.provider.data.constant_count_provider import ConstantCountProvider
from distributed_event_factory.provider.data.increasing_case import IncreasingCaseIdProvider
from distributed_event_factory.simulation.iterator import IteratorSimulation
from distributed_event_factory.topology.model.topology_spec import TopologySpec
from process_mining.datasource.datasource_interface import DataSource
from process_mining.domain.event import Event


class DistributedEventFactoryDataSource(DataSource):
    def __init__(self, topology_spec: TopologySpec, simulation_steps=100, max_concurrent_cases=1):
        factory = EventFactory()
        factory.add_topology("topology", topology_spec)
        factory.add_simulation(
            "iterator",
            IteratorSimulation(
                simulation_steps=simulation_steps,
                case_id_provider=IncreasingCaseIdProvider(),
                max_concurrent_cases=ConstantCountProvider(max_concurrent_cases),
            ),
        )
        self.events = [self._to_event(event) for event in factory.iter_events()]

    def next_event(self) -> Iterator[Event]:
        return iter(self.events)

    @staticmethod
    def _to_event(event) -> Event:
        return Event(
            case_id=event.caseid,
            activity=event.activity,
            location=event.node,
            time=event.timestamp,
            node_id=event.node,
        )
