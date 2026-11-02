from runtime.core import NetworkClient


class LocalClient(NetworkClient):
    def __init__(self, participant):
        self.participant = participant

    def call(self):
        return self.participant

