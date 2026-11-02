from abc import ABC, abstractmethod
from typing import Iterator

from process_mining.domain.event import Event

class DataSource(ABC):

    @abstractmethod
    def next_event(self) -> Iterator[Event]:
        pass