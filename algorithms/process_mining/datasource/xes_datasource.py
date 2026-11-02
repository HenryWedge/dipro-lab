from typing import Iterator

from conformance.tbr.infrastructure.splitter import EventLogSplitter
from process_mining.datasource.datasource_interface import DataSource
from process_mining.domain.event import Event


class XesDataSource(DataSource):
    def __init__(self, path=None, location_key=None, start_index=0, end_index=100) -> None:
        base_splitter = EventLogSplitter(
            file_path=str(path or "/home/here/UNI/Repo/bachelorarbeit/data/Sepsis.xes"),
            training_split=1.0,
            location_key=location_key or "org:group",
            random_seed="abc",
        )
        case_ids = base_splitter.log.case_ids()
        start_index = start_index
        end_index = end_index
        self.log = base_splitter.log.filter_case_ids(case_ids[start_index:end_index])

    def next_event(self) -> Iterator[Event]:
        for case_id, events in self.log.iter_traces():
            for event in events:
                yield event