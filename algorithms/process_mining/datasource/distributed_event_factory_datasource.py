from typing import Iterable, Iterator

from distributed_event_factory.event_factory import EventFactory
from process_mining.datasource.datasource_interface import DataSource
from process_mining.domain.event import Event


class DistributedEventFactoryDataSource(DataSource):
    def __init__(self):
        factory = EventFactory()
        factory.add_file("/home/here/UNI/Repo/dipro-lab/def/config/simulation/iterator.yaml")
        factory.add_directory("/home/here/UNI/Repo/dipro-lab/def/config/datasource/assemblyline")
        self.events = [self._to_event(event) for event in factory.iter_events()]
        self.event_iterator = iter(self.events)

    def next_event(self) -> Iterator[Event]:
        return self.event_iterator

    def reset(self):
        self.event_iterator = iter(self.events)

    @staticmethod
    def _to_event(event) -> Event:
        return Event(
            case_id=event.caseid,
            activity=event.activity,
            location=event.node,
            time=event.timestamp,
            node_id=event.node,
        )
