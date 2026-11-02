from runtime.core import Runtime, Network
from runtime.local.local_client import LocalClient


class LocalRuntime(Runtime):
    def __init__(self, participant):
        self.participant = participant

    def start(self, network: Network) -> LocalClient:
        self.participant.set_network(network)
        return LocalClient(self.participant)

    def stop(self) -> None:
        pass
