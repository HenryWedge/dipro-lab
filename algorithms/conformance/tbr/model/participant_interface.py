from abc import abstractmethod

from conformance.tbr.data.event import Event
from conformance.tbr.model.token_metrics import TokenMetrics
from conformance.tbr.model.wire import TBRModel, IsMarkedResult
from runtime.core import DistributedAlgorithm, operation


class PlaceOperations(DistributedAlgorithm):

    @operation()
    @abstractmethod
    def is_place_marked(self, case_id: str, place_id: str) -> IsMarkedResult:
        pass

    @operation()
    @abstractmethod
    def consume_place(
        self,
        case_id,
        place_id,
    ) -> None:
        pass


    @operation()
    @abstractmethod
    def fire_silent_transition(self, case_id: str, handle: str) -> None:
        pass


class TBRParticipant(PlaceOperations):

    @operation()
    @abstractmethod
    def install_model(self, model: TBRModel) -> None:
        pass

    @operation()
    @abstractmethod
    def process_event(self, event: Event):
        pass

    @operation()
    @abstractmethod
    def get_token_metrics_for_case(self, case_id) -> TokenMetrics:
        pass
